from datetime import datetime
import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class SchemeActivity(Base):
    """References the existing scheme table; it never duplicates scheme data."""

    __tablename__ = "scheme_activities"

    id = Column(String(36), primary_key=True, default=new_uuid)
    scheme_id = Column(Integer, ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_session_id = Column(String(36), nullable=True, index=True)
    ownership_status = Column(String(16), default="active", nullable=False, index=True)
    claimed_at = Column(DateTime, nullable=True)
    action_type = Column(String(32), nullable=False, index=True)
    query_text = Column(Text, nullable=True)
    result_position = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    storage_origin = Column(String(16), default="sqlite", nullable=False)
    sync_status = Column(String(16), default="pending", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "user_id IS NOT NULL OR guest_session_id IS NOT NULL",
            name="ck_scheme_activity_has_owner",
        ),
        CheckConstraint(
            "action_type IN ('searched','viewed','recommended','saved',"
            "'checklist_created','shared','feedback_submitted')",
            name="ck_scheme_activity_action",
        ),
        Index("ix_scheme_activity_user_created", "user_id", "created_at"),
        Index("ix_scheme_activity_guest_created", "guest_session_id", "created_at"),
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_session_id = Column(String(36), nullable=True, index=True)
    ownership_status = Column(String(16), default="active", nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    language = Column(String(16), default="en", nullable=False)
    state = Column(String(100), nullable=True)
    preferences_json = Column(JSON, default=dict, nullable=False)
    storage_origin = Column(String(16), default="sqlite", nullable=False)
    sync_status = Column(String(16), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "user_id IS NOT NULL OR guest_session_id IS NOT NULL",
            name="ck_user_preference_has_owner",
        ),
        UniqueConstraint("user_id", name="uq_user_preferences_user"),
        UniqueConstraint("guest_session_id", name="uq_user_preferences_guest"),
    )


class GuestClaim(Base):
    __tablename__ = "guest_claims"

    id = Column(String(36), primary_key=True, default=new_uuid)
    guest_session_id = Column(String(36), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_json = Column(JSON, default=dict, nullable=False)
    claimed_at = Column(DateTime, default=datetime.utcnow, nullable=False)




class FeatureActivity(Base):
    __tablename__ = "feature_activities"

    id = Column(String(36), primary_key=True, default=new_uuid)
    feature = Column(String(32), nullable=False, index=True)
    action_type = Column(String(40), nullable=False)
    reference_id = Column(String(160), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_session_id = Column(String(36), nullable=True, index=True)
    ownership_status = Column(String(16), default="active", nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    storage_origin = Column(String(16), default="sqlite", nullable=False)
    sync_status = Column(String(16), default="pending", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "user_id IS NOT NULL OR guest_session_id IS NOT NULL",
            name="ck_feature_activity_has_owner",
        ),
        Index("ix_feature_activity_user_created", "user_id", "created_at"),
        Index("ix_feature_activity_guest_created", "guest_session_id", "created_at"),
    )
