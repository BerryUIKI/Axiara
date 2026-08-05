"""Unit tests for the costing engine.

Tests cover:
- Material + process cost composition
- Loss rate / yield application
- Unit conversion
- Missing data handling
"""

from __future__ import annotations

import pytest

from axiara.core.costing import (
    CostBreakdown,
    CostingEngine,
    CostResult,
    MaterialInput,
    ProcessInput,
    UnitConversionError,
    UnitConverter,
)


class TestUnitConverter:
    """Tests for unit conversion."""

    def test_convert_same_unit(self) -> None:
        """Converting to the same unit returns same value."""
        result = UnitConverter.convert(10.0, "kg", "kg")
        assert result == 10.0

    def test_convert_weight_kg_to_g(self) -> None:
        """Convert kg to g."""
        result = UnitConverter.convert(1.0, "kg", "g")
        assert result == 1000.0

    def test_convert_weight_g_to_kg(self) -> None:
        """Convert g to kg."""
        result = UnitConverter.convert(500.0, "g", "kg")
        assert result == 0.5

    def test_convert_weight_ton_to_kg(self) -> None:
        """Convert ton to kg."""
        result = UnitConverter.convert(2.0, "ton", "kg")
        assert result == 2000.0

    def test_convert_weight_lb_to_kg(self) -> None:
        """Convert pounds to kg."""
        result = UnitConverter.convert(1.0, "lb", "kg")
        assert abs(result - 0.453592) < 0.0001

    def test_convert_length_m_to_cm(self) -> None:
        """Convert meters to centimeters."""
        result = UnitConverter.convert(1.0, "m", "cm")
        assert result == 100.0

    def test_convert_length_ft_to_m(self) -> None:
        """Convert feet to meters."""
        result = UnitConverter.convert(10.0, "ft", "m")
        assert abs(result - 3.048) < 0.001

    def test_convert_incompatible_units_raises_error(self) -> None:
        """Converting between incompatible units raises error."""
        with pytest.raises(UnitConversionError) as exc_info:
            UnitConverter.convert(10.0, "kg", "m")

        assert "Cannot convert" in str(exc_info.value)

    def test_convert_unknown_unit_raises_error(self) -> None:
        """Converting unknown unit raises error."""
        with pytest.raises(UnitConversionError) as exc_info:
            UnitConverter.convert(10.0, "unknown", "kg")

        assert "unknown" in str(exc_info.value)

    def test_get_unit_category_weight(self) -> None:
        """Get unit category for weight."""
        assert UnitConverter.get_unit_category("kg") == "weight"
        assert UnitConverter.get_unit_category("g") == "weight"
        assert UnitConverter.get_unit_category("ton") == "weight"

    def test_get_unit_category_length(self) -> None:
        """Get unit category for length."""
        assert UnitConverter.get_unit_category("m") == "length"
        assert UnitConverter.get_unit_category("cm") == "length"

    def test_get_unit_category_unknown(self) -> None:
        """Get unit category for unknown unit."""
        assert UnitConverter.get_unit_category("unknown") is None


class TestCostBreakdown:
    """Tests for cost breakdown."""

    def test_total_sum(self) -> None:
        """Total cost is sum of components."""
        breakdown = CostBreakdown(
            material=100.0,
            labor=20.0,
            loss=5.0,
            processing=15.0,
        )
        assert breakdown.total == 140.0

    def test_default_values(self) -> None:
        """Default values are zero."""
        breakdown = CostBreakdown()
        assert breakdown.material == 0.0
        assert breakdown.labor == 0.0
        assert breakdown.loss == 0.0
        assert breakdown.processing == 0.0
        assert breakdown.total == 0.0


class TestMaterialInput:
    """Tests for material input."""

    def test_material_creation(self) -> None:
        """Create material input."""
        material = MaterialInput(
            name="copper-wire",
            spec="2.5mm",
            quantity=100.0,
            unit="kg",
        )
        assert material.name == "copper-wire"
        assert material.spec == "2.5mm"
        assert material.quantity == 100.0
        assert material.unit == "kg"
        assert material.unit_price is None

    def test_material_with_override_price(self) -> None:
        """Material with price override."""
        material = MaterialInput(
            name="copper-wire",
            quantity=50.0,
            unit="kg",
            unit_price=75.0,
        )
        assert material.unit_price == 75.0


class TestProcessInput:
    """Tests for process input."""

    def test_process_creation(self) -> None:
        """Create process input."""
        process = ProcessInput(
            name="cutting",
            quantity=10.0,
            unit="piece",
        )
        assert process.name == "cutting"
        assert process.quantity == 10.0
        assert process.unit == "piece"


