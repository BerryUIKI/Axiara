"""Axiara LangGraph agents.

Implements four-mode architecture:
- Mode 1 (Archive): manual edit, learn, crawl, review
- Mode 2 (Query): single-item detail query
- Mode 3 (Quote): batch BOM fill, smart quotation
- Mode 4 (Review): user review

All nodes access data layers via storage PermissionManager.
"""

from __future__ import annotations

from axiara.agents.graphs import (
    build_archive_graph,
    build_query_graph,
    build_quote_graph,
    build_review_graph,
    get_archive_graph,
    get_query_graph,
    get_quote_graph,
    get_review_graph,
    run_with_interrupt,
)
from axiara.agents.nodes import (
    batch_fill_agent_node,
    crawl_agent_node,
    dispatcher_node,
    edit_review_node,
    learn_agent_node,
    manual_edit_node,
    query_agent_node,
    quote_agent_node,
    user_review_agent_node,
)
from axiara.agents.state import AgentState

__all__ = [
    "AgentState",
    "build_archive_graph",
    "build_query_graph",
    "build_quote_graph",
    "build_review_graph",
    "get_archive_graph",
    "get_query_graph",
    "get_quote_graph",
    "get_review_graph",
    "run_with_interrupt",
    "dispatcher_node",
    "manual_edit_node",
    "learn_agent_node",
    "crawl_agent_node",
    "edit_review_node",
    "query_agent_node",
    "batch_fill_agent_node",
    "quote_agent_node",
    "user_review_agent_node",
]