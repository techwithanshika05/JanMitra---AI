import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.checklists.enums import (
    ChecklistItemSourceState,
    ChecklistItemType,
    ChecklistStatus,
    StorageOrigin,
    SyncStatus,
)
from app.checklists.note_safety import SensitiveNoteError
from app.checklists.repository import ChecklistOwner
from app.checklists.schemas import (
    ChecklistCreate,
    ChecklistItemPatch,
    ChecklistRefresh,
    ChecklistSourceItem,
    SavedChecklistOut,
)
from app.checklists.service import (
    ChecklistImportApprovalRequiredError,
    ChecklistNotFoundError,
    SavedChecklistService,
)
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


def source_item(
    key: str,
    sequence: int,
    *,
    required: bool = True,
    title: str | None = None,
) -> ChecklistSourceItem:
    return ChecklistSourceItem(
        item_type=ChecklistItemType.DOCUMENT,
        title=title or key.replace("-", " ").title(),
        description="Official requirement",
        sequence_number=sequence,
        is_required=required,
        source_item_key=key,
    )


def payload() -> ChecklistCreate:
    return ChecklistCreate(
        service_id="new_ration_card",
        service_name="New ration card",
        language="en",
        source_version="v1",
        items=[
            source_item("identity-proof", 1),
            source_item("address-proof", 2),
            source_item("optional-photo", 3, required=False),
        ],
    )


def service_and_db():
    db = TestingSession()
    return SavedChecklistService(SQLAlchemyChecklistRepository(db)), db


def create_guest(service: SavedChecklistService, guest_id: str = "guest-one"):
    return service.create(
        ChecklistOwner(guest_session_id=guest_id),
        payload(),
        storage_origin=StorageOrigin.SQLITE,
        sync_status=SyncStatus.PENDING,
    )


def test_create_sets_storage_identity_and_zero_progress():
    service, db = service_and_db()
    checklist = create_guest(service)
    assert checklist.guest_session_id == "guest-one"
    assert checklist.storage_origin == StorageOrigin.SQLITE.value
    assert checklist.sync_status == SyncStatus.PENDING.value
    assert checklist.progress_percentage == 0
    assert checklist.status == ChecklistStatus.NOT_STARTED.value
    response = SavedChecklistOut.model_validate(checklist)
    assert response.storage_origin == StorageOrigin.SQLITE
    assert len(response.items) == 3
    db.close()


def test_progress_uses_required_items_only():
    service, db = service_and_db()
    owner = ChecklistOwner(guest_session_id="guest-one")
    checklist = create_guest(service)

    checklist = service.update_item(
        checklist.id,
        checklist.items[0].id,
        owner,
        ChecklistItemPatch(is_completed=True),
    )
    assert checklist.progress_percentage == 50
    assert checklist.status == ChecklistStatus.IN_PROGRESS.value

    optional = next(item for item in checklist.items if not item.is_required)
    checklist = service.update_item(
        checklist.id,
        optional.id,
        owner,
        ChecklistItemPatch(is_completed=False),
    )
    assert checklist.progress_percentage == 50

    second_required = next(
        item for item in checklist.items if item.is_required and not item.is_completed
    )
    checklist = service.update_item(
        checklist.id,
        second_required.id,
        owner,
        ChecklistItemPatch(is_completed=True),
    )
    assert checklist.progress_percentage == 100
    assert checklist.status == ChecklistStatus.COMPLETED.value
    db.close()


@pytest.mark.parametrize(
    "note",
    [
        "My Aadhaar number is 1234 5678 9012",
        "OTP: 123456",
        "password is Secret123",
        "bank account number 123456789012",
        "ration card number AB-123456",
    ],
)
def test_sensitive_notes_are_rejected(note):
    service, db = service_and_db()
    owner = ChecklistOwner(guest_session_id="guest-one")
    checklist = create_guest(service)
    with pytest.raises(SensitiveNoteError):
        service.update_item(
            checklist.id,
            checklist.items[0].id,
            owner,
            ChecklistItemPatch(user_note=note),
        )
    db.close()


def test_general_note_is_trimmed_and_saved():
    service, db = service_and_db()
    owner = ChecklistOwner(guest_session_id="guest-one")
    checklist = create_guest(service)
    updated = service.update_item(
        checklist.id,
        checklist.items[0].id,
        owner,
        ChecklistItemPatch(user_note="  Submitted at the local office.  "),
    )
    assert updated.items[0].user_note == "Submitted at the local office."
    cleared = service.update_item(
        checklist.id,
        checklist.items[0].id,
        owner,
        ChecklistItemPatch(user_note=None),
    )
    assert cleared.items[0].user_note is None
    db.close()


def test_archive_restore_delete_and_owner_isolation():
    service, db = service_and_db()
    owner = ChecklistOwner(guest_session_id="guest-one")
    checklist = create_guest(service)
    archived = service.archive(checklist.id, owner)
    assert archived.is_archived is True
    assert archived.status == ChecklistStatus.ARCHIVED.value
    assert service.list_active(owner) == []

    restored = service.restore(checklist.id, owner)
    assert restored.is_archived is False
    assert restored.status == ChecklistStatus.NOT_STARTED.value

    with pytest.raises(ChecklistNotFoundError):
        service.get(checklist.id, ChecklistOwner(guest_session_id="outsider"))

    service.delete(checklist.id, owner)
    with pytest.raises(ChecklistNotFoundError):
        service.get(checklist.id, owner)
    db.close()


def test_guest_import_requires_consent_and_preserves_progress():
    service, db = service_and_db()
    guest = ChecklistOwner(guest_session_id="guest-one")
    user = ChecklistOwner(user_id=81)
    checklist = create_guest(service)
    checklist = service.update_item(
        checklist.id,
        checklist.items[0].id,
        guest,
        ChecklistItemPatch(is_completed=True),
    )

    with pytest.raises(ChecklistImportApprovalRequiredError):
        service.import_guest(guest, user, approved=False)
    assert service.import_guest(guest, user, approved=True) == 1
    imported = service.get(checklist.id, user)
    assert imported.user_id == 81
    assert imported.guest_session_id is None
    assert imported.progress_percentage == 50
    db.close()


def test_refresh_preserves_completion_and_marks_source_changes():
    service, db = service_and_db()
    owner = ChecklistOwner(guest_session_id="guest-one")
    checklist = create_guest(service)
    checklist = service.update_item(
        checklist.id,
        checklist.items[0].id,
        owner,
        ChecklistItemPatch(is_completed=True),
    )

    refresh = ChecklistRefresh(
        source_version="v2",
        items=[
            source_item("identity-proof", 1, title="Updated identity proof"),
            source_item("optional-photo", 2, required=False),
            source_item("income-proof", 3),
        ],
    )
    result = service.refresh(checklist.id, owner, refresh)
    by_key = {item.source_item_key: item for item in result.checklist.items}

    assert result.source_version_changed is True
    assert result.new_items == 1
    assert result.changed_items == 2
    assert result.removed_items == 1
    assert by_key["identity-proof"].is_completed is True
    assert by_key["identity-proof"].source_state == ChecklistItemSourceState.CHANGED.value
    assert by_key["address-proof"].source_state == ChecklistItemSourceState.REMOVED.value
    assert by_key["address-proof"].is_required is False
    assert by_key["income-proof"].source_state == ChecklistItemSourceState.NEW.value
    assert result.checklist.status == ChecklistStatus.OUTDATED.value
    assert result.checklist.progress_percentage == 50
    db.close()
