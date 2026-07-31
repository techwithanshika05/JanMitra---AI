"""Local heartbeat written only after LiveKit confirms worker registration."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any


HEARTBEAT_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "runtime"
    / "voice-worker-heartbeat.json"
)
HEARTBEAT_INTERVAL_SECONDS = 5.0
HEARTBEAT_MAX_AGE_SECONDS = 20.0

_state_lock = Lock()
_heartbeat_stop = Event()
_heartbeat_thread: Thread | None = None
_worker_state: dict[str, Any] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _write_heartbeat() -> None:
    with _state_lock:
        payload = {
            **_worker_state,
            "pid": os.getpid(),
            "last_seen": _utc_now().isoformat(),
        }
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = HEARTBEAT_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    temporary.replace(HEARTBEAT_PATH)


def _heartbeat_loop() -> None:
    while not _heartbeat_stop.wait(HEARTBEAT_INTERVAL_SECONDS):
        try:
            _write_heartbeat()
        except OSError:
            # Worker registration must not fail because local health reporting
            # is temporarily unwritable.
            continue


def record_worker_registration(
    worker_id: str,
    *,
    agent_name: str,
    region: str = "",
) -> None:
    """Mark a worker live after the SDK emits ``worker_registered``."""
    global _heartbeat_thread
    with _state_lock:
        _worker_state.update({
            "worker_id": worker_id,
            "agent_name": agent_name,
            "region": region,
            "registered_at": _utc_now().isoformat(),
        })
    _write_heartbeat()
    if _heartbeat_thread is None or not _heartbeat_thread.is_alive():
        _heartbeat_thread = Thread(
            target=_heartbeat_loop,
            name="voice-worker-heartbeat",
            daemon=True,
        )
        _heartbeat_thread.start()


def worker_heartbeat_status(
    *,
    max_age_seconds: float = HEARTBEAT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    """Return registration freshness without contacting LiveKit on each health check."""
    try:
        payload = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        last_seen = datetime.fromisoformat(str(payload["last_seen"]))
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        age_seconds = max(0.0, (_utc_now() - last_seen).total_seconds())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {"status": "offline", "age_seconds": None}

    return {
        "status": "ready" if age_seconds <= max_age_seconds else "stale",
        "age_seconds": round(age_seconds, 1),
        "worker_id": payload.get("worker_id"),
        "agent_name": payload.get("agent_name"),
        "region": payload.get("region"),
        "registered_at": payload.get("registered_at"),
    }
