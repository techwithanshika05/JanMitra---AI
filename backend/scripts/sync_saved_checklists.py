r"""Synchronize pending saved checklists from SQLite to PostgreSQL.

Run from ``backend`` only after the checklist migration has created both
storage targets:

    .\venv\Scripts\python.exe scripts\sync_saved_checklists.py
"""
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.checklists.storage import ChecklistStorage
from app.checklists.sync_service import ChecklistSynchronizationService


if __name__ == "__main__":
    result = ChecklistSynchronizationService(ChecklistStorage()).sync_pending()
    print(
        "Checklist sync:",
        f"primary_available={result.primary_available}",
        f"examined={result.examined}",
        f"synced={result.synced}",
        f"failed={result.failed}",
        f"conflicts={result.conflicts}",
    )
