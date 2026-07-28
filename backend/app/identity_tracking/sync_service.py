from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.identity_tracking.models import FeatureActivity, SchemeActivity, UserPreference


@dataclass(frozen=True)
class IdentitySyncResult:
    examined: int = 0
    synced: int = 0
    conflicts: int = 0


def sync_pending_identity_records(
    source: Session, target: Session
) -> IdentitySyncResult:
    """Idempotently copy fallback identity records without overwriting target rows."""

    examined = synced = conflicts = 0
    for model in (SchemeActivity, UserPreference, FeatureActivity):
        rows = source.query(model).filter(model.sync_status == "pending").all()
        for row in rows:
            examined += 1
            if target.get(model, row.id) is not None:
                row.sync_status = "synced"
                conflicts += 1
                continue
            values = {
                column.name: getattr(row, column.name)
                for column in model.__table__.columns
            }
            values["storage_origin"] = "sqlite"
            values["sync_status"] = "synced"
            target.add(model(**values))
            row.sync_status = "synced"
            synced += 1
    target.flush()
    source.flush()
    return IdentitySyncResult(
        examined=examined, synced=synced, conflicts=conflicts
    )
