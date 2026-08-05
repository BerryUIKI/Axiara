"""Fetch step - HTTP client with retry logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class FetchResult:
    """Result of a fetch operation."""

    url: str
    success: bool
    status_code: int | None = None
    content: str | None = None
    error: str | None = None


class Fetcher:
    """Fetches pages from sources.

    - HTTP client with retry/backoff
    - Respects rate limits
    - Handles errors gracefully
    """

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        """Initialize fetcher.

        Args:
            settings: Crawler settings
        """
        self.settings = settings or {}
        http_settings = self.settings.get("http", {})
        self.timeout = http_settings.get("timeout", {})
        self.retries = http_settings.get("retries", {})
        self.user_agent = http_settings.get("user_agent", "Axiara-PriceBot/0.1")

    def fetch(self, url: str, method: str = "http") -> FetchResult:
        """Fetch a page.

        Args:
            url: URL to fetch
            method: Fetch method (http or browser)

        Returns:
            FetchResult instance
        """
        if method == "browser":
            # Placeholder for browser automation
            return FetchResult(url=url, success=False, error="Browser mode not implemented")

        # HTTP fetch with retry
        max_attempts = self.retries.get("max_attempts", 3)
        backoffs = self.retries.get("backoff", [1, 5, 15])

        for attempt in range(max_attempts):
            try:
                with httpx.Client(timeout=httpx.Timeout(
                    connect=self.timeout.get("connect", 10),
                    read=self.timeout.get("read", 30)
                )) as client:
                    response = client.get(
                        url,
                        headers={"User-Agent": self.user_agent},
                        follow_redirects=True
                    )

                    if response.status_code == 200:
                        return FetchResult(
                            url=url,
                            success=True,
                            status_code=response.status_code,
                            content=response.text
                        )
                    elif response.status_code < 500:
                        # Client error - don't retry
                        return FetchResult(
                            url=url,
                            success=False,
                            status_code=response.status_code,
                            error=f"HTTP {response.status_code}"
                        )
                    else:
                        # Server error - retry
                        if attempt < max_attempts - 1:
                            import time
                            time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
                            continue

                        return FetchResult(
                            url=url,
                            success=False,
                            status_code=response.status_code,
                            error=f"HTTP {response.status_code} after {max_attempts} retries"
                        )

            except Exception as e:
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
                    continue

                return FetchResult(url=url, success=False, error=str(e))

        return FetchResult(url=url, success=False, error="Max retries exceeded")