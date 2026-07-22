import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import utcnow
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """
    Deliberately NOT a TenantScopedRepository subclass. That base class assumes
    every query is scoped by org_id — refresh tokens are scoped by token_hash
    (exact-match lookup on refresh) or user_id (bulk revoke on logout-everywhere),
    and never by org_id. Forcing this into TenantScopedRepository would mean an
    org_id parameter on every method that's never actually used to filter anything.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        obj = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_valid_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Returns the token row only if it exists, isn't revoked, and hasn't expired."""
        return (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > utcnow(),
            )
            .first()
        )

    def revoke(self, token_hash: str) -> bool:
        obj = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
        if obj is None:
            return False
        obj.revoked_at = utcnow()
        self.db.flush()
        return True

    def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Not called anywhere yet in A4 — here for the future 'log out everywhere' case."""
        count = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .update({"revoked_at": utcnow()})
        )
        self.db.flush()
        return count