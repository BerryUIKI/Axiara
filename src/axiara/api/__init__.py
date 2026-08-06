"""FastAPI application for Axiara.

RESTful API exposing four modes via endpoints:
- /archive/*: Mode 1 (manual edit, learn, crawl, review)
- /query: Mode 2 (single-item query)
- /quote: Mode 3 (batch fill, smart quotation)
- /review: Mode 4 (user review)

Interactive client (REST session) is deferred until Axiara-Web.
"""

from __future__ import annotations

from axiara.api.main import app

__all__ = ["app"]