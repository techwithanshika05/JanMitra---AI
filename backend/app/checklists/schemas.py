from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.checklists.enums import (
    ChecklistItemSourceState,
    ChecklistItemType,
    ChecklistStatus,
    StorageOrigin,
    SyncStatus,
)


class ChecklistSourceItem(BaseModel):
    item_type: ChecklistItemType
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    sequence_number: int = Field(ge=0)
    is_required: bool = True
    source_item_key: str = Field(min_length=1, max_length=128)


class ChecklistCreate(BaseModel):
    service_id: str = Field(min_length=1, max_length=160)
    service_name: str = Field(min_length=1, max_length=240)
    language: str = Field(default="en", pattern=r"^(en|hi|hinglish)$")
    source_version: str = Field(min_length=1, max_length=128)
    source_citations: list[dict] = Field(default_factory=list, max_length=20)
    knowledge_context: dict = Field(default_factory=dict)
    items: list[ChecklistSourceItem] = Field(min_length=1, max_length=250)

    @model_validator(mode="after")
    def unique_source_keys(self):
        keys = [item.source_item_key for item in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("Checklist source item keys must be unique")
        return self


class ChecklistPatch(BaseModel):
    language: str | None = Field(default=None, pattern=r"^(en|hi|hinglish)$")

    @model_validator(mode="after")
    def has_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one checklist change is required")
        return self


class ChecklistItemPatch(BaseModel):
    is_completed: bool | None = None
    user_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def has_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one item change is required")
        return self


class ChecklistRefresh(BaseModel):
    source_version: str = Field(min_length=1, max_length=128)
    source_citations: list[dict] = Field(default_factory=list, max_length=20)
    items: list[ChecklistSourceItem] = Field(min_length=1, max_length=250)

    @model_validator(mode="after")
    def unique_source_keys(self):
        keys = [item.source_item_key for item in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("Checklist source item keys must be unique")
        return self


class GuestChecklistImport(BaseModel):
    approved: bool


class ChecklistKnowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_id: str = Field(min_length=1, max_length=160)
    service_name: str = Field(min_length=1, max_length=240)
    language: str = Field(default="en", pattern=r"^(en|hi|hinglish)$")
    state: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=120)


class ChecklistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    checklist_id: str
    item_type: ChecklistItemType
    title: str
    description: str | None
    sequence_number: int
    is_required: bool
    is_completed: bool
    completed_at: datetime | None
    user_note: str | None
    source_item_key: str
    source_state: ChecklistItemSourceState
    created_at: datetime
    updated_at: datetime


class SavedChecklistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int | None
    guest_session_id: str | None
    service_id: str
    service_name: str
    language: str
    status: ChecklistStatus
    progress_percentage: float
    source_version: str
    source_citations: list[dict]
    knowledge_context: dict
    storage_origin: StorageOrigin
    sync_status: SyncStatus
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime
    items: list[ChecklistItemOut] = Field(default_factory=list)


class ChecklistListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_id: str
    service_name: str
    language: str
    status: ChecklistStatus
    progress_percentage: float
    source_version: str
    storage_origin: StorageOrigin
    sync_status: SyncStatus
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime


class ChecklistListResponse(BaseModel):
    storage_mode: StorageOrigin
    sync_status: SyncStatus
    checklists: list[SavedChecklistOut]


class ChecklistResponse(BaseModel):
    storage_mode: StorageOrigin
    sync_status: SyncStatus
    checklist: SavedChecklistOut


class ChecklistImportResult(BaseModel):
    storage_mode: StorageOrigin
    sync_status: SyncStatus
    imported_count: int
    skipped_count: int


class ChecklistRefreshResult(BaseModel):
    storage_mode: StorageOrigin
    sync_status: SyncStatus
    checklist: SavedChecklistOut
    new_items: int
    changed_items: int
    removed_items: int
    source_version_changed: bool




class ChecklistGuidance(BaseModel):
    progress_summary: str
    next_steps: list[str]
    missing_documents: list[str]
    short_explanations: list[str]
    alternative_actions: list[str]
    reminders: list[str]




class ChecklistAnalytics(BaseModel):
    active_storage_mode: StorageOrigin
    total_checklists: int
    completion_rate: float
    abandonment_rate: float
    average_completion_hours: float
    outdated_count: int
    most_saved_checklists: list[dict]
    frequently_incomplete_steps: list[dict]
    storage_usage: dict[str, int]
