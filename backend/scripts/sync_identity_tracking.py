r"""Synchronize pending identity records after PostgreSQL is available.

Run from ``backend``:
    .\venv\Scripts\python.exe scripts\sync_identity_tracking.py
"""
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy.orm import Session  # noqa: E402

from app.checklists.enums import StorageOrigin  # noqa: E402
from app.checklists.storage import ChecklistStorage  # noqa: E402
from app.identity_tracking.sync_service import sync_pending_identity_records  # noqa: E402


if __name__ == "__main__":
    storage = ChecklistStorage()
    if not storage.primary_is_healthy():
        raise SystemExit("PostgreSQL is not available; nothing was synchronized.")
    source = Session(storage._engine(StorageOrigin.SQLITE))
    target = Session(storage._engine(StorageOrigin.POSTGRESQL))
    try:
        result = sync_pending_identity_records(source, target)
        target.commit()
        source.commit()
    except Exception:
        target.rollback()
        source.rollback()
        raise
    finally:
        target.close()
        source.close()
    print(
        f"Identity sync examined={result.examined} "
        f"synced={result.synced} conflicts={result.conflicts}"
    )
