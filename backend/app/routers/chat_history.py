"""Owned persistent chat sessions and per-response feedback."""
from datetime import datetime
from inspect import signature

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import chat_models, chat_schemas
from app.chat_history_service import create_session, owned_session, touch_session
from app.chat_identity import (
    GUEST_COOKIE,
    ChatIdentity,
    guest_id_from_request,
    resolve_identity,
)
from app.database import get_db
from app.faq_formatter import format_if_informational
from app.rag.language import resolve_response_language
from app.rag.response_router import generate_chat_response

router = APIRouter(prefix="/api/chat", tags=["chat-history"])


def identity_for(request: Request, response: Response, db: Session) -> ChatIdentity:
    return resolve_identity(request, response, db)


@router.post("/sessions", response_model=chat_schemas.SessionOut, status_code=201)
def new_session(
    payload: chat_schemas.SessionCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    return create_session(db, identity_for(request, response, db), payload.title)


@router.get("/sessions", response_model=list[chat_schemas.SessionOut])
def list_sessions(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    identity = identity_for(request, response, db)
    query = db.query(chat_models.ChatSession).filter(chat_models.ChatSession.is_deleted.is_(False))
    query = (
        query.filter(chat_models.ChatSession.user_id == identity.user_id)
        if identity.user_id is not None
        else query.filter(chat_models.ChatSession.guest_id == identity.guest_id)
    )
    return query.order_by(chat_models.ChatSession.last_message_at.desc()).limit(100).all()


@router.get("/sessions/{session_id}", response_model=chat_schemas.SessionDetail)
def session_detail(
    session_id: str, request: Request, response: Response, db: Session = Depends(get_db)
):
    identity = identity_for(request, response, db)
    session = owned_session(db, session_id, identity)
    session.messages.sort(key=lambda item: item.created_at)
    return session


@router.patch("/sessions/{session_id}", response_model=chat_schemas.SessionOut)
def rename_session(
    session_id: str,
    payload: chat_schemas.SessionUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    session = owned_session(db, session_id, identity_for(request, response, db))
    session.title = payload.title
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str, request: Request, response: Response, db: Session = Depends(get_db)
):
    session = owned_session(db, session_id, identity_for(request, response, db))
    session.is_deleted = True
    session.updated_at = datetime.utcnow()
    db.commit()


def _generate(
    message: str,
    language: str,
    conversation_context: list[dict[str, str]] | None = None,
) -> dict:
    return generate_chat_response(message, language, conversation_context)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=chat_schemas.MessagePair,
    status_code=201,
)
def send_message(
    session_id: str,
    payload: chat_schemas.MessageCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identity = identity_for(request, response, db)
    session = owned_session(db, session_id, identity)
    existing = db.query(chat_models.ChatMessage).filter(
        chat_models.ChatMessage.session_id == session.id,
        chat_models.ChatMessage.client_message_id == payload.client_message_id,
    ).first()
    if existing:
        assistant = db.query(chat_models.ChatMessage).filter(
            chat_models.ChatMessage.session_id == session.id,
            chat_models.ChatMessage.role == "assistant",
            chat_models.ChatMessage.created_at >= existing.created_at,
        ).order_by(chat_models.ChatMessage.created_at.asc()).first()
        if assistant:
            return _pair(existing, assistant)
        raise HTTPException(status_code=409, detail="Message is still being processed")

    response_language = resolve_response_language(payload.message, payload.language)
    user_message = chat_models.ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.message,
        language=response_language,
        client_message_id=payload.client_message_id,
    )
    db.add(user_message)
    touch_session(session, payload.message)
    db.commit()
    db.refresh(user_message)

    try:
        recent_rows = (
            db.query(chat_models.ChatMessage)
            .filter(
                chat_models.ChatMessage.session_id == session.id,
                chat_models.ChatMessage.id != user_message.id,
            )
            .order_by(chat_models.ChatMessage.created_at.desc())
            .limit(4)
            .all()
        )
        conversation_context = [
            {"role": row.role, "content": row.content}
            for row in reversed(recent_rows)
        ]
        if len(signature(_generate).parameters) >= 3:
            result = _generate(
                payload.message, response_language, conversation_context
            )
        else:
            # Preserve compatibility with existing two-argument integrations
            # and test doubles while the built-in generator receives context.
            result = _generate(payload.message, response_language)
        response_type = result.get("response_type")
        structured = result.get("structured_content")
        if not response_type:
            response_type, structured = format_if_informational(
                payload.message, result["answer"], response_language
            )
    except Exception:
        error_message = chat_models.ChatMessage(
            session_id=session.id,
            role="assistant",
            content="The assistant could not generate a response. Please try again.",
            language=response_language,
            response_type="error",
        )
        db.add(error_message)
        touch_session(session)
        db.commit()
        raise HTTPException(status_code=503, detail="The assistant is temporarily unavailable")

    assistant = chat_models.ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        language=response_language,
        response_type=response_type,
        structured_content=structured,
        sources=result["sources"],
        confidence=float(result["confidence"]),
        disclaimer=result["disclaimer"],
    )
    db.add(assistant)
    touch_session(session)
    db.commit()
    db.refresh(assistant)
    return _pair(user_message, assistant, result)


