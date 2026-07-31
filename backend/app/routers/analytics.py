from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/feedback")
def submit_feedback(
    payload: schemas.FeedbackCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    fb = models.Feedback(
        user_id=user.id, chat_id=payload.chat_id, rating=payload.rating, comment=payload.comment
    )
    db.add(fb)
    db.commit()
    return {"status": "recorded", "id": fb.id}


@router.get("/events-by-type")
def events_by_type(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(auth.require_admin),
):
    rows = (
        db.query(models.AnalyticsEvent.event_type, func.count(models.AnalyticsEvent.id))
        .group_by(models.AnalyticsEvent.event_type)
        .all()
    )
    return [{"event_type": t, "count": c} for t, c in rows]
