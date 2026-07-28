import uuid
from pathlib import Path

import pytest

from app.models.chunk import Chunk
from app.models.user import User
from app.services.embedding_pipeline import embed_document_version
from app.services.ingestion import process_document_version
from app.services.vector_store import delete_vectors_by_document_version, get_collection, query
from app.services.embedding_service import embed_query

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
    """
    Tracks document_version_ids embedded into the REAL Chroma container
    during a test, and deletes their vectors on teardown. Chroma is not
    wrapped in db_session's SAVEPOINT rollback (that only covers Postgres)
    -- it's a separate system that needs its own explicit cleanup, matching
    the same "test the real thing" reasoning behind A5's decision to run
    the real Alembic chain instead of create_all().
    """
    ids: list[uuid.UUID] = []
    yield ids
    for version_id in ids:
        delete_vectors_by_document_version(version_id)


def test_embed_document_version_writes_correct_vectors(
    signed_up_client, db_session, embedded_version_ids
):
    upload_result = _upload(signed_up_client.client)
    version_id = uuid.UUID(upload_result["version"]["id"])
    embedded_version_ids.append(version_id)

    process_document_version(db_session, version_id)
    db_session.flush()

    chunks = (
        db_session.query(Chunk)
        .filter(Chunk.document_version_id == version_id)
        .all()
    )
    assert len(chunks) > 0

    embed_document_version(db_session, version_id)

    collection = get_collection()
    result = collection.get(where={"document_version_id": str(version_id)})

    assert len(result["ids"]) == len(chunks)
    assert set(result["ids"]) == {str(c.id) for c in chunks}

    metadata = result["metadatas"][0]
    assert metadata["org_id"] == str(signed_up_client.org_id)
    assert metadata["document_id"] == upload_result["document_id"]
    assert metadata["document_version_id"] == str(version_id)
    assert metadata["is_current"] is True


def test_embed_document_version_is_idempotent(
    signed_up_client, db_session, embedded_version_ids
):
    upload_result = _upload(signed_up_client.client)
    version_id = uuid.UUID(upload_result["version"]["id"])
    embedded_version_ids.append(version_id)

    process_document_version(db_session, version_id)
    db_session.flush()

    embed_document_version(db_session, version_id)
    collection = get_collection()
    first_ids = set(collection.get(where={"document_version_id": str(version_id)})["ids"])
    assert len(first_ids) > 0

    # Retry -- unlike Postgres chunks (which get new UUIDs on reprocess),
    # chunk IDs here are unchanged, so vector IDs must be IDENTICAL after
    # a retry, not merely equal in count.
    embed_document_version(db_session, version_id)
    second_ids = set(collection.get(where={"document_version_id": str(version_id)})["ids"])

    assert first_ids == second_ids


def test_vector_query_respects_tenant_isolation(
    signed_up_client, db_session, embedded_version_ids
):
    # --- Org A: upload, chunk, and embed a real document ---
    upload_result = _upload(signed_up_client.client)
    version_id = uuid.UUID(upload_result["version"]["id"])
    embedded_version_ids.append(version_id)

    process_document_version(db_session, version_id)
    db_session.flush()
    embed_document_version(db_session, version_id)

    # --- Org B: independent signup via the same shared TestClient, using an
    # explicit per-request header so we don't disturb signed_up_client's
    # default Authorization header for the rest of this test. ---
    signup_email = f"test-{uuid.uuid4()}@example.com"
    signup_response = signed_up_client.client.post(
        "/auth/signup",
        json={
            "email": signup_email,
            "password": "TestPassword123!",
            "organization_name": f"Test Org {uuid.uuid4()}",
        },
        headers={"Authorization": ""},
    )
    assert signup_response.status_code == 201, signup_response.text

    org_b_user = db_session.query(User).filter(User.email == signup_email).first()
    assert org_b_user is not None
    assert org_b_user.org_id != signed_up_client.org_id

    q_vec = embed_query("does this contract auto-renew?")

    org_a_results = query(q_vec, org_id=signed_up_client.org_id, top_k=5)
    org_b_results = query(q_vec, org_id=org_b_user.org_id, top_k=5)

    assert len(org_a_results) > 0
    assert org_b_results == []