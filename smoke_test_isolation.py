import uuid

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository


def run():
    db = SessionLocal()
    try:
        # --- Set up two separate tenants ---
        org_a = Organization(id=uuid.uuid4(), name="Org A")
        org_b = Organization(id=uuid.uuid4(), name="Org B")
        db.add_all([org_a, org_b])
        db.flush()

        user_a = User(
            id=uuid.uuid4(), org_id=org_a.id, email="a@example.com",
            hashed_password="x", role=UserRole.ADMIN,
        )
        db.add(user_a)
        db.flush()

        doc_b = Document(
            id=uuid.uuid4(), org_id=org_b.id, uploaded_by=user_a.id,  # deliberately wrong FK below
        )
        # uploaded_by must belong to org_b really — fix by creating a user_b too
        user_b = User(
            id=uuid.uuid4(), org_id=org_b.id, email="b@example.com",
            hashed_password="x", role=UserRole.ADMIN,
        )
        db.add(user_b)
        db.flush()

        doc_b.uploaded_by = user_b.id
        doc_b.filename = "org_b_contract.pdf"
        doc_b.status = DocumentStatus.READY
        db.add(doc_b)
        db.flush()

        # --- The actual test: can org A's repository see org B's document? ---
        doc_repo = DocumentRepository(db)

        leaked = doc_repo.get_by_id(org_id=org_a.id, record_id=doc_b.id)
        correct = doc_repo.get_by_id(org_id=org_b.id, record_id=doc_b.id)

        assert leaked is None, "LEAK: org A could read org B's document!"
        assert correct is not None, "BROKEN: org B can't read its own document!"

        print("PASS: cross-tenant read blocked, same-tenant read works.")

    finally:
        db.rollback()  # never commit test data
        db.close()


if __name__ == "__main__":
    run()