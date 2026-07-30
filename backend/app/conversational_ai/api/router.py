from datetime import timedelta
import json
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.chat_identity import resolve_identity
from app.conversational_ai.config import voice_settings
from app.conversational_ai.monitoring.health import health_snapshot
from app.conversational_ai.persistence.repository import VoiceRepository
from app.conversational_ai.schemas import (
    EndSessionRequest, HealthOut, SessionDetail, SessionList, SessionOut,
    SourceOut, StartSessionRequest, StartSessionResponse, TurnOut,
)
from app.database import get_db

router = APIRouter(prefix="/api/voice", tags=["conversational-ai"])


def _session_out(row) -> SessionOut:
    return SessionOut.model_validate(row, from_attributes=True)


def _detail(row) -> SessionDetail:
    data = _session_out(row).model_dump()
    data["turns"] = [
        TurnOut(
            id=turn.id, turn_number=turn.turn_number, speaker=turn.speaker,
            original_text=turn.original_text, language_code=turn.language_code,
            intent=turn.intent, answer_mode=turn.answer_mode,
            evidence_status=turn.evidence_status, confidence_score=turn.confidence_score,
            latency_ms=turn.latency_ms, interrupted=turn.interrupted, created_at=turn.created_at,
            sources=[SourceOut(
                title=s.source_title, snippet=s.snippet or "", score=s.retrieval_score or 0.0,
                document_id=s.document_id, chunk_id=s.chunk_id,
            ) for s in turn.sources],
        ) for turn in row.turns
    ]
    return SessionDetail(**data)


def _token(room_name: str, participant_identity: str, session_id: str) -> str:
    if not voice_settings.livekit_ready:
        raise HTTPException(status_code=503, detail="LiveKit is not configured")
    try:
        from livekit import api
        return (
            api.AccessToken(voice_settings.livekit_api_key, voice_settings.livekit_api_secret)
            .with_identity(participant_identity)
            .with_name("JanMitra citizen")
            .with_ttl(timedelta(minutes=voice_settings.room_ttl_minutes))
            .with_grants(api.VideoGrants(room_join=True, room=room_name, can_publish=True, can_subscribe=True))
            .with_room_config(api.RoomConfiguration(agents=[
                api.RoomAgentDispatch(
                    agent_name=voice_settings.agent_name,
                    metadata=json.dumps({"session_id": session_id, "room_name": room_name}),
                )
            ]))
            .to_jwt()
        )
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="LiveKit server SDK is not installed") from exc


@router.post("/sessions", response_model=StartSessionResponse, status_code=201)
def start(payload: StartSessionRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    identity = resolve_identity(request, response, db)
    room_name = f"janmitra-{secrets.token_urlsafe(12)}"
    row = VoiceRepository(db).create_session(identity, room_name, payload.language.value)
    token = _token(
        room_name,
        f"user-{identity.user_id}" if identity.user_id else f"guest-{identity.guest_id}",
        row.id,
    )
    db.commit()
    return StartSessionResponse(
        session_id=row.id, room_name=room_name, token=token,
        livekit_url=voice_settings.livekit_url, default_language=row.default_language,
        storage_mode=row.storage_origin,
    )


@router.get("/sessions", response_model=SessionList)
def sessions(request: Request, response: Response, page: int = Query(1, ge=1),
             page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    identity = resolve_identity(request, response, db)
    total, rows = VoiceRepository(db).list_owned(identity, page, page_size)
    return SessionList(total=total, page=page, page_size=page_size, items=[_session_out(row) for row in rows])


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def session_detail(session_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    identity = resolve_identity(request, response, db)
    row = VoiceRepository(db).owned_session(session_id, identity, with_turns=True)
    if row is None:
        raise HTTPException(status_code=404, detail="Voice session not found")
    return _detail(row)


@router.post("/sessions/{session_id}/end", response_model=SessionOut)
def end(session_id: str, payload: EndSessionRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    identity = resolve_identity(request, response, db)
    repo = VoiceRepository(db)
    row = repo.owned_session(session_id, identity)
    if row is None:
        raise HTTPException(status_code=404, detail="Voice session not found")
    repo.end(row, payload.reason)
    db.commit()
    db.refresh(row)
    return _session_out(row)


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)):
    return HealthOut(**health_snapshot(db))
