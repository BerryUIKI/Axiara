"""Unit tests for the quotation generator.

Tests cover:
- BOM to quotation
- Three-tier defaults when no constraints
- Constraint negotiation
- Template adaptation
- Approval event emission for learning
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from axiara.core.costing import MaterialInput, ProcessInput
from axiara.core.quote import (
    LearningEvent,
    PricingTier,
    Quotation,
    QuoteConstraints,
    QuoteGenerator,
    TierPricing,
)


class TestQuoteConstraints:
    """Tests for quote constraints."""

    def test_constraints_creation(self) -> None:
        """Create quote constraints."""
        constraints = QuoteConstraints(
            min_margin=10.0,
            max_margin=30.0,
            price_cap=1000.0,
            currency="CNY",
        )
        assert constraints.min_margin == 10.0
        assert constraints.max_margin == 30.0
        assert constraints.price_cap == 1000.0
        assert constraints.currency == "CNY"

    def test_constraints_defaults(self) -> None:
        """Default constraints."""
        constraints = QuoteConstraints()
        assert constraints.min_margin is None
        assert constraints.max_margin is None
        assert constraints.price_cap is None
        assert constraints.currency == "CNY"


class TestTierPricing:
    """Tests for tier pricing."""

    def test_tier_pricing_creation(self) -> None:
        """Create tier pricing."""
        pricing = TierPricing(
            low=100.0,
            mid=115.0,
            high=125.0,
            low_margin=5.0,
            mid_margin=15.0,
            high_margin=25.0,
        )
        assert pricing.low == 100.0
        assert pricing.mid == 115.0
        assert pricing.high == 125.0


class TestQuoteGenerator:
    """Tests for the quote generator."""

    def test_generate_quotation_basic(self) -> None:
        """Generate basic quotation without constraints."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            quotation = generator.generate_quotation(materials=materials)

            assert quotation.cost == 700.0
            assert quotation.price > quotation.cost
            assert quotation.tier == PricingTier.MID  # Default to mid
            assert quotation.confidence == 1.0

    def test_generate_quotation_with_processes(self) -> None:
        """Generate quotation with processes."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
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

            quotation = generator.generate_quotation(
                materials=materials,
                processes=processes,
                learn_rules=learn_rules,
            )

            # Material: 700, Processing: 50, Loss: 1, Total: 751
            assert quotation.cost == 751.0
            assert quotation.price > quotation.cost

    def test_generate_quotation_with_constraints(self) -> None:
        """Generate quotation with user constraints."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            constraints = QuoteConstraints(
                min_margin=20.0,  # Require at least 20% margin
            )

            quotation = generator.generate_quotation(
                materials=materials,
                constraints=constraints,
            )

            # With min_margin=20%, should select mid or high tier
            assert quotation.margin >= 20.0

    def test_generate_quotation_price_cap_constraint(self) -> None:
        """Generate quotation with price cap."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            constraints = QuoteConstraints(
                price_cap=800.0,  # Cap below high tier
            )

            quotation = generator.generate_quotation(
                materials=materials,
                constraints=constraints,
            )

            assert quotation.price <= 800.0

    def test_generate_three_tier_quote(self) -> None:
        """Generate three-tier quotations."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            quotations = generator.generate_three_tier_quote(materials=materials)

            assert PricingTier.LOW in quotations
            assert PricingTier.MID in quotations
            assert PricingTier.HIGH in quotations

            # Verify ordering
            assert quotations[PricingTier.LOW].price < quotations[PricingTier.MID].price
            assert quotations[PricingTier.MID].price < quotations[PricingTier.HIGH].price

    def test_generate_three_tier_quote_with_learned_margins(self) -> None:
        """Generate three-tier with learned margins."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            learn_rules = {
                "pricing_tiers": {
                    "low_margin": 8.0,
                    "mid_margin": 18.0,
                    "high_margin": 28.0,
                }
            }

            quotations = generator.generate_three_tier_quote(
                materials=materials,
                learn_rules=learn_rules,
            )

            # Verify margins are applied
            low_quote = quotations[PricingTier.LOW]
            assert abs(low_quote.margin - 8.0) < 1.0

    def test_emit_learning_event(self) -> None:
        """Emit learning event for approved quotation."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            quotation = generator.generate_quotation(materials=materials)

            event = generator.emit_learning_event(quotation)

            assert isinstance(event, LearningEvent)
            assert event.quotation_id  # Non-empty ID
            assert len(event.material_costs) == 1
            assert event.final_price == quotation.price
            assert event.margin == quotation.margin
            assert event.correction is False

    def test_emit_learning_event_correction(self) -> None:
        """Emit learning event for corrected quotation."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            quotation = generator.generate_quotation(materials=materials)

            event = generator.emit_learning_event(quotation, corrected=True)

            assert event.correction is True

    def test_save_quotation(self) -> None:
        """Save quotation to file."""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator = QuoteGenerator(output_dir=output_dir)

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            quotation = generator.generate_quotation(materials=materials)

            saved_path = generator.save_quotation(quotation)

            assert saved_path.exists()
            assert saved_path.suffix == ".json"

            # Verify content
            import json
            with open(saved_path) as f:
                data = json.load(f)

            assert data["cost"] == 700.0
            assert "price" in data

    def test_save_quotation_custom_path(self) -> None:
        """Save quotation to custom path."""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator = QuoteGenerator(output_dir=output_dir)

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
            ]

            quotation = generator.generate_quotation(materials=materials)

            custom_path = output_dir / "custom-quote.json"
            saved_path = generator.save_quotation(quotation, output_path=custom_path)

            assert saved_path == custom_path
            assert saved_path.exists()

    def test_quotation_items_structure(self) -> None:
        """Verify quotation items structure."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg", unit_price=70.0),
                MaterialInput(name="aluminum", quantity=5.0, unit="kg", unit_price=20.0),
            ]

            quotation = generator.generate_quotation(materials=materials)

            assert len(quotation.items) == 2
            assert all(item["type"] == "material" for item in quotation.items)

    def test_quotation_with_baseline_data(self) -> None:
        """Generate quotation with baseline data."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg"),
            ]

            baseline_data = {
                "copper-wire": {
                    "unit_price": 65.0,
                    "unit": "kg",
                }
            }

            quotation = generator.generate_quotation(
                materials=materials,
                baseline_data=baseline_data,
            )

            assert quotation.cost == 650.0
            assert "main" in quotation.sources

    def test_quotation_with_learn_data(self) -> None:
        """Generate quotation with learned data."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="copper-wire", quantity=10.0, unit="kg"),
            ]

            learn_data = {
                "copper-wire": {
                    "unit_price": 68.0,
                    "unit": "kg",
                }
            }

            quotation = generator.generate_quotation(
                materials=materials,
                learn_data=learn_data,
            )

            assert quotation.cost == 680.0
            assert "learn" in quotation.sources
            assert quotation.confidence == 0.9  # Lower for learned data

    def test_quotation_warnings_no_data(self) -> None:
        """Quotation warns when no price data."""
        with TemporaryDirectory() as tmpdir:
            generator = QuoteGenerator(output_dir=Path(tmpdir))

            materials = [
                MaterialInput(name="unknown-material", quantity=10.0, unit="kg"),
            ]

            quotation = generator.generate_quotation(materials=materials)

            assert len(quotation.warnings) > 0
            assert quotation.confidence < 1.0