"""Quotation generator with template adaptation and three-tier pricing.

Implements Mode 3 (batch BOM backfill) and Mode 3.2 (smart quotation).
Supports default template and user-provided template adaptation.
Emits learning events for approved/corrected quotations.
"""

from __future__ import annotations

from axiara.core.quote.generator import (
    LearningEvent,
    PricingTier,
    Quotation,
    QuotationError,
    QuoteConstraints,
    QuoteGenerator,
    TierPricing,
)

__all__ = [
    "LearningEvent",
    "PricingTier",
    "Quotation",
    "QuotationError",
    "QuoteConstraints",
    "QuoteGenerator",
    "TierPricing",
]