"""FastAPI application — scaffold.

RESTful API for external clients. Interactive client (REST session)
is deferred until Axiara-Web.
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="Axiara",
    description="Agent quotation core — REST API",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
