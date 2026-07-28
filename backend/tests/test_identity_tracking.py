from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import auth, chat_models, models
from app.database import Base, get_db
from app.identity_tracking.models import GuestClaim, SchemeActivity
from app.identity_tracking.router import router as identity_router
from app.identity_tracking.models import FeatureActivity
from app.identity_tracking.sync_service import sync_pending_identity_records
from app.checklists.enums import StorageOrigin
from app.checklists.storage import ChecklistStorage
from app.routers.auth import router as auth_router
from app.routers.checklist import router as checklist_router
from app.routers.grievance import router as grievance_router
from app.routers.faqs import router as faqs_router
from app.routers.schemes import router as schemes_router


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
test_app = FastAPI()
test_app.include_router(auth_router)
test_app.include_router(schemes_router)
test_app.include_router(identity_router)
test_app.include_router(checklist_router)
test_app.include_router(grievance_router)
test_app.include_router(faqs_router)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


test_app.dependency_overrides[get_db] = override_db


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSession() as db:
        db.add(
            models.Scheme(
                name="Existing Scheme",
                category="Food Security",
                state="All India",
                description="Existing master record",
            )
        )
        db.commit()


def create_user(email: str) -> tuple[int, str]:
    with TestingSession() as db:
        user = models.User(
            name="Citizen",
            email=email,
            hashed_password=auth.hash_password("Password@123"),
            preferred_language="en",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id, auth.create_access_token({"sub": str(user.id)})


def test_guest_id_is_created_and_reused():
    client = TestClient(test_app)
    first = client.post("/api/guest/session")
    second = client.post("/api/guest/session")
    assert first.status_code == 200
    assert first.json()["guest_session_id"] == second.json()["guest_session_id"]
    assert "HttpOnly" in first.headers["set-cookie"]


def test_guest_and_authenticated_scheme_activity_reuse_existing_scheme():
    guest = TestClient(test_app)
    assert guest.get("/schemes/1").status_code == 200
    user_id, token = create_user("scheme-user@example.com")
    authenticated = TestClient(test_app)
    assert authenticated.get(
        "/schemes/1", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 200
    with TestingSession() as db:
        rows = db.query(SchemeActivity).order_by(SchemeActivity.created_at).all()
        assert len(rows) == 2
        assert rows[0].guest_session_id
        assert rows[1].user_id == user_id
        assert db.query(models.Scheme).count() == 1
        assert db.query(models.Scheme).first().name == "Existing Scheme"


def test_login_claims_guest_activity_once_and_preserves_audit_id():
    user_id, _ = create_user("claim@example.com")
    client = TestClient(test_app)
    assert client.get("/schemes/1").status_code == 200
    login = client.post(
        "/auth/login",
        json={"email": "claim@example.com", "password": "Password@123"},
    )
    assert login.status_code == 200
    assert login.json()["guest_data_imported"] is True
    assert login.json()["migration"]["scheme_activities"] == 1
    with TestingSession() as db:
        activity = db.query(SchemeActivity).one()
        assert activity.user_id == user_id
        assert activity.guest_session_id
        assert activity.ownership_status == "claimed"
        assert db.query(GuestClaim).count() == 1

        summary = db.query(GuestClaim).one().summary_json
        assert summary["scheme_activities"] == 1


def test_registration_claims_guest_activity():
    client = TestClient(test_app)
    client.get("/schemes/1")
    response = client.post(
        "/auth/register",
        json={
            "name": "New Citizen",
            "email": "new@example.com",
            "password": "Password@123",
            "preferred_language": "hi",
        },
    )
    assert response.status_code == 200
    assert response.json()["migration"]["scheme_activities"] == 1


def test_claim_is_idempotent_and_cross_user_claim_is_blocked():
    first_id, first_token = create_user("first@example.com")
    _, second_token = create_user("second@example.com")
    client = TestClient(test_app)
    client.get("/schemes/1")
    guest_cookie = client.cookies.get("janmitra_guest")

    headers = {"Authorization": f"Bearer {first_token}"}
    first = client.post("/api/auth/claim-guest-data", headers=headers)
    assert first.status_code == 200

    replay = TestClient(test_app)
    replay.cookies.set("janmitra_guest", guest_cookie)
    repeated = replay.post("/api/auth/claim-guest-data", headers=headers)
    assert repeated.status_code == 200
    assert repeated.json()["migration"]["already_claimed"] is True

    attacker = TestClient(test_app)
    attacker.cookies.set("janmitra_guest", guest_cookie)
    blocked = attacker.post(
        "/api/auth/claim-guest-data",
        headers={"Authorization": f"Bearer {second_token}"},
    )
    assert blocked.status_code == 403
    with TestingSession() as db:
        assert db.query(GuestClaim).one().user_id == first_id


def test_history_is_paginated_and_owner_scoped():
    first_id, first_token = create_user("history-one@example.com")
    second_id, second_token = create_user("history-two@example.com")
    with TestingSession() as db:
        db.add_all(
            [
                SchemeActivity(
                    scheme_id=1,
                    user_id=first_id,
                    action_type="viewed",
                    storage_origin="sqlite",
                    sync_status="pending",
                ),
                SchemeActivity(
                    scheme_id=1,
                    user_id=second_id,
                    action_type="saved",
                    storage_origin="sqlite",
                    sync_status="pending",
                ),
            ]
        )
        db.commit()
    response = TestClient(test_app).get(
        "/api/me/history?feature=scheme&page=1&page_size=1",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["action"] == "viewed"


def test_public_scheme_routes_remain_accessible():
    client = TestClient(test_app)
    assert client.get("/schemes").status_code == 200
    result = client.post("/schemes/find", json={"state": "Delhi"})
    assert result.status_code == 200
    assert result.json()[0]["id"] == 1


def test_other_public_features_are_tracked_for_guest():
    client = TestClient(test_app)
    checklist = client.post(
        "/checklist/generate", json={"service_type": "new_ration_card"}
    )
    grievance = client.post(
        "/grievance/guide",
        json={"category": "ration", "description": "Card is delayed"},
    )
    assert checklist.status_code == 200
    assert grievance.status_code == 200
    with TestingSession() as db:
        assert {
            (row.feature, row.action_type)
            for row in db.query(FeatureActivity).all()
        } == {("checklist", "generated"), ("grievance", "guide_generated")}


def test_postgresql_unavailable_selects_sqlite_fallback():
    storage = ChecklistStorage(
        primary_url="",
        fallback_url="sqlite://",
        connect_timeout=1,
    )
    with storage.repository() as selection:
        assert selection.origin == StorageOrigin.SQLITE
        assert selection.sync_status.value == "pending"


def test_pending_identity_sync_is_idempotent():
    source_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    target_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(source_engine)
    Base.metadata.create_all(target_engine)
    Source = sessionmaker(bind=source_engine)
    Target = sessionmaker(bind=target_engine)
    with Source() as source, Target() as target:
        source.add(
            FeatureActivity(
                id="sync-record",
                feature="grievance",
                action_type="guide_generated",
                guest_session_id="6f59596e-cd3e-4f98-b6c4-b42e8c31d1b1",
                storage_origin="sqlite",
                sync_status="pending",
            )
        )
        source.commit()
        first = sync_pending_identity_records(source, target)
        target.commit()
        source.commit()
        second = sync_pending_identity_records(source, target)
        assert first.synced == 1
        assert second.examined == 0
        assert target.query(FeatureActivity).count() == 1


def test_frontend_mobile_registration_and_login_contract():
    client = TestClient(test_app)
    registration = client.post(
        "/auth/register",
        json={
            "full_name": "Mobile Citizen",
            "address": "Bhopal, Madhya Pradesh",
            "gender": "female",
            "pincode": "462001",
            "mobile": "9876543210",
            "password": "Password@123",
        },
    )
    assert registration.status_code == 200
    assert registration.json()["user"]["mobile"] == "9876543210"
    assert registration.json()["user"]["public_id"].startswith("PDS")

    login = client.post(
        "/auth/login",
        json={"mobile": "9876543210", "password": "Password@123"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_faq_route_and_category_filter():
    with TestingSession() as db:
        db.add_all(
            [
                models.FAQ(
                    question="Ration question",
                    answer="Ration answer",
                    category="ration",
                    language="en",
                ),
                models.FAQ(
                    question="Scheme question",
                    answer="Scheme answer",
                    category="scheme",
                    language="en",
                ),
            ]
        )
        db.commit()
    client = TestClient(test_app)
    all_rows = client.get("/faqs")
    ration_rows = client.get("/faqs?category=ration")
    assert all_rows.status_code == 200
    assert len(all_rows.json()) == 2
    assert [row["category"] for row in ration_rows.json()] == ["ration"]
