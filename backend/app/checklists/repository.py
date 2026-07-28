from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from app.checklists.models import ChecklistItem, SavedChecklist


@dataclass(frozen=True)
class ChecklistOwner:
    user_id: int | None = None
    guest_session_id: str | None = None

    def __post_init__(self) -> None:
        if (self.user_id is None) == (self.guest_session_id is None):
            raise ValueError("Exactly one checklist owner is required")


class ChecklistRepository(ABC):
    @abstractmethod
    def add(self, checklist: SavedChecklist) -> SavedChecklist:
        raise NotImplementedError

    @abstractmethod
    def get_owned(
        self,
        checklist_id: str,
        owner: ChecklistOwner,
        *,
        include_deleted: bool = False,
    ) -> SavedChecklist | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id_for_sync(self, checklist_id: str) -> SavedChecklist | None:
        raise NotImplementedError

    @abstractmethod
    def list_owned(
        self,
        owner: ChecklistOwner,
        *,
        archived: bool = False,
    ) -> Sequence[SavedChecklist]:
        raise NotImplementedError

    @abstractmethod
    def save(self, checklist: SavedChecklist) -> SavedChecklist:
        raise NotImplementedError

    @abstractmethod
    def save_item(self, item: ChecklistItem) -> ChecklistItem:
        raise NotImplementedError

    @abstractmethod
    def delete(self, checklist: SavedChecklist) -> None:
        raise NotImplementedError

    @abstractmethod
    def pending_sync(self, *, limit: int = 100) -> Sequence[SavedChecklist]:
        raise NotImplementedError

    @abstractmethod
    def all_for_analytics(self) -> Sequence[SavedChecklist]:
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError
