import uuid

from app.models.document import Document, DocumentStatus
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.repositories.document_repository import DocumentRepository


def _make_org_and_user(db_session, org_name: str, email: str) -> tuple[Organization, User]:
    org = Organization(id=uuid.uuid4(), name=org_name)
    db_session.add(org)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        org_id=org.id,
        email=email,
        hashed_password="x",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.flush()
    return org, user


def test_cross_tenant_get_by_id_returns_none(db_session):
    org_a, user_a = _make_org_and_user(db_session, "Org A", f"a-{uuid.uuid4()}@example.com")
    org_b, user_b = _make_org_and_user(db_session, "Org B", f"b-{uuid.uuid4()}@example.com")

    doc_b = Document(
        id=uuid.uuid4(),
        org_id=org_b.id,
        uploaded_by=user_b.id,
        filename="org_b_contract.pdf",
        status=DocumentStatus.READY,
        is_archived=False,
    )
    db_session.add(doc_b)
    db_session.flush()

    repo = DocumentRepository(db_session)

    leaked = repo.get_by_id(org_id=org_a.id, record_id=doc_b.id)
    correct = repo.get_by_id(org_id=org_b.id, record_id=doc_b.id)

    assert leaked is None
    assert correct is not None
    assert correct.id == doc_b.id


def test_cross_tenant_list_all_excludes_other_org(db_session):
    org_a, user_a = _make_org_and_user(db_session, "Org A", f"a-{uuid.uuid4()}@example.com")
    org_b, user_b = _make_org_and_user(db_session, "Org B", f"b-{uuid.uuid4()}@example.com")

    doc_a = Document(
        id=uuid.uuid4(), org_id=org_a.id, uploaded_by=user_a.id,
        filename="org_a.pdf", status=DocumentStatus.READY, is_archived=False,
    )
    doc_b = Document(
        id=uuid.uuid4(), org_id=org_b.id, uploaded_by=user_b.id,
        filename="org_b.pdf", status=DocumentStatus.READY, is_archived=False,
    )
    db_session.add_all([doc_a, doc_b])
    db_session.flush()

    repo = DocumentRepository(db_session)
    org_a_docs = repo.list_all(org_a.id)

    assert len(org_a_docs) == 1
    assert org_a_docs[0].id == doc_a.id