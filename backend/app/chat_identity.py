"""Verified JWT-or-signed-cookie ownership for the additive chat API."""
from dataclasses import dataclass
import uuid

from fastapi import HTTPException, Request, Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import models
from app.config import settings

GUEST_COOKIE = "janmitra_guest"


@dataclass(frozen=True)
class ChatIdentity:
    user_id: int | None = None
    guest_id: str | None = None

    @property
    def key(self) -> str:
        return f"u:{self.user_id}" if self.user_id is not None else f"g:{self.guest_id}"


def _authenticated_user_id(request: Request, db: Session) -> int | None:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    try:
        payload = jwt.decode(
            header.split(" ", 1)[1], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not db.query(models.User.id).filter(models.User.id == user_id).first():
        raise HTTPException(status_code=401, detail="User not found")
    return user_id


def _decode_guest(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        guest_id = str(uuid.UUID(payload["sub"]))
        return guest_id if payload.get("kind") == "guest" else None
    except (JWTError, KeyError, TypeError, ValueError):
        return None


def issue_guest_cookie(response: Response, guest_id: str) -> None:
    token = jwt.encode(
        {"sub": guest_id, "kind": "guest"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    response.set_cookie(
        GUEST_COOKIE,
        token,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def resolve_identity(
    request: Request, response: Response, db: Session, create_guest: bool = True
) -> ChatIdentity:
    user_id = _authenticated_user_id(request, db)
    if user_id is not None:
        return ChatIdentity(user_id=user_id)
    guest_id = _decode_guest(request.cookies.get(GUEST_COOKIE))
    if guest_id:
        return ChatIdentity(guest_id=guest_id)
    if not create_guest:
        raise HTTPException(status_code=401, detail="Valid guest identity or login required")
    guest_id = str(uuid.uuid4())
    issue_guest_cookie(response, guest_id)
    return ChatIdentity(guest_id=guest_id)


def guest_id_from_request(request: Request) -> str | None:
    return _decode_guest(request.cookies.get(GUEST_COOKIE))
