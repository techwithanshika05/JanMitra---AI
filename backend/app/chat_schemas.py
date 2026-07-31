from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class FAQSection(BaseModel):
    heading: str
    points: list[str] = []


class StructuredFAQ(BaseModel):
    response_type: Literal["faq"] = "faq"
    title: str
    summary: str
    sections: list[FAQSection] = []
    steps: list[str] = []
    note: Optional[str] = None


class SessionCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)


class SessionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        return " ".join(value.split())


class SessionOut(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    language: str
    response_type: str
    structured_content: Optional[dict] = None
    sources: Optional[list[dict]] = None
    confidence: Optional[float] = None
    disclaimer: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetail(SessionOut):
    messages: list[MessageOut]


class MessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    language: str = Field(default="en", max_length=16)
    client_message_id: str = Field(min_length=8, max_length=64)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value


class MessagePair(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut
    answer: str
    confidence: float
    sources: list[dict]
    disclaimer: str
    is_grounded: bool
    api_status: Optional[str] = None
    alert: Optional[str] = None


class MessagePage(BaseModel):
    items: list[MessageOut]
    next_cursor: Optional[str] = None


class FeedbackUpsert(BaseModel):
    reaction: Literal["like", "dislike", "neutral"] = "neutral"
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback_text: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("feedback_text")
    @classmethod
    def clean_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = " ".join(value.replace("\x00", "").split())
        return cleaned or None


class FeedbackOut(BaseModel):
    id: str
    session_id: str
    message_id: str
    reaction: str
    rating: Optional[int]
    feedback_text: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MigrationResult(BaseModel):
    migrated_sessions: int
    migrated_feedback: int
    already_migrated: bool
