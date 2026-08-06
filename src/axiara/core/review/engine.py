"""Anomaly-detection review engine (复核引擎).

Implements the review engine per docs/business-modes.md:
- Mode 1.3 Edit review: three-way cross-check across main / learn / market.
- Mode 4 Review: user cost/quote table validation against main + market.

Detects: price anomalies, missing processes, stale prices, missing baseline.
The engine is **read-only** — it never writes to any data layer. Output is a
pending-review list for human confirmation (it cannot write main_db).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

# Default detection thresholds (tunable via ReviewThresholds).
# Aligned with the 50% conflict ratio used by learnsync.review.
DEFAULT_PRICE_DEVIATION = 0.25  # ±25% vs baseline → anomaly
DEFAULT_BASELINE_CONFLICT = 0.50  # ±50% vs baseline → conflict (high)
DEFAULT_MARKET_BAND = 0.20  # ±20% market reference band
DEFAULT_STALE_MAX_AGE_DAYS = 30  # market data older than 30 days → stale


class ReviewError(Exception):
    """Raised when review operations fail."""

    pass


class IssueType(StrEnum):
    """Type of detected issue."""

    PRICE_ANOMALY = "price_anomaly"
    MISSING_PROCESS = "missing_process"
    STALE_PRICE = "stale_price"
    MISSING_BASELINE = "missing_baseline"


class IssueSeverity(StrEnum):
    """Severity level of an issue."""

    HIGH = "high"  # Requires human attention (conflict / large deviation)
    MEDIUM = "medium"  # Should be reviewed before use
    LOW = "low"  # Informational


@dataclass
class ReviewThresholds:
    """Configurable thresholds for anomaly detection."""

    price_deviation: float = DEFAULT_PRICE_DEVIATION
    baseline_conflict: float = DEFAULT_BASELINE_CONFLICT
    market_band: float = DEFAULT_MARKET_BAND
    stale_max_age_days: int = DEFAULT_STALE_MAX_AGE_DAYS


@dataclass
class ReviewIssue:
    """A single detected issue."""

    type: IssueType
    severity: IssueSeverity
    message: str
    material: str = ""
    ref_layer: str = ""  # main | learn | market | user
    ref_value: float | None = None
    current_value: float | None = None
    deviation: float | None = None  # relative deviation ratio (0.25 = 25%)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (serializable)."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "message": self.message,
            "material": self.material,
            "ref_layer": self.ref_layer,
            "ref_value": self.ref_value,
            "current_value": self.current_value,
            "deviation": self.deviation,
            "details": self.details,
        }


@dataclass
class ReviewReport:
    """Result of a review run."""

    issues: list[ReviewIssue] = field(default_factory=list)
    checked: dict[str, Any] = field(default_factory=dict)
    status: str = "clean"  # clean | issues_found

    @property
    def has_issues(self) -> bool:
        """Whether any issues were found."""
        return bool(self.issues) or self.status == "issues_found"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (serializable)."""
        return {
            "status": self.status,
            "issues": [i.to_dict() for i in self.issues],
            "checked": self.checked,
        }


