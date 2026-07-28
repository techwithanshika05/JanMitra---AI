from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.auth import create_access_token
from app.checklists.enums import StorageOrigin, SyncStatus
from app.checklists.router import (
    get_checklist_knowledge_service,
    get_checklist_selection,
    router,
)
from app.checklists.schemas import (
    ChecklistCreate,
    ChecklistRefresh,
    ChecklistSourceItem,
)
from app.checklists.sqlalchemy_repository import SQLAlchemyChecklistRepository
from app.checklists.storage import ChecklistStorageSelection
from app.database import Base
from app.database import get_db


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
route_test_app = FastAPI()
route_test_app.include_router(router)


class RouteKnowledgeStub:
    def build(self, request):
        return ChecklistCreate(
            service_id=request.service_id,
            service_name=request.service_name,
            language=request.language,
            source_version="rag-v1",
            source_citations=[
                {"title": "official-guidelines.pdf", "snippet": "Checklist", "score": 0.9}
            ],
            items=[
                ChecklistSourceItem(
                    item_type="document",
                    title="Identity proof",
                    description="Official requirement",
                    sequence_number=1,
                    is_required=True,
                    source_item_key="document:identity",
                ),
                ChecklistSourceItem(
                    item_type="process_step",
                    title="Submit application",
                    description="Submit through the official channel",
                    sequence_number=2,
                    is_required=True,
                    source_item_key="step:submit",
                ),
            ],
        )

    def refresh_payload(self, request):
        return ChecklistRefresh(
            source_version="rag-v2",
            source_citations=[
                {"title": "official-guidelines.pdf", "snippet": "Updated", "score": 0.91}
            ],
            items=[
                ChecklistSourceItem(
                    item_type="document",
                    title="Updated identity proof",
                    description="Updated official requirement",
                    sequence_number=1,
                    is_required=True,
                    source_item_key="document:identity",
                ),
                ChecklistSourceItem(
                    item_type="warning",
                    title="Use official portal",
                    sequence_number=2,
                    is_required=False,
                    source_item_key="warning:official-portal",
                ),
            ],
        )


def override_selection():
    db = TestingSession()
    try:
        yield ChecklistStorageSelection(
            origin=StorageOrigin.SQLITE,
            sync_status=SyncStatus.PENDING,
            repository=SQLAlchemyChecklistRepository(db),
        )
    finally:
        db.close()


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


route_test_app.dependency_overrides[get_checklist_selection] = override_selection
route_test_app.dependency_overrides[get_checklist_knowledge_service] = RouteKnowledgeStub
route_test_app.dependency_overrides[get_db] = override_db


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def checklist_payload():
    return {
        "service_id": "new_ration_card",
        "service_name": "New ration card",
        "language": "en",
    }


