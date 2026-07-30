import hashlib
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion, ParseStatus
from app.models.user import User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.document_version_repository import DocumentVersionRepository
from app.schemas.document import (
    DocumentDetailOut,
    DocumentListOut,
    DocumentSearchResultOut,
    DocumentUploadResponse,
    DocumentVersionOut,
)
from app.services.jobs import process_document_version_job
from app.services.queue import document_queue
from app.services.storage import LocalStorageClient


from app.core.deps import get_current_org_id, get_current_user, require_role
from app.schemas.qa import AskRequest, AskResponse, CitationOut
from app.services.llm import LLMServiceError, ask_llm
from app.services.retrieval import get_context_chunks

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    # viewer role is deliberately excluded — matches the least-privilege intent
    # set in A2's role model; a read-only role shouldn't be able to write data.
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.REVIEWER)),
):
    org_id = current_user.org_id
    uploaded_by = current_user.id

    content = file.file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    # --- Org-wide dedup check (unchanged from A3) ---
    existing_version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.org_id == org_id,
            DocumentVersion.file_hash == file_hash,
        )
        .first()
    )
    if existing_version is not None:
        AuditLogRepository(db).create(
            org_id=org_id,
            action="document.upload_deduplicated",
            resource_type="document",
            resource_id=existing_version.document_id,
            user_id=uploaded_by,
            event_metadata={"filename": file.filename, "file_hash": file_hash},
        )
        db.commit()
        return DocumentUploadResponse(
            document_id=existing_version.document_id,
            version=existing_version,
            duplicate=True,
        )

    doc_repo = DocumentRepository(db)
    version_repo = DocumentVersionRepository(db)
    storage = LocalStorageClient()

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

    AuditLogRepository(db).create(
        org_id=org_id,
        action="document.uploaded",
        resource_type="document",
        resource_id=document.id,
        user_id=uploaded_by,
        event_metadata={"filename": file.filename, "version_id": str(version.id)},
    )

    db.commit()

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
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.id == version_id,
            DocumentVersion.document_id == document_id,
            DocumentVersion.org_id == org_id,  # closes the A3 TODO
        )
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Document version not found")
    return version


@router.get("", response_model=list[DocumentListOut])
def list_documents(
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    include_archived: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    repo = DocumentRepository(db)
    return repo.list_paginated(
        org_id, include_archived=include_archived, skip=skip, limit=limit
    )


# IMPORTANT: this must be registered BEFORE GET /{document_id} — FastAPI
# matches path templates in registration order, and "/search" would otherwise
# be swallowed by the "/{document_id}" pattern (and fail as a bad UUID, 422,
# never reaching this handler).
@router.get("/search", response_model=list[DocumentSearchResultOut])
def search_documents(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    include_archived: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
):
    repo = DocumentRepository(db)
    rows = repo.search(org_id, query=q, include_archived=include_archived, limit=limit)
    return [
        DocumentSearchResultOut(
            id=doc.id,
            filename=doc.filename,
            status=doc.status,
            is_archived=doc.is_archived,
            rank=rank,
        )
        for doc, rank in rows
    ]


@router.get("/{document_id}", response_model=DocumentDetailOut)
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    repo = DocumentRepository(db)
    document = repo.get_by_id(org_id, document_id)
    if document is None:
        # 404, not 403 — consistent with the A2 pattern: don't reveal to a
        # caller from another org whether a given document ID even exists.
        raise HTTPException(status_code=404, detail="Document not found")

    current_version = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == document.id,
            DocumentVersion.org_id == org_id,
            DocumentVersion.is_current.is_(True),
        )
        .first()
    )

    return DocumentDetailOut(
        id=document.id,
        filename=document.filename,
        status=document.status,
        is_archived=document.is_archived,
        created_at=document.created_at,
        updated_at=document.updated_at,
        current_version=current_version,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.REVIEWER)),
):
    """
    Soft-delete only: sets is_archived=True, never a real DELETE FROM. In a
    legal-tech product with an audit trail, an irrecoverable hard delete is
    the wrong default. A genuine hard-delete path (if ever needed) should be
    a separate, explicitly admin-only endpoint — not what this verb does.
    """
    repo = DocumentRepository(db)
    document = repo.get_by_id(org_id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    document.is_archived = True

    AuditLogRepository(db).create(
        org_id=org_id,
        action="document.archived",
        resource_type="document",
        resource_id=document.id,
        user_id=current_user.id,
        event_metadata={"filename": document.filename},
    )

    db.commit()
    return None
@router.post("/{document_id}/ask", response_model=AskResponse)
def ask_document(
    document_id: uuid.UUID,
    body: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grounded Q&A over a single document, via hybrid (BM25 + vector) retrieval
    fused with RRF, answered by an LLM constrained to structured JSON output.
    No role restriction beyond authentication -- this is a read action, and
    per A2's least-privilege role model a viewer should be able to ask
    questions on documents they can already see.
    """
    org_id = current_user.org_id

    doc_repo = DocumentRepository(db)
    document = doc_repo.get_by_id(org_id, document_id)
    if document is None:
        # 404, not 403 -- same cross-tenant existence-hiding pattern as
        # get_document above.
        raise HTTPException(status_code=404, detail="Document not found")

    if document.is_archived:
        # Archived-ness is a request-validity concern, checked here at the
        # endpoint boundary -- not baked into the retrieval query itself.
        # See B2 decisions log.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ask questions of an archived document",
        )

    chunks = get_context_chunks(db, org_id, document_id, body.question)

    if not chunks:
        # No retrieval hits at all -- don't call the LLM with an empty
        # context, that's a wasted call guaranteed to produce a useless
        # or hallucinated answer. Return a clean, honest "nothing found."
        return AskResponse(
            answer="No relevant content was found in this document to answer the question.",
            citations=[],
            retrieved_chunk_ids=[],
        )

    try:
        llm_answer = ask_llm(body.question, chunks)
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM service error: {exc}",
        )

    AuditLogRepository(db).create(
        org_id=org_id,
        action="document.asked",
        resource_type="document",
        resource_id=document_id,
        user_id=current_user.id,
        event_metadata={"question": body.question},
    )
    db.commit()

    return AskResponse(
        answer=llm_answer.answer,
        citations=[CitationOut(chunk_id=c.chunk_id, quote=c.quote) for c in llm_answer.citations],
        retrieved_chunk_ids=[chunk.id for chunk in chunks],
    )