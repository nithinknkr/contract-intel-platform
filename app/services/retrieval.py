"""
Hybrid retrieval — combines vector similarity search (Chroma) and BM25
full-text search (Postgres) into a single fused ranking of candidate
chunks. See docs/project1-decisions-log.md for the B2 decision entry.
"""

import uuid

from app.core.config import settings
from app.services.embedding_service import embed_query
from app.services.vector_store import query as vector_store_query

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.repositories.chunk_repository import ChunkRepository


def get_vector_matches(
    org_id: uuid.UUID,
    document_id: uuid.UUID,
    query_text: str,
    limit: int = settings.top_k_vector,
) -> list[uuid.UUID]:
    """
    Embed the query text and retrieve the top-k most similar chunk IDs
    from Chroma, scoped to org_id and the given document.

    Always queries current_only=True (default on vector_store.query) --
    B2 retrieval never targets a specific historical version, matching
    the same scope decision applied to BM25 retrieval (ChunkRepository.
    get_bm25_matches).

    Returns chunk_ids as UUID objects, not raw strings -- vector_store.
    query() returns strings (Chroma's native ID type), converted here so
    downstream fusion (Step 5) and content lookup (Step 6) work with a
    single consistent type across both the BM25 and vector result lists.
    """
    embedding = embed_query(query_text)
    chunk_id_strs = vector_store_query(
        query_embedding=embedding,
        org_id=org_id,
        document_id=document_id,
        top_k=limit,
        current_only=True,
    )
    return [uuid.UUID(cid) for cid in chunk_id_strs]

def fuse_rankings(
    vector_chunk_ids: list[uuid.UUID],
    bm25_chunk_ids: list[uuid.UUID],
    k: int = settings.rrf_k,
    limit: int = settings.top_k_fused,
    ) -> list[uuid.UUID]:
    """
    Reciprocal Rank Fusion — combines two ranked candidate lists (vector
    similarity and BM25) into one fused ranking, without needing to
    normalize or weight two incomparable score scales (cosine similarity
    vs ts_rank). See docs/project1-decisions-log.md for the B2 decision
    entry on why RRF over a hand-tuned weighted blend.

    score(chunk) = sum of 1/(k + rank) across every list the chunk
    appears in, where rank is 0-indexed position. A chunk appearing in
    both lists accumulates score from both -- this is the actual fusion
    mechanism, not just a merge-and-dedupe.

    k=60 is RRF's standard constant from the original paper (Cormack et
    al., 2009) -- not tuned for this project specifically, a deliberate
    default rather than an invented value.
    """
    scores: dict[uuid.UUID, float] = {}

    for rank, chunk_id in enumerate(vector_chunk_ids):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    for rank, chunk_id in enumerate(bm25_chunk_ids):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [chunk_id for chunk_id, _ in ranked[:limit]]



def get_context_chunks(
    db: Session,
    org_id: uuid.UUID,
    document_id: uuid.UUID,
    query_text: str,
) -> list[Chunk]:
    """
    Full hybrid retrieval pipeline: run vector + BM25 search, fuse via
    RRF, then fetch actual chunk content through the tenant-scoped
    repository -- never trusting Chroma's IDs directly (see vector_store.
    py module docstring / B1 decisions log).

    Returns Chunk objects in fused-rank order (most relevant first) --
    this order is preserved into the LLM prompt (Step 7), so a chunk's
    position in this list has real meaning downstream.
    """
    vector_chunk_ids = get_vector_matches(org_id, document_id, query_text)

    bm25_matches = ChunkRepository(db).get_bm25_matches(
        org_id, document_id=document_id, query=query_text
    )
    bm25_chunk_ids = [chunk.id for chunk, _rank in bm25_matches]

    fused_ids = fuse_rankings(vector_chunk_ids, bm25_chunk_ids)

    # Five-ish individual PK lookups, not a batch query -- see B2 decisions
    # log for why a batch get_by_ids wasn't added to the shared repository
    # base class for this. Order preserved to match fused_ids.
    chunk_repo = ChunkRepository(db)
    chunks = []
    for chunk_id in fused_ids:
        chunk = chunk_repo.get_by_id(org_id, chunk_id)
        if chunk is not None:
            chunks.append(chunk)

    return chunks