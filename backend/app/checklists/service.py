from dataclasses import dataclass

from app.checklists.enums import (
    ChecklistItemSourceState,
    ChecklistStatus,
    StorageOrigin,
    SyncStatus,
)
from app.checklists.models import ChecklistItem, SavedChecklist, utc_now
from app.checklists.note_safety import validate_general_note
from app.checklists.repository import ChecklistOwner, ChecklistRepository
from app.checklists.schemas import (
    ChecklistCreate,
    ChecklistItemPatch,
    ChecklistPatch,
    ChecklistRefresh,
)


class ChecklistNotFoundError(LookupError):
    pass


class ChecklistItemNotFoundError(LookupError):
    pass


class ChecklistImportApprovalRequiredError(PermissionError):
    pass


@dataclass(frozen=True)
class RefreshSummary:
    checklist: SavedChecklist
    new_items: int
    changed_items: int
    removed_items: int
    source_version_changed: bool


class SavedChecklistService:
    def __init__(self, repository: ChecklistRepository):
        self.repository = repository

    def _transaction(self, operation):
        try:
            result = operation()
            self.repository.commit()
            return result
        except Exception:
            self.repository.rollback()
            raise

    @staticmethod
    def _owned_checklist(
        repository: ChecklistRepository,
        checklist_id: str,
        owner: ChecklistOwner,
    ) -> SavedChecklist:
        checklist = repository.get_owned(checklist_id, owner)
        if checklist is None:
            raise ChecklistNotFoundError("Saved checklist not found")
        return checklist

    @staticmethod
    def _find_item(checklist: SavedChecklist, item_id: str) -> ChecklistItem:
        item = next((candidate for candidate in checklist.items if candidate.id == item_id), None)
        if item is None:
            raise ChecklistItemNotFoundError("Checklist item not found")
        return item

    @staticmethod
    def recalculate_progress(checklist: SavedChecklist) -> float:
        required = [
            item
            for item in checklist.items
            if item.is_required
            and item.source_state
            not in {
                ChecklistItemSourceState.REMOVED.value,
                ChecklistItemSourceState.OUTDATED.value,
            }
        ]
        completed = sum(1 for item in required if item.is_completed)
        percentage = round((completed / len(required)) * 100, 2) if required else 0.0
        checklist.progress_percentage = percentage

        if checklist.is_archived:
            checklist.status = ChecklistStatus.ARCHIVED.value
        elif checklist.status == ChecklistStatus.OUTDATED.value:
            pass
        elif percentage == 100 and required:
            checklist.status = ChecklistStatus.COMPLETED.value
        elif completed:
            checklist.status = ChecklistStatus.IN_PROGRESS.value
        else:
            checklist.status = ChecklistStatus.NOT_STARTED.value
        return percentage

    def create(
        self,
        owner: ChecklistOwner,
        payload: ChecklistCreate,
        *,
        storage_origin: StorageOrigin,
        sync_status: SyncStatus,
    ) -> SavedChecklist:
        def operation():
            checklist = SavedChecklist(
                user_id=owner.user_id,
                guest_session_id=owner.guest_session_id,
                service_id=payload.service_id,
                service_name=payload.service_name,
                language=payload.language,
                source_version=payload.source_version,
                source_citations=payload.source_citations,
                knowledge_context=payload.knowledge_context,
                storage_origin=storage_origin.value,
                sync_status=sync_status.value,
                items=[
                    ChecklistItem(
                        item_type=item.item_type.value,
                        title=item.title,
                        description=item.description,
                        sequence_number=item.sequence_number,
                        is_required=item.is_required,
                        source_item_key=item.source_item_key,
                        source_state=ChecklistItemSourceState.CURRENT.value,
                    )
                    for item in payload.items
                ],
            )
            self.recalculate_progress(checklist)
            return self.repository.add(checklist)

        return self._transaction(operation)

    def list_active(self, owner: ChecklistOwner):
        return self.repository.list_owned(owner, archived=False)

    def list_archived(self, owner: ChecklistOwner):
        return self.repository.list_owned(owner, archived=True)

    def get(self, checklist_id: str, owner: ChecklistOwner) -> SavedChecklist:
        def operation():
            checklist = self._owned_checklist(self.repository, checklist_id, owner)
            return self.repository.save(checklist)

        return self._transaction(operation)

    def update(
        self,
        checklist_id: str,
        owner: ChecklistOwner,
        payload: ChecklistPatch,
    ) -> SavedChecklist:
        def operation():
            checklist = self._owned_checklist(self.repository, checklist_id, owner)
            if payload.language is not None:
                checklist.language = payload.language
            return self.repository.save(checklist)

        return self._transaction(operation)

    def update_item(
        self,
        checklist_id: str,
        item_id: str,
        owner: ChecklistOwner,
        payload: ChecklistItemPatch,
    ) -> SavedChecklist:
        def operation():
            checklist = self._owned_checklist(self.repository, checklist_id, owner)
            item = self._find_item(checklist, item_id)
            if payload.is_completed is not None:
                item.is_completed = payload.is_completed
                item.completed_at = utc_now() if payload.is_completed else None
            if "user_note" in payload.model_fields_set:
                item.user_note = validate_general_note(payload.user_note)
            self.repository.save_item(item)
            self.recalculate_progress(checklist)
            return self.repository.save(checklist)

        return self._transaction(operation)

    def archive(self, checklist_id: str, owner: ChecklistOwner) -> SavedChecklist:
        def operation():
            checklist = self._owned_checklist(self.repository, checklist_id, owner)
            checklist.is_archived = True
            checklist.status = ChecklistStatus.ARCHIVED.value
            return self.repository.save(checklist)

        return self._transaction(operation)

    def restore(self, checklist_id: str, owner: ChecklistOwner) -> SavedChecklist:
        def operation():
            checklist = self._owned_checklist(self.repository, checklist_id, owner)
            checklist.is_archived = False
            checklist.status = ChecklistStatus.NOT_STARTED.value
            self.recalculate_progress(checklist)
            return self.repository.save(checklist)

        return self._transaction(operation)

    def delete(self, checklist_id: str, owner: ChecklistOwner) -> None:
        def operation():
            checklist = self._owned_checklist(self.repository, checklist_id, owner)
            self.repository.delete(checklist)

        self._transaction(operation)

    def import_guest(
        self,
        guest_owner: ChecklistOwner,
        user_owner: ChecklistOwner,
        *,
        approved: bool,
    ) -> int:
        if not approved:
            raise ChecklistImportApprovalRequiredError(
                "Guest checklist import requires explicit user approval"
            )
        if guest_owner.guest_session_id is None or user_owner.user_id is None:
            raise ValueError("Guest-to-user import requires guest and user identities")

        def operation():
            rows = [
                *self.repository.list_owned(guest_owner, archived=False),
                *self.repository.list_owned(guest_owner, archived=True),
            ]
            for checklist in rows:
                checklist.user_id = user_owner.user_id
                checklist.guest_session_id = None
                self.repository.save(checklist)
            return len(rows)

        return self._transaction(operation)

    def refresh(
        self,
        checklist_id: str,
        owner: ChecklistOwner,
        payload: ChecklistRefresh,
    ) -> RefreshSummary:
        def operation():
            checklist = self._owned_checklist(self.repository, checklist_id, owner)
            version_changed = checklist.source_version != payload.source_version
            existing = {item.source_item_key: item for item in checklist.items}
            incoming_keys = {item.source_item_key for item in payload.items}
            new_count = changed_count = removed_count = 0

            for source_item in payload.items:
                current = existing.get(source_item.source_item_key)
                if current is None:
                    checklist.items.append(
                        ChecklistItem(
                            item_type=source_item.item_type.value,
                            title=source_item.title,
                            description=source_item.description,
                            sequence_number=source_item.sequence_number,
                            is_required=source_item.is_required,
                            source_item_key=source_item.source_item_key,
                            source_state=ChecklistItemSourceState.NEW.value,
                        )
                    )
                    new_count += 1
                    continue

                changed = any(
                    (
                        current.item_type != source_item.item_type.value,
                        current.title != source_item.title,
                        current.description != source_item.description,
                        current.sequence_number != source_item.sequence_number,
                        current.is_required != source_item.is_required,
                    )
                )
                current.item_type = source_item.item_type.value
                current.title = source_item.title
                current.description = source_item.description
                current.sequence_number = source_item.sequence_number
                current.is_required = source_item.is_required
                current.source_state = (
                    ChecklistItemSourceState.CHANGED.value
                    if changed
                    else ChecklistItemSourceState.CURRENT.value
                )
                if changed:
                    changed_count += 1

            for key, current in existing.items():
                if key not in incoming_keys:
                    current.source_state = ChecklistItemSourceState.REMOVED.value
                    current.is_required = False
                    removed_count += 1

            checklist.source_version = payload.source_version
            checklist.source_citations = payload.source_citations
            if version_changed or new_count or changed_count or removed_count:
                checklist.status = ChecklistStatus.OUTDATED.value
            self.recalculate_progress(checklist)
            saved = self.repository.save(checklist)
            return RefreshSummary(
                checklist=saved,
                new_items=new_count,
                changed_items=changed_count,
                removed_items=removed_count,
                source_version_changed=version_changed,
            )

        return self._transaction(operation)
