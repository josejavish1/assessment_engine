"""Domain schemas for Stochastic FinOps, Open FAIR Risk Attenuation, and ROSI calculations (RFC-027).

100% Technical English. Zero Hardcoding. Multi-tenant and Multi-vertical compliant.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FairFactorTarget(str, Enum):
    """Open FAIR ontology factors targeted by a mitigation project."""

    TEF = "THREAT_EVENT_FREQUENCY"
    VULN = "VULNERABILITY"
    LEF = "LOSS_EVENT_FREQUENCY"
    PRIMARY_LOSS = "PRIMARY_LOSS_MAGNITUDE"
    SECONDARY_LOSS = "SECONDARY_LOSS_MAGNITUDE"
    COMBINED_LM = "COMBINED_LOSS_MAGNITUDE"


class PertDistributionParams(BaseModel):
    """Three-point estimation parameters for Beta-PERT stochastic modeling."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    min_val: float = Field(..., ge=0.0, description="Optimistic bound (minimum value)")
    mode_val: float = Field(..., ge=0.0, description="Most likely value (mode)")
    max_val: float = Field(..., ge=0.0, description="Pessimistic bound (maximum value)")
    gamma: float = Field(default=4.0, gt=0.0, description="PERT shape/peakedness parameter")

    @model_validator(mode="after")
    def validate_bounds(self) -> PertDistributionParams:
        """Validate that min <= mode <= max strictly holds."""
        if not (self.min_val <= self.mode_val <= self.max_val):
            raise ValueError(
                f"Invalid PERT bounds: min ({self.min_val}) <= mode ({self.mode_val}) <= max ({self.max_val}) must hold."
            )
        return self


class ControlAttenuationVector(BaseModel):
    """Defines how a remediation project dampens a specific Open FAIR factor."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    target_factor: FairFactorTarget = Field(..., description="The FAIR factor being mitigated")
    efficacy_distribution: PertDistributionParams = Field(
        ..., description="Stochastic percentage reduction [0.0 to 1.0]"
    )

    @model_validator(mode="after")
    def validate_normalized_efficacy(self) -> ControlAttenuationVector:
        """Ensure attenuation efficacy does not exceed 100%."""
        if self.efficacy_distribution.max_val > 1.0:
            raise ValueError("Control efficacy cannot exceed 1.0 (100% risk reduction).")
        return self


class EnterpriseFinancialContext(BaseModel):
    """Tenant-specific macro-financial parameters for multi-vertical scaling."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    tenant_id: str = Field(..., min_length=1)
    currency_code: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 Currency Code (e.g. USD, EUR, JPY)"
    )
    discount_rate_wacc: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted Average Cost of Capital (WACC)"
    )
    amortization_horizon_years: int = Field(
        default=3, ge=1, le=10, description="CapEx depreciation/amortization window"
    )
    regional_purchasing_power_multiplier: float = Field(
        default=1.0, gt=0.0, description="PPP / Geographic rate adjustment factor"
    )
    vertical_complexity_multiplier: float = Field(
        default=1.0, gt=0.0, description="Regulatory/Industry overhead multiplier"
    )


class StochasticCostProfile(BaseModel):
    """Stochastic FinOps representation of a project's Total Cost of Ownership (TCO)."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    capex_distribution: PertDistributionParams = Field(..., description="One-time Capital Expenditure distribution")
    opex_annual_distribution: PertDistributionParams = Field(
        ..., description="Recurring Annual Operational Expenditure"
    )
    headcount_fte_allocation: float = Field(
        default=0.0, ge=0.0, description="Full-Time Equivalent engineering/ops resources"
    )
    implementation_duration_months: float = Field(
        default=6.0, gt=0.0, description="Estimated time to full operational capability"
    )


class DistributionMetrics(BaseModel):
    """Summary statistics extracted from a Monte Carlo simulation vector."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    mean: float
    std_dev: float
    p10: float = Field(..., description="10th Percentile (Optimistic / Lower Bound)")
    p50: float = Field(..., description="50th Percentile (Median)")
    p90: float = Field(..., description="90th Percentile (Value at Risk / Pessimistic Bound)")
    p95: float = Field(..., description="95th Percentile (Extreme Tail)")


class RosiActuarialResult(BaseModel):
    """Complete actuarial output coupling Open FAIR risk reduction with FinOps TCO."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    project_id: str
    currency_code: str
    simulations_count: int = Field(..., ge=1000)

    # Risk Exposure Metrics (Annualized)
    ale_pre_mitigation: DistributionMetrics
    ale_post_mitigation: DistributionMetrics
    delta_ale_reduction: DistributionMetrics

    # Financial Cost Metrics (Annualized & NPV)
    annualized_tco: DistributionMetrics
    npv_total_cost: DistributionMetrics
    npv_net_benefit: DistributionMetrics

    # Return on Security Investment (ROSI) Ratio & Percentage
    rosi_percentage: DistributionMetrics
    probability_of_positive_return: float = Field(
        ..., ge=0.0, le=1.0, description="Probability that Delta ALE > Annualized TCO"
    )
    payback_period_months: DistributionMetrics
    cost_of_delay_monthly: DistributionMetrics = Field(
        ..., description="Monthly unmitigated risk exposure incurred by delaying execution"
    )
    investment_verdict: str = Field(..., description="Algorithmic classification of financial viability")
