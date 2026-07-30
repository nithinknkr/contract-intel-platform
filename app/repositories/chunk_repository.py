import uuid

from sqlalchemy import func

from app.models.chunk import Chunk
from app.models.document_version import DocumentVersion
from app.repositories.base import TenantScopedRepository


class ChunkRepository(TenantScopedRepository[Chunk]):
    model = Chunk

    def get_bm25_matches(
        self,
        org_id: uuid.UUID,
        *,
        document_id: uuid.UUID,
        query: str,
        limit: int = 15,
    ) -> list[tuple[Chunk, float]]:
        """
        BM25-style full-text search over chunks.content_tsvector (see B2
        migration — a Postgres GENERATED column, GIN-indexed). Returns
        (Chunk, rank) pairs, ordered by relevance.

        Scoped to org_id (denormalized directly on chunks, per A3) and to
        the *current* version of the given document — joins to
        document_versions specifically for is_current, since that flag
        lives there, not on chunks. A query against an older version can
        never surface via this method, consistent with the project's
        version-aware retrieval requirement.
        """
        ts_query = func.plainto_tsquery("english", query)
        rank = func.ts_rank(Chunk.content_tsvector, ts_query).label("rank")
        rows = (
            self.db.query(Chunk, rank)
            .join(DocumentVersion, Chunk.document_version_id == DocumentVersion.id)
            .filter(
                Chunk.org_id == org_id,
                DocumentVersion.document_id == document_id,
                DocumentVersion.is_current.is_(True),
                Chunk.content_tsvector.op("@@")(ts_query),
            )
            .order_by(rank.desc())
            .limit(limit)
            .all()
        )
        return [(row[0], row[1]) for row in rows]