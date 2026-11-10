"""Multi-dimensional macroeconomic baselines for Polymorphic Open FAIR risk modeling."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from assessment_engine.domain.actuarial.financial_profile import (
    IndustryArchetype,
    TenantFinancialProfile,
)


class AvailabilityBaseline(BaseModel):
    """Macroeconomic baseline for Availability and Operational Outage risks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    hourly_revenue_at_risk: float = Field(..., gt=0.0, description="Gross transactional revenue velocity per hour")
    critical_service_mttr_hours: float = Field(default=2.0, gt=0.0, description="Baseline Mean Time to Restore for critical services")


class CapitalEfficiencyBaseline(BaseModel):
    """Macroeconomic baseline for Cloud Cost, FinOps, and IT Capital Inefficiency risks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    annual_it_opex: float = Field(..., gt=0.0, description="Annual operating expenditure for IT and technology")
    annual_cloud_infrastructure_spend: float = Field(..., ge=0.0, description="Annual cloud/infrastructure spend portion")
    estimated_unoptimized_spend_ratio: float = Field(
        default=0.22, ge=0.0, le=1.0, description="Industry benchmark ratio of addressable cloud waste (typically 20-30%)"
    )


class ProductivityBaseline(BaseModel):
    """Macroeconomic baseline for Engineering Toil, Workplace friction, and Human Capital risks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_impacted_ftes: int = Field(..., gt=0, description="Total full-time employee headcount impacted by platform")
    fully_burdened_hourly_rate: float = Field(..., gt=0.0, description="Fully loaded hourly compensation cost per FTE")
    annual_working_hours_per_fte: int = Field(default=1920, gt=0, description="Standard productive working hours per employee per year")
    desk_worker_ratio: float = Field(default=0.30, ge=0.01, le=1.0, description="Fraction of employees who are active workstation / desk users")
    it_staff_ratio: float = Field(default=0.05, ge=0.005, le=0.50, description="Fraction of desk workforce representing dedicated IT engineering staff")


