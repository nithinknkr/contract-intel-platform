import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.risk_review import RiskReview, RiskReviewStatus
from app.repositories.base import TenantScopedRepository


class RiskReviewRepository(TenantScopedRepository[RiskReview]):
    model = RiskReview

    def __init__(self, db: Session):
        super().__init__(db)

    def list_for_document(self, org_id: uuid.UUID, document_id: uuid.UUID) -> list[RiskReview]:
        return (
            self.db.query(RiskReview)
            .filter(RiskReview.org_id == org_id, RiskReview.document_id == document_id)
            .order_by(RiskReview.created_at.desc())
            .all()
        )

    def mark_completed(self, org_id: uuid.UUID, review_id: uuid.UUID) -> RiskReview | None:
        review = self.get_by_id(org_id, review_id)
        if review is None:
            return None
        review.status = RiskReviewStatus.COMPLETED
        review.completed_at = datetime.now(timezone.utc)
        self.db.flush()
        return review

    def mark_failed(self, org_id: uuid.UUID, review_id: uuid.UUID) -> RiskReview | None:
        review = self.get_by_id(org_id, review_id)
        if review is None:
            return None
        review.status = RiskReviewStatus.FAILED
        review.completed_at = datetime.now(timezone.utc)
        self.db.flush()
        return review