from app.models.document_version import DocumentVersion
from app.repositories.base import TenantScopedRepository


class DocumentVersionRepository(TenantScopedRepository[DocumentVersion]):
    model = DocumentVersion