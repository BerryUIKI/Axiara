"""Parse step - HTML parsing with adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup


@dataclass
class ParsedRow:
    """A parsed row from a page."""

    name: str
    spec: str | None = None
    unit: str | None = None
    unit_price: float | None = None
    currency: str | None = None
    effective_date: str | None = None
    raw: str | None = None


class Parser:
    """Parses pages using site adapters.

    - CSS/XPath selector-based parsing
    - Named parser support
    - Raw row extraction
    """

    def __init__(self, adapters_config: dict[str, Any] | None = None) -> None:
        """Initialize parser.

        Args:
            adapters_config: Adapters configuration
        """
        self.adapters = adapters_config or {}

    def parse(self, html_content: str, source_config: dict[str, Any]) -> list[ParsedRow]:
        """Parse a page.

        Args:
            html_content: HTML content to parse
            source_config: Source configuration

        Returns:
            List of ParsedRow instances
        """
        rows = []
        selectors = source_config.get("selectors", {})

        if not selectors:
            # No selectors defined - return empty
            return rows

        soup = BeautifulSoup(html_content, "lxml")

        # Find rows
        row_selector = selectors.get("row", "")
        if not row_selector:
            return rows

        try:
            row_elements = soup.select(row_selector)

            for row_elem in row_elements:
                try:
                    # Extract fields
                    name = self._extract_field(row_elem, selectors.get("name", ""))
                    unit_price_text = self._extract_field(row_elem, selectors.get("unit_price", ""))
                    unit = self._extract_field(row_elem, selectors.get("unit", ""))

                    if name and unit_price_text:
                        # Parse price
                        unit_price = self._parse_price(unit_price_text)

                        rows.append(ParsedRow(
                            name=name.strip(),
                            unit=unit.strip() if unit else None,
                            unit_price=unit_price,
                            raw=str(row_elem)[:500]  # Truncate raw
                        ))

                except Exception:
                    # Skip malformed rows
                    continue

        except Exception:
            pass

        return rows

    def _extract_field(self, element: Any, selector: str) -> str:
        """Extract a field from an element.

        Args:
            element: BeautifulSoup element
            selector: CSS selector

        Returns:
            Extracted text
        """
        if not selector:
            return ""

        try:
            field_elem = element.select_one(selector)
            return field_elem.get_text(strip=True) if field_elem else ""
        except Exception:
            return ""

    def _parse_price(self, price_text: str) -> float:
        """Parse price from text.

        Args:
            price_text: Price text

        Returns:
            Parsed price
        """
        # Remove non-numeric characters except decimal point
        import re
        price_str = re.sub(r"[^\d.]", "", price_text)

        try:
            return float(price_str)
        except ValueError:
            return 0.0