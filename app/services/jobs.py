import uuid

from app.db.session import SessionLocal
from app.services.ingestion import process_document_version


def process_document_version_job(version_id: str) -> None:
    """
    RQ entrypoint. Opens its own DB session — RQ workers run in a
    separate process from the API, so they cannot share the request's
    session. Always create a fresh session per job.
    """
    db = SessionLocal()
    try:
        process_document_version(db, uuid.UUID(version_id))
    finally:
        db.close()