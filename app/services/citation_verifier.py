"""
Citation verification for grounded Q&A responses.

Two checks per citation, run in order:

1. Membership -- was this chunk_id actually part of the retrieved context
   sent to the LLM? This formalizes a check that previously lived inside
   ask_llm (llm.py), where it was fatal (raised LLMServiceError, aborting
   the whole request with a 502). It's non-fatal here by design -- a
   single bad citation shouldn't take down an otherwise-correct answer.
   See B3 decisions log.

2. Grounding -- does the cited quote actually appear (after normalization)
   in that chunk's real content, or is the model citing a real, retrieved
   chunk_id while fabricating/paraphrasing supporting text? This is the
   failure mode B2's own manual testing caught empirically: on negative
   answers ("this clause isn't in the document"), the LLM cited real
   chunk_ids but quoted section-header fragments instead of genuine
   supporting text, since there's nothing real to quote for an absence.

A citation that fails either check is dropped from the caller-facing
response but never silently -- every citation's verification outcome is
reported in CitationVerificationResult, and all_citations_verified gives
a single flag for "was every citation on this answer actually grounded."

Deliberately pure: no DB, no HTTP, no LLM calls. Deterministic in,
deterministic out -- this is what makes it unit-testable without a live
LLM, and reusable as-is by B4's agentic reviewer for its own per-flag
citations.
"""

import re
from typing import Literal

from pydantic import BaseModel

from app.models.chunk import Chunk
from app.services.llm import Citation


class VerifiedCitation(BaseModel):
    chunk_id: str
    quote: str
    verified: bool
    failure_reason: Literal["chunk_not_retrieved", "quote_not_grounded"] | None = None


class CitationVerificationResult(BaseModel):
    citations: list[VerifiedCitation]
    all_citations_verified: bool

    @property
    def verified_only(self) -> list[VerifiedCitation]:
        """The subset actually safe to return to a caller."""
        return [c for c in self.citations if c.verified]


def _normalize(text: str) -> str:
    """
    Lowercase, strip punctuation, collapse whitespace.

    Exact substring matching would false-fail constantly -- an LLM won't
    reproduce whitespace/punctuation perfectly even when genuinely
    quoting real text. Fuzzy matching (e.g. rapidfuzz) would catch more,
    but adds a new dependency and overlaps with what B6's LLM-as-judge is
    meant to do (semantic quality scoring, not grounding verification).
    Normalization is cheap, dependency-free, and targets the actual
    observed failure mode: fabricated quotes, not near-miss quoting.
    See B3 decisions log.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def verify_citations(
    citations: list[Citation],
    retrieved_chunks: list[Chunk],
) -> CitationVerificationResult:
    """
    Args:
        citations: what the LLM returned (llm.LLMAnswer.citations).
        retrieved_chunks: the actual Chunk objects that were sent to the
            LLM as context (same list passed into ask_llm/build_user_prompt).

    Returns every citation annotated with its verification outcome, plus
    a single all_citations_verified flag.
    """
    chunk_by_id: dict[str, Chunk] = {str(chunk.id): chunk for chunk in retrieved_chunks}

    results: list[VerifiedCitation] = []
    for citation in citations:
        chunk = chunk_by_id.get(citation.chunk_id)

        if chunk is None:
            results.append(
                VerifiedCitation(
                    chunk_id=citation.chunk_id,
                    quote=citation.quote,
                    verified=False,
                    failure_reason="chunk_not_retrieved",
                )
            )
            continue

        if _normalize(citation.quote) not in _normalize(chunk.content):
            results.append(
                VerifiedCitation(
                    chunk_id=citation.chunk_id,
                    quote=citation.quote,
                    verified=False,
                    failure_reason="quote_not_grounded",
                )
            )
            continue

        results.append(
            VerifiedCitation(
                chunk_id=citation.chunk_id,
                quote=citation.quote,
                verified=True,
                failure_reason=None,
            )
        )

    return CitationVerificationResult(
        citations=results,
        all_citations_verified=all(c.verified for c in results),
    )