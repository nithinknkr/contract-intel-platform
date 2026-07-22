import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RefreshToken(Base):
    """
    Deliberately has NO org_id column, unlike most models in this schema.
    Refresh tokens are only ever looked up by token_hash (on /auth/refresh)
    or by user_id (on a future "log out everywhere" feature) — never by org_id.
    Adding org_id here would be a column with no query path that ever uses it.

    FK is ON DELETE CASCADE (a deliberate deviation from the RESTRICT-by-default
    convention set in A2) — same reasoning as chunks.document_version_id: a
    refresh token has no independent meaning once its user is gone.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SHA-256 hex digest (64 chars) of the raw token — see app/core/security.py
    # for why SHA-256 and not bcrypt is used here.
    token_hash: Mapped[str] = mapped_column(
        unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )