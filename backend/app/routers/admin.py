from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/summary")
def admin_summary(db: Session = Depends(get_db), admin: models.User = Depends(auth.require_admin)):
    total_users = db.query(models.User).count()
    chats = db.query(models.ChatHistory).filter(models.ChatHistory.role == "assistant").all()
    total_chats = len(chats)
    avg_conf = round(sum(c.confidence or 0 for c in chats) / total_chats, 3) if total_chats else 0
    low_conf = sum(1 for c in chats if (c.confidence or 0) < 0.35)
    low_conf_rate = round(low_conf / total_chats, 3) if total_chats else 0

    user_questions = [c.message for c in db.query(models.ChatHistory).filter(models.ChatHistory.role == "user").all()]
    top_questions = Counter(user_questions).most_common(10)

    return {
        "total_users": total_users,
        "total_chats": total_chats,
        "avg_confidence": avg_conf,
        "low_confidence_rate": low_conf_rate,
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "total_documents": db.query(models.Document).count(),
        "total_schemes": db.query(models.Scheme).count(),
    }


@router.get("/feedback")
def list_feedback(db: Session = Depends(get_db), admin: models.User = Depends(auth.require_admin)):
    rows = db.query(models.Feedback).order_by(models.Feedback.created_at.desc()).limit(100).all()
    return [
        {"id": r.id, "rating": r.rating, "comment": r.comment, "created_at": r.created_at}
        for r in rows
    ]


@router.get("/missing-knowledge")
def missing_knowledge(db: Session = Depends(get_db), admin: models.User = Depends(auth.require_admin)):
    """Surfaces low-confidence queries -> tells admins exactly what content gaps to fill."""
    rows = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.role == "assistant", models.ChatHistory.confidence < 0.35)
        .order_by(models.ChatHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return [{"message": r.message[:200], "confidence": r.confidence, "created_at": r.created_at} for r in rows]
