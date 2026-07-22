import uuid

from sqlalchemy import func

from app.models.document import Document
from app.repositories.base import TenantScopedRepository


class DocumentRepository(TenantScopedRepository[Document]):
    model = Document

    def list_paginated(
        self,
        org_id: uuid.UUID,
        *,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Document]:
        query = self.db.query(Document).filter(Document.org_id == org_id)
        if not include_archived:
            query = query.filter(Document.is_archived.is_(False))
        return (
            query.order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(
        self,
        org_id: uuid.UUID,
        *,
        query: str,
        include_archived: bool = False,
        limit: int = 20,
    ) -> list[tuple[Document, float]]:
        """
        Full-text search over documents.search_vector (see the model — a
        Postgres GENERATED column, GIN-indexed). Returns (Document, rank)
        pairs, ordered by relevance. Filename-only — see model docstring for
        why this doesn't overlap with B2's content-level hybrid retrieval.

        Excludes archived documents by default, matching list_paginated's
        behavior — a deliberate consistency choice: both "browse" surfaces
        (list and search) default to "what I'm currently working with,"
        with an explicit opt-in to see archived results too.
        """
        ts_query = func.plainto_tsquery("english", query)
        rank = func.ts_rank(Document.search_vector, ts_query).label("rank")
        q = self.db.query(Document, rank).filter(
            Document.org_id == org_id,
            Document.search_vector.op("@@")(ts_query),
        )
        if not include_archived:
            q = q.filter(Document.is_archived.is_(False))
        rows = q.order_by(rank.desc()).limit(limit).all()
        return [(row[0], row[1]) for row in rows]