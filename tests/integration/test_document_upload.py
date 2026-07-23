import io

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_upload_document_success(signed_up_client):
    content = (FIXTURES / "sample_valid.pdf").read_bytes()

    response = signed_up_client.client.post(
        "/documents",
        files={"file": ("contract.pdf", content, "application/pdf")},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["duplicate"] is False
    assert body["document_id"] is not None
    assert body["version"]["version_number"] == 1


def test_upload_same_file_twice_is_deduplicated(signed_up_client):
    content = (FIXTURES / "sample_valid.pdf").read_bytes()

    first = signed_up_client.client.post(
        "/documents",
        files={"file": ("contract.pdf", content, "application/pdf")},
    )
    assert first.status_code == 201

    second = signed_up_client.client.post(
        "/documents",
        files={"file": ("contract_renamed.pdf", content, "application/pdf")},
    )
    assert second.status_code == 201
    body = second.json()
    assert body["duplicate"] is True
    assert body["document_id"] == first.json()["document_id"]


def test_upload_enqueues_processing_job(signed_up_client, mock_enqueue):
    content = (FIXTURES / "sample_valid.pdf").read_bytes()

    response = signed_up_client.client.post(
        "/documents",
        files={"file": ("contract.pdf", content, "application/pdf")},
    )
    assert response.status_code == 201

    assert len(mock_enqueue) == 1
    func, args, kwargs = mock_enqueue[0]
    version_id = response.json()["version"]["id"]
    assert args[0] == version_id or str(args[0]) == str(version_id)


def test_viewer_role_cannot_upload(second_user_in_org):
    viewer, token, viewer_client = second_user_in_org
    content = (FIXTURES / "sample_valid.pdf").read_bytes()

    response = viewer_client.post(
        "/documents",
        files={"file": ("contract.pdf", content, "application/pdf")},
    )
    assert response.status_code == 403