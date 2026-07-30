from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Index,
    Integer, JSON, String, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    room_name = Column(String(160), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_session_id = Column(String(36), nullable=True, index=True)
    claimed_guest_session_id = Column(String(36), nullable=True, index=True)
    ownership_status = Column(String(16), default="active", nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    status = Column(String(24), default="created", nullable=False, index=True)
    default_language = Column(String(16), default="hi-IN", nullable=False)
    current_language = Column(String(16), default="hi-IN", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    total_turns = Column(Integer, default=0, nullable=False)
    summary = Column(Text, nullable=True)
    primary_intent = Column(String(80), nullable=True)
    fallback_mode = Column(String(40), nullable=True)
    storage_origin = Column(String(16), nullable=False)
    sync_status = Column(String(16), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    turns = relationship("VoiceTurn", back_populates="session", cascade="all, delete-orphan", order_by="VoiceTurn.turn_number")
    events = relationship("VoiceEvent", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("user_id IS NOT NULL OR guest_session_id IS NOT NULL", name="ck_voice_session_has_owner"),
        Index("ix_voice_session_user_started", "user_id", "started_at"),
        Index("ix_voice_session_guest_started", "guest_session_id", "started_at"),
    )


class VoiceTurn(Base):
    __tablename__ = "voice_turns"

    id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(String(36), ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)
    speaker = Column(String(16), nullable=False)
    original_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=True)
    language_code = Column(String(16), nullable=False)
    intent = Column(String(80), nullable=True, index=True)
    answer_mode = Column(String(40), nullable=True)
    evidence_status = Column(String(40), nullable=True)
    confidence_score = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    interrupted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("VoiceSession", back_populates="turns")
    sources = relationship("VoiceTurnSource", back_populates="turn", cascade="all, delete-orphan")
    tool_calls = relationship("VoiceToolCall", back_populates="turn", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_voice_turn_session_number", "session_id", "turn_number", unique=True),)


class VoiceTurnSource(Base):
    __tablename__ = "voice_turn_sources"

    id = Column(String(36), primary_key=True, default=new_uuid)
    turn_id = Column(String(36), ForeignKey("voice_turns.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(160), nullable=True)
    chunk_id = Column(String(160), nullable=True)
    source_title = Column(String(500), nullable=False)
    source_section = Column(String(500), nullable=True)
    snippet = Column(Text, nullable=True)
    retrieval_score = Column(Float, nullable=True)
    source_version = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    turn = relationship("VoiceTurn", back_populates="sources")


class VoiceToolCall(Base):
    __tablename__ = "voice_tool_calls"

    id = Column(String(36), primary_key=True, default=new_uuid)
    turn_id = Column(String(36), ForeignKey("voice_turns.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(80), nullable=False)
    request_json = Column(JSON, nullable=True)
    result_summary = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    error_code = Column(String(80), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    turn = relationship("VoiceTurn", back_populates="tool_calls")


class VoiceEvent(Base):
    __tablename__ = "voice_events"

    id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(String(36), ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(80), nullable=False, index=True)
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    session = relationship("VoiceSession", back_populates="events")
