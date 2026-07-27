from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import chat_models
from app.chat_identity import ChatIdentity


def owned_session(db: Session, session_id: str, identity: ChatIdentity):
    query = db.query(chat_models.ChatSession).filter(
        chat_models.ChatSession.id == session_id,
        chat_models.ChatSession.is_deleted.is_(False),
    )
    if identity.user_id is not None:
        query = query.filter(chat_models.ChatSession.user_id == identity.user_id)
    else:
        query = query.filter(chat_models.ChatSession.guest_id == identity.guest_id)
    session = query.first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


def create_session(db: Session, identity: ChatIdentity, title: str | None = None):
    session = chat_models.ChatSession(
        user_id=identity.user_id,
        guest_id=identity.guest_id,
        title=title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def title_from_message(message: str) -> str:
    compact = " ".join(message.split())
    return compact[:57] + ("..." if len(compact) > 57 else "")


def touch_session(session, first_message: str | None = None):
    now = datetime.utcnow()
    session.updated_at = now
    session.last_message_at = now
    if first_message and not session.title:
        session.title = title_from_message(first_message)
