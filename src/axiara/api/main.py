"""FastAPI REST API for Axiara.

Exposes four modes via REST endpoints:
- /archive/*: Mode 1 (manual edit, learn, crawl, review)
- /query: Mode 2 (single-item query)
- /quote: Mode 3 (batch fill, smart quotation)
- /review: Mode 4 (user review)

Additional endpoints:
- /upload: Learning sync upload
- /review/confirm: Admin confirmation for learning proposals
- /health: Health check
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Create FastAPI app
app = FastAPI(
    title="Axiara API",
    description="Multi-agent valuation core - costing engine + price-fetch agent + quotation generator",
    version="0.2.0",
)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Single-item query request."""

    material: str
    quantity: float = 1.0
    unit: str = "kg"


class QuotationRequest(BaseModel):
    """Smart quotation request."""

    materials: list[dict[str, Any]]
    constraints: dict[str, Any] | None = None
    approved: bool = False


class CrawlRequest(BaseModel):
    """Crawl request."""

    source_id: str
    material: str


class UploadRequest(BaseModel):
    """Upload request for learning sync."""

    user_id: str
    scope: str = "generic"  # "generic" | "full"


class ConfirmRequest(BaseModel):
    """Confirmation request."""

    action: str
    thread_id: str
    confirmed: bool


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    version: str


# Archive endpoints (Mode 1)
@app.post("/archive/manual-edit")
async def manual_edit(request: dict[str, Any]) -> dict[str, Any]:
    """Manual edit to official baseline (Mode 1.1).

    Args:
        request: Edit request with data

    Returns:
        Edit result with confirmation requirement
    """
    from axiara.agents import get_archive_graph

    initial_state = {
        "user_input": request,
        "mode": "archive",
    }

    graph = get_archive_graph()
    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/archive/learn")
async def learn(request: dict[str, Any]) -> dict[str, Any]:
    """Learning from historical data (Mode 1.2 learning sub-mode).

    Args:
        request: Learning request with source data

    Returns:
        Learning result
    """
    from axiara.agents import get_archive_graph

    initial_state = {
        "user_input": request,
        "mode": "archive",
    }

    graph = get_archive_graph()
    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/archive/crawl")
async def crawl(request: CrawlRequest) -> dict[str, Any]:
    """Crawl market prices (Mode 1.2 crawler sub-mode).

    Args:
        request: Crawl request with source_id and material

    Returns:
        Crawl result with confirmation requirement
    """
    from axiara.agents import get_archive_graph

    initial_state = {
        "user_input": {
            "action": "crawl",
            "source_id": request.source_id,
            "material": request.material,
        },
        "mode": "archive",
    }

    graph = get_archive_graph()
    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/archive/review")
async def edit_review(request: dict[str, Any]) -> dict[str, Any]:
    """Edit review (Mode 1.3).

    Args:
        request: Review request

    Returns:
        Review suggestions
    """
    from axiara.agents import get_archive_graph

    initial_state = {
        "user_input": request,
        "mode": "archive",
    }

    graph = get_archive_graph()
    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# Query endpoint (Mode 2)
@app.post("/query")
async def query(request: QueryRequest) -> dict[str, Any]:
    """Single-item detail query (Mode 2).

    Args:
        request: Query request with material name

    Returns:
        Cost result with baseline + market reference
    """
    from axiara.agents import get_query_graph

    initial_state = {
        "user_input": {
            "action": "query",
            "material": request.material,
            "quantity": request.quantity,
            "unit": request.unit,
        },
        "mode": "query",
    }

    graph = get_query_graph()
    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# Quote endpoints (Mode 3)
@app.post("/quote/batch-fill")
async def batch_fill(file: UploadFile) -> dict[str, Any]:
    """Batch BOM fill (Mode 3.1).

    Args:
        file: BOM file (Excel/CSV)

    Returns:
        Filled BOM
    """
    from axiara.agents import get_quote_graph

    # Placeholder - would process uploaded file
    initial_state = {
        "user_input": {
            "action": "batch_fill",
            "bom_path": file.filename,
        },
        "mode": "quote",
    }

    graph = get_quote_graph()
    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/quote/generate")
async def generate_quote(request: QuotationRequest) -> dict[str, Any]:
    """Generate smart quotation (Mode 3.2).

    Args:
        request: Quotation request with materials and optional constraints

    Returns:
        Generated quotation
    """
    from axiara.agents import get_quote_graph

    initial_state = {
        "user_input": {
            "action": "quote",
            "materials": request.materials,
            "constraints": request.constraints,
            "approved": request.approved,
        },
        "mode": "quote",
    }

    graph = get_quote_graph()
    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# Review endpoint (Mode 4)
@app.post("/review")
async def review(request: dict[str, Any]) -> dict[str, Any]:
    """User review (Mode 4).

    Args:
        request: Review request with cost/quote table

    Returns:
        Review suggestions
    """
    from axiara.agents import get_review_graph

    initial_state = {
        "user_input": request,
        "mode": "review",
    }

    graph = get_review_graph()
    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# Learning sync endpoints
@app.post("/upload")
async def upload_learning_data(request: UploadRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Upload personal learning library to central hub.

    Args:
        request: Upload request with user_id and scope
        background_tasks: Background tasks for async upload

    Returns:
        Upload status
    """
    # Placeholder - would integrate with learnsync upload
    # from axiara.core.learnsync import upload_bundle

    # Upload would be done in background
    # For now, return placeholder
    return {
        "status": "pending",
        "user_id": request.user_id,
        "scope": request.scope,
        "message": "Upload queued for background processing",
    }


@app.post("/review/confirm")
async def confirm_proposal(request: ConfirmRequest) -> dict[str, Any]:
    """Confirm or reject a learning proposal.

    Admin-only endpoint for central training Agent review.

    Args:
        request: Confirmation request

    Returns:
        Confirmation result
    """
    # Placeholder - would integrate with learnsync review
    return {
        "status": "confirmed" if request.confirmed else "rejected",
        "action": request.action,
        "thread_id": request.thread_id,
    }


# Health check
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="0.2.0",
    )


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API info.

    Returns:
        API information
    """
    return {
        "name": "Axiara API",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
    }