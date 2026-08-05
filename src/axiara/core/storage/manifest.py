"""Manifest management for data integrity.

Implements anti-tampering detection via SHA-256 checksums (per D21):
- Detects unauthorized changes to official baseline (data/main/)
- Enables recovery from git history or snapshots
- Supports audit trail via ledger/

Manifest location: .data/db_dump/manifest.json
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class DataLayer(StrEnum):
    """The three data layers plus user uploads."""

    MAIN = "main"  # official price baseline — manual edit ONLY
    LEARN = "learn"  # AI-learned reference
    MARKET = "market"  # crawled market prices
    UPLOADS = "uploads"  # user-provided tables/documents


class ManifestError(Exception):
    """Raised when manifest operations fail."""

    pass


class ManifestEntry:
    """A single manifest entry for a file."""

    def __init__(
        self,
        file_path: Path,
        checksum: str,
        size: int,
        mtime: str,
        layer: str,
        recorded_at: str,
    ) -> None:
        """Initialize a manifest entry.

        Args:
            file_path: Path to the file
            checksum: SHA-256 checksum
            size: File size in bytes
            mtime: Modification time
            layer: Data layer (main, learn, market, uploads)
            recorded_at: When this entry was recorded
        """
        self.file_path = file_path
        self.checksum = checksum
        self.size = size
        self.mtime = mtime
        self.layer = layer
        self.recorded_at = recorded_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "file_path": str(self.file_path),
            "checksum": self.checksum,
            "size": self.size,
            "mtime": self.mtime,
            "layer": self.layer,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManifestEntry":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ManifestEntry instance
        """
        return cls(
            file_path=Path(data["file_path"]),
            checksum=data["checksum"],
            size=data["size"],
            mtime=data["mtime"],
            layer=data["layer"],
            recorded_at=data["recorded_at"],
        )


