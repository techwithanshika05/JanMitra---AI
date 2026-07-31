from sqlalchemy import text
from sqlalchemy.orm import Session

from app.conversational_ai.config import voice_settings
from app.conversational_ai.monitoring.worker_heartbeat import worker_heartbeat_status


def health_snapshot(db: Session) -> dict:
    database = "unavailable"
    try:
        db.execute(text("SELECT 1"))
        database = db.bind.dialect.name if db.bind else "unknown"
    except Exception:
        pass
    worker = worker_heartbeat_status()
    configured = voice_settings.livekit_ready and voice_settings.sarvam_ready
    return {
        "status": "ready" if configured and worker["status"] == "ready" else "degraded",
        "livekit_configured": voice_settings.livekit_ready,
        "sarvam_configured": voice_settings.sarvam_ready,
        "database": database,
        "rag": "configured",
        "agent_name": voice_settings.agent_name,
        "models": {"stt": voice_settings.stt_model, "tts": voice_settings.tts_model, "llm": voice_settings.llm_model},
        "details": {
            "default_language": voice_settings.default_language,
            "worker": worker,
        },
    }
