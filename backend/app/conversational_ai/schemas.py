from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VoiceLanguage(str, Enum):
    HINDI = "hi-IN"
    ENGLISH = "en-IN"
    HINGLISH = "hi-IN"


class EvidenceStatus(str, Enum):
    VERIFIED_DOCUMENT = "verified_document"
    VERIFIED_SCHEME = "verified_scheme"
    CURATED_RULE = "curated_rule"
    INSUFFICIENT = "insufficient_evidence"
    CONFLICTING = "conflicting_information"
    UNAVAILABLE = "system_unavailable"


class StartSessionRequest(BaseModel):
    language: VoiceLanguage = VoiceLanguage.HINDI


class StartSessionResponse(BaseModel):
    session_id: str
    room_name: str
    token: str
    livekit_url: str
    default_language: str
    storage_mode: str


class EndSessionRequest(BaseModel):
    reason: str = Field(default="user_ended", max_length=80)


class SourceOut(BaseModel):
    title: str
    snippet: str = ""
    score: float = 0.0
    document_id: str | None = None
    chunk_id: str | None = None


class TurnOut(BaseModel):
    id: str
    turn_number: int
    speaker: str
    original_text: str
    language_code: str
    intent: str | None
    answer_mode: str | None
    evidence_status: str | None
    confidence_score: float | None
    latency_ms: int | None
    interrupted: bool
    created_at: datetime
    sources: list[SourceOut] = []


class SessionOut(BaseModel):
    id: str
    room_name: str
    status: str
    default_language: str
    current_language: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    total_turns: int
    summary: str | None
    primary_intent: str | None
    storage_origin: str
    sync_status: str


class SessionDetail(SessionOut):
    turns: list[TurnOut] = []


class SessionList(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SessionOut]


class HealthOut(BaseModel):
    status: str
    livekit_configured: bool
    sarvam_configured: bool
    database: str
    rag: str
    agent_name: str
    models: dict[str, str]
    details: dict[str, Any] = {}