class ManifestManager:
    """Manages SHA-256 manifest for data integrity.

    Features:
    - Records checksums for all files in data layers
    - Detects unauthorized changes (especially to data/main/)
    - Supports snapshot creation and recovery
    - Audit trail integration with ledger/

    Usage:
        manager = ManifestManager()
        manager.record_layer(DataLayer.MAIN)
        if not manager.verify_layer(DataLayer.MAIN):
            # Unexpected change detected
            pass
    """

    def __init__(self, manifest_dir: Path | None = None) -> None:
        """Initialize the manifest manager.

        Args:
            manifest_dir: Directory for manifest files (default: .data/db_dump/)
        """
        self.manifest_dir = manifest_dir or Path(".data/db_dump")
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.manifest_dir / "manifest.json"
        # Initialize _manifest before calling _load_manifest
        self._manifest: dict[str, dict[str, Any]] = {}
        self._manifest = self._load_manifest()

    def _load_manifest(self) -> dict[str, dict[str, Any]]:
        """Load manifest from disk.

        Returns:
            Manifest dictionary
        """
        if not self.manifest_path.exists():
            # Create empty manifest
            manifest = {"version": "1.0", "entries": {}, "snapshots": []}
            self._save_manifest()
            return manifest

        with open(self.manifest_path) as f:
            return json.load(f)

    def _save_manifest(self) -> None:
        """Save manifest to disk."""
        with open(self.manifest_path, "w") as f:
            json.dump(self._manifest, f, indent=2, default=str)

    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal checksum string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def record_file(self, layer: str, file_path: Path) -> ManifestEntry:
        """Record a file in the manifest.

        Args:
            layer: Data layer
            file_path: Path to file

        Returns:
            ManifestEntry instance

        Raises:
            ManifestError: If file doesn't exist
        """
        if not file_path.exists():
            raise ManifestError(f"File not found: {file_path}")

        checksum = self._compute_checksum(file_path)
        stat = file_path.stat()
        entry = ManifestEntry(
            file_path=file_path,
            checksum=checksum,
            size=stat.st_size,
            mtime=str(stat.st_mtime),
            layer=layer,
            recorded_at=datetime.utcnow().isoformat(),
        )

        # Store in manifest
        file_key = str(file_path)
        self._manifest["entries"][file_key] = entry.to_dict()
        self._save_manifest()

        return entry

    def record_layer(self, layer: str, data_dir: Path | None = None) -> dict[str, ManifestEntry]:
        """Record all files in a layer.

        Args:
            layer: Data layer
            data_dir: Root data directory (default: data/)

        Returns:
            Dict mapping file paths to ManifestEntry instances
        """
        data_dir = data_dir or Path("data")
        layer_dir = data_dir / layer

        if not layer_dir.exists():
            return {}

        entries = {}
        for file_path in layer_dir.glob("**/*"):
            if file_path.is_file() and file_path.suffix.lower() in [".csv", ".json", ".yaml", ".yml"]:
                entry = self.record_file(layer, file_path)
                entries[str(file_path)] = entry

        return entries

    def verify_file(self, file_path: Path) -> bool:
        """Verify a file against the manifest.

        Args:
            file_path: Path to file

        Returns:
            True if file matches manifest, False otherwise
        """
        file_key = str(file_path)

        # Check if file is in manifest
        if file_key not in self._manifest["entries"]:
            return False

        # Check if file exists
        if not file_path.exists():
            return False

        # Verify checksum
        entry_data = self._manifest["entries"][file_key]
        current_checksum = self._compute_checksum(file_path)

        return current_checksum == entry_data["checksum"]

    def verify_layer(self, layer: str, data_dir: Path | None = None) -> dict[str, bool]:
        """Verify all files in a layer against the manifest.

        Args:
            layer: Data layer
            data_dir: Root data directory (default: data/)

        Returns:
            Dict mapping file paths to verification status
        """
        data_dir = data_dir or Path("data")
        layer_dir = data_dir / layer

        if not layer_dir.exists():
            return {}

        results = {}
        for file_path in layer_dir.glob("**/*"):
            if file_path.is_file() and file_path.suffix.lower() in [".csv", ".json", ".yaml", ".yml"]:
                results[str(file_path)] = self.verify_file(file_path)

        return results

    def detect_changes(self, layer: str, data_dir: Path | None = None) -> dict[str, list[str]]:
        """Detect changes in a layer compared to manifest.

        Args:
            layer: Data layer
            data_dir: Root data directory (default: data/)

        Returns:
            Dict with keys: 'added', 'removed', 'modified', 'unchanged'
        """
        data_dir = data_dir or Path("data")
        layer_dir = data_dir / layer

        changes = {
            "added": [],
            "removed": [],
            "modified": [],
            "unchanged": [],
        }

        # Get current files
        current_files: set[str] = set()
        if layer_dir.exists():
            for file_path in layer_dir.glob("**/*"):
                if file_path.is_file() and file_path.suffix.lower() in [".csv", ".json", ".yaml", ".yml"]:
                    current_files.add(str(file_path))

        # Get manifest files for this layer
        manifest_files: set[str] = {
            path_str
            for path_str, entry in self._manifest["entries"].items()
            if entry.get("layer") == layer
        }

        # Detect added files
        for file_path in current_files - manifest_files:
            changes["added"].append(file_path)

        # Detect removed files
        for file_path in manifest_files - current_files:
            changes["removed"].append(file_path)

        # Detect modified files
        for file_path in current_files & manifest_files:
            if self.verify_file(Path(file_path)):
                changes["unchanged"].append(file_path)
            else:
                changes["modified"].append(file_path)

        return changes

    def create_snapshot(self, name: str | None = None) -> str:
        """Create a named snapshot of the current manifest.

        Args:
            name: Snapshot name (default: timestamp)

        Returns:
            Snapshot identifier
        """
        snapshot_id = name or datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        snapshot_data = {
            "id": snapshot_id,
            "created_at": datetime.utcnow().isoformat(),
            "entries": dict(self._manifest["entries"]),
        }

        # Store snapshot
        if "snapshots" not in self._manifest:
            self._manifest["snapshots"] = []

        self._manifest["snapshots"].append(snapshot_data)
        self._save_manifest()

        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore manifest from a snapshot.

        Note: This only restores the manifest, not the actual files.
        Use git or file backup to restore files.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            True if snapshot was found and restored
        """
        for snapshot in self._manifest.get("snapshots", []):
            if snapshot["id"] == snapshot_id:
                self._manifest["entries"] = dict(snapshot["entries"])
                self._save_manifest()
                return True

        return False

    def list_snapshots(self) -> list[dict[str, Any]]:
        """List all snapshots.

        Returns:
            List of snapshot metadata
        """
        return [
            {
                "id": snap["id"],
                "created_at": snap["created_at"],
                "file_count": len(snap["entries"]),
            }
            for snap in self._manifest.get("snapshots", [])
        ]

    def get_entry(self, file_path: Path) -> ManifestEntry | None:
        """Get manifest entry for a file.

        Args:
            file_path: Path to file

        Returns:
            ManifestEntry if found, None otherwise
        """
        file_key = str(file_path)
        entry_data = self._manifest["entries"].get(file_key)

        if entry_data:
            return ManifestEntry.from_dict(entry_data)
        return None

    def remove_entry(self, file_path: Path) -> bool:
        """Remove a file entry from the manifest.

        Args:
            file_path: Path to file

        Returns:
            True if entry was removed
        """
        file_key = str(file_path)
        if file_key in self._manifest["entries"]:
            del self._manifest["entries"][file_key]
            self._save_manifest()
            return True
        return False

    def clear_manifest(self) -> None:
        """Clear all entries from manifest.

        Warning: This removes all recorded checksums.
        """
        self._manifest["entries"] = {}
        self._save_manifest()

    def get_stats(self) -> dict[str, Any]:
        """Get manifest statistics.

        Returns:
            Dict with file counts per layer
        """
        stats = {
            "total_files": len(self._manifest["entries"]),
            "layers": {},
            "snapshots": len(self._manifest.get("snapshots", [])),
        }

        for entry in self._manifest["entries"].values():
            layer = entry.get("layer", "unknown")
            stats["layers"][layer] = stats["layers"].get(layer, 0) + 1

        return stats


# Global manifest manager instance
_manifest_manager: ManifestManager | None = None


def get_manifest_manager() -> ManifestManager:
    """Get the global manifest manager instance.

    Returns:
        Global ManifestManager instance
    """
    global _manifest_manager
    if _manifest_manager is None:
        _manifest_manager = ManifestManager()
    return _manifest_manager
