r"""Add the profile fields required by the existing mobile registration UI.

Run from ``backend`` with:
    .\venv\Scripts\python.exe migrations\004_add_mobile_auth_profile.py
"""
import sys
from pathlib import Path

from sqlalchemy import inspect, text


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.checklists.enums import StorageOrigin  # noqa: E402
from app.checklists.storage import ChecklistStorage  # noqa: E402


COLUMNS = {
    "mobile": "VARCHAR(10)",
    "address": "TEXT",
    "gender": "VARCHAR(16)",
    "pincode": "VARCHAR(6)",
    "public_id": "VARCHAR(16)",
}


def migrate_engine(engine) -> None:
    existing = {
        column["name"] for column in inspect(engine).get_columns("users")
    }
    with engine.begin() as connection:
        for name, sql_type in COLUMNS.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE users ADD COLUMN {name} {sql_type}")
                )
        connection.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_mobile ON users (mobile)")
        )
        connection.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_public_id ON users (public_id)")
        )


def migrate() -> list[str]:
    storage = ChecklistStorage()
    origins = [StorageOrigin.SQLITE]
    if storage.primary_is_healthy():
        origins.append(StorageOrigin.POSTGRESQL)
    for origin in origins:
        migrate_engine(storage._engine(origin))
    return [origin.value for origin in origins]


if __name__ == "__main__":
    print(f"Mobile authentication profile is ready: {', '.join(migrate())}")
