"""
Integration tests for citation verification on POST /documents/{id}/ask.

Exercises the real pipeline (upload -> chunk -> embed -> hybrid retrieval
-> citation_verifier) end to end, against real Postgres and real Chroma --
the only thing mocked is ask_llm itself (see B3 decisions log for why:
Groq is an external, costed, non-deterministic dependency, and this test
needs to deterministically control what citations come back in order to
prove the verifier actually catches a bad one, the same reasoning behind
mock_enqueue in conftest.py for RQ).

Follows the same real-Chroma-with-manual-cleanup pattern as
test_embeddings.py, since Chroma isn't covered by db_session's SAVEPOINT
rollback (that only covers Postgres).
"""

import uuid
from pathlib import Path

import pytest

from app.models.audit_log import AuditLog
from app.models.chunk import Chunk
from app.services.embedding_pipeline import embed_document_version
from app.services.ingestion import process_document_version
from app.services.llm import Citation, LLMAnswer
from app.services.vector_store import delete_vectors_by_document_version

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _upload(client, filename="contract.pdf"):
    content = (FIXTURES / "sample_valid.pdf").read_bytes()
    response = client.post(
        "/documents",
        files={"file": (filename, content, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def embedded_version_ids():
    """Same pattern as test_embeddings.py -- explicit Chroma cleanup."""
    ids: list[uuid.UUID] = []
    yield ids
    for version_id in ids:
        delete_vectors_by_document_version(version_id)


def _ingest_and_embed(client, db_session, embedded_version_ids):
    """
    Shared setup for both tests below: upload, chunk, and embed a real
    document, then return (document_id, the real Chunk row) so tests can
    build citations that reference an actual retrieved chunk.
    """
    upload_result = _upload(client)
    document_id = uuid.UUID(upload_result["document_id"])
    version_id = uuid.UUID(upload_result["version"]["id"])
    embedded_version_ids.append(version_id)

    process_document_version(db_session, version_id)
    db_session.flush()
    embed_document_version(db_session, version_id)

    chunk = (
        db_session.query(Chunk)
        .filter(Chunk.document_version_id == version_id)
        .first()
    )
    assert chunk is not None

    return document_id, chunk


def test_ask_drops_unverified_citation_and_flags_response(
    signed_up_client, db_session, embedded_version_ids, monkeypatch
):
    """
    LLM returns one genuinely grounded citation and one referencing a
    chunk_id that was never retrieved. The response should keep the good
    citation, drop the bad one, and flag all_citations_verified=False --
    and the drop should be independently confirmed via the audit log,
    not just trusted from the API response.
    """
    document_id, chunk = _ingest_and_embed(
        signed_up_client.client, db_session, embedded_version_ids
    )

    # Pull a real, verbatim substring from the real chunk's content so the
    # "good" citation is genuinely grounded, not just plausible-looking.
    real_excerpt = chunk.content.strip().split(".")[0]  # first sentence
    fabricated_chunk_id = str(uuid.uuid4())  # never actually retrieved

    fake_answer = LLMAnswer(
        answer="This contract contains a liability clause and an auto-renewal clause.",
        citations=[
            Citation(chunk_id=str(chunk.id), quote=real_excerpt),
            Citation(chunk_id=fabricated_chunk_id, quote="a clause that was never retrieved"),
        ],
    )

    def fake_ask_llm(question, chunks):
        return fake_answer

    monkeypatch.setattr("app.routers.documents.ask_llm", fake_ask_llm)

    response = signed_up_client.client.post(
        f"/documents/{document_id}/ask",
        json={"question": "What clauses does this contract contain?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["all_citations_verified"] is False
    assert len(body["citations"]) == 1
    assert body["citations"][0]["chunk_id"] == str(chunk.id)
    # answer text is untouched -- B3 drops citations, not claims (see
    # decisions log: per-claim redaction isn't supported by the schema)
    assert body["answer"] == fake_answer.answer

    failure_events = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.resource_id == document_id,
            AuditLog.action == "document.citation_verification_failed",
        )
        .all()
    )
    assert len(failure_events) == 1
    failed_ids = {c["chunk_id"] for c in failure_events[0].event_metadata["failed_citations"]}
    assert failed_ids == {fabricated_chunk_id}


def test_ask_all_citations_verified_when_all_grounded(
    signed_up_client, db_session, embedded_version_ids, monkeypatch
):
    """
    Counterpart to the failure case above -- when every citation the LLM
    returns is genuinely grounded, nothing gets dropped and no
    citation_verification_failed event fires. Guards against the verifier
    being overly aggressive and stripping good citations.
    """
    document_id, chunk = _ingest_and_embed(
        signed_up_client.client, db_session, embedded_version_ids
    )
    real_excerpt = chunk.content.strip().split(".")[0]

    fake_answer = LLMAnswer(
        answer="This contract contains a liability clause and an auto-renewal clause.",
        citations=[Citation(chunk_id=str(chunk.id), quote=real_excerpt)],
    )

    monkeypatch.setattr(
        "app.routers.documents.ask_llm", lambda question, chunks: fake_answer
    )

    response = signed_up_client.client.post(
        f"/documents/{document_id}/ask",
        json={"question": "What clauses does this contract contain?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["all_citations_verified"] is True
    assert len(body["citations"]) == 1
    assert body["citations"][0]["chunk_id"] == str(chunk.id)

    failure_events = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.resource_id == document_id,
            AuditLog.action == "document.citation_verification_failed",
        )
        .all()
    )
    assert failure_events == []