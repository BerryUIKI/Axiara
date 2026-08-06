"""LangGraph nodes for Axiara agents.

Implements nodes for the four modes:
- Mode 1 (Archive): manual_edit, learn_agent, crawl_agent, edit_review
- Mode 2 (Query): query_agent
- Mode 3 (Quote): batch_fill_agent, quote_agent
- Mode 4 (Review): user_review_agent
"""

from __future__ import annotations

from typing import Any

from axiara.agents.state import AgentState


def dispatcher_node(state: AgentState) -> dict[str, Any]:
    """Dispatch to appropriate mode based on user input.

    Args:
        state: Current agent state

    Returns:
        State updates with mode set
    """
    # Determine mode from user input
    user_input = state.get("user_input", {})
    action = user_input.get("action", "")

    # Map actions to modes
    mode_map = {
        "import": "archive",
        "upload": "archive",
        "edit": "archive",
        "learn": "archive",
        "crawl": "archive",
        "query": "query",
        "quote": "quote",
        "batch_fill": "quote",
        "review": "review",
    }

    mode = mode_map.get(action, "query")  # Default to query

    return {"mode": mode}


def manual_edit_node(state: AgentState) -> dict[str, Any]:
    """Handle manual edit operations (Mode 1.1).

    Args:
        state: Current agent state

    Returns:
        State updates after manual edit
    """
    # Manual edit is human-only - this node validates and records
    user_input = state.get("user_input", {})

    # Validate input
    if not user_input.get("data"):
        return {
            "error": "No data provided for manual edit",
            "needs_confirmation": False,
        }

    # Set confirmation flag (manual edits need confirmation before writing)
    return {
        "needs_confirmation": True,
        "confirmation_message": "Confirm manual edit to official baseline (main_db)?",
    }


def learn_agent_node(state: AgentState) -> dict[str, Any]:
    """Handle learning operations (Mode 1.2 learning sub-mode).

    Args:
        state: Current agent state

    Returns:
        State updates with learning results
    """
    # Learning agent extracts rules from historical data
    user_input = state.get("user_input", {})

    # Placeholder - would call core/learnsync/ modules
    return {
        "learning_event": {
            "type": "learning",
            "source": user_input.get("source", "unknown"),
            "status": "pending_review",
        },
        "needs_confirmation": True,
        "confirmation_message": "Confirm learning results to be reviewed?",
    }


def crawl_agent_node(state: AgentState) -> dict[str, Any]:
    """Handle crawl operations (Mode 1.2 crawler sub-mode).

    Uses LangGraph interrupt() for user confirmation before market writes.

    Args:
        state: Current agent state

    Returns:
        State updates with crawl results
    """
    from axiara.core.crawler import CrawlerPipeline

    user_input = state.get("user_input", {})
    source_id = user_input.get("source_id")
    material = user_input.get("material")

    if not source_id or not material:
        return {
            "error": "Missing source_id or material for crawl",
            "needs_confirmation": False,
        }

    # Run crawler pipeline
    pipeline = CrawlerPipeline()
    result = pipeline.crawl(source_id, material)

    if not result.success:
        return {
            "error": result.error or "Crawl failed",
            "needs_confirmation": False,
        }

    # Set confirmation flag - uses interrupt() in graph
    return {
        "market_db_ref": {
            "source": source_id,
            "material": material,
            "rows": result.rows,
            "timestamp": result.timestamp,
        },
        "needs_confirmation": True,
        "confirmation_message": f"Confirm writing {len(result.rows)} crawled prices to market_db?",
    }


def edit_review_node(state: AgentState) -> dict[str, Any]:
    """Handle edit review operations (Mode 1.3).

    Runs the anomaly-detection review engine for a three-way cross-check
    across main / learn / market. The engine is read-only: it produces a
    pending-review list for human confirmation and can never write main_db.

    Args:
        state: Current agent state

    Returns:
        State updates with review suggestions
    """
    from axiara.core.review import ReviewEngine

    # Cross-validate main_db + learn_db + market_db
    main_ref = state.get("main_db_ref")
    learn_ref = state.get("learn_db_ref")
    market_ref = state.get("market_db_ref")

    report = ReviewEngine().check_three_way(main_ref, learn_ref, market_ref)

    if not report.has_issues:
        return {
            "review_suggestions": [],
            "checked": report.checked,
            "needs_confirmation": False,
            "confirmation_message": "Three-way cross-check passed: no anomalies found.",
        }

    suggestions = [issue.to_dict() for issue in report.issues]
    return {
        "review_suggestions": suggestions,
        "checked": report.checked,
        "needs_confirmation": True,
        "confirmation_message": (
            f"Cross-check found {len(suggestions)} issue(s) "
            f"({report.checked.get('price_anomalies', 0)} price anomalies, "
            f"{report.checked.get('missing_processes', 0)} missing processes, "
            f"{report.checked.get('stale_prices', 0)} stale prices, "
            f"{report.checked.get('missing_baseline', 0)} missing baselines). "
            "Confirm to proceed?"
        ),
    }


