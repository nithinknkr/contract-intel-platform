import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, func, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskCategory(str, enum.Enum):
    """
    Fixed, closed checklist -- see app/services/risk_checklist.py (Step 2)
    for the single source of truth these values are drawn from. Unlike
    audit_log.action (open-ended, growing -- see A2 decisions log), this
    set is deliberately closed, so a real enum is the correct choice here,
    not free text.
    """
    AUTO_RENEWAL = "auto_renewal"
    LIABILITY_CAP = "liability_cap"
    TERMINATION_TERMS = "termination_terms"
    INDEMNIFICATION = "indemnification"
    GOVERNING_LAW = "governing_law"
    CONFIDENTIALITY_SCOPE = "confidentiality_scope"


class RiskVerdict(str, enum.Enum):
    FLAGGED = "flagged"
    CLEARED = "cleared"
    UNABLE_TO_VERIFY = "unable_to_verify"


class RiskFlag(Base):
    __tablename__ = "risk_flags"
    __table_args__ = (
        Index("ix_risk_flags_risk_review_id", "risk_review_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    risk_review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Denormalized, same reasoning as chunks.org_id (B1/A3 decisions log):
    # TenantScopedRepository assumes every model has a direct org_id column,
    # keeping tenant-scoped queries a single-table WHERE instead of a join.
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    category: Mapped[RiskCategory] = mapped_column(
        Enum(RiskCategory, name="risk_category",
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    verdict: Mapped[RiskVerdict] = mapped_column(
        Enum(RiskVerdict, name="risk_verdict",
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    # List of {chunk_id, quote, verified, failure_reason} -- same shape as
    # citation_verifier.VerifiedCitation, dumped as plain dicts. Only
    # verified citations should be written here by the orchestrator
    # (Step 6), matching the "verified_only" behavior already established
    # for /ask in B3.
    citations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)