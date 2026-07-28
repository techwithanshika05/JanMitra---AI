from enum import StrEnum


class ChecklistStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    OUTDATED = "outdated"


class ChecklistItemType(StrEnum):
    DOCUMENT = "document"
    PROCESS_STEP = "process_step"
    WARNING = "warning"
    IMPORTANT_NOTE = "important_note"
    TIMELINE = "timeline"


class ChecklistItemSourceState(StrEnum):
    CURRENT = "current"
    NEW = "new"
    CHANGED = "changed"
    REMOVED = "removed"
    OUTDATED = "outdated"


class StorageOrigin(StrEnum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


class SyncStatus(StrEnum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"
