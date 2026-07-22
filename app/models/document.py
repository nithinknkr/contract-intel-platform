import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Computed, Enum, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status",
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=DocumentStatus.UPLOADED,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Added in A4: filename-only full-text search ---
    # This is a Postgres GENERATED ALWAYS AS ... STORED column — Postgres
    # recomputes it automatically on every INSERT/UPDATE to filename, there is
    # no application code that writes to this column directly (SQLAlchemy will
    # correctly refuse to include it in INSERT/UPDATE statements).
    #
    # Deliberately filename-only, not chunk content: this answers "help me
    # find a document by name" (human browsing). Content-level relevance
    # ranking against chunk text is B2's hybrid retrieval (BM25 + vector),
    # a different job serving a different consumer (LLM context, not a
    # document list). Don't conflate the two when explaining this in interviews.
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', filename)", persisted=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_documents_search_vector", "search_vector", postgresql_using="gin"),
    )