from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.checklists.analytics import ChecklistAnalyticsService
from app.checklists.enums import StorageOrigin, SyncStatus
from app.checklists.repository import ChecklistOwner
from app.checklists.schemas import ChecklistCreate, ChecklistSourceItem
from app.checklists.service import SavedChecklistService
from app.checklists.sqlalchemy_repository import SQLAlchemyChecklistRepository
from app.database import Base


def test_analytics_are_aggregate_and_non_sensitive():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine, autoflush=False)()
    repository = SQLAlchemyChecklistRepository(db)
    service = SavedChecklistService(repository)
    owner = ChecklistOwner(user_id=5)
    payload = ChecklistCreate(
        service_id="ration_card",
        service_name="Ration card",
        source_version="rag-v1",
        items=[
            ChecklistSourceItem(
                item_type="document",
                title="Residence proof",
                sequence_number=1,
                source_item_key="document:residence",
            )
        ],
    )
    first = service.create(
        owner,
        payload,
        storage_origin=StorageOrigin.SQLITE,
        sync_status=SyncStatus.PENDING,
    )
    second = service.create(
        owner,
        payload,
        storage_origin=StorageOrigin.SQLITE,
        sync_status=SyncStatus.PENDING,
    )
    service.archive(second.id, owner)

    summary = ChecklistAnalyticsService.summarize(
        repository, active_storage_mode=StorageOrigin.SQLITE
    )
    serialized = summary.model_dump()
    assert summary.total_checklists == 2
    assert summary.abandonment_rate == 0.5
    assert summary.most_saved_checklists[0]["count"] == 2
    assert summary.frequently_incomplete_steps[0]["title"] == "Residence proof"
    assert summary.storage_usage["sqlite"] == 2
    assert "user_id" not in serialized
    assert "guest_session_id" not in serialized
    assert first.id not in str(serialized)
    db.close()
