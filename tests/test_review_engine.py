"""Unit tests for the review engine (复核引擎 / anomaly detection).

Covers:
- ReviewEngine.check_three_way (Mode 1.3): price anomalies, missing
  processes, stale prices, missing baseline, tunable thresholds
- ReviewEngine.check_cost_table (Mode 4): user cost-table validation
- Agent node wiring: edit_review_node / user_review_agent_node
- Serialization (to_dict) and edge cases
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from axiara.agents import edit_review_node, user_review_agent_node
from axiara.core.review import (
    IssueSeverity,
    IssueType,
    ReviewEngine,
    ReviewError,
    ReviewThresholds,
)


def _iso_ago(days: int) -> str:
    """ISO timestamp `days` ago in UTC."""
    ts = datetime.now(timezone.utc) - timedelta(days=days)
    return ts.isoformat()


# Common fixtures -----------------------------------------------------------

MAIN_DATA = {
    "copper-wire": {"unit_price": 65.0, "unit": "kg"},
    "aluminum-sheet": {"unit_price": 22.0, "unit": "kg", "spec": "2mm"},
}

MARKET_FRESH = {
    "copper-wire": {
        "unit_price": 68.0,
        "unit": "kg",
        "timestamp": _iso_ago(3),
    },
    "aluminum-sheet": {
        "unit_price": 21.0,
        "unit": "kg",
        "spec": "2mm",
        "timestamp": _iso_ago(5),
    },
}

LEARN_WITH_PROCESS = {
    "aluminum-sheet": {
        "unit_price": 22.5,
        "unit": "kg",
        "process_cost": [
            {"process": "cutting", "unit_fee": 0.8},
            {"process": "welding", "unit_fee": 2.5},
        ],
    }
}


class TestReviewEngineThreeWay:
    """Tests for Mode 1.3 three-way cross-check."""

    def test_clean_when_no_data(self) -> None:
        """No data → clean report."""
        report = ReviewEngine().check_three_way(None, None, None)
        assert report.status == "clean"
        assert not report.has_issues
        assert report.issues == []

    def test_clean_when_within_band(self) -> None:
        """Prices within threshold → no price anomaly."""
        report = ReviewEngine().check_three_way(
            MAIN_DATA, LEARN_WITH_PROCESS, MARKET_FRESH
        )
        anomalies = [
            i for i in report.issues if i.type == IssueType.PRICE_ANOMALY
        ]
        assert anomalies == []

    def test_market_deviation_detected(self) -> None:
        """Market price deviating > 25% from baseline → anomaly."""
        main = {"steel": {"unit_price": 10.0, "unit": "kg"}}
        market = {"steel": {"unit_price": 14.0, "unit": "kg"}}  # +40%
        report = ReviewEngine().check_three_way(main, None, market)

        anomalies = [
            i for i in report.issues if i.type == IssueType.PRICE_ANOMALY
        ]
        assert len(anomalies) == 1
        issue = anomalies[0]
        assert issue.material == "steel"
        assert issue.severity == IssueSeverity.MEDIUM
        assert issue.deviation == pytest.approx(0.4)
        assert report.checked["price_anomalies"] == 1

    def test_market_conflict_high_severity(self) -> None:
        """Market price deviating > 50% → high severity."""
        main = {"steel": {"unit_price": 10.0, "unit": "kg"}}
        market = {"steel": {"unit_price": 16.0, "unit": "kg"}}  # +60%
        report = ReviewEngine().check_three_way(main, None, market)
        issue = report.issues[0]
        assert issue.severity == IssueSeverity.HIGH

    def test_learn_conflict_detected(self) -> None:
        """Learned price conflicting > 50% with baseline → high."""
        main = {"steel": {"unit_price": 10.0, "unit": "kg"}}
        learn = {"steel": {"unit_price": 20.0, "unit": "kg"}}  # +100%
        report = ReviewEngine().check_three_way(main, learn, None)
        assert len(report.issues) == 1
        issue = report.issues[0]
        assert issue.type == IssueType.PRICE_ANOMALY
        assert issue.severity == IssueSeverity.HIGH
        assert issue.ref_layer == "main"

    def test_missing_process_detected(self) -> None:
        """Learn has process rules but baseline entry has none."""
        main = {"aluminum-sheet": {"unit_price": 22.0, "unit": "kg"}}
        learn = {
            "aluminum-sheet": {
                "unit_price": 22.5,
                "process_cost": [{"process": "cutting", "unit_fee": 0.8}],
            }
        }
        report = ReviewEngine().check_three_way(main, learn, None)
        missing = [
            i for i in report.issues if i.type == IssueType.MISSING_PROCESS
        ]
        assert len(missing) == 1
        assert missing[0].material == "aluminum-sheet"
        assert missing[0].severity == IssueSeverity.MEDIUM

    def test_no_missing_process_when_covered(self) -> None:
        """Baseline entry with process info → no missing-process issue."""
        main = {
            "aluminum-sheet": {
                "unit_price": 22.0,
                "unit": "kg",
                "process": ["cutting", "welding"],
            }
        }
        report = ReviewEngine().check_three_way(main, LEARN_WITH_PROCESS, None)
        missing = [
            i for i in report.issues if i.type == IssueType.MISSING_PROCESS
        ]
        assert missing == []

    def test_stale_price_detected(self) -> None:
        """Market entry older than 30 days → stale."""
        main = {"steel": {"unit_price": 10.0, "unit": "kg"}}
        market = {
            "steel": {
                "unit_price": 10.2,
                "unit": "kg",
                "timestamp": _iso_ago(45),
            }
        }
        report = ReviewEngine().check_three_way(main, None, market)
        stale = [i for i in report.issues if i.type == IssueType.STALE_PRICE]
        assert len(stale) == 1
        assert stale[0].severity == IssueSeverity.LOW

    def test_fresh_price_not_stale(self) -> None:
        """Fresh market entry → no stale issue."""
        main = {"steel": {"unit_price": 10.0, "unit": "kg"}}
        market = {
            "steel": {
                "unit_price": 10.2,
                "unit": "kg",
                "timestamp": _iso_ago(5),
            }
        }
        report = ReviewEngine().check_three_way(main, None, market)
        stale = [i for i in report.issues if i.type == IssueType.STALE_PRICE]
        assert stale == []

    def test_missing_baseline_detected(self) -> None:
        """Learn/market entries without main baseline → low issue."""
        market = {"zinc-plate": {"unit_price": 30.0, "unit": "kg"}}
        report = ReviewEngine().check_three_way(MAIN_DATA, None, market)
        missing = [
            i for i in report.issues if i.type == IssueType.MISSING_BASELINE
        ]
        assert len(missing) == 1
        assert missing[0].material == "zinc-plate"
        assert missing[0].severity == IssueSeverity.LOW

    def test_thresholds_tunable(self) -> None:
        """Custom thresholds change detection behavior."""
        main = {"steel": {"unit_price": 10.0, "unit": "kg"}}
        market = {"steel": {"unit_price": 12.0, "unit": "kg"}}  # +20%

        default_report = ReviewEngine().check_three_way(main, None, market)
        assert default_report.issues == []  # 20% < 25% default

        tight = ReviewThresholds(price_deviation=0.1)
        tight_report = ReviewEngine(thresholds=tight).check_three_way(
            main, None, market
        )
        assert len(tight_report.issues) == 1  # 20% > 10% tight

    def test_list_and_container_formats(self) -> None:
        """Accept list / container-key payload formats."""
        main = [{"name": "steel", "unit_price": 10.0, "unit": "kg"}]
        market = {"items": [{"name": "steel", "price": 14.0}]}
        report = ReviewEngine().check_three_way(main, None, market)
        assert len(report.issues) == 1
        assert report.issues[0].type == IssueType.PRICE_ANOMALY

    def test_report_serialization(self) -> None:
        """to_dict produces serializable output."""
        main = {"steel": {"unit_price": 10.0, "unit": "kg"}}
        market = {"steel": {"unit_price": 14.0, "unit": "kg"}}
        report = ReviewEngine().check_three_way(main, None, market)

        data = report.to_dict()
        assert data["status"] == "issues_found"
        assert isinstance(data["issues"], list)
        assert data["issues"][0]["type"] == "price_anomaly"
        assert data["issues"][0]["severity"] == "medium"
        assert data["issues"][0]["material"] == "steel"
        assert data["checked"]["price_anomalies"] == 1


class TestReviewEngineCostTable:
    """Tests for Mode 4 user cost-table validation."""

    def test_clean_within_baseline(self) -> None:
        """User prices within threshold → clean."""
        cost_table = [
            {"material": "copper-wire", "unit_price": 66.0},
            {"material": "aluminum-sheet", "unit_price": 22.5},
        ]
        report = ReviewEngine().check_cost_table(
            cost_table, main_data=MAIN_DATA, market_data=MARKET_FRESH
        )
        assert report.status == "clean"
        assert report.checked["rows_checked"] == 2

    def test_high_price_flagged(self) -> None:
        """User price 80% above baseline → high anomaly."""
        cost_table = [
            {"material": "copper-wire", "unit_price": 117.0}  # +80%
        ]
        report = ReviewEngine().check_cost_table(
            cost_table, main_data=MAIN_DATA
        )
        issues = [
            i for i in report.issues if i.type == IssueType.PRICE_ANOMALY
        ]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.HIGH
        assert issues[0].details["direction"] == "above"

    def test_low_price_flagged(self) -> None:
        """User price 30% below baseline → medium anomaly."""
        cost_table = [
            {"material": "copper-wire", "unit_price": 45.5}  # -30%
        ]
        report = ReviewEngine().check_cost_table(
            cost_table, main_data=MAIN_DATA
        )
        issues = [
            i for i in report.issues if i.type == IssueType.PRICE_ANOMALY
        ]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.MEDIUM
        assert issues[0].details["direction"] == "below"

    def test_market_band_check(self) -> None:
        """No baseline but market ref exists → band check."""
        cost_table = [{"material": "zinc-plate", "unit_price": 50.0}]
        market = {"zinc-plate": {"unit_price": 30.0, "unit": "kg"}}
        report = ReviewEngine().check_cost_table(
            cost_table, market_data=market
        )
        anomalies = [
            i for i in report.issues if i.type == IssueType.PRICE_ANOMALY
        ]
        assert len(anomalies) == 1
        assert anomalies[0].ref_layer == "market"

    def test_no_reference_flagged(self) -> None:
        """No baseline/market reference → medium missing-baseline."""
        cost_table = [{"material": "unknown-metal", "unit_price": 10.0}]
        report = ReviewEngine().check_cost_table(cost_table)
        missing = [
            i for i in report.issues if i.type == IssueType.MISSING_BASELINE
        ]
        assert len(missing) == 1
        assert missing[0].severity == IssueSeverity.MEDIUM

    def test_missing_process_in_row(self) -> None:
        """Learn covers process but row lacks it → low issue."""
        cost_table = [{"material": "aluminum-sheet", "unit_price": 22.0}]
        report = ReviewEngine().check_cost_table(
            cost_table,
            main_data=MAIN_DATA,
            learn_data=LEARN_WITH_PROCESS,
        )
        missing = [
            i for i in report.issues if i.type == IssueType.MISSING_PROCESS
        ]
        assert len(missing) == 1
        assert missing[0].severity == IssueSeverity.LOW

    def test_row_with_process_not_flagged(self) -> None:
        """Row carrying process info → no missing-process issue."""
        cost_table = [
            {
                "material": "aluminum-sheet",
                "unit_price": 22.0,
                "process": ["cutting"],
            }
        ]
        report = ReviewEngine().check_cost_table(
            cost_table,
            main_data=MAIN_DATA,
            learn_data=LEARN_WITH_PROCESS,
        )
        missing = [
            i for i in report.issues if i.type == IssueType.MISSING_PROCESS
        ]
        assert missing == []

    def test_dict_cost_table_format(self) -> None:
        """Accept {material: {unit_price: ...}} mapping."""
        cost_table = {"copper-wire": {"unit_price": 130.0}}  # +100%
        report = ReviewEngine().check_cost_table(
            cost_table, main_data=MAIN_DATA
        )
        assert report.checked["rows_checked"] == 1
        assert report.issues[0].severity == IssueSeverity.HIGH

    def test_empty_table_raises(self) -> None:
        """Empty cost table → ReviewError."""
        with pytest.raises(ReviewError):
            ReviewEngine().check_cost_table({})


class TestReviewNodes:
    """Tests for agent node wiring."""

    def test_edit_review_clean(self) -> None:
        """No anomalies → no confirmation needed."""
        result = edit_review_node({})
        assert result["review_suggestions"] == []
        assert result["needs_confirmation"] is False
        assert result["checked"]["materials_checked"] == 0

    def test_edit_review_detects_anomaly(self) -> None:
        """Anomalies → suggestions + confirmation gate."""
        state = {
            "main_db_ref": {"steel": {"unit_price": 10.0, "unit": "kg"}},
            "market_db_ref": {"steel": {"unit_price": 16.0, "unit": "kg"}},
        }
        result = edit_review_node(state)
        assert result["needs_confirmation"] is True
        assert len(result["review_suggestions"]) >= 1
        suggestion = result["review_suggestions"][0]
        assert suggestion["type"] == "price_anomaly"
        assert suggestion["material"] == "steel"
        assert "severity" in suggestion

    def test_user_review_missing_table(self) -> None:
        """No cost table → error."""
        result = user_review_agent_node({"user_input": {}})
        assert "error" in result
        assert result["needs_confirmation"] is False

    def test_user_review_generates_suggestions(self) -> None:
        """Cost table with anomaly → suggestions."""
        state = {
            "user_input": {
                "cost_table": [
                    {"material": "copper-wire", "unit_price": 130.0}
                ]
            },
            "main_db_ref": {"copper-wire": {"unit_price": 65.0, "unit": "kg"}},
        }
        result = user_review_agent_node(state)
        assert result["needs_confirmation"] is True
        assert len(result["review_suggestions"]) == 1
        assert result["review_suggestions"][0]["type"] == "price_anomaly"

    def test_user_review_clean(self) -> None:
        """Cost table without anomalies → clean."""
        state = {
            "user_input": {
                "cost_table": [
                    {"material": "copper-wire", "unit_price": 65.0}
                ]
            },
            "main_db_ref": {"copper-wire": {"unit_price": 65.0, "unit": "kg"}},
        }
        result = user_review_agent_node(state)
        assert result["needs_confirmation"] is False
        assert result["review_suggestions"] == []

    def test_user_review_empty_table_error(self) -> None:
        """Empty table → error, not crash."""
        state = {"user_input": {"cost_table": []}}
        result = user_review_agent_node(state)
        assert "error" in result
