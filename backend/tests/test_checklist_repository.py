import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.checklists.enums import (
    ChecklistItemType,
    ChecklistStatus,
    StorageOrigin,
    SyncStatus,
)
from app.checklists.models import ChecklistItem, SavedChecklist, utc_now
from app.checklists.repository import ChecklistOwner
from app.checklists.sqlalchemy_repository import SQLAlchemyChecklistRepository
from app.database import Base


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def make_checklist(
    *,
    user_id: int | None = None,
    guest_session_id: str | None = None,
    sync_status: SyncStatus = SyncStatus.SYNCED,
) -> SavedChecklist:
    return SavedChecklist(
        user_id=user_id,
        guest_session_id=guest_session_id,
        service_id="new_ration_card",
        service_name="New ration card",
        language="en",
        status=ChecklistStatus.NOT_STARTED.value,
        progress_percentage=0,
        source_version="source-v1",
        storage_origin=StorageOrigin.SQLITE.value,
        sync_status=sync_status.value,
        items=[
            ChecklistItem(
                item_type=ChecklistItemType.DOCUMENT.value,
                title="Identity proof",
                description="Use an accepted identity document.",
                sequence_number=1,
                is_required=True,
                source_item_key="document:identity-proof",
            )
        ],
    )


def test_owner_requires_exactly_one_identity():
    with pytest.raises(ValueError):
        ChecklistOwner()
    with pytest.raises(ValueError):
        ChecklistOwner(user_id=1, guest_session_id="guest")


def test_repository_enforces_owner_filtering():
    db = TestingSession()
    repository = SQLAlchemyChecklistRepository(db)
    checklist = repository.add(make_checklist(guest_session_id="guest-one"))
    repository.commit()

    assert repository.get_owned(
        checklist.id, ChecklistOwner(guest_session_id="guest-one")
    ) is not None
    assert repository.get_owned(
        checklist.id, ChecklistOwner(guest_session_id="guest-two")
    ) is None
    assert repository.get_owned(checklist.id, ChecklistOwner(user_id=7)) is None
    db.close()


def test_active_archive_and_soft_delete_filters():
    db = TestingSession()
    repository = SQLAlchemyChecklistRepository(db)
    owner = ChecklistOwner(user_id=42)
    active = repository.add(make_checklist(user_id=42))
    archived = repository.add(make_checklist(user_id=42))
    archived.is_archived = True
    archived.status = ChecklistStatus.ARCHIVED.value
    repository.commit()

    assert [row.id for row in repository.list_owned(owner)] == [active.id]
    assert [row.id for row in repository.list_owned(owner, archived=True)] == [
        archived.id
    ]

    repository.delete(active)
    repository.commit()
    assert repository.get_owned(active.id, owner) is None
    assert repository.get_owned(active.id, owner, include_deleted=True) is not None
    db.close()


def test_pending_sync_returns_pending_and_failed_only():
    db = TestingSession()
    repository = SQLAlchemyChecklistRepository(db)
    pending = repository.add(
        make_checklist(guest_session_id="guest-pending", sync_status=SyncStatus.PENDING)
    )
    failed = repository.add(
        make_checklist(guest_session_id="guest-failed", sync_status=SyncStatus.FAILED)
    )
    repository.add(
        make_checklist(guest_session_id="guest-synced", sync_status=SyncStatus.SYNCED)
    )
    repository.commit()

    result = {row.id for row in repository.pending_sync()}
    assert result == {pending.id, failed.id}
    db.close()


def test_database_constraints_reject_invalid_owner_and_progress():
    db = TestingSession()
    db.add(make_checklist())
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    invalid_progress = make_checklist(user_id=1)
    invalid_progress.progress_percentage = 101
    db.add(invalid_progress)
    with pytest.raises(IntegrityError):
        db.commit()
    db.close()


def test_item_completion_fields_persist_without_sensitive_profile_data():
    db = TestingSession()
    repository = SQLAlchemyChecklistRepository(db)
    checklist = repository.add(make_checklist(user_id=9))
    item = checklist.items[0]
    item.is_completed = True
    item.completed_at = utc_now()
    item.user_note = "Submitted at the district office."
    repository.save_item(item)
    repository.commit()

    loaded = repository.get_owned(checklist.id, ChecklistOwner(user_id=9))
    assert loaded is not None
    assert loaded.items[0].is_completed is True
    assert loaded.items[0].user_note == "Submitted at the district office."
    db.close()
