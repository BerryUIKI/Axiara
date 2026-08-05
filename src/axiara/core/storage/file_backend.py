"""File-based storage backend with CSV/JSON/YAML support.

Extends LocalStorage to support multiple file formats and integrates
with SQLite cache and permission enforcement.

File format decision (per D19/D20):
- CSV: Default for tabular data (Excel-editable)
- JSON: Agent-generated artifacts
- YAML: Configuration files
"""

from __future__ import annotations

import csv
import json
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


class DataLayer(StrEnum):
    """The three data layers plus user uploads."""

    MAIN = "main"  # official price baseline — manual edit ONLY
    LEARN = "learn"  # AI-learned reference
    MARKET = "market"  # crawled market prices
    UPLOADS = "uploads"  # user-provided tables/documents


class StorageBackend:
    """Base storage backend protocol."""

    def read(self, layer: DataLayer, key: str) -> Any:
        raise NotImplementedError

    def write(self, layer: DataLayer, key: str, value: Any) -> None:
        raise NotImplementedError

    def list(self, layer: DataLayer) -> list[str]:
        raise NotImplementedError


class LocalStorage(StorageBackend):
    """Filesystem-backed storage (scaffold default, SQLite comes next)."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("data")

    def _path(self, layer: DataLayer, key: str) -> Path:
        return self.root / layer.value / key

    def read(self, layer: DataLayer, key: str) -> str:
        return self._path(layer, key).read_text(encoding="utf-8")

    def write(self, layer: DataLayer, key: str, value: str) -> None:
        path = self._path(layer, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def list(self, layer: DataLayer) -> list[str]:
        path = self.root / layer.value
        if not path.exists():
            return []
        return [p.name for p in path.iterdir() if p.is_file()]


from axiara.core.storage.cache import SQLiteCache, get_cache
from axiara.core.storage.manifest import ManifestManager, get_manifest_manager
from axiara.core.storage.permissions import PermissionError, get_permission_manager


class FileStorageError(Exception):
    """Raised when file storage operations fail."""

    pass


class FileStorage(LocalStorage):
    """File-based storage with CSV/JSON/YAML support.

    Features:
    - Multi-format support (CSV, JSON, YAML)
    - Permission enforcement at write
    - SQLite cache integration
    - Manifest tracking
    - Auto-format detection by file extension
    """

    def __init__(
        self,
        root: Path | None = None,
        enable_cache: bool = True,
        enable_manifest: bool = True,
    ) -> None:
        """Initialize file storage.

        Args:
            root: Root directory for data (default: data/)
            enable_cache: Enable SQLite cache integration
            enable_manifest: Enable manifest tracking
        """
        super().__init__(root)
        self.enable_cache = enable_cache
        self.enable_manifest = enable_manifest
        self._permission_manager = get_permission_manager() if enable_manifest else None
        self._cache = get_cache() if enable_cache else None
        self._manifest = get_manifest_manager() if enable_manifest else None

    def _detect_format(self, key: str) -> str:
        """Detect file format from extension.

        Args:
            key: File key/path

        Returns:
            Format identifier (csv, json, yaml)
        """
        ext = Path(key).suffix.lower()
        if ext == ".csv":
            return "csv"
        elif ext == ".json":
            return "json"
        elif ext in [".yaml", ".yml"]:
            return "yaml"
        else:
            # Default to JSON for unknown extensions
            return "json"

    def _read_csv(self, path: Path) -> list[dict[str, Any]]:
        """Read CSV file.

        Args:
            path: Path to CSV file

        Returns:
            List of row dictionaries
        """
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _write_csv(self, path: Path, data: list[dict[str, Any]]) -> None:
        """Write CSV file.

        Args:
            path: Path to CSV file
            data: List of row dictionaries
        """
        if not data:
            # Write empty file
            path.write_text("", encoding="utf-8")
            return

        fieldnames = list(data[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    def _read_json(self, path: Path) -> Any:
        """Read JSON file.

        Args:
            path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: Any) -> None:
        """Write JSON file.

        Args:
            path: Path to JSON file
            data: Data to write
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _read_yaml(self, path: Path) -> Any:
        """Read YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML data
        """
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _write_yaml(self, path: Path, data: Any) -> None:
        """Write YAML file.

        Args:
            path: Path to YAML file
            data: Data to write
        """
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def read(self, layer: DataLayer, key: str) -> Any:
        """Read data from a file.

        Automatically detects format from file extension.

        Args:
            layer: Data layer
            key: File key/path

        Returns:
            Parsed file contents
        """
        path = self._path(layer, key)

        if not path.exists():
            raise FileStorageError(f"File not found: {path}")

        # Check cache first if enabled
        if self.enable_cache and self._cache and self._cache.is_file_cached(path):
            # Query cache instead of reading file
            results = self._cache.query(layer, {"file_path": str(path)})
            if results:
                return results

        # Read from file based on format
        fmt = self._detect_format(key)
        try:
            if fmt == "csv":
                data = self._read_csv(path)
            elif fmt == "json":
                data = self._read_json(path)
            elif fmt == "yaml":
                data = self._read_yaml(path)
            else:
                # Fallback to text
                data = path.read_text(encoding="utf-8")

            # Sync to cache if enabled
            if self.enable_cache and self._cache and isinstance(data, list):
                self._cache.sync_file(layer, path)

            return data

        except Exception as e:
            raise FileStorageError(f"Failed to read {path}: {e}") from e

    def write(
        self,
        layer: DataLayer,
        key: str,
        value: Any,
        source: str = "manual",
        user_confirmed: bool = False,
    ) -> None:
        """Write data to a file with permission enforcement.

        Args:
            layer: Data layer
            key: File key/path
            value: Data to write
            source: Source of write operation
            user_confirmed: Whether user has confirmed

        Raises:
            PermissionError: If write is not permitted
            FileStorageError: If write fails
        """
        # Check permissions
        if self._permission_manager:
            self._permission_manager.check_write_permission(layer, source, user_confirmed)

        path = self._path(layer, key)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Detect format and write
        fmt = self._detect_format(key)
        try:
            if fmt == "csv":
                if not isinstance(value, list):
                    raise FileStorageError("CSV format requires list of dictionaries")
                self._write_csv(path, value)
            elif fmt == "json":
                self._write_json(path, value)
            elif fmt == "yaml":
                self._write_yaml(path, value)
            else:
                # Fallback to text
                if not isinstance(value, str):
                    raise FileStorageError("Unknown format requires string value")
                path.write_text(value, encoding="utf-8")

            # Update manifest if enabled
            if self.enable_manifest and self._manifest:
                self._manifest.record_file(layer.value, path)

            # Update cache if enabled
            if self.enable_cache and self._cache:
                self._cache.sync_file(layer, path)

        except PermissionError:
            raise
        except Exception as e:
            raise FileStorageError(f"Failed to write {path}: {e}") from e

    def delete(
        self,
        layer: DataLayer,
        key: str,
        source: str = "manual",
        user_confirmed: bool = False,
    ) -> None:
        """Delete a file with permission enforcement.

        Args:
            layer: Data layer
            key: File key/path
            source: Source of delete operation
            user_confirmed: Whether user has confirmed

        Raises:
            PermissionError: If delete is not permitted
            FileStorageError: If delete fails
        """
        # Check permissions
        if self._permission_manager:
            self._permission_manager.check_delete_permission(layer, source, user_confirmed)

        path = self._path(layer, key)

        if not path.exists():
            raise FileStorageError(f"File not found: {path}")

        try:
            path.unlink()

            # Remove from manifest if enabled
            if self.enable_manifest and self._manifest:
                self._manifest.remove_entry(path)

        except Exception as e:
            raise FileStorageError(f"Failed to delete {path}: {e}") from e

    def list(self, layer: DataLayer, pattern: str = "*") -> list[str]:
        """List files in a layer.

        Args:
            layer: Data layer
            pattern: Glob pattern (default: *)

        Returns:
            List of file keys
        """
        path = self.root / layer.value
        if not path.exists():
            return []

        return [str(p.relative_to(path)) for p in path.glob(pattern) if p.is_file()]

    def query(
        self,
        layer: DataLayer,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Query data using SQLite cache.

        Args:
            layer: Data layer
            filters: Column filters
            order_by: Column to order by
            limit: Maximum rows to return

        Returns:
            List of matching rows

        Raises:
            FileStorageError: If cache is not enabled
        """
        if not self.enable_cache or not self._cache:
            raise FileStorageError("Query requires cache to be enabled")

        return self._cache.query(layer, filters, order_by, limit)

    def verify_manifest(self, layer: DataLayer) -> dict[str, bool]:
        """Verify files against manifest.

        Args:
            layer: Data layer

        Returns:
            Dict mapping file paths to verification status

        Raises:
            FileStorageError: If manifest is not enabled
        """
        if not self.enable_manifest or not self._manifest:
            raise FileStorageError("Manifest verification requires manifest to be enabled")

        return self._manifest.verify_layer(layer.value, self.root)

    def detect_changes(self, layer: DataLayer) -> dict[str, list[str]]:
        """Detect changes in a layer.

        Args:
            layer: Data layer

        Returns:
            Dict with added/removed/modified files

        Raises:
            FileStorageError: If manifest is not enabled
        """
        if not self.enable_manifest or not self._manifest:
            raise FileStorageError("Change detection requires manifest to be enabled")

        return self._manifest.detect_changes(layer.value, self.root)

    def sync_cache(self, layer: DataLayer) -> dict[str, int]:
        """Sync all files in a layer to cache.

        Args:
            layer: Data layer

        Returns:
            Dict mapping file paths to row counts

        Raises:
            FileStorageError: If cache is not enabled
        """
        if not self.enable_cache or not self._cache:
            raise FileStorageError("Cache sync requires cache to be enabled")

        return self._cache.sync_layer(layer, self.root)

    def convert_format(
        self,
        layer: DataLayer,
        key: str,
        target_format: str,
        source: str = "manual",
        user_confirmed: bool = False,
    ) -> str:
        """Convert a file to a different format.

        Args:
            layer: Data layer
            key: File key/path
            target_format: Target format (csv, json, yaml)
            source: Source of operation
            user_confirmed: Whether user has confirmed

        Returns:
            New file key

        Raises:
            FileStorageError: If conversion fails
        """
        # Read existing data
        data = self.read(layer, key)

        # Generate new filename
        path = Path(key)
        ext_map = {"csv": ".csv", "json": ".json", "yaml": ".yaml"}
        new_ext = ext_map.get(target_format)
        if not new_ext:
            raise FileStorageError(f"Unknown target format: {target_format}")

        new_key = str(path.with_suffix(new_ext))

        # Write in new format
        self.write(layer, new_key, data, source, user_confirmed)

        return new_key


def create_file_storage(
    backend: str = "file",
    enable_cache: bool = True,
    enable_manifest: bool = True,
    **kwargs: Any,
) -> FileStorage:
    """Factory for file storage backends.

    Args:
        backend: Backend type (file, csv, json, yaml)
        enable_cache: Enable SQLite cache
        enable_manifest: Enable manifest tracking
        **kwargs: Additional arguments

    Returns:
        FileStorage instance
    """
    if backend in ["file", "csv", "json", "yaml"]:
        return FileStorage(enable_cache=enable_cache, enable_manifest=enable_manifest, **kwargs)

    raise NotImplementedError(f"Storage backend {backend!r} not implemented")
