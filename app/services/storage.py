import shutil
from pathlib import Path

from app.core.config import settings


class LocalStorageClient:
    """
    Local-disk file storage. Same three-method interface (save/get/delete)
    that a future S3StorageClient would implement — callers never touch
    the filesystem directly, only this class does.
    """

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.storage_base_dir)

    def _full_path(self, relative_path: str) -> Path:
        full = (self.base_dir / relative_path).resolve()
        if self.base_dir.resolve() not in full.parents and full != self.base_dir.resolve():
            raise ValueError(f"Invalid storage path: {relative_path}")
        return full

    def save(self, relative_path: str, content: bytes) -> str:
        full = self._full_path(relative_path)
        full.parent.mkdir(parents=True, exist_ok=True)
        with open(full, "wb") as f:
            f.write(content)
        return relative_path

    def get(self, relative_path: str) -> bytes:
        full = self._full_path(relative_path)
        with open(full, "rb") as f:
            return f.read()

    def delete(self, relative_path: str) -> None:
        full = self._full_path(relative_path)
        if full.exists():
            full.unlink()

    def delete_document_folder(self, org_id: str, document_id: str) -> None:
        """Removes all versions of a document at once (e.g. on hard-delete)."""
        folder = self._full_path(f"{org_id}/{document_id}")
        if folder.exists():
            shutil.rmtree(folder)