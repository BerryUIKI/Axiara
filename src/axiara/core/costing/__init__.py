"""Multi-dimensional costing engine (scaffold)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostItem:
    """A single cost component in a quote."""

    name: str
    unit_cost: float
    quantity: float = 1.0

    @property
    def subtotal(self) -> float:
        return self.unit_cost * self.quantity


def total_cost(items: list[CostItem]) -> float:
    """Sum all cost items."""
    return sum(item.subtotal for item in items)
