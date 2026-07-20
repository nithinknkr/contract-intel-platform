from app.models.chunk import Chunk
from app.repositories.base import TenantScopedRepository


class ChunkRepository(TenantScopedRepository[Chunk]):
    model = Chunk