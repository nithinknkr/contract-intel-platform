"""
Unit tests for app.services.citation_verifier.

Pure-function tests -- no DB, no LLM, no fixtures beyond plain Chunk
objects constructed in-memory (never persisted). This is what makes B3's
"caught a bad citation" claim deterministic and repeatable, rather than
relying on real LLM output to reproduce a fabrication on demand.
"""

import uuid

from app.models.chunk import Chunk
from app.services.citation_verifier import Citation, verify_citations


def _make_chunk(content: str) -> Chunk:
    """
    Builds a plain, unpersisted Chunk with a real UUID id and the given
    content -- everything verify_citations actually looks at. Other
    required columns are filled with throwaway values since they're
    never touched by the function under test.
    """
    return Chunk(
        id=uuid.uuid4(),
        document_version_id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        chunk_index=0,
        content=content,
        content_hash="irrelevant-for-this-test",
        char_start=0,
        char_end=len(content),
    )


def test_all_citations_valid():
    chunk = _make_chunk("The term of this agreement is five years from the effective date.")
    citation = Citation(chunk_id=str(chunk.id), quote="term of this agreement is five years")

    result = verify_citations([citation], [chunk])

    assert result.all_citations_verified is True
    assert len(result.citations) == 1
    assert result.citations[0].verified is True
    assert result.citations[0].failure_reason is None
    assert result.verified_only == result.citations


def test_citation_referencing_unretrieved_chunk_fails_membership():
    retrieved_chunk = _make_chunk("This clause covers indemnification obligations.")
    fabricated_chunk_id = str(uuid.uuid4())  # never actually retrieved
    citation = Citation(chunk_id=fabricated_chunk_id, quote="indemnification obligations")

    result = verify_citations([citation], [retrieved_chunk])

    assert result.all_citations_verified is False
    assert result.citations[0].verified is False
    assert result.citations[0].failure_reason == "chunk_not_retrieved"
    assert result.verified_only == []


def test_citation_with_fabricated_quote_fails_grounding():
    chunk = _make_chunk("3. SCOPE OF SERVICES\n4. CLIENT OBLIGATIONS")
    # Real chunk_id, but a quote that doesn't actually appear in the
    # chunk -- the exact failure mode B2 caught on negative answers.
    citation = Citation(
        chunk_id=str(chunk.id),
        quote="the contract does not contain a non-compete clause",
    )

    result = verify_citations([citation], [chunk])

    assert result.all_citations_verified is False
    assert result.citations[0].verified is False
    assert result.citations[0].failure_reason == "quote_not_grounded"
    assert result.verified_only == []


def test_grounding_check_tolerates_whitespace_and_case_differences():
    chunk = _make_chunk(
        "The   Vendor  shall  maintain,   at its own expense,\nComprehensive General Liability insurance."
    )
    # Genuine excerpt, but with different casing and collapsed whitespace
    # -- exactly what a real LLM produces even when accurately quoting.
    citation = Citation(
        chunk_id=str(chunk.id),
        quote="vendor shall maintain, at its own expense, comprehensive general liability insurance",
    )

    result = verify_citations([citation], [chunk])

    assert result.all_citations_verified is True
    assert result.citations[0].verified is True


def test_mixed_valid_and_invalid_citations_drops_only_the_bad_one():
    good_chunk = _make_chunk("Either party may terminate this agreement with 30 days notice.")
    bad_chunk = _make_chunk("Payment is due within 45 days of invoice.")

    good_citation = Citation(chunk_id=str(good_chunk.id), quote="terminate this agreement with 30 days notice")
    bad_citation = Citation(chunk_id=str(bad_chunk.id), quote="unlimited liability for consequential damages")

    result = verify_citations([good_citation, bad_citation], [good_chunk, bad_chunk])

    assert result.all_citations_verified is False
    assert len(result.citations) == 2
    assert len(result.verified_only) == 1
    assert result.verified_only[0].chunk_id == str(good_chunk.id)

    failed = [c for c in result.citations if not c.verified]
    assert len(failed) == 1
    assert failed[0].chunk_id == str(bad_chunk.id)
    assert failed[0].failure_reason == "quote_not_grounded"


def test_no_citations_is_vacuously_verified():
    """
    An LLM answer with zero citations (e.g. it chose not to cite
    anything) is a different case from "citations existed but all
    failed" -- all_citations_verified=True here just means "nothing to
    fail," not "the answer is well-grounded." See B3 decisions log.
    """
    chunk = _make_chunk("Some retrieved content that was never cited.")

    result = verify_citations([], [chunk])

    assert result.citations == []
    assert result.all_citations_verified is True
    assert result.verified_only == []