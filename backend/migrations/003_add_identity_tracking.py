r"""Add guest-to-user identity tracking without changing master scheme data.

Run from ``backend`` with:
    .\venv\Scripts\python.exe migrations\003_add_identity_tracking.py
"""
import sys
from pathlib import Path

from sqlalchemy import inspect, text


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import chat_models, models as core_models  # noqa: E402,F401
from app.checklists import models as checklist_models  # noqa: E402,F401
from app.checklists.enums import StorageOrigin  # noqa: E402
from app.checklists.storage import ChecklistStorage  # noqa: E402
from app.database import Base  # noqa: E402
from app.identity_tracking import models as identity_models  # noqa: E402,F401


ADDITIONS = {
    "chat_sessions": {
        "claimed_guest_id": "VARCHAR(36)",
        "ownership_status": "VARCHAR(16) NOT NULL DEFAULT 'active'",
        "claimed_at": "TIMESTAMP",
    },
    "chat_feedback": {
        "claimed_guest_id": "VARCHAR(36)",
        "ownership_status": "VARCHAR(16) NOT NULL DEFAULT 'active'",
        "claimed_at": "TIMESTAMP",
    },
    "saved_checklists": {
        "claimed_guest_session_id": "VARCHAR(36)",
        "ownership_status": "VARCHAR(16) NOT NULL DEFAULT 'active'",
        "claimed_at": "TIMESTAMP",
    },
}


def add_missing_columns(engine) -> None:
    table_names = set(inspect(engine).get_table_names())
    with engine.begin() as connection:
        for table_name, additions in ADDITIONS.items():
            if table_name not in table_names:
                continue
            existing = {
                column["name"]
                for column in inspect(engine).get_columns(table_name)
            }
            for name, sql_type in additions.items():
                if name not in existing:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {name} {sql_type}")
                    )


def migrate() -> list[str]:
    storage = ChecklistStorage()
    targets: list[str] = []
    origins = [StorageOrigin.SQLITE]
    if storage.primary_is_healthy():
        origins.append(StorageOrigin.POSTGRESQL)
    for origin in origins:
        engine = storage._engine(origin)
        Base.metadata.create_all(
            bind=engine,
            tables=[
                identity_models.SchemeActivity.__table__,
                identity_models.UserPreference.__table__,
                identity_models.GuestClaim.__table__,
                identity_models.FeatureActivity.__table__,
            ],
        )
        add_missing_columns(engine)
        targets.append(origin.value)
    return targets


if __name__ == "__main__":
    print(f"Identity tracking tables are ready: {', '.join(migrate())}")
