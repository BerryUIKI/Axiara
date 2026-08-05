"""LangGraph graphs for Axiara four modes.

Implements four separate graphs:
- archive_graph: Mode 1 (manual edit, learn, crawl, review)
- query_graph: Mode 2 (single-item query)
- quote_graph: Mode 3 (batch fill, smart quotation)
- review_graph: Mode 4 (user review)

Each graph uses interrupt() for user confirmation.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

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


def build_archive_graph() -> StateGraph:
    """Build the archive graph (Mode 1).

    Nodes: manual_edit, learn_agent, crawl_agent, edit_review
    Flows:
    - manual_edit → END (after confirmation)
    - learn_agent → END (after confirmation)
    - crawl_agent → END (after confirmation)
    - edit_review → crawl_agent / learn_agent / END

    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("manual_edit", manual_edit_node)
    graph.add_node("learn_agent", learn_agent_node)
    graph.add_node("crawl_agent", crawl_agent_node)
    graph.add_node("edit_review", edit_review_node)

    # Set entry point based on action
    graph.set_conditional_entry_point(
        dispatcher_node,
        {
            "manual_edit": "manual_edit",
            "learn_agent": "learn_agent",
            "crawl_agent": "crawl_agent",
            "edit_review": "edit_review",
        },
    )

    # Add edges
    graph.add_edge("manual_edit", END)
    graph.add_edge("learn_agent", END)
    graph.add_edge("crawl_agent", END)

    # Edit review can cycle back to crawl/learn
    graph.add_conditional_edges(
        "edit_review",
        lambda state: "crawl" if state.get("needs_crawl") else "learn" if state.get("needs_learn") else END,
        {
            "crawl": "crawl_agent",
            "learn": "learn_agent",
            END: END,
        },
    )

    # Compile with checkpointer for interrupt/resume
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


def build_query_graph() -> StateGraph:
    """Build the query graph (Mode 2).

    Single flow: query_agent → END

    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("query_agent", query_agent_node)

    # Set entry point
    graph.set_entry_point("query_agent")

    # Add edge
    graph.add_edge("query_agent", END)

    # Compile
    return graph.compile()


def build_quote_graph() -> StateGraph:
    """Build the quote graph (Mode 3).

    Flows:
    - batch_fill → END (after confirmation)
    - quote_agent → END (after confirmation)

    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("batch_fill_agent", batch_fill_agent_node)
    graph.add_node("quote_agent", quote_agent_node)

    # Set entry point based on action
    graph.set_conditional_entry_point(
        dispatcher_node,
        {
            "batch_fill": "batch_fill_agent",
            "quote": "quote_agent",
        },
    )

    # Add edges
    graph.add_edge("batch_fill_agent", END)
    graph.add_edge("quote_agent", END)

    # Compile with checkpointer for interrupt/resume
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


def build_review_graph() -> StateGraph:
    """Build the review graph (Mode 4).

    Single flow: user_review_agent → END

    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("user_review_agent", user_review_agent_node)

    # Set entry point
    graph.set_entry_point("user_review_agent")

    # Add edge
    graph.add_edge("user_review_agent", END)

    # Compile with checkpointer for interrupt/resume
    memory = MemorySaver()
    return graph.compile()


# Pre-built graphs for reuse
_archive_graph = None
_query_graph = None
_quote_graph = None
_review_graph = None


def get_archive_graph() -> StateGraph:
    """Get or create the archive graph.

    Returns:
        Compiled archive graph
    """
    global _archive_graph
    if _archive_graph is None:
        _archive_graph = build_archive_graph()
    return _archive_graph


def get_query_graph() -> StateGraph:
    """Get or create the query graph.

    Returns:
        Compiled query graph
    """
    global _query_graph
    if _query_graph is None:
        _query_graph = build_query_graph()
    return _query_graph


def get_quote_graph() -> StateGraph:
    """Get or create the quote graph.

    Returns:
        Compiled quote graph
    """
    global _quote_graph
    if _quote_graph is None:
        _quote_graph = build_quote_graph()
    return _quote_graph


def get_review_graph() -> StateGraph:
    """Get or create the review graph.

    Returns:
        Compiled review graph
    """
    global _review_graph
    if _review_graph is None:
        _review_graph = build_review_graph()
    return _review_graph


async def run_with_interrupt(
    graph: StateGraph,
    initial_state: AgentState,
    confirm_callback: callable,
    thread_id: str = "default",
) -> AgentState:
    """Run a graph with interrupt support.

    When a node sets needs_confirmation=True, the graph interrupts
    and calls confirm_callback. If confirmed, the graph resumes.

    Args:
        graph: Compiled graph to run
        initial_state: Initial state
        confirm_callback: Async callback for confirmation
        thread_id: Thread identifier for checkpointing

    Returns:
        Final state after graph completion
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Run graph
    result = await graph.ainvoke(initial_state, config=config)

    # Check if confirmation needed
    while result.get("needs_confirmation"):
        message = result.get("confirmation_message", "Confirm?")
        confirmed = await confirm_callback(message)

        if not confirmed:
            # User rejected - end flow
            result["confirmed"] = False
            break

        # Resume graph with confirmation
        result["confirmed"] = True
        result = await graph.ainvoke(result, config=config)

    return result