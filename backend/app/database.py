import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger(__name__)


def _engine_for(url: str):
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    if url.startswith("postgresql"):
        connect_args["connect_timeout"] = settings.DATABASE_CONNECT_TIMEOUT
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


def _configured_engine():
    requested_url = settings.DATABASE_URL.strip()
    if requested_url and requested_url.startswith("postgresql"):
        try:
            candidate = _engine_for(requested_url)
            with candidate.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Using configured PostgreSQL database")
            return candidate
        except Exception as exc:
            logger.warning(
                "PostgreSQL unavailable; using SQLite fallback: %s", exc
            )
            return _engine_for(settings.SQLITE_FALLBACK_URL)
    return _engine_for(requested_url or settings.SQLITE_FALLBACK_URL)


engine = _configured_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and guarantees it closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
