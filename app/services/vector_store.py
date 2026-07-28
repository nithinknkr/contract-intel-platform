"""
Vector store wrapper -- talks to Chroma for storing and querying chunk embeddings.

Single collection (contract_chunks) with metadata filtering, rather than
one collection per tenant. See docs/project1-decisions-log.md for the B1
decision entry on this trade-off.

Security note: Chroma's metadata filter narrows candidates for relevance/
performance, but it is NOT the tenant-isolation boundary. Every chunk_id
returned by query() must still be re-verified against Postgres via the
existing tenant-scoped ChunkRepository before its content is ever returned
to a caller -- exactly like how a JWT's claims are trusted for identity but
re-checked against the DB in get_current_user (A4). Chroma is an index,
not an authorization system.
"""

import os

import uuid

import chromadb

from app.core.config import settings
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

COLLECTION_NAME = "contract_chunks"

_client = chromadb.HttpClient(
    host=settings.chroma_url.split("://")[1].split(":")[0],
    port=int(settings.chroma_url.split(":")[-1]),
)


def get_collection():
    """
    Get (or create, on first run) the single shared Chroma collection.

    Not cached at module level the way the embedding model is -- Chroma's
    client is cheap to call this on, and get_or_create_collection is
    idempotent, so there's no real cost to calling it each time versus
    the meaningful cost of reloading a transformer model repeatedly.
    """
    return _client.get_or_create_collection(name=COLLECTION_NAME)


def add_vectors(
    chunk_ids: list[uuid.UUID],
    embeddings: list[list[float]],
    org_id: uuid.UUID,
    document_id: uuid.UUID,
    document_version_id: uuid.UUID,
    is_current: bool,
) -> None:
    """
    Write a batch of chunk embeddings to Chroma, tagged with tenant/version metadata.

    chunk_ids double as Chroma's own vector IDs -- this is deliberate: it
    means deleting/updating vectors for a given chunk is a direct ID lookup,
    with no separate mapping table to keep in sync.
    """
    if not chunk_ids:
        return

    ids = [str(cid) for cid in chunk_ids]
    metadatas = [
        {
            "org_id": str(org_id),
            "document_id": str(document_id),
            "document_version_id": str(document_version_id),
            "is_current": is_current,
        }
        for _ in chunk_ids
    ]

    collection = get_collection()
    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)


def delete_vectors(chunk_ids: list[uuid.UUID]) -> None:
    """
    Delete vectors by chunk ID. Safe to call with IDs that don't exist in
    Chroma (e.g. a version that was never successfully embedded) -- Chroma
    treats deleting a non-existent ID as a no-op, not an error.
    """
    if not chunk_ids:
        return
    collection = get_collection()
    collection.delete(ids=[str(cid) for cid in chunk_ids])


def delete_vectors_by_document_version(document_version_id: uuid.UUID) -> None:
    """
    Delete all vectors belonging to a specific document version, without
    needing to know the individual chunk IDs up front. Used for version-
    transition cleanup (Step 7) and reprocess cleanup (Step 6).
    """
    collection = get_collection()
    collection.delete(where={"document_version_id": str(document_version_id)})


def query(
    query_embedding: list[float],
    org_id: uuid.UUID,
    document_id: uuid.UUID | None = None,
    top_k: int = 5,
    current_only: bool = True,
) -> list[str]:
    """
    Query Chroma for the top_k most similar chunk IDs, scoped by org_id
    (required) and optionally a specific document_id.

    Returns chunk_id strings only -- NOT chunk content. Callers must look
    up the actual content via the tenant-scoped ChunkRepository, which is
    the real security boundary (see module docstring).
    """
    collection = get_collection()

    conditions: list[dict] = [{"org_id": str(org_id)}]
    if document_id is not None:
        conditions.append({"document_id": str(document_id)})
    if current_only:
        conditions.append({"is_current": True})

    where_clause = conditions[0] if len(conditions) == 1 else {"$and": conditions}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause,
    )

    return results["ids"][0] if results["ids"] else []