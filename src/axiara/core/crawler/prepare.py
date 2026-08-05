"""Prepare step - source resolution and robots check."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml


@dataclass
class PreparedSource:
    """Prepared source for fetching."""

    source_id: str
    base_url: str
    method: str
    legal: str
    robots_allowed: bool
    query_urls: list[str]
    config: dict[str, Any]


class Preparer:
    """Prepares sources for crawling.

    - Loads source from registry
    - Checks robots.txt (cached)
    - Validates source is enabled
    - Composes query URLs
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize preparer.

        Args:
            cache_dir: Cache directory for robots.txt (default: .data/cache/robots/)
        """
        self.cache_dir = cache_dir or Path(".data/cache/robots")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def check_robots_txt(self, robots_url: str, user_agent: str = "*") -> bool:
        """Check if robots.txt allows crawling.

        Args:
            robots_url: URL to robots.txt
            user_agent: User agent to check

        Returns:
            True if allowed
        """
        # Check cache first
        cache_file = self.cache_dir / f"{hashlib.md5(robots_url.encode()).hexdigest()}.json"

        if cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    cached = json.load(f)
                # Check if cache is still valid (24h TTL)
                cached_time = datetime.fromisoformat(cached["timestamp"])
                if (datetime.utcnow() - cached_time).total_seconds() < 86400:
                    return cached.get("allowed", False)
            except Exception:
                pass

        # Fetch robots.txt
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(robots_url)

                # No robots.txt = allowed
                if response.status_code != 200:
                    return True

                # Parse robots.txt (simplified)
                robots_content = response.text
                allowed = self._parse_robots(robots_content, user_agent)

                # Cache result
                cache_file.write_text(
                    json.dumps(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "robots_url": robots_url,
                            "allowed": allowed,
                        }
                    )
                )

                return allowed

        except Exception:
            # On error, assume allowed
            return True

    def _parse_robots(self, robots_content: str, user_agent: str) -> bool:
        """Parse robots.txt content.

        Simplified parser - in production would use urllib.robotparser.

        Args:
            robots_content: robots.txt content
            user_agent: User agent to check

        Returns:
            True if allowed
        """
        # Very simplified - just check for "Disallow: /"
        lines = robots_content.lower().split("\n")
        current_agent = ""

        for line in lines:
            line = line.strip()
            if line.startswith("user-agent:"):
                current_agent = line.split(":", 1)[1].strip()
            elif line.startswith("disallow:") and (current_agent == "*" or current_agent == user_agent):
                path = line.split(":", 1)[1].strip()
                if path == "/":
                    return False

        return True

    def prepare(self, source_config: dict[str, Any], material: str) -> PreparedSource:
        """Prepare a source for crawling.

        Args:
            source_config: Source configuration
            material: Material to crawl

        Returns:
            PreparedSource instance
        """
        source_id = source_config.get("name", "unknown")

        # Check if enabled
        if not source_config.get("enabled", False):
            raise ValueError(f"Source {source_id} is disabled")

        # Check robots.txt
        robots_url = source_config.get("robots_url", "")
        robots_allowed = True
        if robots_url:
            robots_allowed = self.check_robots_txt(robots_url)

        # Compose query URLs (simplified - would be source-specific)
        base_url = source_config.get("base_url", "")
        query_urls = [base_url]  # Simplified - would compose actual query URLs

        return PreparedSource(
            source_id=source_id,
            base_url=base_url,
            method=source_config.get("method", "http"),
            legal=source_config.get("legal", "needs_review"),
            robots_allowed=robots_allowed,
            query_urls=query_urls,
            config=source_config,
        )