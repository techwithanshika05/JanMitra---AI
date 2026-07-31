from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.routers.admin import router as admin_router
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
test_app = FastAPI()
test_app.include_router(auth_router)
test_app.include_router(admin_router)
test_app.include_router(analytics_router)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


test_app.dependency_overrides[get_db] = override_db
client = TestClient(test_app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_admin_analytics_require_authentication():
    assert client.get("/admin/summary").status_code == 401
    assert client.get("/analytics/events-by-type").status_code == 401


def test_fixed_admin_login_rejects_invalid_credentials():
    response = client.post(
        "/auth/admin-login",
        json={"email": "wrong@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_fixed_admin_login_creates_single_admin_and_unlocks_analytics():
    from app.config import settings

    payload = {"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD}
    first = client.post("/auth/admin-login", json=payload)
    second = client.post("/auth/admin-login", json=payload)

    assert first.status_code == 200
    assert first.json()["user"]["role"] == "admin"
    assert second.status_code == 200

    with TestingSession() as db:
        assert db.query(models.User).filter(models.User.role == "admin").count() == 1

    token = first.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/admin/summary", headers=headers).status_code == 200
    assert client.get("/analytics/events-by-type", headers=headers).status_code == 200
