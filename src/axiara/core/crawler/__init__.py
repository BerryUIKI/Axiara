"""Crawler engine for commodity price fetching.

Implements a 7-step pipeline:
prepare → fetch → parse → normalize → dedup/denoise → confirm → store

All crawled data goes to data/market/ (reference only).
Never writes to data/main/ (official baseline is human-only).
"""

from axiara.core.crawler.fetch import Fetcher
from axiara.core.crawler.normalize import Normalizer
from axiara.core.crawler.parse import Parser
from axiara.core.crawler.pipeline import CrawlerPipeline
from axiara.core.crawler.prepare import Preparer
from axiara.core.crawler.store import Storer

__all__ = [
    "CrawlerPipeline",
    "Preparer",
    "Fetcher",
    "Parser",
    "Normalizer",
    "Storer",
]
