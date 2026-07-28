from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.checklists.enums import StorageOrigin, SyncStatus
from app.checklists.repository import ChecklistOwner
from app.checklists.schemas import ChecklistCreate, ChecklistSourceItem
from app.checklists.service import SavedChecklistService
from app.checklists.sqlalchemy_repository import SQLAlchemyChecklistRepository
from app.checklists.sync_service import (
    ChecklistSynchronizationService,
    _clone_for_primary,
)
from app.database import Base


def repository_pair():
    fallback_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    primary_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=fallback_engine)
    Base.metadata.create_all(bind=primary_engine)
    fallback_db = sessionmaker(bind=fallback_engine, autoflush=False)()
    primary_db = sessionmaker(bind=primary_engine, autoflush=False)()
    return (
        SQLAlchemyChecklistRepository(fallback_db),
        SQLAlchemyChecklistRepository(primary_db),
        fallback_db,
        primary_db,
    )


def create_pending(repository):
    return SavedChecklistService(repository).create(
        ChecklistOwner(guest_session_id="sync-guest"),
        ChecklistCreate(
            service_id="new_ration_card",
            service_name="New ration card",
            source_version="v1",
            items=[
                ChecklistSourceItem(
                    item_type="document",
                    title="Identity proof",
                    sequence_number=1,
                    source_item_key="document:identity",
                )
            ],
        ),
        storage_origin=StorageOrigin.SQLITE,
        sync_status=SyncStatus.PENDING,
    )


def test_pending_record_is_copied_and_source_marked_synced():
    fallback, primary, fallback_db, primary_db = repository_pair()
    source = create_pending(fallback)
    result = ChecklistSynchronizationService.sync_repositories(fallback, primary)

    assert result.examined == 1
    assert result.synced == 1
    target = primary.get_by_id_for_sync(source.id)
    assert target is not None
    assert target.storage_origin == StorageOrigin.POSTGRESQL.value
    assert target.sync_status == SyncStatus.SYNCED.value
    assert target.items[0].title == "Identity proof"
    assert fallback.get_by_id_for_sync(source.id).sync_status == SyncStatus.SYNCED.value
    fallback_db.close()
    primary_db.close()


def test_retry_after_target_write_is_idempotent():
    fallback, primary, fallback_db, primary_db = repository_pair()
    source = create_pending(fallback)
    first = ChecklistSynchronizationService.sync_repositories(fallback, primary)
    assert first.synced == 1

    source = fallback.get_by_id_for_sync(source.id)
    source.sync_status = SyncStatus.PENDING.value
    fallback.save(source)
    fallback.commit()
    retry = ChecklistSynchronizationService.sync_repositories(fallback, primary)

    assert retry.synced == 1
    assert retry.conflicts == 0
    fallback_db.close()
    primary_db.close()


def test_different_primary_record_is_marked_conflict_without_overwrite():
    fallback, primary, fallback_db, primary_db = repository_pair()
    source = create_pending(fallback)
    divergent = _clone_for_primary(source)
    divergent.service_name = "Different primary version"
    primary.add(divergent)
    primary.commit()

    result = ChecklistSynchronizationService.sync_repositories(fallback, primary)
    conflict = fallback.get_by_id_for_sync(source.id)
    preserved = primary.get_by_id_for_sync(source.id)

    assert result.conflicts == 1
    assert conflict.sync_status == SyncStatus.CONFLICT.value
    assert "neither record was overwritten" in conflict.sync_error
    assert preserved.service_name == "Different primary version"
    fallback_db.close()
    primary_db.close()


class FailingPrimary(SQLAlchemyChecklistRepository):
    def add(self, checklist):
        raise RuntimeError("simulated PostgreSQL outage")


def test_target_failure_marks_fallback_record_failed_for_retry():
    fallback, primary, fallback_db, primary_db = repository_pair()
    source = create_pending(fallback)
    failing = FailingPrimary(primary.session)

    result = ChecklistSynchronizationService.sync_repositories(fallback, failing)
    failed = fallback.get_by_id_for_sync(source.id)

    assert result.failed == 1
    assert failed.sync_status == SyncStatus.FAILED.value
    assert "simulated PostgreSQL outage" in failed.sync_error
    fallback_db.close()
    primary_db.close()


def test_soft_deleted_pending_record_syncs_as_tombstone():
    fallback, primary, fallback_db, primary_db = repository_pair()
    source = create_pending(fallback)
    SavedChecklistService(fallback).delete(
        source.id, ChecklistOwner(guest_session_id="sync-guest")
    )

    result = ChecklistSynchronizationService.sync_repositories(fallback, primary)
    target = primary.get_by_id_for_sync(source.id)

    assert result.synced == 1
    assert target is not None
    assert target.deleted_at is not None
    fallback_db.close()
    primary_db.close()
