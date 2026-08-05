"""Quotation generation (scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field

from axiara.core.costing import CostItem, total_cost


@dataclass
class QuoteConstraints:
    """User constraints for smart quotation."""

    min_margin: float | None = None  # minimum guaranteed margin (%)
    price_cap: float | None = None  # quote cap threshold
    market_tolerance: float | None = None  # market price tolerance range (%)


@dataclass
class Quotation:
    """A generated quotation."""

    items: list[CostItem] = field(default_factory=list)
    constraints: QuoteConstraints = field(default_factory=QuoteConstraints)
    price: float = 0.0

    @property
    def cost(self) -> float:
        return total_cost(self.items)


def generate_quotation(
    items: list[CostItem],
    constraints: QuoteConstraints | None = None,
) -> Quotation:
    """Generate a quotation from cost items (deterministic scaffold)."""
    constraints = constraints or QuoteConstraints()
    cost = total_cost(items)
    price = cost  # scaffold: no margin applied yet
    return Quotation(items=items, constraints=constraints, price=price)
