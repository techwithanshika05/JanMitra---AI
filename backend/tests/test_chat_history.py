import sys
from types import ModuleType

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Persistence tests do not load embeddings. Stub the heavyweight retriever
# before importing the application so these tests remain deterministic.
retriever_module = ModuleType("app.rag.retriever")


class StubRetriever:
    def query(self, _message):
        return []


retriever_module.retriever = StubRetriever()
sys.modules["app.rag.retriever"] = retriever_module

from app import chat_models, models
from app.auth import create_access_token
from app.database import Base, get_db
from app.main import app
from app.routers import chat_history


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_cors_accepts_local_development_port():
    response = TestClient(app).options(
        "/api/chat/sessions",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"


def fake_generate(message: str, language: str):
    return {
        "answer": "Eligibility information\nApplicants must provide identity proof.\n1. Collect documents\n2. Submit the application",
        "confidence": 0.9,
        "is_grounded": True,
        "disclaimer": "",
        "sources": [],
    }


def fake_generate_with_visual(message: str, language: str):
    return {
        **fake_generate(message, language),
        "retrieved_images": [{
            "url": "/api/chat/visual-evidence/retrieved_visuals/allocation.png",
            "layout": "chart",
            "title": "Total foodgrain allocations",
            "source_file": "foodgrain.pdf",
            "page_number": 6,
        }],
    }


def create_user(email: str = "citizen@example.com") -> tuple[int, str]:
    db = TestingSession()
    user = models.User(name="Citizen", email=email, hashed_password="unused")
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    user_id = user.id
    db.close()
    return user_id, token


def test_guest_session_cookie_and_ownership():
    first = TestClient(app)
    second = TestClient(app)
    created = first.post("/api/chat/sessions", json={})
    assert created.status_code == 201
    assert "janmitra_guest" in first.cookies
    session_id = created.json()["id"]
    assert first.get(f"/api/chat/sessions/{session_id}").status_code == 200
    assert second.get(f"/api/chat/sessions/{session_id}").status_code == 404


def test_signed_in_session_uses_verified_token():
    user_id, token = create_user()
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    response = client.post("/api/chat/sessions", json={"title": "Benefits"})
    assert response.status_code == 201
    db = TestingSession()
    row = db.get(chat_models.ChatSession, response.json()["id"])
    assert row.user_id == user_id
    assert row.guest_id is None
    db.close()


def test_message_persistence_idempotency_and_faq(monkeypatch):
    monkeypatch.setattr(chat_history, "_generate", fake_generate)
    client = TestClient(app)
    session_id = client.post("/api/chat/sessions", json={}).json()["id"]
    payload = {
        "message": "How do I apply?",
        "language": "en",
        "client_message_id": "client-message-0001",
    }
    first = client.post(f"/api/chat/sessions/{session_id}/messages", json=payload)
    second = client.post(f"/api/chat/sessions/{session_id}/messages", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["assistant_message"]["response_type"] == "faq"
    detail = client.get(f"/api/chat/sessions/{session_id}").json()
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["content"] == payload["message"]


def test_visual_evidence_is_persisted_with_assistant_message(monkeypatch):
    monkeypatch.setattr(chat_history, "_generate", fake_generate_with_visual)
    client = TestClient(app)
    session_id = client.post("/api/chat/sessions", json={}).json()["id"]
    sent = client.post(
        f"/api/chat/sessions/{session_id}/messages",
        json={
            "message": "Show the allocation chart",
            "language": "en",
            "client_message_id": "visual-message-0001",
        },
    )
    assert sent.status_code == 201
    visual = sent.json()["assistant_message"]["structured_content"]["visual_evidence"][0]
    assert visual["layout"] == "chart"
    assert visual["page_number"] == 6


def test_visual_evidence_endpoint_serves_only_images_under_data_root(
    monkeypatch, tmp_path
):
    visual_root = tmp_path / "data"
    image = visual_root / "retrieved_visuals" / "allocation.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    (visual_root / "private.txt").write_text("not public", encoding="utf-8")
    monkeypatch.setattr(chat_history, "VISUAL_DATA_ROOT", visual_root.resolve())

    client = TestClient(app)
    served = client.get("/api/chat/visual-evidence/retrieved_visuals/allocation.png")
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/png"
    assert client.get("/api/chat/visual-evidence/private.txt").status_code == 404
    assert client.get("/api/chat/visual-evidence/../private.txt").status_code == 404


def test_feedback_create_update_validation_and_ownership(monkeypatch):
    monkeypatch.setattr(chat_history, "_generate", fake_generate)
    owner = TestClient(app)
    outsider = TestClient(app)
    session_id = owner.post("/api/chat/sessions", json={}).json()["id"]
    sent = owner.post(
        f"/api/chat/sessions/{session_id}/messages",
        json={"message": "Eligibility?", "language": "en", "client_message_id": "feedback-msg-001"},
    ).json()
    message_id = sent["assistant_message"]["id"]
    assert owner.post(
        f"/api/chat/messages/{message_id}/feedback",
        json={"reaction": "like", "rating": 5, "feedback_text": "Useful"},
    ).status_code == 200
    updated = owner.post(
        f"/api/chat/messages/{message_id}/feedback",
        json={"reaction": "dislike", "rating": 2, "feedback_text": "Needs detail"},
    )
    assert updated.json()["rating"] == 2
    assert owner.post(
        f"/api/chat/messages/{message_id}/feedback",
        json={"reaction": "like", "rating": 6},
    ).status_code == 422
    assert outsider.get(f"/api/chat/messages/{message_id}/feedback").status_code == 404


def test_guest_migration_is_transactional_and_idempotent(monkeypatch):
    monkeypatch.setattr(chat_history, "_generate", fake_generate)
    client = TestClient(app)
    session_id = client.post("/api/chat/sessions", json={}).json()["id"]
    sent = client.post(
        f"/api/chat/sessions/{session_id}/messages",
        json={"message": "Documents?", "language": "hi", "client_message_id": "migration-msg-01"},
    ).json()
    message_id = sent["assistant_message"]["id"]
    client.post(
        f"/api/chat/messages/{message_id}/feedback",
        json={"reaction": "like", "rating": 4},
    )
    user_id, token = create_user("migrate@example.com")
    client.headers["Authorization"] = f"Bearer {token}"
    first = client.post("/api/chat/migrate-guest")
    second = client.post("/api/chat/migrate-guest")
    assert first.status_code == 200
    assert first.json()["migrated_sessions"] == 1
    assert second.json()["already_migrated"] is True
    db = TestingSession()
    session = db.get(chat_models.ChatSession, session_id)
    assert session.user_id == user_id and session.guest_id is None
    assert db.query(chat_models.ChatMessage).filter_by(session_id=session_id).count() == 2
    db.close()


def test_soft_delete_hides_session():
    client = TestClient(app)
    session_id = client.post("/api/chat/sessions", json={}).json()["id"]
    assert client.delete(f"/api/chat/sessions/{session_id}").status_code == 204
    assert client.get(f"/api/chat/sessions/{session_id}").status_code == 404
    assert client.get("/api/chat/sessions").json() == []