class ReviewEngine:
    """Anomaly detection across the three data layers.

    Style follows CostingEngine: pure logic over dict snapshots supplied by
    the caller (LangGraph nodes pass main/learn/market refs from state).
    """

    def __init__(self, thresholds: ReviewThresholds | None = None) -> None:
        """Initialize the review engine.

        Args:
            thresholds: Detection thresholds (default: ReviewThresholds())
        """
        self.thresholds = thresholds or ReviewThresholds()

    # ------------------------------------------------------------------
    # Mode 1.3 — three-way cross-check (main + learn + market)
    # ------------------------------------------------------------------

    def check_three_way(
        self,
        main_data: dict[str, Any] | None,
        learn_data: dict[str, Any] | None,
        market_data: dict[str, Any] | None,
        now: datetime | None = None,
    ) -> ReviewReport:
        """Cross-check main / learn / market for anomalies (Mode 1.3).

        Detects:
        - price anomalies (main vs market, main vs learn)
        - missing processes (learn rules not covered by main)
        - stale market prices (older than stale_max_age_days)
        - missing baseline (learn/market entries without a main baseline)

        Args:
            main_data: Official baseline snapshot (data/main/)
            learn_data: Learned reference snapshot (data/learn/)
            market_data: Market price snapshot (data/market/)
            now: Reference time for staleness (default: datetime.now(UTC))

        Returns:
            ReviewReport with all detected issues
        """
        now = now or datetime.now(timezone.utc)
        main_idx = self._index_entries(main_data)
        learn_idx = self._index_entries(learn_data)
        market_idx = self._index_entries(market_data)

        issues: list[ReviewIssue] = []
        materials = sorted(
            set(main_idx) | set(learn_idx) | set(market_idx)
        )

        for name in materials:
            entry = main_idx.get(name)
            learn_entry = learn_idx.get(name)
            market_entry = market_idx.get(name)

            # 1. main vs market: deviation beyond band → anomaly
            if entry is not None and market_entry is not None:
                base_price = self._extract_price(entry)
                market_price = self._extract_price(market_entry)
                if base_price is not None and market_price is not None:
                    ratio = self._deviation_ratio(market_price, base_price)
                    if ratio > self.thresholds.price_deviation:
                        severity = (
                            IssueSeverity.HIGH
                            if ratio > self.thresholds.baseline_conflict
                            else IssueSeverity.MEDIUM
                        )
                        issues.append(
                            ReviewIssue(
                                type=IssueType.PRICE_ANOMALY,
                                severity=severity,
                                message=(
                                    f"Market price for '{name}' deviates "
                                    f"{ratio:.0%} from baseline "
                                    f"({market_price:.2f} vs {base_price:.2f})"
                                ),
                                material=name,
                                ref_layer="main",
                                ref_value=base_price,
                                current_value=market_price,
                                deviation=ratio,
                                details={"source": "market"},
                            )
                        )

            # 2. main vs learn: conflict → high severity
            if entry is not None and learn_entry is not None:
                base_price = self._extract_price(entry)
                learn_price = self._extract_price(learn_entry)
                if base_price is not None and learn_price is not None:
                    ratio = self._deviation_ratio(learn_price, base_price)
                    if ratio > self.thresholds.baseline_conflict:
                        issues.append(
                            ReviewIssue(
                                type=IssueType.PRICE_ANOMALY,
                                severity=IssueSeverity.HIGH,
                                message=(
                                    f"Learned price for '{name}' conflicts "
                                    f"with baseline ({ratio:.0%} deviation)"
                                ),
                                material=name,
                                ref_layer="main",
                                ref_value=base_price,
                                current_value=learn_price,
                                deviation=ratio,
                                details={"source": "learn"},
                            )
                        )

            # 3. Missing process: learn has process rules, main entry has none
            if entry is not None and learn_entry is not None:
                if self._has_process_rules(learn_entry) and not self._has_process(entry):
                    issues.append(
                        ReviewIssue(
                            type=IssueType.MISSING_PROCESS,
                            severity=IssueSeverity.MEDIUM,
                            message=(
                                f"Learned process rules exist for '{name}' "
                                f"but baseline entry has no process info"
                            ),
                            material=name,
                            ref_layer="learn",
                            details={"source": "learn"},
                        )
                    )

            # 4. Missing baseline: learn/market have data, main does not
            if entry is None and (learn_entry is not None or market_entry is not None):
                ref_layer = "learn" if learn_entry is not None else "market"
                issues.append(
                    ReviewIssue(
                        type=IssueType.MISSING_BASELINE,
                        severity=IssueSeverity.LOW,
                        message=(
                            f"No official baseline for '{name}' — "
                            f"available in {ref_layer} only"
                        ),
                        material=name,
                        ref_layer=ref_layer,
                        details={
                            "in_learn": learn_entry is not None,
                            "in_market": market_entry is not None,
                        },
                    )
                )

            # 5. Stale market price
            if market_entry is not None:
                age_days = self._entry_age_days(market_entry, now)
                if age_days is not None and age_days > self.thresholds.stale_max_age_days:
                    issues.append(
                        ReviewIssue(
                            type=IssueType.STALE_PRICE,
                            severity=IssueSeverity.LOW,
                            message=(
                                f"Market price for '{name}' is stale "
                                f"({age_days:.0f} days old)"
                            ),
                            material=name,
                            ref_layer="market",
                            details={"age_days": round(age_days, 1)},
                        )
                    )

        checked = {
            "main_entries": len(main_idx),
            "learn_entries": len(learn_idx),
            "market_entries": len(market_idx),
            "materials_checked": len(materials),
            "price_anomalies": sum(
                1 for i in issues if i.type == IssueType.PRICE_ANOMALY
            ),
            "missing_processes": sum(
                1 for i in issues if i.type == IssueType.MISSING_PROCESS
            ),
            "stale_prices": sum(
                1 for i in issues if i.type == IssueType.STALE_PRICE
            ),
            "missing_baseline": sum(
                1 for i in issues if i.type == IssueType.MISSING_BASELINE
            ),
        }
        return ReviewReport(
            issues=issues,
            checked=checked,
            status="issues_found" if issues else "clean",
        )

    # ------------------------------------------------------------------
    # Mode 4 — user cost/quote table validation
    # ------------------------------------------------------------------

    def check_cost_table(
        self,
        cost_table: Any,
        main_data: dict[str, Any] | None = None,
        market_data: dict[str, Any] | None = None,
        learn_data: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> ReviewReport:
        """Validate a user cost/quote table (Mode 4).

        For each row flags:
        - abnormal high/low prices vs main baseline (price_deviation)
        - prices outside the market reference band (market_band)
        - rows with no baseline or market reference (missing_baseline)
        - rows missing processes that learn rules cover (missing_process)

        Args:
            cost_table: User cost table — list of row dicts or dict of
                {material_name: {unit_price, ...}}
            main_data: Official baseline snapshot
            market_data: Market price snapshot
            learn_data: Learned reference snapshot
            now: Reference time for staleness (default: datetime.now(UTC))

        Returns:
            ReviewReport with adjustment suggestions
        """
        now = now or datetime.now(timezone.utc)
        main_idx = self._index_entries(main_data)
        market_idx = self._index_entries(market_data)
        learn_idx = self._index_entries(learn_data)

        rows = self._parse_cost_table(cost_table)
        if not rows:
            raise ReviewError("Cost table is empty or has no readable rows")

        issues: list[ReviewIssue] = []

        for row in rows:
            name = self._row_name(row)
            price = self._row_price(row)
            if not name or price is None:
                continue

            base_entry = main_idx.get(name)
            market_entry = market_idx.get(name)
            learn_entry = learn_idx.get(name)

            # 1. Deviation vs official baseline
            if base_entry is not None:
                base_price = self._extract_price(base_entry)
                if base_price is not None:
                    ratio = self._deviation_ratio(price, base_price)
                    if ratio > self.thresholds.price_deviation:
                        direction = "above" if price > base_price else "below"
                        severity = (
                            IssueSeverity.HIGH
                            if ratio > self.thresholds.baseline_conflict
                            else IssueSeverity.MEDIUM
                        )
                        issues.append(
                            ReviewIssue(
                                type=IssueType.PRICE_ANOMALY,
                                severity=severity,
                                message=(
                                    f"User price for '{name}' is {ratio:.0%} "
                                    f"{direction} baseline "
                                    f"({price:.2f} vs {base_price:.2f})"
                                ),
                                material=name,
                                ref_layer="main",
                                ref_value=base_price,
                                current_value=price,
                                deviation=ratio,
                                details={"direction": direction},
                            )
                        )
            # 2. Outside market reference band
            elif market_entry is not None:
                market_price = self._extract_price(market_entry)
                if market_price is not None:
                    lo = market_price * (1 - self.thresholds.market_band)
                    hi = market_price * (1 + self.thresholds.market_band)
                    if price < lo or price > hi:
                        issues.append(
                            ReviewIssue(
                                type=IssueType.PRICE_ANOMALY,
                                severity=IssueSeverity.MEDIUM,
                                message=(
                                    f"User price for '{name}' ({price:.2f}) "
                                    f"outside market band "
                                    f"[{lo:.2f}, {hi:.2f}] (ref {market_price:.2f})"
                                ),
                                material=name,
                                ref_layer="market",
                                ref_value=market_price,
                                current_value=price,
                                deviation=self._deviation_ratio(price, market_price),
                                details={"band": [round(lo, 2), round(hi, 2)]},
                            )
                        )
                    else:
                        issues.append(
                            ReviewIssue(
                                type=IssueType.MISSING_BASELINE,
                                severity=IssueSeverity.LOW,
                                message=(
                                    f"No official baseline for '{name}' — "
                                    f"validated against market reference only"
                                ),
                                material=name,
                                ref_layer="market",
                                current_value=price,
                                details={"in_learn": learn_entry is not None},
                            )
                        )
            # 3. No reference at all
            else:
                issues.append(
                    ReviewIssue(
                        type=IssueType.MISSING_BASELINE,
                        severity=IssueSeverity.MEDIUM,
                        message=(
                            f"No baseline or market reference for '{name}' — "
                            f"price cannot be validated"
                        ),
                        material=name,
                        ref_layer="user",
                        current_value=price,
                        details={"in_learn": learn_entry is not None},
                    )
                )

            # 4. Missing process vs learned rules
            if learn_entry is not None and self._has_process_rules(learn_entry):
                if not self._row_has_process(row):
                    issues.append(
                        ReviewIssue(
                            type=IssueType.MISSING_PROCESS,
                            severity=IssueSeverity.LOW,
                            message=(
                                f"Learn rules cover process for '{name}' "
                                f"but the row has no process info"
                            ),
                            material=name,
                            ref_layer="learn",
                            current_value=price,
                        )
                    )

        checked = {
            "rows_checked": len(rows),
            "price_anomalies": sum(
                1 for i in issues if i.type == IssueType.PRICE_ANOMALY
            ),
            "missing_processes": sum(
                1 for i in issues if i.type == IssueType.MISSING_PROCESS
            ),
            "missing_baseline": sum(
                1 for i in issues if i.type == IssueType.MISSING_BASELINE
            ),
        }
        return ReviewReport(
            issues=issues,
            checked=checked,
            status="issues_found" if issues else "clean",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _index_entries(
        self, data: dict[str, Any] | list[Any] | None
    ) -> dict[str, dict[str, Any]]:
        """Normalize layer data into {name: entry} index.

        Accepts:
        - {name: {...entry}} (primary format, used by CostingEngine)
        - {materials: [...]} / {rules: [...]} / {process_cost: [...]}
        - [entry, ...]
        """
        index: dict[str, dict[str, Any]] = {}
        if not data:
            return index

        if isinstance(data, dict):
            # Container keys with list payloads
            for key in ("materials", "rules", "items", "entries"):
                payload = data.get(key)
                if isinstance(payload, list):
                    for item in payload:
                        self._index_entry(item, index)
                    return index
            # Direct {name: entry} mapping
            for name, entry in data.items():
                self._index_entry(entry, index, default_name=name)
        elif isinstance(data, list):
            for item in data:
                self._index_entry(item, index)

        return index

    def _index_entry(
        self,
        entry: Any,
        index: dict[str, dict[str, Any]],
        default_name: str = "",
    ) -> None:
        """Add a single entry to the index (best-effort, never raises)."""
        if not isinstance(entry, dict):
            return
        name = (
            entry.get("name")
            or entry.get("material")
            or entry.get("material_name")
            or default_name
        )
        if not name:
            return
        # Merge spec so same-name different-spec entries don't clobber
        existing = index.get(name)
        if existing is None:
            index[name] = dict(entry)
        else:
            existing.setdefault("spec", entry.get("spec", ""))
            for k, v in entry.items():
                existing.setdefault(k, v)

    def _extract_price(self, entry: dict[str, Any]) -> float | None:
        """Extract unit price from an entry, or None."""
        price = (
            entry.get("unit_price")
            or entry.get("price")
            or entry.get("cost")
        )
        if price is None:
            return None
        try:
            return float(price)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _deviation_ratio(value: float, reference: float) -> float:
        """Relative deviation |value - reference| / reference."""
        if not reference:
            return float("inf") if value else 0.0
        return abs(value - reference) / abs(reference)

    def _has_process(self, entry: dict[str, Any]) -> bool:
        """Whether an entry carries process information."""
        return bool(
            entry.get("process")
            or entry.get("processes")
            or entry.get("process_cost")
        )

    def _has_process_rules(self, entry: dict[str, Any]) -> bool:
        """Whether a learn entry carries process-cost rules."""
        return bool(
            entry.get("process_cost")
            or entry.get("processes")
            or entry.get("process")
        )

    def _entry_age_days(
        self, entry: dict[str, Any], now: datetime
    ) -> float | None:
        """Age in days of an entry's timestamp, or None if absent/invalid."""
        raw = entry.get("timestamp") or entry.get("fetched_at") or entry.get("updated_at")
        if not raw:
            return None
        ts = self._parse_timestamp(raw)
        if ts is None:
            return None
        try:
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return (now - ts).total_seconds() / 86400.0
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_timestamp(raw: Any) -> datetime | None:
        """Parse a timestamp (datetime or ISO string)."""
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str):
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                return None
        return None

    def _parse_cost_table(self, cost_table: Any) -> list[dict[str, Any]]:
        """Normalize a user cost table into a list of row dicts."""
        if isinstance(cost_table, dict):
            # {name: {...}} mapping
            rows: list[dict[str, Any]] = []
            for name, entry in cost_table.items():
                if isinstance(entry, dict):
                    row = dict(entry)
                    row.setdefault("material", name)
                    rows.append(row)
                else:
                    rows.append({"material": name, "unit_price": entry})
            return rows
        if isinstance(cost_table, list):
            return [
                row for row in cost_table if isinstance(row, dict)
            ]
        return []

    @staticmethod
    def _row_name(row: dict[str, Any]) -> str:
        """Extract material name from a table row."""
        return (
            row.get("material")
            or row.get("name")
            or row.get("material_name")
            or ""
        )

    @staticmethod
    def _row_price(row: dict[str, Any]) -> float | None:
        """Extract unit price from a table row."""
        price = row.get("unit_price") or row.get("price") or row.get("cost")
        if price is None:
            return None
        try:
            return float(price)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _row_has_process(row: dict[str, Any]) -> bool:
        """Whether a table row carries process information."""
        return bool(
            row.get("process")
            or row.get("processes")
            or row.get("process_cost")
        )
