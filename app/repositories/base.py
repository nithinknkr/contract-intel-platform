import uuid
from typing import Generic, TypeVar, Type, Optional

from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class TenantScopedRepository(Generic[ModelType]):
    """
    Base repository for any model with an org_id column.
    Every method requires org_id explicitly — there is no code path
    in this class that queries without a tenant filter.
    """

    model: Type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, record_id: uuid.UUID) -> Optional[ModelType]:
        return (
            self.db.query(self.model)
            .filter(self.model.org_id == org_id, self.model.id == record_id)
            .first()
        )

    def list_all(self, org_id: uuid.UUID) -> list[ModelType]:
        return self.db.query(self.model).filter(self.model.org_id == org_id).all()

    def create(self, org_id: uuid.UUID, **kwargs) -> ModelType:
        obj = self.model(org_id=org_id, **kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, org_id: uuid.UUID, record_id: uuid.UUID) -> bool:
        obj = self.get_by_id(org_id, record_id)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.flush()
        return True