from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import models, schemas
from app.rag.response_router import generate_chat_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    recent_rows = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.session_id == payload.session_id)
        .order_by(models.ChatHistory.created_at.desc())
        .limit(4)
        .all()
    )
    conversation_context = [
        {"role": row.role, "content": row.message}
        for row in reversed(recent_rows)
    ]
    result = generate_chat_response(
        payload.message, payload.language, conversation_context
    )

    # 3. Persist to chat history for the admin analytics dashboard
    user_msg = models.ChatHistory(
        session_id=payload.session_id, role="user", message=payload.message,
        language=payload.language, created_at=datetime.utcnow(),
    )
    assistant_msg = models.ChatHistory(
        session_id=payload.session_id, role="assistant", message=result["answer"],
        sources=result["sources"], confidence=result["confidence"],
        language=payload.language, created_at=datetime.utcnow(),
    )
    db.add_all([user_msg, assistant_msg])
    db.add(models.AnalyticsEvent(event_type="query", payload={
        "question": payload.message, "confidence": result["confidence"],
        "grounded": result["is_grounded"],
    }))
    db.commit()

    return schemas.ChatResponse(
        answer=result["answer"],
        confidence=result["confidence"],
        sources=[schemas.SourceRef(**s) for s in result["sources"]],
        disclaimer=result["disclaimer"],
        is_grounded=result["is_grounded"],
    )


@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.session_id == session_id)
        .order_by(models.ChatHistory.created_at.asc())
        .all()
    )
    return [
        {
            "role": r.role, "message": r.message, "sources": r.sources,
            "confidence": r.confidence, "created_at": r.created_at,
        }
        for r in rows
    ]
