"""Smoke test: package imports and core functions work."""

from axiara.core.costing import CostingEngine, MaterialInput, UnitConverter
from axiara.core.quote import QuoteGenerator, Quotation
from axiara.core.storage.permissions import DataLayer


def test_unit_converter() -> None:
    """Unit conversion works."""
    result = UnitConverter.convert(1000.0, "g", "kg")
    assert result == 1.0


def test_costing_engine() -> None:
    """Costing engine calculates material cost."""
    engine = CostingEngine()
    materials = [
        MaterialInput(name="steel", quantity=10.0, unit="kg", unit_price=5.0),
    ]
    result = engine.calculate_total_cost(materials=materials)
    assert result.breakdown.material == 50.0
    assert result.breakdown.total == 50.0


def test_quote_generator() -> None:
    """Quote generator creates quotation."""
    generator = QuoteGenerator()
    materials = [
        MaterialInput(name="steel", quantity=10.0, unit="kg", unit_price=5.0),
    ]
    quotation = generator.generate_quotation(materials=materials)
    assert quotation.cost == 50.0
    assert quotation.price > 0.0
    assert isinstance(quotation, Quotation)


def test_data_layer_enum() -> None:
    """Data layer enum works."""
    assert DataLayer.MAIN.value == "main"
    assert DataLayer.MARKET.value == "market"