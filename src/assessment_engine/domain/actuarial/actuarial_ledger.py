"""Immutable Single Source of Truth (SSOT) Actuarial Ledger.

Guarantees 100% mathematical consistency across all executive summaries,
chapter tables, and specialist annexes under Open FAIR.
Strictly 100% Technical English, frozen value objects.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DomainFinancialMetric(BaseModel):
    """Immutable financial metrics for a single technical domain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str = Field(..., pattern=r"^[A-Z0-9_-]{2,32}$")
    raw_standalone_ale: int = Field(..., ge=0)
    diversification_adjustment: int = Field(..., le=0)
    calibrated_net_ale: int = Field(..., ge=0)
    worst_crisis_event_p90: int = Field(..., ge=0)
    portfolio_weight_pct: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("100.0"))

    @model_validator(mode="after")
    def validate_row_conservation(self) -> Self:
        expected = self.raw_standalone_ale + self.diversification_adjustment
        if expected != self.calibrated_net_ale:
            raise ValueError(
                f"Row conservation failed for {self.tower_id}: "
                f"Standalone ({self.raw_standalone_ale}) + Adj ({self.diversification_adjustment}) "
                f"!= Net ({self.calibrated_net_ale})"
            )
        return self


class ActuarialLedgerSSOT(BaseModel):
    """Immutable, sealed enterprise risk ledger guaranteeing zero arithmetic drift across deliverables."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    currency_iso: str = Field(..., pattern=r"^[A-Z]{3}$")
    domain_metrics: Dict[str, DomainFinancialMetric] = Field(..., min_length=1)
    gross_undiversified_ale: int = Field(..., ge=0)
    copula_adjustment_ale: int = Field(..., le=0)
    copula_overlap_pct: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("100.0"))
    net_consolidated_portfolio_ale: int = Field(..., ge=0)
    total_portfolio_weight_pct: Decimal = Field(default=Decimal("100.0"))

    @model_validator(mode="after")
    def validate_ledger_closure(self) -> Self:
        # 1. Vertical sums
        v_standalone = sum(m.raw_standalone_ale for m in self.domain_metrics.values())
        if v_standalone != self.gross_undiversified_ale:
            raise ValueError("Vertical Standalone mismatch against gross_undiversified_ale.")

        v_adj = sum(m.diversification_adjustment for m in self.domain_metrics.values())
        if v_adj != self.copula_adjustment_ale:
            raise ValueError("Vertical Adjustment mismatch against copula_adjustment_ale.")

        v_net = sum(m.calibrated_net_ale for m in self.domain_metrics.values())
        if v_net != self.net_consolidated_portfolio_ale:
            raise ValueError("Vertical Net mismatch against net_consolidated_portfolio_ale.")

        # 2. Bridge identity
        bridge = self.gross_undiversified_ale + self.copula_adjustment_ale
        if bridge != self.net_consolidated_portfolio_ale:
            raise ValueError("Actuarial bridge identity violation: Gross + Adj != Net.")

        # 3. Simplex weights
        if self.net_consolidated_portfolio_ale > 0:
            v_pct = sum(m.portfolio_weight_pct for m in self.domain_metrics.values())
            if abs(v_pct - Decimal("100.0")) > Decimal("0.01"):
                raise ValueError(f"Percentage simplex violation: {v_pct}% != 100.0%.")

        return self

    def get_domain_metric(self, tower_id: str) -> DomainFinancialMetric:
        """Retrieves domain metric with case-insensitive normalization."""
        clean = tower_id.strip().upper()
        if clean not in self.domain_metrics:
            raise KeyError(f"Domain {tower_id} not present in ActuarialLedgerSSOT.")
        return self.domain_metrics[clean]
