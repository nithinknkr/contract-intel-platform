# Importing all models here ensures they're registered on Base.metadata
# together, regardless of which entrypoint imports app.models first
# (FastAPI, Alembic, a standalone script, the future RQ worker). Prevents
# NoReferencedTableError when SQLAlchemy resolves cross-model foreign keys.
from app.models.organization import Organization  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.document_version import DocumentVersion  # noqa: F401
from app.models.chunk import Chunk  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.risk_review import RiskReview  # noqa: F401
from app.models.risk_flag import RiskFlag  # noqa: F401