def create_user(email: str = "checklists@example.com", role: str = "citizen"):
    db = TestingSession()
    user = models.User(
        name="Checklist User", email=email, hashed_password="unused", role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    user_id = user.id
    db.close()
    return user_id, token


def test_guest_create_list_detail_update_archive_restore_delete():
    client = TestClient(route_test_app)
    created = client.post("/api/checklists", json=checklist_payload())
    assert created.status_code == 201
    body = created.json()
    assert body["storage_mode"] == "sqlite"
    assert body["sync_status"] == "pending"
    checklist_id = body["checklist"]["id"]
    item_id = body["checklist"]["items"][0]["id"]
    assert "janmitra_guest" in client.cookies

    assert len(client.get("/api/checklists").json()["checklists"]) == 1
    assert client.get(f"/api/checklists/{checklist_id}").status_code == 200

    updated = client.patch(
        f"/api/checklists/{checklist_id}/items/{item_id}",
        json={"is_completed": True, "user_note": "Submitted at the office."},
    )
    assert updated.status_code == 200
    assert updated.json()["checklist"]["progress_percentage"] == 50

    archived = client.post(f"/api/checklists/{checklist_id}/archive")
    assert archived.json()["checklist"]["status"] == "archived"
    assert client.get("/api/checklists").json()["checklists"] == []
    assert len(client.get("/api/checklists?archived=true").json()["checklists"]) == 1

    restored = client.post(f"/api/checklists/{checklist_id}/restore")
    assert restored.json()["checklist"]["status"] == "in_progress"
    assert client.delete(f"/api/checklists/{checklist_id}").status_code == 204
    assert client.get(f"/api/checklists/{checklist_id}").status_code == 404


def test_owner_isolation_returns_not_found():
    owner = TestClient(route_test_app)
    outsider = TestClient(route_test_app)
    checklist_id = owner.post("/api/checklists", json=checklist_payload()).json()[
        "checklist"
    ]["id"]
    assert outsider.get(f"/api/checklists/{checklist_id}").status_code == 404
    assert outsider.patch(
        f"/api/checklists/{checklist_id}", json={"language": "hi"}
    ).status_code == 404


def test_sensitive_note_returns_validation_error():
    client = TestClient(route_test_app)
    checklist = client.post("/api/checklists", json=checklist_payload()).json()["checklist"]
    response = client.patch(
        f"/api/checklists/{checklist['id']}/items/{checklist['items'][0]['id']}",
        json={"user_note": "OTP: 123456"},
    )
    assert response.status_code == 422
    assert "OTPs" in response.json()["detail"]


def test_create_rejects_client_supplied_official_items():
    client = TestClient(route_test_app)
    payload = checklist_payload()
    payload["items"] = [
        {
            "item_type": "document",
            "title": "Client invented requirement",
            "sequence_number": 1,
            "source_item_key": "invented",
        }
    ]
    response = client.post("/api/checklists", json=payload)
    assert response.status_code == 422


def test_authenticated_checklist_uses_user_owner():
    user_id, token = create_user()
    client = TestClient(route_test_app, headers={"Authorization": f"Bearer {token}"})
    response = client.post("/api/checklists", json=checklist_payload())
    assert response.status_code == 201
    assert response.json()["checklist"]["user_id"] == user_id
    assert response.json()["checklist"]["guest_session_id"] is None


def test_guest_import_requires_login_and_explicit_approval():
    client = TestClient(route_test_app)
    checklist_id = client.post("/api/checklists", json=checklist_payload()).json()[
        "checklist"
    ]["id"]
    assert client.post(
        "/api/checklists/import-guest", json={"approved": True}
    ).status_code == 401

    user_id, token = create_user("import@example.com")
    client.headers["Authorization"] = f"Bearer {token}"
    assert client.post(
        "/api/checklists/import-guest", json={"approved": False}
    ).status_code == 403
    imported = client.post(
        "/api/checklists/import-guest", json={"approved": True}
    )
    assert imported.status_code == 200
    assert imported.json()["imported_count"] == 1

    detail = client.get(f"/api/checklists/{checklist_id}").json()["checklist"]
    assert detail["user_id"] == user_id
    assert detail["guest_session_id"] is None


def test_refresh_returns_source_change_summary():
    client = TestClient(route_test_app)
    checklist = client.post("/api/checklists", json=checklist_payload()).json()["checklist"]
    response = client.post(
        f"/api/checklists/{checklist['id']}/refresh",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_version_changed"] is True
    assert body["new_items"] == 1
    assert body["changed_items"] == 1
    assert body["removed_items"] == 1
    assert body["checklist"]["status"] == "outdated"


def test_guidance_uses_progress_and_requires_reminder_consent():
    client = TestClient(route_test_app)
    checklist = client.post("/api/checklists", json=checklist_payload()).json()["checklist"]
    item_id = checklist["items"][0]["id"]
    client.patch(
        f"/api/checklists/{checklist['id']}/items/{item_id}",
        json={"is_completed": True},
    )

    without_consent = client.get(
        f"/api/checklists/{checklist['id']}/guidance"
    ).json()
    assert without_consent["reminders"] == []
    assert without_consent["next_steps"] == ["Submit application"]

    with_consent = client.get(
        f"/api/checklists/{checklist['id']}/guidance?reminders_consented=true"
    ).json()
    assert len(with_consent["reminders"]) == 1


def test_admin_analytics_are_protected_and_aggregate():
    citizen_id, citizen_token = create_user("citizen-analytics@example.com")
    citizen = TestClient(
        route_test_app, headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert citizen.post("/api/checklists", json=checklist_payload()).status_code == 201
    assert citizen.get("/api/checklists/admin/analytics").status_code == 403

    _admin_id, admin_token = create_user("admin-analytics@example.com", role="admin")
    admin = TestClient(
        route_test_app, headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = admin.get("/api/checklists/admin/analytics")
    assert response.status_code == 200
    body = response.json()
    assert body["total_checklists"] == 1
    assert body["most_saved_checklists"][0]["count"] == 1
    assert "user_id" not in body
