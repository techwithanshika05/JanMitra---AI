from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace

from app.conversational_ai.monitoring import health, worker_heartbeat


class FakeDatabase:
    bind = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))

    def execute(self, _statement):
        return None


def _settings():
    return SimpleNamespace(
        livekit_ready=True,
        sarvam_ready=True,
        agent_name="janmitra-scheme-agent",
        stt_model="saaras:v3",
        tts_model="bulbul:v3",
        llm_model="sarvam-105b",
        default_language="hi-IN",
    )


def test_health_is_degraded_without_registered_worker(monkeypatch, tmp_path):
    monkeypatch.setattr(worker_heartbeat, "HEARTBEAT_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(health, "voice_settings", _settings())

    result = health.health_snapshot(FakeDatabase())

    assert result["status"] == "degraded"
    assert result["details"]["worker"]["status"] == "offline"


def test_health_is_ready_with_fresh_registered_worker(monkeypatch, tmp_path):
    path = tmp_path / "heartbeat.json"
    path.write_text(json.dumps({
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "worker_id": "AW_test",
        "agent_name": "janmitra-scheme-agent",
        "region": "India South",
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }), encoding="utf-8")
    monkeypatch.setattr(worker_heartbeat, "HEARTBEAT_PATH", path)
    monkeypatch.setattr(health, "voice_settings", _settings())

    result = health.health_snapshot(FakeDatabase())

    assert result["status"] == "ready"
    assert result["details"]["worker"]["worker_id"] == "AW_test"


def test_stale_worker_heartbeat_is_not_ready(monkeypatch, tmp_path):
    path = tmp_path / "heartbeat.json"
    path.write_text(json.dumps({
        "last_seen": (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),
        "worker_id": "AW_stale",
    }), encoding="utf-8")
    monkeypatch.setattr(worker_heartbeat, "HEARTBEAT_PATH", path)

    result = worker_heartbeat.worker_heartbeat_status(max_age_seconds=20)

    assert result["status"] == "stale"
