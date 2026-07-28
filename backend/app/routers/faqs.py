from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app import models, schemas
from app.chat_identity import resolve_identity
from app.database import get_db
from app.identity_tracking.service import track_feature_activity

router = APIRouter(prefix="/faqs", tags=["faqs"])


@router.get("", response_model=list[schemas.FAQOut])
def list_faqs(
    request: Request,
    response: Response,
    category: str | None = Query(default=None),
    language: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    identity = resolve_identity(request, response, db)
    query = db.query(models.FAQ)
    if category:
        query = query.filter(models.FAQ.category == category)
    if language:
        query = query.filter(models.FAQ.language == language)
    rows = query.order_by(models.FAQ.id).all()
    track_feature_activity(
        db,
        identity,
        feature="faq",
        action_type="listed",
        metadata={
            key: value
            for key, value in {"category": category, "language": language}.items()
            if value
        },
    )
    db.commit()
    return rows
