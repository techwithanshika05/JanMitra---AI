"""
ORM models covering the tables requested in the spec:
Users, Schemes, Documents, FAQs, Feedback, ChatHistory, Analytics.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="citizen")  # citizen | admin
    state = Column(String, nullable=True)
    preferred_language = Column(String, default="en")  # en | hi | hinglish
    created_at = Column(DateTime, default=datetime.utcnow)

    chats = relationship("ChatHistory", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String)  # e.g. Food Security, Education, Health, Farmer
    state = Column(String, default="All India")
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    gender = Column(String, default="All")  # All | Male | Female | Other
    max_income = Column(Integer, nullable=True)
    occupation = Column(String, nullable=True)  # farmer | student | laborer | any
    disability_required = Column(Boolean, default=False)
    description = Column(Text)
    benefits = Column(Text)
    required_documents = Column(JSON)  # list[str]
    application_steps = Column(JSON)   # list[str]
    official_source = Column(String)   # citation / URL or document name
    last_updated = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Uploaded government documents/PDFs that get chunked & embedded for RAG."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_type = Column(String, default="policy_pdf")  # policy_pdf | faq | scheme_doc
    file_path = Column(String, nullable=True)
    chunk_count = Column(Integer, default=0)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processed")  # processing | processed | failed


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String)  # ration | scheme | grievance | general
    language = Column(String, default="en")
    source = Column(String)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String, index=True)
    role = Column(String)  # user | assistant
    message = Column(Text)
    sources = Column(JSON, nullable=True)     # list of {title, snippet, score}
    confidence = Column(Float, nullable=True)
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    chat_id = Column(Integer, ForeignKey("chat_history.id"), nullable=True)
    rating = Column(Integer)  # 1-5, or thumbs: 1 = down, 5 = up
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedback")


class AnalyticsEvent(Base):
    """Generic event log powering the admin analytics dashboard."""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)  # query | scheme_search | checklist_generated | grievance_started ...
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
