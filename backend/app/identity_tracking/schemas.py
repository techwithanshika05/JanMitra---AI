from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IdentityOut(BaseModel):
    is_authenticated: bool
    user_id: int | None
    guest_session_id: str | None


class ClaimSummary(BaseModel):
    chat_sessions: int = 0
    chat_feedback: int = 0
    checklists: int = 0
    scheme_activities: int = 0
    preferences: int = 0
    feature_activities: int = 0
    already_claimed: bool = False


class ClaimResponse(BaseModel):
    guest_data_imported: bool
    migration: ClaimSummary


class PreferencePatch(BaseModel):
    language: str | None = Field(default=None, pattern="^(en|hi|hinglish)$")
    state: str | None = Field(default=None, max_length=100)
    preferences: dict[str, Any] | None = None


class PreferenceOut(BaseModel):
    language: str
    state: str | None
    preferences: dict[str, Any]


class HistoryItem(BaseModel):
    feature: str
    record_id: str
    action: str
    scheme_id: int | None = None
    title: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class HistoryResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[HistoryItem]
