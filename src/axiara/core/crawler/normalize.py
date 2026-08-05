"""Normalize step - alias mapping and currency conversion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from axiara.core.crawler.parse import ParsedRow


@dataclass
class NormalizedRow:
    """A normalized price row."""

    name: str
    spec: str | None
    unit: str
    unit_price: float
    currency: str
    effective_date: date
    note: str | None
    source: str
    url: str
    fetched_at: datetime
    confidence: Literal["high", "medium", "low"]
    raw: str | None


class Normalizer:
    """Normalizes parsed rows.

    - Alias → canonical name mapping
    - Currency normalization
    - Confidence assignment
    - Unknown alias flagging
    """

    def __init__(self, normalization_config: dict[str, Any] | None = None) -> None:
        """Initialize normalizer.

        Args:
            normalization_config: Normalization dictionary
        """
        self.config = normalization_config or {}

    def normalize(
        self,
        parsed_row: ParsedRow,
        source: str,
        url: str,
        confidence: Literal["high", "medium", "low"] = "medium"
    ) -> NormalizedRow:
        """Normalize a parsed row.

        Args:
            parsed_row: Parsed row
            source: Source ID
            url: Source URL
            confidence: Confidence level

        Returns:
            NormalizedRow instance
        """
        # Normalize name
        name = self._normalize_name(parsed_row.name)

        # Normalize unit
        unit = self._normalize_unit(parsed_row.unit) if parsed_row.unit else "unknown"

        # Normalize currency (default to CNY for CN sources)
        currency = "CNY" if source.endswith("-cn") or "mofcom" in source else "USD"

        # Parse effective date
        effective_date = self._parse_date(parsed_row.effective_date)

        return NormalizedRow(
            name=name,
            spec=parsed_row.spec,
            unit=unit,
            unit_price=parsed_row.unit_price or 0.0,
            currency=currency,
            effective_date=effective_date,
            note=None,
            source=source,
            url=url,
            fetched_at=datetime.utcnow(),
            confidence=confidence,
            raw=parsed_row.raw
        )

    def _normalize_name(self, name: str) -> str:
        """Normalize a commodity name.

        Args:
            name: Raw name

        Returns:
            Canonical name
        """
        commodities = self.config.get("commodities", {})

        # Check each commodity for matching alias
        for canonical, config in commodities.items():
            aliases = config.get("aliases", [])
            if name.lower() in [a.lower() for a in aliases]:
                return canonical

        # Unknown - keep raw
        return name.lower().replace(" ", "-")

    def _normalize_unit(self, unit: str) -> str:
        """Normalize a unit.

        Args:
            unit: Raw unit

        Returns:
            Canonical unit
        """
        units = self.config.get("units", {})

        # Check each unit for matching alias
        for canonical, config in units.items():
            aliases = config.get("aliases", [])
            if unit.lower() in [a.lower() for a in aliases]:
                return canonical

        # Unknown - keep raw
        return unit.lower()

    def _parse_date(self, date_str: str | None) -> date:
        """Parse a date string.

        Args:
            date_str: Date string

        Returns:
            Parsed date (defaults to today)
        """
        if not date_str:
            return date.today()

        # Try common formats
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return date.today()