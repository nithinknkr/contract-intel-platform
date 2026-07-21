import uuid
from datetime import datetime

from pydantic import BaseModel

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