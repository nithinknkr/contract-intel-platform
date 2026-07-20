import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """
    Deliberately does NOT inherit TenantScopedRepository — audit log rows
    are append-only. No update, no delete, no get-by-id-for-mutation.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        org_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        event_metadata: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            event_metadata=event_metadata or {},
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def list_for_org(self, org_id: uuid.UUID) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.org_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    def list_for_resource(
        self, org_id: uuid.UUID, resource_type: str, resource_id: uuid.UUID
    ) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.org_id == org_id,
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id,
            )
            .order_by(AuditLog.created_at.desc())
            .all()
        )   