def _pair(user_message, assistant, result: dict | None = None):
    confidence = assistant.confidence or 0
    return {
        "user_message": user_message,
        "assistant_message": assistant,
        "answer": assistant.content,
        "confidence": confidence,
        "sources": assistant.sources or [],
        "disclaimer": assistant.disclaimer or "",
        "is_grounded": result["is_grounded"] if result else bool(confidence),
    }


@router.get("/sessions/{session_id}/messages", response_model=chat_schemas.MessagePage)
def messages(
    session_id: str,
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    db: Session = Depends(get_db),
):
    session = owned_session(db, session_id, identity_for(request, response, db))
    query = db.query(chat_models.ChatMessage).filter(
        chat_models.ChatMessage.session_id == session.id
    )
    if cursor:
        try:
            cursor_time = datetime.fromisoformat(cursor)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid pagination cursor")
        query = query.filter(chat_models.ChatMessage.created_at < cursor_time)
    rows = query.order_by(chat_models.ChatMessage.created_at.desc()).limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    return {
        "items": list(reversed(rows)),
        "next_cursor": rows[-1].created_at.isoformat() if has_more and rows else None,
    }


def _owned_assistant(db: Session, message_id: str, identity: ChatIdentity):
    message = db.query(chat_models.ChatMessage).filter(
        chat_models.ChatMessage.id == message_id,
        chat_models.ChatMessage.role == "assistant",
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Assistant message not found")
    owned_session(db, message.session_id, identity)
    return message


@router.post("/messages/{message_id}/feedback", response_model=chat_schemas.FeedbackOut)
def upsert_feedback(
    message_id: str,
    payload: chat_schemas.FeedbackUpsert,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identity = identity_for(request, response, db)
    message = _owned_assistant(db, message_id, identity)
    feedback = db.query(chat_models.ChatFeedback).filter(
        chat_models.ChatFeedback.message_id == message.id,
        chat_models.ChatFeedback.identity_key == identity.key,
    ).first()
    if not feedback:
        feedback = chat_models.ChatFeedback(
            session_id=message.session_id,
            message_id=message.id,
            user_id=identity.user_id,
            guest_id=identity.guest_id,
            identity_key=identity.key,
        )
        db.add(feedback)
    feedback.reaction = payload.reaction
    feedback.rating = payload.rating
    feedback.feedback_text = payload.feedback_text
    feedback.updated_at = datetime.utcnow()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Feedback update conflict")
    db.refresh(feedback)
    return feedback


@router.get("/messages/{message_id}/feedback", response_model=chat_schemas.FeedbackOut)
def get_feedback(
    message_id: str, request: Request, response: Response, db: Session = Depends(get_db)
):
    identity = identity_for(request, response, db)
    _owned_assistant(db, message_id, identity)
    feedback = db.query(chat_models.ChatFeedback).filter(
        chat_models.ChatFeedback.message_id == message_id,
        chat_models.ChatFeedback.identity_key == identity.key,
    ).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


@router.delete("/messages/{message_id}/feedback", status_code=204)
def delete_feedback(
    message_id: str, request: Request, response: Response, db: Session = Depends(get_db)
):
    identity = identity_for(request, response, db)
    _owned_assistant(db, message_id, identity)
    feedback = db.query(chat_models.ChatFeedback).filter(
        chat_models.ChatFeedback.message_id == message_id,
        chat_models.ChatFeedback.identity_key == identity.key,
    ).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    db.delete(feedback)
    db.commit()


@router.post("/migrate-guest", response_model=chat_schemas.MigrationResult)
def migrate_guest(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    identity = resolve_identity(request, response, db, create_guest=False)
    if identity.user_id is None:
        raise HTTPException(status_code=401, detail="Login required")
    guest_id = guest_id_from_request(request)
    if not guest_id:
        return {"migrated_sessions": 0, "migrated_feedback": 0, "already_migrated": True}

    sessions = db.query(chat_models.ChatSession).filter(
        chat_models.ChatSession.guest_id == guest_id
    ).all()
    feedback_items = db.query(chat_models.ChatFeedback).filter(
        chat_models.ChatFeedback.guest_id == guest_id
    ).all()
    for session in sessions:
        session.user_id = identity.user_id
        session.guest_id = None
    for feedback in feedback_items:
        feedback.user_id = identity.user_id
        feedback.guest_id = None
        feedback.identity_key = identity.key
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Guest history migration could not be completed")
    response.delete_cookie(GUEST_COOKIE, path="/")
    return {
        "migrated_sessions": len(sessions),
        "migrated_feedback": len(feedback_items),
        "already_migrated": not sessions and not feedback_items,
    }
