"""Algebraic Data Types (ADTs) for Polymorphic Open FAIR Economic Loss Vectors."""

from __future__ import annotations

from abc import ABC
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from assessment_engine.domain.taxonomy.archetype_registry import LossArchetypeType


class BaseEconomicLossVector(BaseModel, ABC):
    """Abstract immutable base for all actuarial loss vectors."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    annualized_loss_expectancy: float = Field(..., ge=0.0, description="Expected Annual Loss (ALE) in currency units")
    probable_loss_magnitude: float = Field(..., ge=0.0, description="Single loss event magnitude (P50)")
    loss_event_frequency_annual: float = Field(..., ge=0.0, description="Expected annual loss frequency (LEF)")
    confidence_interval_95_low: float = Field(..., ge=0.0, description="5th percentile loss boundary")
    confidence_interval_95_high: float = Field(..., ge=0.0, description="95th percentile loss boundary (P90/P95 tail)")
    currency_iso: str = Field(default="USD", pattern=r"^[A-Z]{3}$")


class AvailabilityOutageVector(BaseEconomicLossVector):
    """Economic loss vector for Operational Outages, Network Partitions, and Hardware Halts."""

    archetype: Literal[LossArchetypeType.AVAILABILITY_OUTAGE] = LossArchetypeType.AVAILABILITY_OUTAGE
    projected_annual_downtime_hours: float = Field(..., ge=0.0, description="Cumulative expected hours of service downtime per year")
    revenue_burn_rate_per_hour: float = Field(..., gt=0.0, description="Gross transactional revenue loss velocity per outage hour")


class CapitalInefficiencyVector(BaseEconomicLossVector):
    """Economic loss vector for Cloud Cost Drift, Unoptimized Resources, and Software Licensing True-ups."""

    archetype: Literal[LossArchetypeType.CAPITAL_INEFFICIENCY] = LossArchetypeType.CAPITAL_INEFFICIENCY
    annual_addressable_waste: float = Field(..., ge=0.0, description="Estimated addressable annual cloud and licensing waste")
    inefficiency_leakage_rate_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of IT/Cloud budget lost to unoptimized drift")


class ProductivityToilVector(BaseEconomicLossVector):
    """Economic loss vector for Engineering Friction, Manual Runbook Toil, and Workplace Inefficiency."""

    archetype: Literal[LossArchetypeType.PRODUCTIVITY_TOIL] = LossArchetypeType.PRODUCTIVITY_TOIL
    annual_hours_lost_to_toil: float = Field(..., ge=0.0, description="Cumulative productive employee hours lost annually to friction")
    equivalent_fte_capacity_burned: float = Field(..., ge=0.0, description="Equivalent full-time employees lost to unproductive toil")


class RegulatoryBreachVector(BaseEconomicLossVector):
    """Economic loss vector for Cyber Incidents, Data Breaches, and Statutory Non-Compliance Fines."""

    archetype: Literal[LossArchetypeType.REGULATORY_AND_BREACH] = LossArchetypeType.REGULATORY_AND_BREACH
    statutory_penalty_exposure: float = Field(..., ge=0.0, description="Potential statutory sanctions (e.g. DORA / GDPR / PRA fines)")
    remediation_and_forensic_cost: float = Field(..., ge=0.0, description="Direct incident recovery, forensic audit, and client notice costs")


# Algebraic Data Type: Discriminated Union over the 'archetype' field
PolymorphicLossVector = Annotated[
    Union[
        AvailabilityOutageVector,
        CapitalInefficiencyVector,
        ProductivityToilVector,
        RegulatoryBreachVector,
    ],
    Field(discriminator="archetype"),
]


class LossVectorEnvelope(BaseModel):
    """Serialization container model for polymorphic loss vectors."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    vector: PolymorphicLossVector
