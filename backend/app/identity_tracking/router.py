from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app import chat_models
from app.checklists.models import SavedChecklist
from app.chat_identity import GUEST_COOKIE, guest_id_from_request, resolve_identity
from app.database import get_db
from app.identity_tracking.models import FeatureActivity, SchemeActivity, UserPreference
from app.identity_tracking.schemas import (
    ClaimResponse,
    HistoryItem,
    HistoryResponse,
    IdentityOut,
    PreferenceOut,
    PreferencePatch,
)
from app.identity_tracking.service import claim_guest_data, owned_filter
from app.conversational_ai.persistence.models import VoiceSession

router = APIRouter(prefix="/api", tags=["identity-history"])


@router.post("/guest/session", response_model=IdentityOut)
def guest_session(request: Request, response: Response, db: Session = Depends(get_db)):
    identity = resolve_identity(request, response, db)
    return IdentityOut(
        is_authenticated=identity.user_id is not None,
        user_id=identity.user_id,
        guest_session_id=identity.guest_id,
    )


@router.post("/auth/claim-guest-data", response_model=ClaimResponse)
def claim(request: Request, response: Response, db: Session = Depends(get_db)):
    identity = resolve_identity(request, response, db, create_guest=False)
    if identity.user_id is None:
        raise HTTPException(status_code=401, detail="Login required")
    guest_id = guest_id_from_request(request)
    if not guest_id:
        return ClaimResponse(guest_data_imported=False, migration={"already_claimed": True})
    try:
        summary = claim_guest_data(db, guest_id=guest_id, user_id=identity.user_id)
        db.commit()
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise
    response.delete_cookie(GUEST_COOKIE, path="/")
    return ClaimResponse(
        guest_data_imported=any(
            value for key, value in summary.items() if key != "already_claimed"
        ),
        migration=summary,
    )


def _identity(request: Request, response: Response, db: Session):
    return resolve_identity(request, response, db)


@router.get("/me/history", response_model=HistoryResponse)
def history(
    request: Request,
    response: Response,
    feature: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    identity = _identity(request, response, db)
    items: list[HistoryItem] = []
    if feature in (None, "scheme"):
        rows = db.query(SchemeActivity).filter(owned_filter(SchemeActivity, identity)).all()
        items.extend(
            HistoryItem(
                feature="scheme",
                record_id=row.id,
                action=row.action_type,
                scheme_id=row.scheme_id,
                metadata=row.metadata_json,
                created_at=row.created_at,
            )
            for row in rows
        )
    if feature in (None, "chat"):
        query = db.query(chat_models.ChatSession)
        query = query.filter(
            chat_models.ChatSession.user_id == identity.user_id
            if identity.user_id is not None
            else chat_models.ChatSession.guest_id == identity.guest_id
        )
        items.extend(
            HistoryItem(
                feature="chat",
                record_id=row.id,
                action="conversation",
                title=row.title,
                created_at=row.created_at,
            )
            for row in query.filter(chat_models.ChatSession.is_deleted.is_(False)).all()
        )
    if feature in (None, "checklist"):
        rows = db.query(SavedChecklist).filter(owned_filter(SavedChecklist, identity)).all()
        items.extend(
            HistoryItem(
                feature="checklist",
                record_id=row.id,
                action=row.status,
                title=row.service_name,
                created_at=row.created_at,
            )
            for row in rows
            if row.deleted_at is None
        )
    if feature in (None, "voice"):
        rows = db.query(VoiceSession).filter(owned_filter(VoiceSession, identity)).all()
        items.extend(
            HistoryItem(
                feature="voice",
                record_id=row.id,
                action=row.status,
                title=row.summary or "Voice guidance call",
                created_at=row.created_at,
            )
            for row in rows
        )
    generic_query = db.query(FeatureActivity).filter(
        owned_filter(FeatureActivity, identity)
    )
    if feature is not None:
        generic_query = generic_query.filter(FeatureActivity.feature == feature)
    items.extend(
        HistoryItem(
            feature=row.feature,
            record_id=row.id,
            action=row.action_type,
            metadata=row.metadata_json,
            created_at=row.created_at,
        )
        for row in generic_query.all()
    )
    items.sort(key=lambda item: item.created_at, reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    return HistoryResponse(
        page=page, page_size=page_size, total=total, items=items[start : start + page_size]
    )


@router.get("/me/activity", response_model=HistoryResponse)
def activity(
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return history(request, response, None, page, page_size, db)


@router.get("/me/preferences", response_model=PreferenceOut)
def get_preferences(request: Request, response: Response, db: Session = Depends(get_db)):
    identity = _identity(request, response, db)
    row = db.query(UserPreference).filter(owned_filter(UserPreference, identity)).first()
    return PreferenceOut(
        language=row.language if row else "en",
        state=row.state if row else None,
        preferences=row.preferences_json if row else {},
    )


@router.patch("/me/preferences", response_model=PreferenceOut)
def patch_preferences(
    payload: PreferencePatch,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identity = _identity(request, response, db)
    row = db.query(UserPreference).filter(owned_filter(UserPreference, identity)).first()
    if row is None:
        row = UserPreference(
            user_id=identity.user_id,
            guest_session_id=identity.guest_id,
            storage_origin="sqlite" if db.bind and db.bind.dialect.name == "sqlite" else "postgresql",
            sync_status="pending" if db.bind and db.bind.dialect.name == "sqlite" else "synced",
        )
        db.add(row)
    values = payload.model_dump(exclude_unset=True)
    if "language" in values:
        row.language = values["language"]
    if "state" in values:
        row.state = values["state"]
    if "preferences" in values:
        row.preferences_json = values["preferences"]
    db.commit()
    db.refresh(row)
    return PreferenceOut(
        language=row.language, state=row.state, preferences=row.preferences_json
    )
