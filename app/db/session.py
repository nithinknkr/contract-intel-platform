from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Shared FastAPI dependency for a scoped DB session.
    IMPORTANT: check app/routers/documents.py — if it already defines its own
    get_db (likely, since it predates this file), delete the duplicate there
    and import this one instead. Two separate get_db functions creating two
    separate session-lifecycle patterns is a bug waiting to happen, not a
    harmless duplication.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()