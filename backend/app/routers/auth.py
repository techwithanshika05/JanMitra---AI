from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session
import secrets

from app.database import get_db
from app import models, schemas, auth
from app.chat_identity import GUEST_COOKIE, guest_id_from_request
from app.identity_tracking.service import claim_guest_data

router = APIRouter(prefix="/auth", tags=["auth"])


def _new_public_id(db: Session) -> str:
    for _ in range(20):
        candidate = f"PDS{secrets.randbelow(1_000_000):06d}"
        if not db.query(models.User.id).filter(models.User.public_id == candidate).first():
            return candidate
    raise HTTPException(status_code=503, detail="Could not allocate a user ID")


def _claim_current_guest(
    request: Request, db: Session, user_id: int
) -> tuple[bool, dict]:
    guest_id = guest_id_from_request(request)
    if not guest_id:
        return False, {}
    summary = claim_guest_data(db, guest_id=guest_id, user_id=user_id)
    imported = any(value for key, value in summary.items() if key != "already_claimed")
    return imported, summary


@router.post("/register", response_model=schemas.Token)
def register(
    payload: schemas.UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email = str(payload.email) if payload.email else f"{payload.mobile}@janmitra.local"
    conditions = [models.User.email == email]
    if payload.mobile:
        conditions.append(models.User.mobile == payload.mobile)
    existing = db.query(models.User).filter(or_(*conditions)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email or mobile number already registered")

    user = models.User(
        name=payload.name or payload.full_name,
        email=email,
        mobile=payload.mobile,
        address=payload.address,
        gender=payload.gender,
        pincode=payload.pincode,
        public_id=_new_public_id(db),
        hashed_password=auth.hash_password(payload.password),
        state=payload.state,
        preferred_language=payload.preferred_language or "en",
        role="citizen",
    )
    db.add(user)
    try:
        db.flush()
        imported, migration = _claim_current_guest(request, db, user.id)
        db.commit()
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    db.refresh(user)
    if guest_id_from_request(request):
        response.delete_cookie(GUEST_COOKIE, path="/")

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.Token(
        access_token=token,
        user=user,
        guest_data_imported=imported,
        migration=migration,
    )


@router.post("/login", response_model=schemas.Token)
def login(
    payload: schemas.UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    query = db.query(models.User)
    user = (
        query.filter(models.User.email == str(payload.email)).first()
        if payload.email
        else query.filter(models.User.mobile == payload.mobile).first()
    )
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        imported, migration = _claim_current_guest(request, db, user.id)
        db.commit()
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if guest_id_from_request(request):
        response.delete_cookie(GUEST_COOKIE, path="/")
    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.Token(
        access_token=token,
        user=user,
        guest_data_imported=imported,
        migration=migration,
    )


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
