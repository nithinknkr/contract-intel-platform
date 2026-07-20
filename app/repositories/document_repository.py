from app.models.document import Document
from app.repositories.base import TenantScopedRepository


class DocumentRepository(TenantScopedRepository[Document]):
    model = Document