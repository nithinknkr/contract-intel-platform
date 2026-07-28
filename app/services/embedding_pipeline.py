"""
Orchestrates embedding a document version's chunks and writing them to
the vector store. Mirrors the same delete-then-recreate idempotency
pattern used for chunks themselves in app/services/ingestion.py.

Unlike parsing (DocumentVersion.parse_status), there is no status column
tracking embedding success/failure -- deliberately deferred, not an
oversight. See B1 decisions log. Failures here propagate as raised
exceptions, which RQ records in its own failure registry.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document_version import DocumentVersion
from app.services.embedding_service import embed_passages
from app.services.vector_store import add_vectors, delete_vectors_by_document_version


def embed_document_version(db: Session, version_id: uuid.UUID) -> None:
    """
    Embeds all chunks belonging to a document version and writes them to
    Chroma. Safe to retry: always deletes any existing vectors for this
    version before writing fresh ones -- a retry never leaves duplicate
    or stale vectors behind, matching the chunk-level idempotency
    guarantee this project already proved in A3.
    """
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    if version is None:
        raise ValueError(f"DocumentVersion {version_id} not found")

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_version_id == version.id)
        .order_by(Chunk.chunk_index)
        .all()
    )

    # Delete-then-recreate: safe even if no vectors exist yet for this
    # version (Chroma treats deleting non-existent IDs as a no-op).
    delete_vectors_by_document_version(version.id)

    if not chunks:
        return  # nothing to embed; cleanup above still ran

    texts = [c.content for c in chunks]
    embeddings = embed_passages(texts)
    chunk_ids = [c.id for c in chunks]

    add_vectors(
        chunk_ids=chunk_ids,
        embeddings=embeddings,
        org_id=version.org_id,
        document_id=version.document_id,
        document_version_id=version.id,
        is_current=version.is_current,
    )