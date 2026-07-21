import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion, ParseStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_version_repository import DocumentVersionRepository
from app.schemas.document import DocumentUploadResponse
from app.services.storage import LocalStorageClient
from app.services.queue import document_queue
from app.services.jobs import process_document_version_job
from app.schemas.document import DocumentUploadResponse, DocumentVersionOut

router = APIRouter(prefix="/documents", tags=["documents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    org_id: uuid.UUID = Form(...),          # TODO: replace with auth dependency in A4
    uploaded_by: uuid.UUID = Form(...),     # TODO: replace with auth dependency in A4
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = file.file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    # --- Org-wide dedup check ---
    existing_version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.org_id == org_id,
            DocumentVersion.file_hash == file_hash,
        )
        .first()
    )
    if existing_version is not None:
        return DocumentUploadResponse(
            document_id=existing_version.document_id,
            version=existing_version,
            duplicate=True,
        )

    doc_repo = DocumentRepository(db)
    version_repo = DocumentVersionRepository(db)
    storage = LocalStorageClient()

    # --- Create Document + first Version ---
    document = doc_repo.create(
        org_id=org_id,
        uploaded_by=uploaded_by,
        filename=file.filename,
        status=DocumentStatus.UPLOADED,
        is_archived=False,
    )

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    relative_path = f"{org_id}/{document.id}/1/original.{ext}"

    version = version_repo.create(
        org_id=org_id,
        document_id=document.id,
        version_number=1,
        storage_path=relative_path,
        file_hash=file_hash,
        parse_status=ParseStatus.PENDING,
        is_current=True,
    )

    storage.save(relative_path, content)
    db.commit()

    # --- Enqueue async processing (was inline/synchronous before Step 7) ---
    document_queue.enqueue(process_document_version_job, str(version.id))

    return DocumentUploadResponse(
        document_id=document.id,
        version=version,
        duplicate=False,
    )
@router.get("/{document_id}/versions/{version_id}", response_model=DocumentVersionOut)
def get_document_version_status(
    document_id: uuid.UUID,
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id == document_id,
             #TODO : also filter by org_id once auth exists (A4) — currently any
            # caller can poll any org's document status if they know the UUIDs.
        )
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Document version not found")

    return version