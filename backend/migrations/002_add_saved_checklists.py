r"""Create additive saved-checklist tables on the configured storage targets.

Run from ``backend`` with:
    .\venv\Scripts\python.exe migrations\002_add_saved_checklists.py

This migration is intentionally not run automatically by importing it.
"""
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.checklists import models  # noqa: F401
from app.checklists.enums import StorageOrigin
from app.checklists.storage import ChecklistStorage
from app.database import Base
from sqlalchemy import inspect, text


SYNC_COLUMNS = {
    "source_citations": "JSON NOT NULL DEFAULT '[]'",
    "knowledge_context": "JSON NOT NULL DEFAULT '{}'",
    "sync_error": "TEXT",
    "last_sync_attempt_at": "TIMESTAMP",
    "synced_at": "TIMESTAMP",
}


def ensure_sync_columns(engine) -> None:
    existing = {
        column["name"]
        for column in inspect(engine).get_columns("saved_checklists")
    }
    missing = {
        name: sql_type for name, sql_type in SYNC_COLUMNS.items() if name not in existing
    }
    if not missing:
        return
    with engine.begin() as connection:
        for name, sql_type in missing.items():
            connection.execute(
                text(f"ALTER TABLE saved_checklists ADD COLUMN {name} {sql_type}")
            )


def create_tables() -> list[str]:
    storage = ChecklistStorage()
    created: list[str] = []

    fallback_engine = storage._engine(StorageOrigin.SQLITE)
    Base.metadata.create_all(
        bind=fallback_engine,
        tables=[
            models.SavedChecklist.__table__,
            models.ChecklistItem.__table__,
        ],
    )
    ensure_sync_columns(fallback_engine)
    created.append(StorageOrigin.SQLITE.value)

    if storage.primary_is_healthy():
        primary_engine = storage._engine(StorageOrigin.POSTGRESQL)
        Base.metadata.create_all(
            bind=primary_engine,
            tables=[
                models.SavedChecklist.__table__,
                models.ChecklistItem.__table__,
            ],
        )
        ensure_sync_columns(primary_engine)
        created.append(StorageOrigin.POSTGRESQL.value)

    return created


if __name__ == "__main__":
    targets = ", ".join(create_tables())
    print(f"Saved checklist tables are ready: {targets}")
