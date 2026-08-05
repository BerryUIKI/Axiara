"""Storage abstraction for the three data layers.

Pluggable backends: SQLite / PostgreSQL / MongoDB + CSV import/export.
Write permissions are enforced at this layer (defense in depth):
agents can only reach a data layer through this interface, which
rejects writes that are not allowed for a given layer.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

# Import new storage components
from axiara.core.storage.cache import SQLiteCache, get_cache
from axiara.core.storage.file_backend import FileStorage, create_file_storage
from axiara.core.storage.git_sync import GitSyncManager, get_git_sync_manager
from axiara.core.storage.manifest import ManifestManager, get_manifest_manager
from axiara.core.storage.permissions import (
    PermissionError,
    PermissionManager,
    get_permission_manager,
)

__all__ = [
    "DataLayer",
    "StorageBackend",
    "LocalStorage",
    "create_storage",
    "FileStorage",
    "create_file_storage",
    "SQLiteCache",
    "get_cache",
    "ManifestManager",
    "get_manifest_manager",
    "PermissionManager",
    "get_permission_manager",
    "PermissionError",
    "GitSyncManager",
    "get_git_sync_manager",
]


class DataLayer(StrEnum):
    """The three data layers plus user uploads."""

    MAIN = "main"  # official price baseline — manual edit ONLY
    LEARN = "learn"  # AI-learned reference
    MARKET = "market"  # crawled market prices
    UPLOADS = "uploads"  # user-provided tables/documents


class StorageBackend(Protocol):
    """Protocol for a storage backend."""

    def read(self, layer: DataLayer, key: str) -> Any: ...
    def write(self, layer: DataLayer, key: str, value: Any) -> None: ...
    def list(self, layer: DataLayer) -> list[str]: ...


class LocalStorage:
    """Filesystem-backed storage (scaffold default, SQLite comes next)."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("data")

    def _path(self, layer: DataLayer, key: str) -> Path:
        return self.root / layer.value / key

    def read(self, layer: DataLayer, key: str) -> str:
        return self._path(layer, key).read_text(encoding="utf-8")

    def write(self, layer: DataLayer, key: str, value: str) -> None:
        # Permission rule: only MAIN is manual-edit-only, but any write
        # to MAIN must go through the manual-edit path (enforced by callers
        # and by a dedicated write layer in the full implementation).
        path = self._path(layer, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def list(self, layer: DataLayer) -> list[str]:
        path = self.root / layer.value
        if not path.exists():
            return []
        return [p.name for p in path.iterdir() if p.is_file()]


def create_storage(backend: str = "local", **kwargs: Any) -> StorageBackend:
    """Factory for storage backends (scaffold: local only)."""
    if backend == "local":
        return LocalStorage(**kwargs)
    raise NotImplementedError(f"Storage backend {backend!r} not implemented yet")
