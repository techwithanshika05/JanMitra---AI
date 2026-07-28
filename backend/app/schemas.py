from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, model_validator


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(default=None, pattern=r"^\d{10}$")
    address: Optional[str] = None
    gender: Optional[str] = None
    pincode: Optional[str] = Field(default=None, pattern=r"^\d{6}$")
    password: str
    state: Optional[str] = None
    preferred_language: Optional[str] = "en"

    @model_validator(mode="after")
    def validate_registration_identity(self):
        if not (self.name or self.full_name):
            raise ValueError("Name is required")
        if not (self.email or self.mobile):
            raise ValueError("Email or mobile number is required")
        return self


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(default=None, pattern=r"^\d{10}$")
    password: str

    @model_validator(mode="after")
    def validate_login_identity(self):
        if not (self.email or self.mobile):
            raise ValueError("Email or mobile number is required")
        return self


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    state: Optional[str]
    preferred_language: str
    mobile: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    pincode: Optional[str] = None
    public_id: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    authenticated: bool = True
    guest_data_imported: bool = False
    migration: dict[str, Any] = Field(default_factory=dict)


# ---------- Chat / RAG ----------
class ChatRequest(BaseModel):
    session_id: str
    message: str
    language: Optional[str] = "en"


class SourceRef(BaseModel):
    title: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceRef]
    disclaimer: str
    is_grounded: bool


# ---------- Scheme Finder ----------
class SchemeFinderRequest(BaseModel):
    state: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    income: Optional[int] = None
    occupation: Optional[str] = None
    category: Optional[str] = None
    disability: Optional[bool] = False


class SchemeOut(BaseModel):
    id: int
    name: str
    category: Optional[str]
    state: Optional[str]
    description: Optional[str]
    benefits: Optional[str]
    required_documents: Optional[List[str]]
    application_steps: Optional[List[str]]
    official_source: Optional[str]
    match_reason: Optional[str] = None

    class Config:
        from_attributes = True


class FAQOut(BaseModel):
    id: int
    question: str
    answer: str
    category: Optional[str] = None
    language: str = "en"
    source: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Checklist ----------
class ChecklistRequest(BaseModel):
    service_type: str          # e.g. "new_ration_card", "PMAY", "scholarship"
    state: Optional[str] = None
    category: Optional[str] = None  # SC/ST/OBC/General etc.


class ChecklistResponse(BaseModel):
    service_type: str
    documents: List[str]
    steps: List[str]
    estimated_time: str
    notes: str


# ---------- Ration ----------
class RationProcessRequest(BaseModel):
    process: str  # new_card | duplicate | update_member | address_update | delete_member | migration


# ---------- Grievance ----------
class GrievanceRequest(BaseModel):
    category: str          # ration | scheme | pension | other
    description: str
    state: Optional[str] = None


class GrievanceResponse(BaseModel):
    department: str
    steps: List[str]
    expected_resolution_days: int
    escalation_path: List[str]
    reference_note: str


# ---------- Feedback ----------
class FeedbackCreate(BaseModel):
    chat_id: Optional[int] = None
    rating: int
    comment: Optional[str] = None


# ---------- Admin / Analytics ----------
class AnalyticsSummary(BaseModel):
    total_chats: int
    total_users: int
    avg_confidence: float
    top_questions: List[Any]
    low_confidence_rate: float