class TestCostingEngine:
    """Tests for the costing engine."""

    def test_calculate_material_cost_with_override_price(self) -> None:
        """Calculate material cost with price override."""
        engine = CostingEngine()
        material = MaterialInput(
            name="copper-wire",
            quantity=10.0,
            unit="kg",
            unit_price=70.0,
        )

        result = engine.calculate_material_cost(material)

        assert result.breakdown.material == 700.0  # 70 * 10
        assert result.confidence == 1.0
        assert "override" in result.sources

    def test_calculate_material_cost_from_baseline(self) -> None:
        """Calculate material cost from baseline data."""
        engine = CostingEngine()
        material = MaterialInput(
            name="copper-wire",
            quantity=10.0,
            unit="kg",
        )

        baseline_data = {
            "copper-wire": {
                "unit_price": 65.0,
                "unit": "kg",
            }
        }

        result = engine.calculate_material_cost(
            material,
            baseline_data=baseline_data,
        )

        assert result.breakdown.material == 650.0  # 65 * 10
        assert "main" in result.sources

    def test_calculate_material_cost_from_learn(self) -> None:
        """Calculate material cost from learned data."""
        engine = CostingEngine()
        material = MaterialInput(
            name="copper-wire",
            quantity=5.0,
            unit="kg",
        )

        learn_data = {
            "copper-wire": {
                "unit_price": 68.0,
                "unit": "kg",
            }
        }

        result = engine.calculate_material_cost(
            material,
            learn_data=learn_data,
        )

        assert result.breakdown.material == 340.0  # 68 * 5
        assert "learn" in result.sources
        assert result.confidence == 0.9  # Lower confidence for learned data

    def test_calculate_material_cost_with_unit_conversion(self) -> None:
        """Calculate material cost with unit conversion."""
        engine = CostingEngine()
        material = MaterialInput(
            name="copper-wire",
            quantity=500.0,
            unit="g",  # Grams
        )

        baseline_data = {
            "copper-wire": {
                "unit_price": 65.0,
                "unit": "kg",  # Price per kg
            }
        }

        result = engine.calculate_material_cost(
            material,
            baseline_data=baseline_data,
        )

        # 500g = 0.5kg, 65 * 0.5 = 32.5
        assert result.breakdown.material == 32.5

    def test_calculate_material_cost_no_data(self) -> None:
        """Calculate material cost with no data."""
        engine = CostingEngine()
        material = MaterialInput(
            name="unknown-material",
            quantity=10.0,
            unit="kg",
        )

        result = engine.calculate_material_cost(material)

        assert result.breakdown.material == 0.0
        assert result.confidence == 0.0
        assert len(result.warnings) > 0

    def test_calculate_process_cost(self) -> None:
        """Calculate process cost."""
        engine = CostingEngine()
        process = ProcessInput(
            name="cutting",
            quantity=10.0,
            unit="piece",
        )

        learn_rules = {
            "process_cost": [
                {
                    "process": "cutting",
                    "unit_fee": 5.0,
                    "loss_rate": 0.02,
                    "yield": 0.98,
                }
            ]
        }

        result = engine.calculate_process_cost(process, learn_rules)

        # Processing: 5 * 10 = 50
        # Loss: 50 * 0.02 = 1
        assert result.breakdown.processing == 50.0
        assert result.breakdown.loss == 1.0
        assert "learn" in result.sources

    def test_calculate_process_cost_no_rules(self) -> None:
        """Calculate process cost without rules."""
        engine = CostingEngine()
        process = ProcessInput(
            name="cutting",
            quantity=10.0,
            unit="piece",
        )

        result = engine.calculate_process_cost(process)

        assert result.breakdown.processing == 0.0
        assert result.confidence == 0.0
        assert len(result.warnings) > 0

    def test_calculate_total_cost(self) -> None:
        """Calculate total cost from materials and processes."""
        engine = CostingEngine()

        materials = [
            MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            MaterialInput(name="aluminum", quantity=5.0, unit="kg", unit_price=20.0),
        ]

        processes = [
            ProcessInput(name="cutting", quantity=10.0),
        ]

        learn_rules = {
            "process_cost": [
                {
                    "process": "cutting",
                    "unit_fee": 5.0,
                    "loss_rate": 0.02,
                }
            ]
        }

        result = engine.calculate_total_cost(
            materials=materials,
            processes=processes,
            learn_rules=learn_rules,
        )

        # Materials: (70 * 10) + (20 * 5) = 700 + 100 = 800
        # Processing: 5 * 10 = 50
        # Loss: 50 * 0.02 = 1
        # Total: 800 + 50 + 1 = 851
        assert result.breakdown.material == 800.0
        assert result.breakdown.processing == 50.0
        assert result.breakdown.loss == 1.0
        assert result.breakdown.total == 851.0

    def test_calculate_total_cost_empty_inputs(self) -> None:
        """Calculate total cost with empty inputs."""
        engine = CostingEngine()

        result = engine.calculate_total_cost(materials=[])

        assert result.breakdown.total == 0.0
        assert result.confidence == 1.0  # Empty inputs are valid