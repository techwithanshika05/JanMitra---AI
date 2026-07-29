from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.routers import schemes


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
app = FastAPI()
app.include_router(schemes.router)


def override_db():
    with TestingSession() as db:
        yield db


app.dependency_overrides[get_db] = override_db


class FakeRAG:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def answer(self, question, language):
        self.calls += 1
        return self.result


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_database_match_wins_without_rag(monkeypatch):
    fake = FakeRAG({})
    monkeypatch.setattr(schemes, "rag_adapter", fake)
    with TestingSession() as db:
        db.add(
            models.Scheme(
                name="Farmer Support",
                category="Farmer Welfare",
                state="All India",
                occupation="farmer",
            )
        )
        db.commit()

    response = TestClient(app).post(
        "/schemes/find-hybrid", json={"occupation": "farmer"}
    )

    assert response.status_code == 200
    assert response.json()["result_source"] == "database"
    assert response.json()["schemes"][0]["name"] == "Farmer Support"
    assert fake.calls == 0


def test_grounded_rag_is_used_when_database_has_no_match(monkeypatch):
    fake = FakeRAG(
        {
            "answer": "A verified scheme may match this profile.",
            "confidence": 0.82,
            "is_grounded": True,
            "sources": [
                {"title": "scheme.pdf", "snippet": "Verified text", "score": 0.82}
            ],
        }
    )
    monkeypatch.setattr(schemes, "rag_adapter", fake)

    response = TestClient(app).post(
        "/schemes/find-hybrid", json={"category": "Health"}
    )

    assert response.status_code == 200
    assert response.json()["result_source"] == "rag"
    assert response.json()["rag_result"]["sources"][0]["title"] == "scheme.pdf"


def test_polite_alert_when_database_and_rag_have_no_result(monkeypatch):
    monkeypatch.setattr(
        schemes,
        "rag_adapter",
        FakeRAG(
            {
                "answer": "No evidence",
                "confidence": 0.0,
                "is_grounded": False,
                "sources": [],
            }
        ),
    )

    response = TestClient(app).post(
        "/schemes/find-hybrid", json={"category": "Unknown"}
    )

    assert response.status_code == 200
    assert response.json()["result_source"] == "none"
    assert "could not find a verified matching scheme" in response.json()["alert"]


def test_zero_confidence_sources_are_not_presented_as_verified(monkeypatch):
    monkeypatch.setattr(
        schemes,
        "rag_adapter",
        FakeRAG(
            {
                "answer": "Unverified generated answer",
                "confidence": 0.0,
                "is_grounded": True,
                "sources": [
                    {"title": "scheme.pdf", "snippet": "", "score": 0.0}
                ],
            }
        ),
    )

    response = TestClient(app).post(
        "/schemes/find-hybrid", json={"category": "Unknown"}
    )

    assert response.status_code == 200
    assert response.json()["result_source"] == "none"
    assert response.json()["rag_result"] is None


def test_rag_timeout_returns_polite_alert(monkeypatch):
    class TimedOutFuture:
        def result(self, timeout):
            raise schemes.FutureTimeout()

        def cancel(self):
            return True

    monkeypatch.setattr(
        schemes._rag_executor, "submit", lambda *args, **kwargs: TimedOutFuture()
    )

    response = TestClient(app).post(
        "/schemes/find-hybrid", json={"category": "Unknown"}
    )

    assert response.status_code == 200
    assert response.json()["result_source"] == "none"
    assert "could not find a verified matching scheme" in response.json()["alert"]
