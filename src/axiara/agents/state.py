"""LangGraph state definition for Axiara agents.

Defines the state structure passed between nodes in the graph.
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """State passed between LangGraph nodes.

    Total=False allows optional fields to be added incrementally.
    """

    # Mode identification
    mode: str  # "archive" | "query" | "quote" | "review"

    # User input
    user_input: dict[str, Any]  # Input data (BOM, query, etc.)

    # Data layer references (read-only snapshots)
    main_db_ref: dict[str, Any] | None  # Official baseline data
    learn_db_ref: dict[str, Any] | None  # Learned reference data
    market_db_ref: dict[str, Any] | None  # Market price data

    # Processing results
    cost_result: dict[str, Any] | None  # Cost calculation result
    quotation: dict[str, Any] | None  # Generated quotation

    # Review/learning
    review_suggestions: list[dict[str, Any]] | None  # Review suggestions
    learning_event: dict[str, Any] | None  # Learning event to emit

    # Workflow flags
    needs_confirmation: bool  # Requires user confirmation
    confirmation_message: str | None  # Message for user
    confirmed: bool  # User has confirmed

    # Error handling
    error: str | None  # Error message if any
    warnings: list[str]  # Warning messages

    # Metadata
    session_id: str | None  # Session identifier
    timestamp: str | None  # Operation timestamp