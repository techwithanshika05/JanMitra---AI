from typing import Sequence

from sqlalchemy.orm import Session, selectinload

from app.checklists.enums import SyncStatus
from app.checklists.models import ChecklistItem, SavedChecklist, utc_now
from app.checklists.repository import ChecklistOwner, ChecklistRepository


class SQLAlchemyChecklistRepository(ChecklistRepository):
    """One repository implementation shared by PostgreSQL and SQLite."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _owned_query(session: Session, owner: ChecklistOwner):
        query = session.query(SavedChecklist)
        if owner.user_id is not None:
            return query.filter(
                SavedChecklist.user_id == owner.user_id,
                SavedChecklist.guest_session_id.is_(None),
            )
        return query.filter(
            SavedChecklist.guest_session_id == owner.guest_session_id,
            SavedChecklist.user_id.is_(None),
        )

    def add(self, checklist: SavedChecklist) -> SavedChecklist:
        self.session.add(checklist)
        self.session.flush()
        return checklist

    def get_owned(
        self,
        checklist_id: str,
        owner: ChecklistOwner,
        *,
        include_deleted: bool = False,
    ) -> SavedChecklist | None:
        query = self._owned_query(self.session, owner).filter(
            SavedChecklist.id == checklist_id
        )
        if not include_deleted:
            query = query.filter(SavedChecklist.deleted_at.is_(None))
        checklist = query.options(selectinload(SavedChecklist.items)).first()
        if checklist is not None:
            checklist.last_opened_at = utc_now()
        return checklist

    def get_by_id_for_sync(self, checklist_id: str) -> SavedChecklist | None:
        return (
            self.session.query(SavedChecklist)
            .filter(SavedChecklist.id == checklist_id)
            .options(selectinload(SavedChecklist.items))
            .first()
        )

    def list_owned(
        self,
        owner: ChecklistOwner,
        *,
        archived: bool = False,
    ) -> Sequence[SavedChecklist]:
        return (
            self._owned_query(self.session, owner)
            .filter(
                SavedChecklist.is_archived.is_(archived),
                SavedChecklist.deleted_at.is_(None),
            )
            .options(selectinload(SavedChecklist.items))
            .order_by(SavedChecklist.updated_at.desc())
            .all()
        )

    def save(self, checklist: SavedChecklist) -> SavedChecklist:
        checklist.updated_at = utc_now()
        self.session.add(checklist)
        self.session.flush()
        return checklist

    def save_item(self, item: ChecklistItem) -> ChecklistItem:
        item.updated_at = utc_now()
        self.session.add(item)
        self.session.flush()
        return item

    def delete(self, checklist: SavedChecklist) -> None:
        checklist.deleted_at = utc_now()
        checklist.updated_at = utc_now()
        self.session.add(checklist)
        self.session.flush()

    def pending_sync(self, *, limit: int = 100) -> Sequence[SavedChecklist]:
        return (
            self.session.query(SavedChecklist)
            .filter(
                SavedChecklist.sync_status.in_(
                    [SyncStatus.PENDING.value, SyncStatus.FAILED.value]
                ),
            )
            .options(selectinload(SavedChecklist.items))
            .order_by(SavedChecklist.updated_at.asc())
            .limit(limit)
            .all()
        )

    def all_for_analytics(self) -> Sequence[SavedChecklist]:
        return (
            self.session.query(SavedChecklist)
            .filter(SavedChecklist.deleted_at.is_(None))
            .options(selectinload(SavedChecklist.items))
            .all()
        )

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
