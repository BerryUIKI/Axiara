"""Multi-dimensional costing engine.

Implements the costing formula: total cost = material + labor + loss + processing.
Reads from main/learn/market layers via the storage PermissionManager (read-only).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from axiara.core.storage.permissions import DataLayer, PermissionManager


class CostingError(Exception):
    """Raised when costing operations fail."""

    pass


class UnitConversionError(CostingError):
    """Raised when unit conversion fails."""

    pass


@dataclass
class CostBreakdown:
    """Detailed breakdown of a cost calculation."""

    material: float = 0.0
    labor: float = 0.0
    loss: float = 0.0
    processing: float = 0.0

    @property
    def total(self) -> float:
        """Total cost = material + labor + loss + processing."""
        return self.material + self.labor + self.loss + self.processing


@dataclass
class CostResult:
    """Result of a cost calculation with metadata."""

    breakdown: CostBreakdown
    confidence: float = 1.0  # 0.0 to 1.0
    sources: dict[str, list[str]] = field(default_factory=dict)  # {layer: [refs]}
    warnings: list[str] = field(default_factory=list)


@dataclass
class MaterialInput:
    """Input material specification."""

    name: str
    spec: str = ""
    quantity: float = 1.0
    unit: str = "kg"
    unit_price: float | None = None  # Optional override


@dataclass
class ProcessInput:
    """Processing step specification."""

    name: str  # e.g., "cutting", "welding", "plating"
    quantity: float = 1.0
    unit: str = "piece"


class UnitConverter:
    """Unit conversion using the shared normalization dictionary.

    Supports weight, length, area, volume conversions.
    Never guesses silently - unknown units raise UnitConversionError.
    """

    # Weight conversions (to kg)
    WEIGHT_TO_KG: dict[str, float] = {
        "kg": 1.0,
        "kilogram": 1.0,
        "g": 0.001,
        "gram": 0.001,
        "ton": 1000.0,
        "tonne": 1000.0,
        "t": 1000.0,
        "lb": 0.453592,
        "pound": 0.453592,
        "oz": 0.0283495,
        "ounce": 0.0283495,
    }

    # Length conversions (to m)
    LENGTH_TO_M: dict[str, float] = {
        "m": 1.0,
        "meter": 1.0,
        "cm": 0.01,
        "centimeter": 0.01,
        "mm": 0.001,
        "millimeter": 0.001,
        "ft": 0.3048,
        "foot": 0.3048,
        "in": 0.0254,
        "inch": 0.0254,
    }

    # Area conversions (to m²)
    AREA_TO_M2: dict[str, float] = {
        "m2": 1.0,
        "m²": 1.0,
        "sqm": 1.0,
        "cm2": 0.0001,
        "cm²": 0.0001,
        "ft2": 0.092903,
        "ft²": 0.092903,
    }

    # Volume conversions (to m³)
    VOLUME_TO_M3: dict[str, float] = {
        "m3": 1.0,
        "m³": 1.0,
        "l": 0.001,
        "liter": 0.001,
        "ml": 0.000001,
        "gallon": 0.00378541,
    }

    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str) -> float:
        """Convert a value from one unit to another.

        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Converted value

        Raises:
            UnitConversionError: If units are incompatible or unknown
        """
        from_unit_lower = from_unit.lower().strip()
        to_unit_lower = to_unit.lower().strip()

        # Same unit - no conversion needed
        if from_unit_lower == to_unit_lower:
            return value

        # Try weight conversion
        if from_unit_lower in cls.WEIGHT_TO_KG and to_unit_lower in cls.WEIGHT_TO_KG:
            kg_value = value * cls.WEIGHT_TO_KG[from_unit_lower]
            return kg_value / cls.WEIGHT_TO_KG[to_unit_lower]

        # Try length conversion
        if from_unit_lower in cls.LENGTH_TO_M and to_unit_lower in cls.LENGTH_TO_M:
            m_value = value * cls.LENGTH_TO_M[from_unit_lower]
            return m_value / cls.LENGTH_TO_M[to_unit_lower]

        # Try area conversion
        if from_unit_lower in cls.AREA_TO_M2 and to_unit_lower in cls.AREA_TO_M2:
            m2_value = value * cls.AREA_TO_M2[from_unit_lower]
            return m2_value / cls.AREA_TO_M2[to_unit_lower]

        # Try volume conversion
        if from_unit_lower in cls.VOLUME_TO_M3 and to_unit_lower in cls.VOLUME_TO_M3:
            m3_value = value * cls.VOLUME_TO_M3[from_unit_lower]
            return m3_value / cls.VOLUME_TO_M3[to_unit_lower]

        # Unknown or incompatible units
        raise UnitConversionError(
            f"Cannot convert from '{from_unit}' to '{to_unit}': "
            f"unknown or incompatible units"
        )

    @classmethod
    def get_unit_category(cls, unit: str) -> str | None:
        """Get the category of a unit.

        Args:
            unit: Unit to categorize

        Returns:
            Category name ('weight', 'length', 'area', 'volume') or None
        """
        unit_lower = unit.lower().strip()

        if unit_lower in cls.WEIGHT_TO_KG:
            return "weight"
        elif unit_lower in cls.LENGTH_TO_M:
            return "length"
        elif unit_lower in cls.AREA_TO_M2:
            return "area"
        elif unit_lower in cls.VOLUME_TO_M3:
            return "volume"

        return None


class CostingEngine:
    """Multi-dimensional costing engine.

    Computes costs from material + labor + loss + processing.
    Reads from data layers via the storage PermissionManager (read-only).
    """

    def __init__(
        self,
        data_root: Path | None = None,
        permission_manager: PermissionManager | None = None,
    ) -> None:
        """Initialize the costing engine.

        Args:
            data_root: Root directory for data (default: data/)
            permission_manager: Permission manager instance
        """
        self.data_root = data_root or Path("data")
        self.permission_manager = permission_manager or PermissionManager()

    def calculate_material_cost(
        self,
        material: MaterialInput,
        baseline_data: dict[str, Any] | None = None,
        learn_data: dict[str, Any] | None = None,
        market_data: dict[str, Any] | None = None,
    ) -> CostResult:
        """Calculate material cost with breakdown.

        Args:
            material: Material specification
            baseline_data: Official baseline price data (from main/)
            learn_data: Learned reference data (from learn/)
            market_data: Market price data (from market/)

        Returns:
            CostResult with breakdown and metadata
        """
        breakdown = CostBreakdown()
        sources: dict[str, list[str]] = {}
        warnings: list[str] = []
        confidence = 1.0

        # Use override price if provided
        if material.unit_price is not None:
            breakdown.material = material.unit_price * material.quantity
            sources["override"] = [f"{material.name}: {material.unit_price}/unit"]
            return CostResult(
                breakdown=breakdown,
                confidence=confidence,
                sources=sources,
                warnings=warnings,
            )

        # Try baseline first (highest priority)
        if baseline_data:
            price_entry = self._find_price_entry(material.name, material.spec, baseline_data)
            if price_entry:
                unit_price, unit = self._extract_price_info(price_entry)
                if unit_price is not None:
                    # Convert units if needed
                    try:
                        converted_qty = UnitConverter.convert(
                            material.quantity, material.unit, unit
                        )
                        breakdown.material = unit_price * converted_qty
                        sources["main"] = [f"{material.name}: {unit_price}/{unit}"]
                    except UnitConversionError as e:
                        warnings.append(f"Unit conversion failed: {e}")
                        confidence *= 0.8

        # Fallback to learn data
        if breakdown.material == 0.0 and learn_data:
            price_entry = self._find_price_entry(material.name, material.spec, learn_data)
            if price_entry:
                unit_price, unit = self._extract_price_info(price_entry)
                if unit_price is not None:
                    try:
                        converted_qty = UnitConverter.convert(
                            material.quantity, material.unit, unit
                        )
                        breakdown.material = unit_price * converted_qty
                        sources["learn"] = [f"{material.name}: {unit_price}/{unit}"]
                        confidence *= 0.9  # Lower confidence for learned data
                    except UnitConversionError as e:
                        warnings.append(f"Unit conversion failed: {e}")
                        confidence *= 0.8

        # Use market data as reference (lower weight)
        if market_data:
            price_entry = self._find_price_entry(material.name, material.spec, market_data)
            if price_entry:
                sources["market"] = [f"{material.name}: reference price available"]

        # No data found
        if breakdown.material == 0.0:
            warnings.append(f"No price data found for {material.name}")
            confidence = 0.0

        return CostResult(
            breakdown=breakdown,
            confidence=confidence,
            sources=sources,
            warnings=warnings,
        )

    def calculate_process_cost(
        self,
        process: ProcessInput,
        learn_rules: dict[str, Any] | None = None,
    ) -> CostResult:
        """Calculate processing cost.

        Args:
            process: Process specification
            learn_rules: Learned process-cost rules (from learn/rules/)

        Returns:
            CostResult with processing cost breakdown
        """
        breakdown = CostBreakdown()
        sources: dict[str, list[str]] = {}
        warnings: list[str] = []
        confidence = 1.0

        if not learn_rules:
            warnings.append("No process-cost rules available")
            return CostResult(
                breakdown=breakdown,
                confidence=0.0,
                sources=sources,
                warnings=warnings,
            )

        # Find process-cost rule
        rule = self._find_process_rule(process.name, learn_rules)
        if rule:
            unit_fee = rule.get("unit_fee", 0.0)
            loss_rate = rule.get("loss_rate", 0.0)
            yield_rate = rule.get("yield", 1.0)

            # Calculate processing cost
            breakdown.processing = unit_fee * process.quantity

            # Apply loss rate (adds to cost)
            if loss_rate > 0:
                breakdown.loss = breakdown.processing * loss_rate

            sources["learn"] = [f"{process.name}: {unit_fee}/unit (loss: {loss_rate:.1%})"]

        else:
            warnings.append(f"No process-cost rule for {process.name}")
            confidence = 0.0

        return CostResult(
            breakdown=breakdown,
            confidence=confidence,
            sources=sources,
            warnings=warnings,
        )

    def calculate_total_cost(
        self,
        materials: list[MaterialInput],
        processes: list[ProcessInput] | None = None,
        baseline_data: dict[str, Any] | None = None,
        learn_data: dict[str, Any] | None = None,
        market_data: dict[str, Any] | None = None,
        learn_rules: dict[str, Any] | None = None,
    ) -> CostResult:
        """Calculate total cost from materials and processes.

        Args:
            materials: List of materials
            processes: List of processing steps
            baseline_data: Official baseline data
            learn_data: Learned reference data
            market_data: Market price data
            learn_rules: Learned process-cost rules

        Returns:
            Aggregated CostResult
        """
        total_breakdown = CostBreakdown()
        all_sources: dict[str, list[str]] = {}
        all_warnings: list[str] = []
        min_confidence = 1.0

        # Calculate material costs
        for material in materials:
            result = self.calculate_material_cost(
                material, baseline_data, learn_data, market_data
            )
            total_breakdown.material += result.breakdown.material
            self._merge_sources(all_sources, result.sources)
            all_warnings.extend(result.warnings)
            min_confidence = min(min_confidence, result.confidence)

        # Calculate process costs
        if processes:
            for process in processes:
                result = self.calculate_process_cost(process, learn_rules)
                total_breakdown.processing += result.breakdown.processing
                total_breakdown.loss += result.breakdown.loss
                self._merge_sources(all_sources, result.sources)
                all_warnings.extend(result.warnings)
                min_confidence = min(min_confidence, result.confidence)

        return CostResult(
            breakdown=total_breakdown,
            confidence=min_confidence,
            sources=all_sources,
            warnings=all_warnings,
        )

    def _find_price_entry(
        self, name: str, spec: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Find a price entry matching name and spec.

        Args:
            name: Material name
            spec: Material specification
            data: Price data dictionary

        Returns:
            Matching price entry or None
        """
        # Try exact match first
        if name in data:
            entry = data[name]
            if isinstance(entry, dict):
                if not spec or entry.get("spec", "") == spec:
                    return entry

        # Try partial match
        for key, entry in data.items():
            if isinstance(entry, dict):
                if key == name or entry.get("name") == name:
                    if not spec or entry.get("spec", "") == spec:
                        return entry

        return None

    def _extract_price_info(
        self, entry: dict[str, Any]
    ) -> tuple[float | None, str]:
        """Extract unit price and unit from a price entry.

        Args:
            entry: Price entry dictionary

        Returns:
            Tuple of (unit_price, unit) or (None, "")
        """
        unit_price = entry.get("unit_price") or entry.get("price")
        unit = entry.get("unit", "kg")

        if unit_price is not None:
            return float(unit_price), unit

        return None, ""

    def _find_process_rule(
        self, process_name: str, rules: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Find a process-cost rule.

        Args:
            process_name: Process name
            rules: Process-cost rules dictionary

        Returns:
            Matching rule or None
        """
        # Try direct match
        if process_name in rules:
            return rules[process_name]

        # Try in process_cost section
        if "process_cost" in rules:
            for rule in rules["process_cost"]:
                if isinstance(rule, dict) and rule.get("process") == process_name:
                    return rule

        return None

    def _merge_sources(
        self, target: dict[str, list[str]], source: dict[str, list[str]]
    ) -> None:
        """Merge source references into target.

        Args:
            target: Target dictionary
            source: Source dictionary
        """
        for key, refs in source.items():
            if key not in target:
                target[key] = []
            target[key].extend(refs)