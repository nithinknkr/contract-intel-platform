import uuid
from pathlib import Path

from app.models.chunk import Chunk
from app.models.document_version import DocumentVersion, ParseStatus
from app.services.ingestion import process_document_version

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _upload(client, filename="contract.pdf"):
    content = (FIXTURES / "sample_valid.pdf").read_bytes()
    response = client.post(
        "/documents",
        files={"file": (filename, content, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_process_document_version_is_idempotent(signed_up_client, db_session):
    upload_result = _upload(signed_up_client.client)
    version_id = uuid.UUID(upload_result["version"]["id"])

    # --- First pass ---
    process_document_version(db_session, version_id)
    db_session.flush()

    first_chunks = (
        db_session.query(Chunk)
        .filter(Chunk.document_version_id == version_id)
        .order_by(Chunk.chunk_index)
        .all()
    )
    assert len(first_chunks) > 0
    first_ids = {c.id for c in first_chunks}
    first_signature = [
        (c.chunk_index, c.char_start, c.char_end, c.content_hash) for c in first_chunks
    ]

    version = db_session.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    assert version.parse_status == ParseStatus.PARSED

    # --- Second pass: reprocess the same version ---
    process_document_version(db_session, version_id)
    db_session.flush()
    db_session.expire_all()

    second_chunks = (
        db_session.query(Chunk)
        .filter(Chunk.document_version_id == version_id)
        .order_by(Chunk.chunk_index)
        .all()
    )
    second_ids = {c.id for c in second_chunks}
    second_signature = [
        (c.chunk_index, c.char_start, c.char_end, c.content_hash) for c in second_chunks
    ]

    # Same three invariants your manual script already proved:
    assert len(first_chunks) == len(second_chunks)
    assert first_ids.isdisjoint(second_ids)  # old chunks deleted, new ones created
    assert first_signature == second_signature  # deterministic content/offsets

    version_after = db_session.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
    assert version_after.parse_status == ParseStatus.PARSED