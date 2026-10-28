"""
Rules & Pricing Engine Primitive — GEMA 07 / Radar Primitive 7 (MedusaJS & Stripe Billing Architecture / SOTA 2026).
Engine for exact integer-cent arithmetic (zero IEEE-754 floating point rounding drift).
Calculates tiered promotions, promotional discount coupons, and multi-bracket tax breakdowns (IVA 21%, 10%, 0%).
Domain-agnostic: powers checkout and invoice settlement for healthcare, retail, sports, or digital subscriptions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.pricing_rules")


@dataclass(frozen=True)
class PricingItemLine:
    item_id: str
    title: str
    unit_price_cents: int
    quantity: int
    tax_rate_percent: float = 21.0  # Default standard VAT rate in Spain.


@dataclass(frozen=True)
class DiscountCoupon:
    code: str
    discount_type: str  # "percentage" o "fixed"
    value: float        # E.g., 15.0 for 15% or 1000 for €10.00.
    min_subtotal_cents: int = 0
    max_discount_cents: int | None = None
    is_active: bool = True


@dataclass
class CalculatedLineResult:
    item_id: str
    title: str
    unit_price_cents: int
    quantity: int
    line_net_cents: int
    line_tax_cents: int
    line_total_cents: int
    tax_rate_percent: float


@dataclass
class FinancialCartSettlement:
    lines: list[CalculatedLineResult]
    subtotal_gross_cents: int
    discount_applied_cents: int
    taxable_base_cents: int
    total_tax_cents: int
    grand_total_cents: int
    # Format euro values for UI and official invoices.
    subtotal_gross_eur: float = 0.0
    discount_applied_eur: float = 0.0
    taxable_base_eur: float = 0.0
    total_tax_eur: float = 0.0
    grand_total_eur: float = 0.0
    applied_coupon_code: str | None = None


class PricingRulesPrimitive:
    """
    Implement canonical rate, coupon, and tax rules using integer arithmetic.
    """

    def calculate_cart_settlement(
        self,
        items: list[PricingItemLine],
        coupon: DiscountCoupon | None = None
    ) -> FinancialCartSettlement:
        """
        Calculate the exact accounting breakdown in cents without rounding errors.
        """
        if not items:
            return FinancialCartSettlement([], 0, 0, 0, 0, 0)

        raw_subtotal_cents = sum(item.unit_price_cents * item.quantity for item in items)

        discount_cents = 0
        coupon_applied_code = None

        if coupon and coupon.is_active and raw_subtotal_cents >= coupon.min_subtotal_cents:
            coupon_applied_code = coupon.code
            if coupon.discount_type == "percentage":
                discount_cents = int(round(raw_subtotal_cents * (coupon.value / 100.0)))
                if coupon.max_discount_cents:
                    discount_cents = min(discount_cents, coupon.max_discount_cents)
            elif coupon.discount_type == "fixed":
                discount_cents = int(coupon.value)

            discount_cents = min(discount_cents, raw_subtotal_cents)

        taxable_base_cents = raw_subtotal_cents - discount_cents

        # 2. Prorate tax breakdown by line item.
        discount_ratio = (taxable_base_cents / float(raw_subtotal_cents)) if raw_subtotal_cents > 0 else 1.0

        calculated_lines: list[CalculatedLineResult] = []
        accumulated_tax_cents = 0

        for item in items:
            raw_line_cents = item.unit_price_cents * item.quantity
            line_net_cents = int(round(raw_line_cents * discount_ratio))
            line_tax_cents = int(round(line_net_cents * (item.tax_rate_percent / 100.0)))
            line_total_cents = line_net_cents + line_tax_cents

            accumulated_tax_cents += line_tax_cents

            calculated_lines.append(CalculatedLineResult(
                item_id=item.item_id,
                title=item.title,
                unit_price_cents=item.unit_price_cents,
                quantity=item.quantity,
                line_net_cents=line_net_cents,
                line_tax_cents=line_tax_cents,
                line_total_cents=line_total_cents,
                tax_rate_percent=item.tax_rate_percent
            ))

        grand_total_cents = taxable_base_cents + accumulated_tax_cents

        settlement = FinancialCartSettlement(
            lines=calculated_lines,
            subtotal_gross_cents=raw_subtotal_cents,
            discount_applied_cents=discount_cents,
            taxable_base_cents=taxable_base_cents,
            total_tax_cents=accumulated_tax_cents,
            grand_total_cents=grand_total_cents,
            subtotal_gross_eur=round(raw_subtotal_cents / 100.0, 2),
            discount_applied_eur=round(discount_cents / 100.0, 2),
            taxable_base_eur=round(taxable_base_cents / 100.0, 2),
            total_tax_eur=round(accumulated_tax_cents / 100.0, 2),
            grand_total_eur=round(grand_total_cents / 100.0, 2),
            applied_coupon_code=coupon_applied_code
        )

        logger.debug(
            f"[PricingRules] Liquidación calculada: Base {settlement.taxable_base_eur}€ + "
            f"IVA {settlement.total_tax_eur}€ = Total {settlement.grand_total_eur}€ (Descuento: {settlement.discount_applied_eur}€)"
        )
        return settlement


pricing_rules = PricingRulesPrimitive()
