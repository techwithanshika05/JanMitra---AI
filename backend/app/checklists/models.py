from datetime import datetime, UTC
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.checklists.enums import (
    ChecklistItemSourceState,
    ChecklistItemType,
    ChecklistStatus,
    StorageOrigin,
    SyncStatus,
)
from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class SavedChecklist(Base):
    __tablename__ = "saved_checklists"

    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(Integer, nullable=True, index=True)
    guest_session_id = Column(String(36), nullable=True, index=True)
    claimed_guest_session_id = Column(String(36), nullable=True, index=True)
    ownership_status = Column(String(16), default="active", nullable=False, index=True)
    claimed_at = Column(DateTime, nullable=True)
    service_id = Column(String(160), nullable=False, index=True)
    service_name = Column(String(240), nullable=False)
    language = Column(String(16), default="en", nullable=False)
    status = Column(
        String(24), default=ChecklistStatus.NOT_STARTED.value, nullable=False, index=True
    )
    progress_percentage = Column(Float, default=0.0, nullable=False)
    source_version = Column(String(128), nullable=False)
    source_citations = Column(JSON, nullable=False, default=list)
    knowledge_context = Column(JSON, nullable=False, default=dict)
    storage_origin = Column(String(16), nullable=False, index=True)
    sync_status = Column(
        String(16), default=SyncStatus.SYNCED.value, nullable=False, index=True
    )
    sync_error = Column(Text, nullable=True)
    last_sync_attempt_at = Column(DateTime, nullable=True)
    synced_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
    last_opened_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)

    items = relationship(
        "ChecklistItem",
        back_populates="checklist",
        cascade="all, delete-orphan",
        order_by="ChecklistItem.sequence_number",
    )

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_session_id IS NULL) OR "
            "(user_id IS NULL AND guest_session_id IS NOT NULL)",
            name="ck_saved_checklist_single_owner",
        ),
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="ck_saved_checklist_progress_range",
        ),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed', 'archived', 'outdated')",
            name="ck_saved_checklist_status",
        ),
        CheckConstraint(
            "storage_origin IN ('postgresql', 'sqlite')",
            name="ck_saved_checklist_storage_origin",
        ),
        CheckConstraint(
            "sync_status IN ('pending', 'synced', 'failed', 'conflict')",
            name="ck_saved_checklist_sync_status",
        ),
        Index(
            "ix_saved_checklists_user_active",
            "user_id",
            "is_archived",
            "deleted_at",
            "updated_at",
        ),
        Index(
            "ix_saved_checklists_guest_active",
            "guest_session_id",
            "is_archived",
            "deleted_at",
            "updated_at",
        ),
    )


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(String(36), primary_key=True, default=new_uuid)
    checklist_id = Column(
        String(36),
        ForeignKey("saved_checklists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type = Column(String(24), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    sequence_number = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    user_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
    source_item_key = Column(String(128), nullable=False)
    source_state = Column(
        String(16), default=ChecklistItemSourceState.CURRENT.value, nullable=False, index=True
    )

    checklist = relationship("SavedChecklist", back_populates="items")

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('document', 'process_step', 'warning', 'important_note', 'timeline')",
            name="ck_checklist_item_type",
        ),
        CheckConstraint(
            "source_state IN ('current', 'new', 'changed', 'removed', 'outdated')",
            name="ck_checklist_item_source_state",
        ),
        CheckConstraint("sequence_number >= 0", name="ck_checklist_item_sequence"),
        UniqueConstraint(
            "checklist_id", "source_item_key", name="uq_checklist_source_item"
        ),
    )