def query_agent_node(state: AgentState) -> dict[str, Any]:
    """Handle single-item query (Mode 2).

    Args:
        state: Current agent state

    Returns:
        State updates with query results
    """
    from axiara.core.costing import CostingEngine, MaterialInput

    user_input = state.get("user_input", {})
    material_name = user_input.get("material")

    if not material_name:
        return {
            "error": "No material specified for query",
            "needs_confirmation": False,
        }

    # Create material input
    material = MaterialInput(
        name=material_name,
        quantity=user_input.get("quantity", 1.0),
        unit=user_input.get("unit", "kg"),
    )

    # Calculate cost
    engine = CostingEngine()
    result = engine.calculate_material_cost(
        material,
        baseline_data=state.get("main_db_ref"),
        learn_data=state.get("learn_db_ref"),
        market_data=state.get("market_db_ref"),
    )

    return {
        "cost_result": {
            "material": material_name,
            "breakdown": {
                "material": result.breakdown.material,
                "total": result.breakdown.total,
            },
            "confidence": result.confidence,
            "sources": result.sources,
            "warnings": result.warnings,
        },
        "needs_confirmation": False,
    }


def batch_fill_agent_node(state: AgentState) -> dict[str, Any]:
    """Handle batch BOM fill (Mode 3.1).

    Args:
        state: Current agent state

    Returns:
        State updates with filled BOM
    """
    # Placeholder - would use openpyxl to process Excel BOM
    user_input = state.get("user_input", {})

    if not user_input.get("bom_path"):
        return {
            "error": "No BOM file specified",
            "needs_confirmation": False,
        }

    return {
        "error": "BOM fill not yet implemented - requires openpyxl integration",
        "needs_confirmation": False,
    }


def quote_agent_node(state: AgentState) -> dict[str, Any]:
    """Handle smart quotation (Mode 3.2).

    Args:
        state: Current agent state

    Returns:
        State updates with quotation
    """
    from axiara.core.costing import MaterialInput
    from axiara.core.quote import QuoteConstraints, QuoteGenerator

    user_input = state.get("user_input", {})

    # Extract materials
    materials_data = user_input.get("materials", [])
    materials = [
        MaterialInput(
            name=m.get("name"),
            spec=m.get("spec", ""),
            quantity=m.get("quantity", 1.0),
            unit=m.get("unit", "kg"),
            unit_price=m.get("unit_price"),
        )
        for m in materials_data
    ]

    # Extract constraints if any
    constraints = None
    if user_input.get("constraints"):
        c = user_input["constraints"]
        constraints = QuoteConstraints(
            min_margin=c.get("min_margin"),
            max_margin=c.get("max_margin"),
            price_cap=c.get("price_cap"),
            price_floor=c.get("price_floor"),
            currency=c.get("currency", "CNY"),
        )

    # Generate quotation
    generator = QuoteGenerator()
    quotation = generator.generate_quotation(
        materials=materials,
        constraints=constraints,
        baseline_data=state.get("main_db_ref"),
        learn_data=state.get("learn_db_ref"),
        market_data=state.get("market_db_ref"),
        learn_rules=state.get("learn_db_ref", {}).get("rules"),
    )

    # Emit learning event if approved
    learning_event = None
    if user_input.get("approved"):
        event = generator.emit_learning_event(quotation, corrected=False)
        learning_event = {
            "quotation_id": event.quotation_id,
            "material_costs": event.material_costs,
            "final_price": event.final_price,
            "margin": event.margin,
        }

    return {
        "quotation": {
            "cost": quotation.cost,
            "price": quotation.price,
            "margin": quotation.margin,
            "tier": quotation.tier.value if quotation.tier else None,
            "confidence": quotation.confidence,
            "warnings": quotation.warnings,
        },
        "learning_event": learning_event,
        "needs_confirmation": not constraints,  # Ask for confirmation if no constraints
        "confirmation_message": "Review quotation. Confirm to proceed?",
    }


def user_review_agent_node(state: AgentState) -> dict[str, Any]:
    """Handle user review (Mode 4).

    Validates the user's own cost/quote table against main + market via
    the anomaly-detection review engine, flagging abnormal low/high prices,
    missing processes, and unvalidatable rows.

    Args:
        state: Current agent state

    Returns:
        State updates with review results
    """
    from axiara.core.review import ReviewEngine, ReviewError

    user_input = state.get("user_input", {})

    if not user_input.get("cost_table"):
        return {
            "error": "No cost table provided for review",
            "needs_confirmation": False,
        }

    try:
        report = ReviewEngine().check_cost_table(
            user_input["cost_table"],
            main_data=state.get("main_db_ref"),
            market_data=state.get("market_db_ref"),
            learn_data=state.get("learn_db_ref"),
        )
    except ReviewError as e:
        return {
            "error": str(e),
            "needs_confirmation": False,
        }

    if not report.has_issues:
        return {
            "review_suggestions": [],
            "checked": report.checked,
            "needs_confirmation": False,
            "confirmation_message": (
                "Review complete: no anomalies found in cost table."
            ),
        }

    suggestions = [issue.to_dict() for issue in report.issues]
    return {
        "review_suggestions": suggestions,
        "checked": report.checked,
        "needs_confirmation": True,
        "confirmation_message": (
            f"Review found {len(suggestions)} issue(s) in cost table. "
            "Apply suggestions?"
        ),
    }