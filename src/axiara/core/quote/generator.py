"""Quotation generator with template adaptation and three-tier pricing.

Implements Mode 3 (batch BOM backfill) and Mode 3.2 (smart quotation).
Supports default template and user-provided template adaptation.
Emits learning events for approved/corrected quotations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from axiara.core.costing import CostBreakdown, CostResult, CostingEngine, MaterialInput, ProcessInput
from axiara.core.storage.permissions import DataLayer


class QuotationError(Exception):
    """Raised when quotation operations fail."""

    pass


class PricingTier(StrEnum):
    """Three-tier pricing levels."""

    LOW = "low"
    MID = "mid"
    HIGH = "high"


@dataclass
class QuoteConstraints:
    """User constraints for smart quotation."""

    min_margin: float | None = None  # Minimum margin percentage (e.g., 10.0 = 10%)
    max_margin: float | None = None  # Maximum margin percentage
    price_cap: float | None = None  # Maximum allowed price
    price_floor: float | None = None  # Minimum allowed price
    market_tolerance: float | None = None  # Market price tolerance (percentage)
    currency: str = "CNY"  # Quote currency


@dataclass
class TierPricing:
    """Three-tier pricing with low/mid/high options."""

    low: float = 0.0
    mid: float = 0.0
    high: float = 0.0
    low_margin: float = 0.0
    mid_margin: float = 0.0
    high_margin: float = 0.0


@dataclass
class Quotation:
    """Generated quotation with metadata."""

    items: list[dict[str, Any]] = field(default_factory=list)
    cost: float = 0.0
    price: float = 0.0
    margin: float = 0.0
    tier: PricingTier | None = None
    constraints: QuoteConstraints | None = None
    confidence: float = 1.0
    sources: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    template_used: str = "default"


@dataclass
class LearningEvent:
    """Event emitted when a quotation is approved or corrected."""

    quotation_id: str
    material_costs: list[dict[str, Any]]
    process_costs: list[dict[str, Any]]
    final_price: float
    margin: float
    correction: bool = False  # True if this was a user correction
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class QuoteGenerator:
    """Quotation generator with template adaptation.

    Features:
    - Mode 3: BOM backfill with auto column detection
    - Mode 3.2: Three-tier smart quotation with constraint negotiation
    - Template adaptation (default + user-provided)
    - Learning event emission
    """

    # Default margin percentages for three tiers
    DEFAULT_LOW_MARGIN = 5.0   # 5% margin
    DEFAULT_MID_MARGIN = 15.0  # 15% margin
    DEFAULT_HIGH_MARGIN = 25.0 # 25% margin

    def __init__(
        self,
        costing_engine: CostingEngine | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize the quote generator.

        Args:
            costing_engine: Costing engine instance
            output_dir: Output directory for quotations
        """
        self.costing_engine = costing_engine or CostingEngine()
        self.output_dir = output_dir or Path("output")

    def generate_quotation(
        self,
        materials: list[MaterialInput],
        processes: list[ProcessInput] | None = None,
        constraints: QuoteConstraints | None = None,
        baseline_data: dict[str, Any] | None = None,
        learn_data: dict[str, Any] | None = None,
        market_data: dict[str, Any] | None = None,
        learn_rules: dict[str, Any] | None = None,
        template_path: Path | None = None,
    ) -> Quotation:
        """Generate a quotation from materials and processes.

        Args:
            materials: List of materials
            processes: List of processing steps
            constraints: User constraints (if any)
            baseline_data: Official baseline data
            learn_data: Learned reference data
            market_data: Market price data
            learn_rules: Learned process-cost and pricing rules
            template_path: User-provided template path

        Returns:
            Generated Quotation
        """
        # Calculate cost
        cost_result = self.costing_engine.calculate_total_cost(
            materials=materials,
            processes=processes,
            baseline_data=baseline_data,
            learn_data=learn_data,
            market_data=market_data,
            learn_rules=learn_rules,
        )

        # Generate three-tier pricing
        tier_pricing = self._calculate_tier_pricing(
            cost=cost_result.breakdown.total,
            learn_rules=learn_rules,
        )

        # Apply constraints if provided
        if constraints:
            price, tier = self._apply_constraints(
                tier_pricing=tier_pricing,
                constraints=constraints,
            )
        else:
            # No constraints - return mid tier
            price = tier_pricing.mid
            tier = PricingTier.MID

        # Build quotation items
        items = self._build_items(
            materials=materials,
            processes=processes,
            cost_result=cost_result,
        )

        # Determine template used
        template_used = "user" if template_path else "default"

        # Create quotation
        quotation = Quotation(
            items=items,
            cost=cost_result.breakdown.total,
            price=price,
            margin=((price - cost_result.breakdown.total) / cost_result.breakdown.total * 100) if cost_result.breakdown.total > 0 else 0.0,
            tier=tier,
            constraints=constraints,
            confidence=cost_result.confidence,
            sources=cost_result.sources,
            warnings=cost_result.warnings,
            template_used=template_used,
        )

        return quotation

    def backfill_bom(
        self,
        bom_path: Path,
        baseline_data: dict[str, Any] | None = None,
        learn_data: dict[str, Any] | None = None,
        market_data: dict[str, Any] | None = None,
        learn_rules: dict[str, Any] | None = None,
        output_path: Path | None = None,
    ) -> Quotation:
        """Backfill a BOM (Bill of Materials) with costs and prices.

        Implements Mode 3: batch table fill with auto column detection.

        Args:
            bom_path: Path to BOM file (Excel/CSV)
            baseline_data: Official baseline data
            learn_data: Learned reference data
            market_data: Market price data
            learn_rules: Learned rules
            output_path: Output file path

        Returns:
            Quotation with backfilled items
        """
        # For now, scaffold - would use openpyxl for Excel files
        # Auto-detect columns: material name, spec, quantity, unit
        # Fill in: unit_cost, total_cost, market_price

        raise NotImplementedError(
            "BOM backfill not yet implemented - requires openpyxl integration"
        )

    def generate_three_tier_quote(
        self,
        materials: list[MaterialInput],
        processes: list[ProcessInput] | None = None,
        baseline_data: dict[str, Any] | None = None,
        learn_data: dict[str, Any] | None = None,
        market_data: dict[str, Any] | None = None,
        learn_rules: dict[str, Any] | None = None,
    ) -> dict[PricingTier, Quotation]:
        """Generate three-tier quotations (low/mid/high).

        Used when user has no constraints - presents all three options.

        Args:
            materials: List of materials
            processes: List of processing steps
            baseline_data: Official baseline data
            learn_data: Learned reference data
            market_data: Market price data
            learn_rules: Learned rules

        Returns:
            Dict mapping tier to quotation
        """
        # Calculate cost
        cost_result = self.costing_engine.calculate_total_cost(
            materials=materials,
            processes=processes,
            baseline_data=baseline_data,
            learn_data=learn_data,
            market_data=market_data,
            learn_rules=learn_rules,
        )

        # Calculate tier pricing
        tier_pricing = self._calculate_tier_pricing(
            cost=cost_result.breakdown.total,
            learn_rules=learn_rules,
        )

        # Generate quotation for each tier
        quotations = {}
        for tier, price in [
            (PricingTier.LOW, tier_pricing.low),
            (PricingTier.MID, tier_pricing.mid),
            (PricingTier.HIGH, tier_pricing.high),
        ]:
            items = self._build_items(
                materials=materials,
                processes=processes,
                cost_result=cost_result,
            )

            quotations[tier] = Quotation(
                items=items,
                cost=cost_result.breakdown.total,
                price=price,
                margin=((price - cost_result.breakdown.total) / cost_result.breakdown.total * 100) if cost_result.breakdown.total > 0 else 0.0,
                tier=tier,
                confidence=cost_result.confidence,
                sources=cost_result.sources,
                warnings=cost_result.warnings,
            )

        return quotations

    def emit_learning_event(
        self,
        quotation: Quotation,
        corrected: bool = False,
    ) -> LearningEvent:
        """Emit a learning event for an approved or corrected quotation.

        Routes into learn_private for the hub model.

        Args:
            quotation: Approved or corrected quotation
            corrected: Whether this was a user correction

        Returns:
            LearningEvent to be recorded
        """
        import uuid

        # Extract material and process costs
        material_costs = [
            {
                "name": item.get("name", ""),
                "spec": item.get("spec", ""),
                "quantity": item.get("quantity", 0),
                "unit": item.get("unit", ""),
                "unit_cost": item.get("unit_cost", 0),
            }
            for item in quotation.items
            if item.get("type") == "material"
        ]

        process_costs = [
            {
                "name": item.get("name", ""),
                "quantity": item.get("quantity", 0),
                "unit": item.get("unit", "piece"),
                "unit_cost": item.get("unit_cost", 0),
            }
            for item in quotation.items
            if item.get("type") == "process"
        ]

        return LearningEvent(
            quotation_id=str(uuid.uuid4()),
            material_costs=material_costs,
            process_costs=process_costs,
            final_price=quotation.price,
            margin=quotation.margin,
            correction=corrected,
        )

    def _calculate_tier_pricing(
        self,
        cost: float,
        learn_rules: dict[str, Any] | None = None,
    ) -> TierPricing:
        """Calculate three-tier pricing.

        Args:
            cost: Base cost
            learn_rules: Learned pricing rules (optional)

        Returns:
            TierPricing with low/mid/high prices
        """
        # Try to use learned margins
        low_margin = self.DEFAULT_LOW_MARGIN
        mid_margin = self.DEFAULT_MID_MARGIN
        high_margin = self.DEFAULT_HIGH_MARGIN

        if learn_rules and "pricing_tiers" in learn_rules:
            tiers = learn_rules["pricing_tiers"]
            low_margin = tiers.get("low_margin", low_margin)
            mid_margin = tiers.get("mid_margin", mid_margin)
            high_margin = tiers.get("high_margin", high_margin)

        # Calculate prices
        tier_pricing = TierPricing()
        tier_pricing.low_margin = low_margin
        tier_pricing.mid_margin = mid_margin
        tier_pricing.high_margin = high_margin

        tier_pricing.low = cost * (1 + low_margin / 100)
        tier_pricing.mid = cost * (1 + mid_margin / 100)
        tier_pricing.high = cost * (1 + high_margin / 100)

        return tier_pricing

    def _apply_constraints(
        self,
        tier_pricing: TierPricing,
        constraints: QuoteConstraints,
    ) -> tuple[float, PricingTier]:
        """Apply user constraints to select appropriate tier.

        Args:
            tier_pricing: Three-tier pricing
            constraints: User constraints

        Returns:
            Tuple of (selected price, selected tier)
        """
        # Check price cap
        if constraints.price_cap is not None:
            if tier_pricing.high > constraints.price_cap:
                # High tier exceeds cap, try mid
                if tier_pricing.mid <= constraints.price_cap:
                    return tier_pricing.mid, PricingTier.MID
                elif tier_pricing.low <= constraints.price_cap:
                    return tier_pricing.low, PricingTier.LOW
                else:
                    # All tiers exceed cap - use cap with low tier
                    return constraints.price_cap, PricingTier.LOW

        # Check margin constraints
        if constraints.min_margin is not None:
            if tier_pricing.low_margin < constraints.min_margin:
                # Low tier doesn't meet margin requirement
                if tier_pricing.mid_margin >= constraints.min_margin:
                    return tier_pricing.mid, PricingTier.MID
                else:
                    return tier_pricing.high, PricingTier.HIGH

        # Default to mid tier when constraints don't force a specific choice
        return tier_pricing.mid, PricingTier.MID

    def _build_items(
        self,
        materials: list[MaterialInput],
        processes: list[ProcessInput] | None,
        cost_result: CostResult,
    ) -> list[dict[str, Any]]:
        """Build quotation items list.

        Args:
            materials: Material inputs
            processes: Process inputs
            cost_result: Cost calculation result

        Returns:
            List of item dictionaries
        """
        items = []

        # Add materials
        for i, material in enumerate(materials):
            items.append({
                "type": "material",
                "name": material.name,
                "spec": material.spec,
                "quantity": material.quantity,
                "unit": material.unit,
                "unit_cost": material.unit_price or 0.0,
                "total_cost": material.unit_price * material.quantity if material.unit_price else 0.0,
            })

        # Add processes
        if processes:
            for process in processes:
                items.append({
                    "type": "process",
                    "name": process.name,
                    "quantity": process.quantity,
                    "unit": process.unit,
                    "unit_cost": 0.0,  # Would be calculated from process_cost rules
                    "total_cost": 0.0,
                })

        return items

    def save_quotation(
        self,
        quotation: Quotation,
        output_path: Path | None = None,
        template_path: Path | None = None,
    ) -> Path:
        """Save quotation to output file.

        Args:
            quotation: Quotation to save
            output_path: Custom output path
            template_path: Template to use

        Returns:
            Path to saved file
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate default filename
        if output_path is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            output_path = self.output_dir / f"quotation-{timestamp}.json"

        # For now, save as JSON
        # Template adaptation would customize the format
        import json

        quotation_dict = {
            "items": quotation.items,
            "cost": quotation.cost,
            "price": quotation.price,
            "margin": quotation.margin,
            "tier": quotation.tier.value if quotation.tier else None,
            "confidence": quotation.confidence,
            "sources": quotation.sources,
            "warnings": quotation.warnings,
            "created_at": quotation.created_at,
            "template_used": quotation.template_used,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(quotation_dict, f, indent=2, ensure_ascii=False)

        return output_path