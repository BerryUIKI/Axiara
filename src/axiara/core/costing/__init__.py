"""Multi-dimensional costing engine.

Implements the costing formula: total cost = material + labor + loss + processing.
Reads from main/learn/market layers via the storage PermissionManager (read-only).
"""

from __future__ import annotations

from axiara.core.costing.engine import (
    CostBreakdown,
    CostingEngine,
    CostingError,
    CostResult,
    MaterialInput,
    ProcessInput,
    UnitConversionError,
    UnitConverter,
)

__all__ = [
    "CostBreakdown",
    "CostingEngine",
    "CostingError",
    "CostResult",
    "MaterialInput",
    "ProcessInput",
    "UnitConversionError",
    "UnitConverter",
]