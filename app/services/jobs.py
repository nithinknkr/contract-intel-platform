import uuid

from app.db.session import SessionLocal
from app.models.document_version import DocumentVersion, ParseStatus
from app.services.embedding_pipeline import embed_document_version
from app.services.ingestion import process_document_version
from app.services.queue import embedding_queue


def process_document_version_job(version_id: str) -> None:
    """
    RQ entrypoint. Opens its own DB session — RQ workers run in a
    separate process from the API, so they cannot share the request's
    session. Always create a fresh session per job.

    On successful parsing, chains an embedding job onto embedding_queue.
    Chaining here (not inside ingestion.py) keeps the service layer free
    of any RQ/queue knowledge — jobs.py is the one layer that's allowed
    to know about queues.
    """
    db = SessionLocal()
    try:
        process_document_version(db, uuid.UUID(version_id))

        version = (
            db.query(DocumentVersion)
            .filter(DocumentVersion.id == uuid.UUID(version_id))
            .first()
        )
        if version is not None and version.parse_status == ParseStatus.PARSED:
            embedding_queue.enqueue(embed_document_version_job, version_id)
    finally:
        db.close()


def embed_document_version_job(version_id: str) -> None:
    """
    RQ entrypoint for embedding. Same fresh-session-per-job pattern as
    process_document_version_job above.
    """
    db = SessionLocal()
    try:
        embed_document_version(db, uuid.UUID(version_id))
    finally:
        db.close()