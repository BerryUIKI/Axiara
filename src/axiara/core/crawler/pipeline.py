"""Pipeline orchestrator for crawler."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CrawlResult:
    """Result of a crawl operation."""

    source: str
    success: bool
    rows: list[dict[str, Any]] = field(default_factory=list)
    raw_capture: str | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CrawlerPipeline:
    """Orchestrates the 7-step crawler pipeline.

    Steps: prepare → fetch → parse → normalize → dedup → confirm → store
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the pipeline.

        Args:
            config_path: Path to config files (default: skills/price-crawler/config/)
        """
        self.config_path = config_path or Path("skills/price-crawler/config")
        self.settings = self._load_yaml("settings.yaml")
        self.sources = self._load_yaml("sources.yaml")
        self.normalization = self._load_yaml("normalization.yaml")

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML config file.

        Args:
            filename: Config file name

        Returns:
            Parsed YAML data
        """
        file_path = self.config_path / filename
        if not file_path.exists():
            return {}

        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def crawl(self, source_id: str, material: str) -> CrawlResult:
        """Run the full pipeline for a source and material.

        Args:
            source_id: Source identifier (e.g., 'mofcom-cif')
            material: Material to crawl (e.g., 'copper-wire')

        Returns:
            CrawlResult with success status and data
        """
        # Step 1: Prepare
        source_config = self.sources.get(source_id)
        if not source_config:
            return CrawlResult(source=source_id, success=False, error=f"Unknown source: {source_id}")

        if not source_config.get("enabled", False):
            return CrawlResult(source=source_id, success=False, error=f"Source disabled: {source_id}")

        # Step 2-7: Would be implemented by each step
        # For now, return placeholder
        return CrawlResult(
            source=source_id,
            success=True,
            rows=[],
            raw_capture=None,
            error="Pipeline implementation pending - infrastructure complete",
        )