"""
Database connection and session management.
Supports PostgreSQL and SQLite (fallback for local run without Docker).
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from shared.config import settings

Base = declarative_base()

# Engine: SQLite needs check_same_thread=False for FastAPI
_is_sqlite = "sqlite" in (settings.database_url or "")
if _is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        pool_size=1,
        max_overflow=0,
        echo=settings.debug,
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        echo=settings.debug,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions (workers, scripts). Commits on success, rollback on error."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_dependency() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session. Caller must commit/rollback."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Call at startup."""
    import shared.models  # noqa: F401 - register ORM models with Base
    Base.metadata.create_all(bind=engine)
