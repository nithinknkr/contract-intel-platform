import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.document import DocumentStatus
from app.models.document_version import ParseStatus


class DocumentVersionOut(BaseModel):
    id: uuid.UUID
    version_number: int
    parse_status: ParseStatus
    parse_error: str | None
    is_current: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    version: DocumentVersionOut
    duplicate: bool


class DocumentListOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    current_version: Optional[DocumentVersionOut]

    model_config = {"from_attributes": True}


class DocumentSearchResultOut(BaseModel):
    """
    Not built via model_config from_attributes off a plain Document — the
    repository's search() returns (Document, rank) pairs, so the router
    constructs this explicitly. rank has no meaning outside a given search
    call, hence it isn't a field on DocumentListOut/DocumentDetailOut.
    """

    id: uuid.UUID
    filename: str
    status: DocumentStatus
    is_archived: bool
    rank: float