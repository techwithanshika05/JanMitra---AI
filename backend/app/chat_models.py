"""Additive conversation, message, and feedback models.

These tables intentionally coexist with the legacy ``chat_history`` and
``feedback`` tables so existing analytics and API behavior remain unchanged.
"""
from datetime import datetime
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Float,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_id = Column(String(36), nullable=True, index=True)
    title = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
    feedback_items = relationship(
        "ChatFeedback", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_id IS NULL) OR "
            "(user_id IS NULL AND guest_id IS NOT NULL)",
            name="ck_chat_session_single_owner",
        ),
        Index("ix_chat_sessions_user_recent", "user_id", "last_message_at"),
        Index("ix_chat_sessions_guest_recent", "guest_id", "last_message_at"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(16), default="en", nullable=False)
    response_type = Column(String(32), default="plain", nullable=False)
    structured_content = Column(JSON, nullable=True)
    sources = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    disclaimer = Column(Text, nullable=True)
    client_message_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    session = relationship("ChatSession", back_populates="messages")
    feedback_items = relationship(
        "ChatFeedback", back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_chat_message_role"),
        UniqueConstraint("session_id", "client_message_id", name="uq_session_client_message"),
    )


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = Column(String(36), primary_key=True, default=new_uuid)
    session_id = Column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id = Column(
        String(36), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_id = Column(String(36), nullable=True, index=True)
    identity_key = Column(String(64), nullable=False)
    reaction = Column(String(16), default="neutral", nullable=False)
    rating = Column(Integer, nullable=True)
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="feedback_items")
    message = relationship("ChatMessage", back_populates="feedback_items")

    __table_args__ = (
        CheckConstraint("reaction IN ('like', 'dislike', 'neutral')", name="ck_feedback_reaction"),
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="ck_feedback_rating"),
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_id IS NULL) OR "
            "(user_id IS NULL AND guest_id IS NOT NULL)",
            name="ck_feedback_single_owner",
        ),
        UniqueConstraint("message_id", "identity_key", name="uq_feedback_message_identity"),
    )
