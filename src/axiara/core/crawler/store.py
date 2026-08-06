"""Store step - write to data/market/."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from axiara.core.crawler.normalize import NormalizedRow
from axiara.core.storage.file_backend import FileStorage
from axiara.core.storage.manifest import ManifestManager


class Storer:
    """Stores normalized rows.

    - Writes to data/market/<source>/<yyyymmdd>-<material>.json
    - Preserves raw capture
    - Updates manifest
    - Requires user confirmation (handled by pipeline)
    """

    def __init__(
        self,
        storage: FileStorage | None = None,
        manifest_manager: ManifestManager | None = None
    ) -> None:
        """Initialize storer.

        Args:
            storage: File storage backend
            manifest_manager: Manifest manager
        """
        self.storage = storage or FileStorage()
        self.manifest = manifest_manager or ManifestManager()

    def store(
        self,
        rows: list[NormalizedRow],
        source: str,
        material: str,
        raw_capture: str | None = None,
        user_confirmed: bool = False
    ) -> dict[str, Any]:
        """Store normalized rows.

        Args:
            rows: Normalized rows
            source: Source ID
            material: Material name
            raw_capture: Raw HTML capture
            user_confirmed: User confirmation status

        Returns:
            Dict with storage results
        """
        from axiara.core.storage import DataLayer

        if not user_confirmed:
            return {
                "success": False,
                "error": "User confirmation required before storage"
            }

        # Generate filename
        today = date.today().strftime("%Y%m%d")
        filename = f"{today}-{material}.json"

        # Convert rows to dict
        rows_data = [
            {
                "name": row.name,
                "spec": row.spec,
                "unit": row.unit,
                "unit_price": row.unit_price,
                "currency": row.currency,
                "effective_date": row.effective_date.isoformat(),
                "note": row.note,
                "source": row.source,
                "url": row.url,
                "fetched_at": row.fetched_at.isoformat(),
                "confidence": row.confidence,
                "raw": row.raw
            }
            for row in rows
        ]

        # Write to data/market/<source>/<filename>
        relative_path = f"{source}/{filename}"
        self.storage.write(
            DataLayer.MARKET,
            relative_path,
            rows_data,
            source="crawler",
            user_confirmed=True
        )

        # Store raw capture if provided
        if raw_capture:
            raw_filename = f"{source}/raw/{today}-{material}-raw.json"
            self.storage.write(
                DataLayer.MARKET,
                raw_filename,
                {"raw": raw_capture, "source": source, "timestamp": datetime.now(timezone.utc).isoformat()},
                source="crawler",
                user_confirmed=True
            )

        return {
            "success": True,
            "rows_stored": len(rows),
            "path": f"data/market/{relative_path}"
        }