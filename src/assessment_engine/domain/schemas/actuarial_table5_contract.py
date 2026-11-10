"""Data contracts and validation for the Canonical Open FAIR Table 5 Actuarial Matrix."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DomainRiskBreakdownRow(BaseModel):
    """Immutable data row representing an individual domain's actuarial reconciliation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str = Field(..., pattern=r"^T\d{1,2}$")
    tower_name: str = Field(..., min_length=2)
    cmmi_maturity: float = Field(..., ge=1.0, le=5.0)
    standalone_ale: int = Field(..., ge=0)
    diversification_adjustment: int = Field(..., le=0)
    euler_net_contribution: int = Field(..., ge=0)
    portfolio_weight_pct: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("100.0"))

    @model_validator(mode="after")
    def validate_row_closure(self) -> Self:
        expected = self.standalone_ale + self.diversification_adjustment
        if expected != self.euler_net_contribution:
            raise ValueError(
                f"Row {self.tower_id} Incoherence: Standalone ({self.standalone_ale:,}) + "
                f"Adjustment ({self.diversification_adjustment:,}) != Net ({self.euler_net_contribution:,})"
            )
        return self


class ActuarialTable5ReconciliationContract(BaseModel):
    """Full actuarial contract for Table 5 enforcing complete horizontal and vertical accounting closure."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    currency_iso: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    domain_rows: List[DomainRiskBreakdownRow] = Field(..., min_length=1)
    subtotal_gross_cmmi: float = Field(..., ge=1.0, le=5.0)
    subtotal_gross_undiversified_ale: int = Field(..., ge=0)
    actuarial_copula_adjustment_ale: int = Field(..., le=0)
    actuarial_copula_overlap_pct: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("100.0"))
    total_net_consolidated_cmmi: float = Field(..., ge=1.0, le=5.0)
    total_net_consolidated_ale: int = Field(..., ge=0)
    total_portfolio_weight_pct: Decimal = Field(default=Decimal("100.0"))

    @model_validator(mode="after")
    def validate_contract_identities(self) -> Self:
        # 1. Vertical sums
        v_standalone = sum(r.standalone_ale for r in self.domain_rows)
        if v_standalone != self.subtotal_gross_undiversified_ale:
            raise ValueError("Vertical Standalone mismatch against Subtotal Gross.")

        v_adj = sum(r.diversification_adjustment for r in self.domain_rows)
        if v_adj != self.actuarial_copula_adjustment_ale:
            raise ValueError("Vertical Adjustment mismatch against Copula Adjustment total.")

        v_euler = sum(r.euler_net_contribution for r in self.domain_rows)
        if v_euler != self.total_net_consolidated_ale:
            raise ValueError("Vertical Net Euler contribution mismatch against Net Total.")

        # 2. Bridge identity
        bridge_sum = self.subtotal_gross_undiversified_ale + self.actuarial_copula_adjustment_ale
        if bridge_sum != self.total_net_consolidated_ale:
            raise ValueError("Bridge identity violation: Gross Subtotal + Adjustment != Net Total.")

        # 3. Simplex weights
        v_pct = sum(r.portfolio_weight_pct for r in self.domain_rows)
        if abs(v_pct - Decimal("100.0")) > Decimal("0.01"):
            raise ValueError(f"Percentage simplex violation: Sum of weights ({v_pct}%) != 100.0%.")

        return self
