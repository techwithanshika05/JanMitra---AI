from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import models, schemas
from app.rag.retriever import retriever
from app.rag.llm_client import generate_answer
from app.rag.small_talk import detect_small_talk

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    # 0. Handle greetings/small-talk without touching the RAG pipeline
    small_talk_reply = detect_small_talk(payload.message, payload.language or "en")
    if small_talk_reply:
        result = {
            "answer": small_talk_reply,
            "confidence": 1.0,
            "is_grounded": True,
            "disclaimer": "",
            "sources": [],
        }
    else:
        # 1. Retrieve relevant knowledge chunks (semantic search over Chroma)
        chunks = retriever.query(payload.message)
        # 2. Generate a grounded answer (or retrieval-only fallback) + confidence
        result = generate_answer(payload.message, chunks, payload.language or "en")

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