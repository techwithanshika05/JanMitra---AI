from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from app.chat_identity import ChatIdentity
from app.conversational_ai.persistence.models import VoiceEvent, VoiceSession, VoiceTurn, VoiceTurnSource


def storage_fields(db: Session) -> dict[str, str]:
    sqlite = bool(db.bind and db.bind.dialect.name == "sqlite")
    return {"storage_origin": "sqlite" if sqlite else "postgresql", "sync_status": "pending" if sqlite else "synced"}


class VoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _owner(model, identity: ChatIdentity):
        return model.user_id == identity.user_id if identity.user_id is not None else model.guest_session_id == identity.guest_id

    def create_session(self, identity: ChatIdentity, room_name: str, language: str) -> VoiceSession:
        row = VoiceSession(
            room_name=room_name, user_id=identity.user_id, guest_session_id=identity.guest_id,
            default_language=language, current_language=language, **storage_fields(self.db),
        )
        self.db.add(row)
        self.db.flush()
        self.add_event(row.id, "call_created", {"language": language})
        return row

    def owned_session(self, session_id: str, identity: ChatIdentity, *, with_turns: bool = False) -> VoiceSession | None:
        query = self.db.query(VoiceSession).filter(VoiceSession.id == session_id, self._owner(VoiceSession, identity))
        if with_turns:
            query = query.options(selectinload(VoiceSession.turns).selectinload(VoiceTurn.sources))
        return query.first()

    def list_owned(self, identity: ChatIdentity, page: int, page_size: int) -> tuple[int, list[VoiceSession]]:
        query = self.db.query(VoiceSession).filter(self._owner(VoiceSession, identity))
        total = query.count()
        rows = query.order_by(VoiceSession.started_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return total, rows

    def add_turn(self, session_id: str, *, speaker: str, text: str, language: str, intent: str | None = None,
                 answer_mode: str | None = None, evidence_status: str | None = None,
                 confidence: float | None = None, latency_ms: int | None = None,
                 sources: list[dict] | None = None) -> VoiceTurn:
        session = self.db.query(VoiceSession).filter(VoiceSession.id == session_id).with_for_update().one()
        session.total_turns += 1
        if intent and not session.primary_intent:
            session.primary_intent = intent
        turn = VoiceTurn(
            session_id=session_id, turn_number=session.total_turns, speaker=speaker,
            original_text=text, normalized_text=" ".join(text.split()), language_code=language,
            intent=intent, answer_mode=answer_mode, evidence_status=evidence_status,
            confidence_score=confidence, latency_ms=latency_ms,
        )
        self.db.add(turn)
        self.db.flush()
        for source in sources or []:
            self.db.add(VoiceTurnSource(
                turn_id=turn.id, document_id=source.get("document_id"), chunk_id=source.get("chunk_id"),
                source_title=source.get("title", "Government document"), source_section=source.get("section"),
                snippet=source.get("snippet"), retrieval_score=source.get("score"), source_version=source.get("version"),
            ))
        return turn

    def add_event(self, session_id: str, event_type: str, data: dict | None = None) -> VoiceEvent:
        row = VoiceEvent(session_id=session_id, event_type=event_type, event_data=data)
        self.db.add(row)
        return row

    def end(self, row: VoiceSession, reason: str) -> VoiceSession:
        now = datetime.utcnow()
        row.status = "ended"
        row.ended_at = now
        row.duration_seconds = max(0, int((now - row.started_at).total_seconds()))
        self.add_event(row.id, "call_ended", {"reason": reason})
        return row
