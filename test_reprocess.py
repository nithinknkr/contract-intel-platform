import uuid
from app.db.session import SessionLocal
import app.models  # noqa: F401 — registers all models before any DB operation
from app.models.chunk import Chunk
from app.models.document_version import DocumentVersion
from app.services.ingestion import process_document_version

VERSION_ID = uuid.UUID("ce892db3-e537-439a-96c7-b4d9e479176b")

db = SessionLocal()

before_chunks = (
    db.query(Chunk)
    .filter(Chunk.document_version_id == VERSION_ID)
    .order_by(Chunk.chunk_index)
    .all()
)
print(f"BEFORE: {len(before_chunks)} chunks")
before_ids = {c.id for c in before_chunks}
before_content = [(c.chunk_index, c.char_start, c.char_end, c.content_hash) for c in before_chunks]

process_document_version(db, VERSION_ID)

db.expire_all()
after_chunks = (
    db.query(Chunk)
    .filter(Chunk.document_version_id == VERSION_ID)
    .order_by(Chunk.chunk_index)
    .all()
)
print(f"AFTER: {len(after_chunks)} chunks")
after_ids = {c.id for c in after_chunks}
after_content = [(c.chunk_index, c.char_start, c.char_end, c.content_hash) for c in after_chunks]

print()
print("=== Checks ===")
print(f"Chunk count unchanged: {len(before_chunks) == len(after_chunks)}")
print(f"Chunk IDs are all NEW (old ones deleted, not reused): {before_ids.isdisjoint(after_ids)}")
print(f"Chunk content/offsets identical: {before_content == after_content}")

version = db.query(DocumentVersion).filter(DocumentVersion.id == VERSION_ID).first()
print(f"parse_status after reprocess: {version.parse_status}")

db.close()