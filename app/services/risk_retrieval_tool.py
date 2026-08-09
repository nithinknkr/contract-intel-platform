"""
The agentic risk reviewer's single tool: a retrieval function scoped, in
code, to one org and one document. org_id and document_id are closed over
at construction time -- the returned callable's only parameter is a query
string. The LLM never sees, supplies, or can influence org_id/document_id;
it can only ever change *what* it searches for within the document it was
already scoped to when the review started.

This is the concrete implementation of the tool-scoping guarantee from the
B4 design discussion: no agent tool has more permission than the task
strictly requires, and that scoping is enforced structurally, not by
convention or by trusting the model to behave.

Deliberately thin -- reuses get_context_chunks (hybrid retrieval: BM25 +
vector, RRF-fused, content resolved through the tenant-scoped repository)
completely unchanged. No new retrieval logic, no new tenant-isolation
mechanism -- B4 inherits B1/B2's isolation guarantees for free rather than
re-implementing them.
"""

import uuid
from typing import Callable

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.services.retrieval import get_context_chunks

RetrieveFn = Callable[[str], list[Chunk]]


def build_scoped_retriever(
    db: Session,
    org_id: uuid.UUID,
    document_id: uuid.UUID,
) -> RetrieveFn:
    """
    Returns a retrieve(query: str) -> list[Chunk] callable with org_id and
    document_id permanently closed over. The orchestrator (Step 6) builds
    exactly one of these per review and passes it into every category's
    loop -- there is no code path by which a category's loop, or the LLM
    driving it, can supply a different org_id or document_id than the one
    the review was created for.

    Only ever retrieves against the document's *current* version --
    get_context_chunks/vector_store.query/get_bm25_matches all scope to
    is_current internally (same limitation already accepted by /ask in
    B2/B3). A risk review tied to a specific document_version_id (Step 1)
    that is later superseded by a new upload would need this revisited --
    named limitation, not fixed here.
    """

    def retrieve(query: str) -> list[Chunk]:
        return get_context_chunks(db, org_id, document_id, query)

    return retrieve