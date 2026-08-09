import uuid

from sqlalchemy.orm import Session

from app.models.risk_flag import RiskFlag
from app.repositories.base import TenantScopedRepository


class RiskFlagRepository(TenantScopedRepository[RiskFlag]):
    model = RiskFlag

    def __init__(self, db: Session):
        super().__init__(db)

    def list_for_review(self, org_id: uuid.UUID, risk_review_id: uuid.UUID) -> list[RiskFlag]:
        return (
            self.db.query(RiskFlag)
            .filter(RiskFlag.org_id == org_id, RiskFlag.risk_review_id == risk_review_id)
            .order_by(RiskFlag.created_at.asc())
            .all()
        )