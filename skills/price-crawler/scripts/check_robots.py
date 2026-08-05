#!/usr/bin/env python3
"""
Check robots.txt compliance for a given source URL.

Fetches robots.txt from the source domain and checks if the crawler is allowed
to access the specified path. Caches results in .data/cache/robots/.
"""

import hashlib
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


# Cache settings
CACHE_DIR = Path(".data/cache/robots")
CACHE_TTL_HOURS = 24


def get_cache_path(url: str) -> Path:
    """Get cache file path for a URL."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(url)
    domain = parsed.netloc
    cache_key = hashlib.md5(domain.encode()).hexdigest()

    return CACHE_DIR / f"{domain}_{cache_key}.json"


def load_cached_robots(url: str) -> dict | None:
    """Load cached robots.txt data if still valid."""
    cache_path = get_cache_path(url)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, 'r') as f:
            cached = json.load(f)

        # Check if cache is still valid
        cached_time = datetime.fromisoformat(cached['timestamp'])
        if datetime.now() - cached_time > timedelta(hours=CACHE_TTL_HOURS):
            return None

        return cached
    except Exception:
        return None


def save_cached_robots(url: str, robots_url: str, content: str, allowed: bool, details: dict):
    """Save robots.txt check result to cache."""
    cache_path = get_cache_path(url)

    cached = {
        'timestamp': datetime.now().isoformat(),
        'url': url,
        'robots_url': robots_url,
        'robots_content': content,
        'allowed': allowed,
        'details': details
    }

    with open(cache_path, 'w') as f:
        json.dump(cached, f, indent=2)


def check_robots_txt(target_url: str, user_agent: str = "*") -> tuple[bool, dict]:
    """
    Check if crawling target_url is allowed by robots.txt.

    Returns: (allowed: bool, details: dict)
    """
    parsed = urlparse(target_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    # Try cached version first
    cached = load_cached_robots(target_url)
    if cached:
        return cached['allowed'], cached['details']

    # Fetch robots.txt
    try:
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        # Check if allowed
        can_fetch = rp.can_fetch(user_agent, target_url)
        crawl_delay = rp.crawl_delay(user_agent)

        details = {
            'robots_url': robots_url,
            'robots_exists': True,
            'can_fetch': can_fetch,
            'crawl_delay': crawl_delay,
            'user_agent': user_agent,
            'target_path': parsed.path,
        }

        # Save to cache
        robots_content = ""
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(robots_url)
                if resp.status_code == 200:
                    robots_content = resp.text
        except Exception:
            pass

        save_cached_robots(target_url, robots_url, robots_content, can_fetch, details)

        return can_fetch, details

    except Exception as e:
        # If robots.txt doesn't exist or can't be fetched, assume allowed
        # (most sites allow crawling if no robots.txt)
        details = {
            'robots_url': robots_url,
            'robots_exists': False,
            'error': str(e),
            'assumption': 'No robots.txt found - assuming allowed'
        }

        # Cache the result
        save_cached_robots(target_url, robots_url, "", True, details)

        return True, details


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python check_robots.py <URL> [user-agent]")
        print()
        print("Checks robots.txt compliance for the given URL.")
        print()
        print("Arguments:")
        print("  URL          The target URL to check")
        print("  user-agent   User agent string (default: *)")
        print()
        print("Cache: Results cached in .data/cache/robots/ for 24 hours")
        sys.exit(1)

    target_url = sys.argv[1]
    user_agent = sys.argv[2] if len(sys.argv) > 2 else "*"

    print(f"Checking robots.txt for: {target_url}")
    print(f"User-Agent: {user_agent}")
    print("=" * 60)

    allowed, details = check_robots_txt(target_url, user_agent)

    print()
    print(f"Robots URL: {details.get('robots_url', 'N/A')}")
    print(f"Robots exists: {details.get('robots_exists', False)}")

    if 'crawl_delay' in details and details['crawl_delay']:
        print(f"Crawl-delay: {details['crawl_delay']} seconds")

    print()

    if allowed:
        print("✓ ALLOWED - robots.txt permits crawling")
    else:
        print("✗ BLOCKED - robots.txt disallows crawling")
        print()
        print("⚠ WARNING: Respect robots.txt! Do not bypass this restriction.")
        print("  See docs/crawler-spec.md for compliance requirements.")

    print()
    print("=" * 60)

    return 0 if allowed else 1


if __name__ == "__main__":
    sys.exit(main())