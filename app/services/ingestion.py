import uuid
import hashlib

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion, ParseStatus
from app.models.chunk import Chunk
from app.services.storage import LocalStorageClient
from app.services.parsing import parse_document, ParseError
from app.services.chunking import chunk_text


def process_document_version(db: Session, version_id: uuid.UUID) -> None:
    """
    Parses, chunks, and persists chunks for a single document version.
    Safe to retry: always deletes any existing chunks for this version
    before re-inserting, so a retry after partial failure never
    duplicates or corrupts chunk data. Not true resumability — a retry
    redoes the full parse+chunk work, it does not skip already-processed
    chunks.
    """
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if version is None:
        raise ValueError(f"DocumentVersion {version_id} not found")

    document = db.query(Document).filter(Document.id == version.document_id).first()

    storage = LocalStorageClient()

    try:
        version.parse_status = ParseStatus.PARSING
        db.commit()

        content = storage.get(version.storage_path)
        filename_for_ext = version.storage_path  # already carries the extension

        full_text = parse_document(content, filename_for_ext)
        chunk_results = chunk_text(full_text)

        # --- Atomic replace: delete any existing chunks, then insert fresh set ---
        db.query(Chunk).filter(Chunk.document_version_id == version.id).delete()

        for c in chunk_results:
            db.add(
                Chunk(
                    document_version_id=version.id,
                    org_id=version.org_id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    content_hash=hashlib.sha256(c.content.encode("utf-8")).hexdigest(),
                    char_start=c.char_start,
                    char_end=c.char_end,
                )
            )

        version.parse_status = ParseStatus.PARSED
        version.parse_error = None

        if document is not None and document.status != DocumentStatus.READY:
            document.status = DocumentStatus.READY

        db.commit()

    except ParseError as e:
        db.rollback()
        version.parse_status = ParseStatus.FAILED
        version.parse_error = f"{e.reason}: {e.detail}" if e.detail else e.reason
        db.commit()

        if document is not None and version.version_number == 1:
            document.status = DocumentStatus.FAILED
            db.commit()

    except Exception as e:
        db.rollback()
        version.parse_status = ParseStatus.FAILED
        version.parse_error = f"unexpected_error: {str(e)}"
        db.commit()

        if document is not None and version.version_number == 1:
            document.status = DocumentStatus.FAILED
            db.commit()
        raise  # unexpected errors should still surface — don't swallow real bugs