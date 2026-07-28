from dataclasses import dataclass
import hashlib
import json
import logging

from app.checklists.enums import StorageOrigin, SyncStatus
from app.checklists.models import ChecklistItem, SavedChecklist, utc_now
from app.checklists.repository import ChecklistRepository
from app.checklists.storage import ChecklistStorage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncBatchResult:
    examined: int = 0
    synced: int = 0
    failed: int = 0
    conflicts: int = 0
    primary_available: bool = True


def _item_data(item: ChecklistItem) -> dict:
    return {
        "id": item.id,
        "item_type": item.item_type,
        "title": item.title,
        "description": item.description,
        "sequence_number": item.sequence_number,
        "is_required": item.is_required,
        "is_completed": item.is_completed,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "user_note": item.user_note,
        "source_item_key": item.source_item_key,
        "source_state": item.source_state,
        "deleted": False,
    }


def checklist_fingerprint(checklist: SavedChecklist) -> str:
    data = {
        "id": checklist.id,
        "user_id": checklist.user_id,
        "guest_session_id": checklist.guest_session_id,
        "service_id": checklist.service_id,
        "service_name": checklist.service_name,
        "language": checklist.language,
        "status": checklist.status,
        "progress_percentage": checklist.progress_percentage,
        "source_version": checklist.source_version,
        "source_citations": checklist.source_citations,
        "knowledge_context": checklist.knowledge_context,
        "is_archived": checklist.is_archived,
        "deleted_at": checklist.deleted_at.isoformat() if checklist.deleted_at else None,
        "items": sorted(
            (_item_data(item) for item in checklist.items),
            key=lambda item: (item["source_item_key"], item["id"]),
        ),
    }
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _clone_for_primary(source: SavedChecklist) -> SavedChecklist:
    return SavedChecklist(
        id=source.id,
        user_id=source.user_id,
        guest_session_id=source.guest_session_id,
        service_id=source.service_id,
        service_name=source.service_name,
        language=source.language,
        status=source.status,
        progress_percentage=source.progress_percentage,
        source_version=source.source_version,
        source_citations=source.source_citations,
        knowledge_context=source.knowledge_context,
        storage_origin=StorageOrigin.POSTGRESQL.value,
        sync_status=SyncStatus.SYNCED.value,
        is_archived=source.is_archived,
        created_at=source.created_at,
        updated_at=source.updated_at,
        last_opened_at=source.last_opened_at,
        deleted_at=source.deleted_at,
        synced_at=utc_now(),
        items=[
            ChecklistItem(
                id=item.id,
                item_type=item.item_type,
                title=item.title,
                description=item.description,
                sequence_number=item.sequence_number,
                is_required=item.is_required,
                is_completed=item.is_completed,
                completed_at=item.completed_at,
                user_note=item.user_note,
                created_at=item.created_at,
                updated_at=item.updated_at,
                source_item_key=item.source_item_key,
                source_state=item.source_state,
            )
            for item in source.items
        ],
    )


class ChecklistSynchronizationService:
    def __init__(self, storage: ChecklistStorage | None = None):
        self.storage = storage

    @staticmethod
    def sync_repositories(
        fallback: ChecklistRepository,
        primary: ChecklistRepository,
        *,
        limit: int = 100,
    ) -> SyncBatchResult:
        rows = list(fallback.pending_sync(limit=limit))
        synced = failed = conflicts = 0

        for source in rows:
            source_id = source.id
            source.last_sync_attempt_at = utc_now()
            source.sync_error = None
            try:
                target = primary.get_by_id_for_sync(source.id)
                if target is None:
                    primary.add(_clone_for_primary(source))
                    primary.commit()
                elif checklist_fingerprint(target) != checklist_fingerprint(source):
                    primary.rollback()
                    source.sync_status = SyncStatus.CONFLICT.value
                    source.sync_error = (
                        "PostgreSQL contains a different version; neither record was overwritten."
                    )
                    fallback.save(source)
                    fallback.commit()
                    conflicts += 1
                    continue

                source.sync_status = SyncStatus.SYNCED.value
                source.sync_error = None
                source.synced_at = utc_now()
                fallback.save(source)
                fallback.commit()
                synced += 1
            except Exception as exc:
                primary.rollback()
                fallback.rollback()
                source = fallback.get_by_id_for_sync(source_id)
                if source is not None:
                    source.sync_status = SyncStatus.FAILED.value
                    source.sync_error = str(exc)[:1000]
                    source.last_sync_attempt_at = utc_now()
                    fallback.save(source)
                    fallback.commit()
                failed += 1
                logger.exception("Saved checklist synchronization failed for %s", source_id)

        return SyncBatchResult(
            examined=len(rows),
            synced=synced,
            failed=failed,
            conflicts=conflicts,
        )

    def sync_pending(self, *, limit: int = 100) -> SyncBatchResult:
        if self.storage is None:
            raise RuntimeError("Checklist storage is required for live synchronization")
        if not self.storage.primary_is_healthy():
            return SyncBatchResult(primary_available=False)

        with self.storage.repository_for_sync(StorageOrigin.SQLITE) as fallback:
            with self.storage.repository_for_sync(StorageOrigin.POSTGRESQL) as primary:
                return self.sync_repositories(fallback, primary, limit=limit)
