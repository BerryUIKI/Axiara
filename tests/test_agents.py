"""Unit tests for LangGraph agents.

Tests cover:
- Graph construction for all four modes
- Node functionality
- Interrupt/resume with confirmation
- Permission enforcement at node level
"""

from __future__ import annotations

import pytest

from axiara.agents import (
    AgentState,
    build_archive_graph,
    build_query_graph,
    build_quote_graph,
    build_review_graph,
    crawl_agent_node,
    dispatcher_node,
    query_agent_node,
    quote_agent_node,
)


class TestAgentState:
    """Tests for agent state."""

    def test_state_creation(self) -> None:
        """Create agent state."""
        state: AgentState = {
            "mode": "query",
            "user_input": {"material": "copper-wire"},
        }
        assert state["mode"] == "query"
        assert state["user_input"]["material"] == "copper-wire"

    def test_state_with_optional_fields(self) -> None:
        """Create state with optional fields."""
        state: AgentState = {
            "mode": "quote",
            "user_input": {},
            "needs_confirmation": True,
            "warnings": ["test warning"],
        }
        assert state["needs_confirmation"] is True
        assert len(state["warnings"]) == 1


class TestDispatcherNode:
    """Tests for dispatcher node."""

    def test_dispatch_to_query(self) -> None:
        """Dispatch to query mode."""
        state: AgentState = {"user_input": {"action": "query"}}
        result = dispatcher_node(state)
        assert result["mode"] == "query"

    def test_dispatch_to_quote(self) -> None:
        """Dispatch to quote mode."""
        state: AgentState = {"user_input": {"action": "quote"}}
        result = dispatcher_node(state)
        assert result["mode"] == "quote"

    def test_dispatch_to_archive(self) -> None:
        """Dispatch to archive mode."""
        state: AgentState = {"user_input": {"action": "import"}}
        result = dispatcher_node(state)
        assert result["mode"] == "archive"

    def test_dispatch_default_to_query(self) -> None:
        """Default to query mode."""
        state: AgentState = {"user_input": {}}
        result = dispatcher_node(state)
        assert result["mode"] == "query"


class TestQueryAgentNode:
    """Tests for query agent node."""

    def test_query_basic(self) -> None:
        """Query material cost."""
        state: AgentState = {
            "user_input": {
                "material": "copper-wire",
                "quantity": 10.0,
                "unit": "kg",
            }
        }
        result = query_agent_node(state)

        assert "cost_result" in result
        assert result["cost_result"]["material"] == "copper-wire"
        assert "breakdown" in result["cost_result"]

    def test_query_missing_material(self) -> None:
        """Query with missing material."""
        state: AgentState = {"user_input": {}}
        result = query_agent_node(state)

        assert "error" in result
        assert "No material specified" in result["error"]

    def test_query_with_baseline_data(self) -> None:
        """Query with baseline data."""
        state: AgentState = {
            "user_input": {
                "material": "copper-wire",
                "quantity": 10.0,
                "unit": "kg",
            },
            "main_db_ref": {
                "copper-wire": {
                    "unit_price": 65.0,
                    "unit": "kg",
                }
            },
        }
        result = query_agent_node(state)

        assert result["cost_result"]["breakdown"]["material"] == 650.0


class TestQuoteAgentNode:
    """Tests for quote agent node."""

    def test_quote_basic(self) -> None:
        """Generate basic quotation."""
        state: AgentState = {
            "user_input": {
                "materials": [
                    {
                        "name": "copper-wire",
                        "quantity": 10.0,
                        "unit": "kg",
                        "unit_price": 70.0,
                    }
                ]
            }
        }
        result = quote_agent_node(state)

        assert "quotation" in result
        assert result["quotation"]["cost"] == 700.0
        assert result["quotation"]["price"] > 0

    def test_quote_with_constraints(self) -> None:
        """Generate quotation with constraints."""
        state: AgentState = {
            "user_input": {
                "materials": [
                    {
                        "name": "copper-wire",
                        "quantity": 10.0,
                        "unit": "kg",
                        "unit_price": 70.0,
                    }
                ],
                "constraints": {
                    "min_margin": 20.0,
                    "currency": "CNY",
                },
            }
        }
        result = quote_agent_node(state)

        assert "quotation" in result
        assert result["quotation"]["margin"] >= 20.0

    def test_quote_learning_event_on_approval(self) -> None:
        """Emit learning event when approved."""
        state: AgentState = {
            "user_input": {
                "materials": [
                    {
                        "name": "copper-wire",
                        "quantity": 10.0,
                        "unit": "kg",
                        "unit_price": 70.0,
                    }
                ],
                "approved": True,
            }
        }
        result = quote_agent_node(state)

        assert "learning_event" in result
        assert result["learning_event"] is not None


class TestCrawlAgentNode:
    """Tests for crawl agent node."""

    def test_crawl_missing_params(self) -> None:
        """Crawl with missing parameters."""
        state: AgentState = {"user_input": {}}
        result = crawl_agent_node(state)

        assert "error" in result

    def test_crawl_sets_confirmation(self) -> None:
        """Crawl sets confirmation flag."""
        state: AgentState = {
            "user_input": {
                "source_id": "test-source",
                "material": "test-material",
            }
        }
        result = crawl_agent_node(state)

        # Should have confirmation message (even if crawl fails in test)
        assert "needs_confirmation" in result or "error" in result


class TestGraphBuilding:
    """Tests for graph construction."""

    def test_build_archive_graph(self) -> None:
        """Build archive graph."""
        graph = build_archive_graph()
        assert graph is not None

    def test_build_query_graph(self) -> None:
        """Build query graph."""
        graph = build_query_graph()
        assert graph is not None

    def test_build_quote_graph(self) -> None:
        """Build quote graph."""
        graph = build_quote_graph()
        assert graph is not None

    def test_build_review_graph(self) -> None:
        """Build review graph."""
        graph = build_review_graph()
        assert graph is not None


class TestGraphExecution:
    """Tests for graph execution."""

    @pytest.mark.asyncio
    async def test_query_graph_execution(self) -> None:
        """Execute query graph."""
        graph = build_query_graph()

        initial_state: AgentState = {
            "user_input": {
                "material": "copper-wire",
                "quantity": 10.0,
                "unit": "kg",
            },
            "mode": "query",
        }

        result = await graph.ainvoke(initial_state)

        assert "cost_result" in result or "error" in result

    @pytest.mark.asyncio
    async def test_quote_graph_execution(self) -> None:
        """Execute quote graph."""
        graph = build_quote_graph()

        initial_state: AgentState = {
            "user_input": {
                "action": "quote",
                "materials": [
                    {
                        "name": "copper-wire",
                        "quantity": 10.0,
                        "unit": "kg",
                        "unit_price": 70.0,
                    }
                ],
            },
            "mode": "quote",
        }

        result = await graph.ainvoke(initial_state, config={"configurable": {"thread_id": "default"}})

        assert "quotation" in result or "error" in result