class RegulatoryBaseline(BaseModel):
    """Macroeconomic baseline for Cyber Breaches, Statutory Fines, and Compliance liabilities."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    annual_global_turnover: float = Field(..., gt=0.0, description="Consolidated global turnover for statutory fine ceilings (e.g. DORA / GDPR)")
    compromised_record_unit_cost: float = Field(
        default=165.0, ge=0.0, description="Empirical forensic cost per compromised PII/financial record (IBM/Ponemon benchmark)"
    )
    total_pii_records_managed: int = Field(..., ge=0, description="Aggregate volume of customer PII / regulated accounts governed")
    b2b_exposure_dampener: float = Field(
        default=0.20, ge=0.01, le=1.0, description="Regulatory dampening factor distinguishing B2B enterprise exposure from B2C consumer exposure"
    )


class PolymorphicFinancialTelemetry(BaseModel):
    """Immutable composite container holding multi-dimensional economic baselines across all 4 FAIR archetypes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    currency_iso: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    industry_vertical: IndustryArchetype
    availability: AvailabilityBaseline
    capital_efficiency: CapitalEfficiencyBaseline
    productivity: ProductivityBaseline
    regulatory: RegulatoryBaseline

    @model_validator(mode="after")
    def validate_macroeconomic_coherence(self) -> Self:
        """Enforces logical coherence between macroeconomic variables."""
        if self.capital_efficiency.annual_cloud_infrastructure_spend > self.capital_efficiency.annual_it_opex:
            raise ValueError(
                f"Actuarial Incoherence: Cloud infrastructure spend ({self.capital_efficiency.annual_cloud_infrastructure_spend:,.2f}) "
                f"cannot exceed total IT OPEX ({self.capital_efficiency.annual_it_opex:,.2f})."
            )
        if self.availability.hourly_revenue_at_risk > self.regulatory.annual_global_turnover:
            raise ValueError("Actuarial Incoherence: Hourly revenue at risk cannot exceed annual global turnover.")
        return self

    @classmethod
    def from_tenant_profile(
        cls,
        profile: TenantFinancialProfile,
        annual_cloud_spend: Optional[float] = None,
        annual_it_opex: Optional[float] = None,
        total_ftes: Optional[int] = None,
        fully_burdened_hourly_rate: Optional[float] = None,
        total_pii_records: Optional[int] = None,
        critical_mttr_hours: float = 2.0,
    ) -> PolymorphicFinancialTelemetry:
        """Constructs calibrated polymorphic telemetry, dynamically deriving missing variables via industry benchmarks."""
        revenue_f = float(profile.annual_revenue)
        hourly_burn_f = float(profile.hourly_downtime_burn)
        vert = profile.industry_archetype

        # 1. Availability Baseline
        avail = AvailabilityBaseline(
            hourly_revenue_at_risk=max(50.0, hourly_burn_f),
            critical_service_mttr_hours=max(0.1, critical_mttr_hours),
        )

        # 2. Capital Efficiency Baseline (Benchmark-derived if omitted)
        # Ratio of IT OPEX to Revenue based on Gartner IT Key Metrics by Industry
        it_opex_ratios: Dict[IndustryArchetype, float] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: 0.085,  # 8.5% for digital banking / SaaS
            IndustryArchetype.PROCESS_MANUFACTURING_OT: 0.026,    # 2.6% for manufacturing
            IndustryArchetype.LIFE_SAFETY_CRITICAL: 0.045,        # 4.5% for healthcare
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: 0.032,       # 3.2% for retail
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: 0.028,   # 2.8% for logistics
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: 0.065, # 6.5% for government
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: 0.040,     # 4.0% for corporate services
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: 0.040,
        }
        cloud_spend_shares: Dict[IndustryArchetype, float] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: 0.48,  # 48% of IT spend in cloud
            IndustryArchetype.PROCESS_MANUFACTURING_OT: 0.18,
            IndustryArchetype.LIFE_SAFETY_CRITICAL: 0.22,
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: 0.35,
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: 0.25,
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: 0.30,
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: 0.35,
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: 0.30,
        }

        derived_it_opex = annual_it_opex if annual_it_opex is not None else max(100_000.0, revenue_f * it_opex_ratios.get(vert, 0.04))
        derived_cloud_spend = (
            annual_cloud_spend
            if annual_cloud_spend is not None
            else derived_it_opex * cloud_spend_shares.get(vert, 0.30)
        )
        # Ensure cloud spend never exceeds IT opex
        derived_cloud_spend = min(derived_cloud_spend, derived_it_opex * 0.95)

        cap_eff = CapitalEfficiencyBaseline(
            annual_it_opex=derived_it_opex,
            annual_cloud_infrastructure_spend=derived_cloud_spend,
            estimated_unoptimized_spend_ratio=0.22,
        )

        # 3. Productivity Baseline (Benchmark-derived revenue per FTE)
        revenue_per_fte: Dict[IndustryArchetype, float] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: 380_000.0,
            IndustryArchetype.PROCESS_MANUFACTURING_OT: 290_000.0,
            IndustryArchetype.LIFE_SAFETY_CRITICAL: 130_000.0,
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: 210_000.0,
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: 240_000.0,
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: 120_000.0,
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: 200_000.0,
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: 250_000.0,
        }
        hourly_wage_rates: Dict[IndustryArchetype, float] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: 68.0,
            IndustryArchetype.PROCESS_MANUFACTURING_OT: 38.0,
            IndustryArchetype.LIFE_SAFETY_CRITICAL: 42.0,
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: 32.0,
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: 35.0,
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: 45.0,
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: 48.0,
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: 45.0,
        }

        derived_ftes = total_ftes if total_ftes is not None else max(10, round(revenue_f / revenue_per_fte.get(vert, 250_000.0)))
        derived_rate = (
            fully_burdened_hourly_rate
            if fully_burdened_hourly_rate is not None
            else hourly_wage_rates.get(vert, 45.0)
        )

        desk_ratios: Dict[IndustryArchetype, float] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: 0.95,
            IndustryArchetype.PROCESS_MANUFACTURING_OT: 0.15,
            IndustryArchetype.LIFE_SAFETY_CRITICAL: 0.35,
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: 0.18,
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: 0.15,
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: 0.70,
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: 0.60,
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: 0.40,
        }
        b2b_dampeners: Dict[IndustryArchetype, float] = {
            IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH: 1.0,
            IndustryArchetype.HIGH_TEMPO_COMMERCIAL: 0.85,
            IndustryArchetype.LIFE_SAFETY_CRITICAL: 0.75,
            IndustryArchetype.PROCESS_MANUFACTURING_OT: 0.10,
            IndustryArchetype.DEFERRED_NETWORK_LOGISTICS: 0.12,
            IndustryArchetype.PUBLIC_SECTOR_CIVIC_MISSION: 0.30,
            IndustryArchetype.STANDARD_ENTERPRISE_B2B: 0.25,
            IndustryArchetype.DYNAMIC_EMPIRICAL_AUTONOMOUS: 0.20,
        }

        prod = ProductivityBaseline(
            total_impacted_ftes=derived_ftes,
            fully_burdened_hourly_rate=derived_rate,
            annual_working_hours_per_fte=1920,
            desk_worker_ratio=desk_ratios.get(vert, 0.30),
            it_staff_ratio=0.05,
        )

        # 4. Regulatory Baseline (Benchmark-derived accounts from turnover)
        derived_pii = (
            total_pii_records
            if total_pii_records is not None
            else max(1_000, round(revenue_f / 65.0))
        )

        reg = RegulatoryBaseline(
            annual_global_turnover=max(100_000.0, revenue_f),
            compromised_record_unit_cost=165.0,
            total_pii_records_managed=derived_pii,
            b2b_exposure_dampener=b2b_dampeners.get(vert, 0.20),
        )

        return cls(
            currency_iso=profile.currency_code,
            industry_vertical=vert,
            availability=avail,
            capital_efficiency=cap_eff,
            productivity=prod,
            regulatory=reg,
        )
