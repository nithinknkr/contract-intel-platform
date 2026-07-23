import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _signup_and_get_client(db_session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    new_client = TestClient(app)

    email = f"test-{uuid.uuid4()}@example.com"
    response = new_client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": "TestPassword123!",
            "organization_name": f"Test Org {uuid.uuid4()}",
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    new_client.headers["Authorization"] = f"Bearer {token}"
    return new_client


def _upload(client: TestClient, filename: str) -> str:
    content = (FIXTURES / "sample_valid.pdf").read_bytes()
    response = client.post(
        "/documents",
        files={"file": (filename, content, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()["document_id"]


def test_org_a_cannot_get_org_b_document_by_id(db_session, mock_enqueue):
    client_a = _signup_and_get_client(db_session)
    client_b = _signup_and_get_client(db_session)

    doc_id_b = _upload(client_b, "org_b_contract.pdf")

    response = client_a.get(f"/documents/{doc_id_b}")
    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_org_a_cannot_see_org_b_document_in_list(db_session, mock_enqueue):
    client_a = _signup_and_get_client(db_session)
    client_b = _signup_and_get_client(db_session)

    doc_id_a = _upload(client_a, "org_a_contract.pdf")
    doc_id_b = _upload(client_b, "org_b_contract.pdf")

    response = client_a.get("/documents")
    assert response.status_code == 200
    listed_ids = {doc["id"] for doc in response.json()}
    assert doc_id_a in listed_ids
    assert doc_id_b not in listed_ids

    app.dependency_overrides.clear()


def test_org_a_cannot_find_org_b_document_via_search(db_session, mock_enqueue):
    client_a = _signup_and_get_client(db_session)
    client_b = _signup_and_get_client(db_session)

    _upload(client_a, "org_a_agreement_alpha.pdf")
    _upload(client_b, "org_b_agreement_beta.pdf")

    response = client_a.get("/documents/search", params={"q": "beta"})
    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()