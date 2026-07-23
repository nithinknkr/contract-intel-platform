from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _upload(client, filename):
    content = (FIXTURES / "sample_valid.pdf").read_bytes()
    response = client.post(
        "/documents",
        files={"file": (filename, content, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()["document_id"]


def test_search_matches_word_despite_extension_and_underscores(signed_up_client):
    doc_id = _upload(signed_up_client.client, "Vendor_NDA_Agreement.pdf")

    response = signed_up_client.client.get("/documents/search", params={"q": "vendor"})
    assert response.status_code == 200
    results = response.json()
    ids = {r["id"] for r in results}
    assert doc_id in ids


def test_search_matches_second_word_in_underscored_filename(signed_up_client):
    doc_id = _upload(signed_up_client.client, "Vendor_NDA_Agreement.pdf")

    response = signed_up_client.client.get("/documents/search", params={"q": "agreement"})
    assert response.status_code == 200
    ids = {r["id"] for r in response.json()}
    assert doc_id in ids


def test_search_excludes_archived_documents_by_default(signed_up_client):
    doc_id = _upload(signed_up_client.client, "Lease_Agreement.pdf")

    archive_response = signed_up_client.client.delete(f"/documents/{doc_id}")
    assert archive_response.status_code == 204

    response = signed_up_client.client.get("/documents/search", params={"q": "lease"})
    assert response.status_code == 200
    ids = {r["id"] for r in response.json()}
    assert doc_id not in ids


def test_search_includes_archived_when_requested(signed_up_client):
    doc_id = _upload(signed_up_client.client, "Lease_Agreement.pdf")

    archive_response = signed_up_client.client.delete(f"/documents/{doc_id}")
    assert archive_response.status_code == 204

    response = signed_up_client.client.get(
        "/documents/search", params={"q": "lease", "include_archived": "true"}
    )
    assert response.status_code == 200
    ids = {r["id"] for r in response.json()}
    assert doc_id in ids