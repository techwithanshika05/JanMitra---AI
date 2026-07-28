from contextlib import contextmanager
from dataclasses import dataclass
import logging
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.checklists.enums import StorageOrigin, SyncStatus
from app.checklists.sqlalchemy_repository import SQLAlchemyChecklistRepository
from app.config import settings

logger = logging.getLogger(__name__)


def _normalized_postgresql_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def create_checklist_engine(url: str, *, connect_timeout: int) -> Engine:
    normalized = _normalized_postgresql_url(url)
    connect_args: dict[str, object] = {}
    if normalized.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif normalized.startswith("postgresql"):
        connect_args["connect_timeout"] = connect_timeout
    return create_engine(normalized, connect_args=connect_args, pool_pre_ping=True)


@dataclass(frozen=True)
class ChecklistStorageSelection:
    origin: StorageOrigin
    sync_status: SyncStatus
    repository: SQLAlchemyChecklistRepository


class ChecklistStorage:
    """Select checklist persistence without leaking database logic to services.

    Engines and sessions are lazy so importing this module never contacts a
    database or mutates the existing SQLite file.
    """

    def __init__(
        self,
        primary_url: str | None = None,
        fallback_url: str | None = None,
        *,
        connect_timeout: int | None = None,
    ):
        self.primary_url = (primary_url if primary_url is not None else settings.DATABASE_URL).strip()
        self.fallback_url = (
            fallback_url if fallback_url is not None else settings.SQLITE_FALLBACK_URL
        ).strip()
        self.connect_timeout = (
            connect_timeout
            if connect_timeout is not None
            else settings.DATABASE_CONNECT_TIMEOUT
        )
        self._primary_engine: Engine | None = None
        self._fallback_engine: Engine | None = None
        self._primary_sessions: sessionmaker | None = None
        self._fallback_sessions: sessionmaker | None = None

    def _engine(self, origin: StorageOrigin) -> Engine:
        if origin == StorageOrigin.POSTGRESQL:
            if not self.primary_url.startswith("postgresql"):
                raise RuntimeError("PostgreSQL checklist storage is not configured")
            if self._primary_engine is None:
                self._primary_engine = create_checklist_engine(
                    self.primary_url, connect_timeout=self.connect_timeout
                )
            return self._primary_engine
        if self._fallback_engine is None:
            self._fallback_engine = create_checklist_engine(
                self.fallback_url, connect_timeout=self.connect_timeout
            )
        return self._fallback_engine

    def _sessions(self, origin: StorageOrigin) -> sessionmaker:
        if origin == StorageOrigin.POSTGRESQL:
            if self._primary_sessions is None:
                self._primary_sessions = sessionmaker(
                    bind=self._engine(origin), autocommit=False, autoflush=False
                )
            return self._primary_sessions
        if self._fallback_sessions is None:
            self._fallback_sessions = sessionmaker(
                bind=self._engine(origin), autocommit=False, autoflush=False
            )
        return self._fallback_sessions

    def primary_is_healthy(self) -> bool:
        if not self.primary_url.startswith("postgresql"):
            return False
        try:
            with self._engine(StorageOrigin.POSTGRESQL).connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.warning("Checklist PostgreSQL health check failed: %s", exc)
            return False

    @contextmanager
    def repository(self) -> Iterator[ChecklistStorageSelection]:
        if self.primary_is_healthy():
            origin = StorageOrigin.POSTGRESQL
            sync_status = SyncStatus.SYNCED
        else:
            origin = StorageOrigin.SQLITE
            sync_status = SyncStatus.PENDING

        session: Session = self._sessions(origin)()
        try:
            yield ChecklistStorageSelection(
                origin=origin,
                sync_status=sync_status,
                repository=SQLAlchemyChecklistRepository(session),
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def repository_for_sync(
        self, origin: StorageOrigin
    ) -> Iterator[SQLAlchemyChecklistRepository]:
        session: Session = self._sessions(origin)()
        try:
            yield SQLAlchemyChecklistRepository(session)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
