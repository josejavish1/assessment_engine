"""Domain schemas for Open FAIR conditional risk ontology and causal chain modeling."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, condecimal, confloat


class CouplingRegime(str, Enum):
    """Represents the architectural coupling tightness between technical systems."""

    LOOSE = "LOOSE"           # Linear degradation; isolated fault domain
    MODERATE = "MODERATE"     # Partial operational propagation across adjacent components
    TIGHT = "TIGHT"           # Non-linear cascade; immediate holistic operational trip


class CausalBowTie(BaseModel):
    """Represents the 3-phase conditional loss causality chain in Open FAIR."""

    initiating_threat_event: str = Field(
        ...,
        description="The initial external shock or triggering failure event (e.g., utility power grid drop, compressor failure).",
    )
    control_vulnerability_gap: str = Field(
        ...,
        description="The latent physical, architectural, or governance defect that allows the threat to materialize (e.g., single-path PDU, uncontained air mixing).",
    )
    primary_asset_impact: str = Field(
        ...,
        description="The direct physical or business disruption to plant, operations, or data assets.",
    )


class FairActuarialInput(BaseModel):
    """Actuarial parameters quantifying the probability and magnitude of a conditional loss event."""

    loss_event_frequency_annual: confloat(gt=0.0) = Field(
        ...,
        description="Loss Event Frequency (LEF): Expected number of materialized loss events per calendar year.",
    )
    single_loss_magnitude_base: condecimal(gt=Decimal("0.00"), decimal_places=2) = Field(
        ...,
        description="Base Single Loss Expectancy (SLE) before systemic coupling amplification.",
    )
    operational_coupling_factor: confloat(ge=1.0, le=5.0) = Field(
        default=1.0,
        description="Cascading impact multiplier reflecting tight systemic interdependence.",
    )
    coupling_regime: CouplingRegime = Field(
        default=CouplingRegime.LOOSE,
        description="Architectural coupling classification.",
    )
    downtime_hours_mean: confloat(ge=0.1) = Field(
        default=2.0,
        description="Mean Time to Recovery (MTTR) in hours.",
    )
    hourly_operational_impact: condecimal(gt=Decimal("0.00"), decimal_places=2) = Field(
        default=Decimal("15600.00"),
        description="Hourly burn rate during partial or total business interruption.",
    )


class ConditionalLossEvent(BaseModel):
    """An end-to-end defensible risk scenario grounded in empirical Open FAIR physics."""

    event_id: str = Field(
        ...,
        pattern=r"^[A-Z]{2,4}-\d{2,5}$",
        description="Standardized risk identifier (e.g., RSK-01, RVS-05).",
    )
    title: str = Field(
        ...,
        description="Executive business scenario title explaining the loss condition.",
    )
    domain_category: str = Field(
        ...,
        description="Target technological domain or architectural pillar.",
    )
    currency_code: str = Field(
        default="EUR",
        min_length=3,
        max_length=3,
        description="ISO 4217 Currency Code (e.g., EUR, USD, JPY, GBP).",
    )
    causal_chain: CausalBowTie = Field(
        ...,
        description="Three-stage bow-tie causality model.",
    )
    actuarial_input: FairActuarialInput = Field(
        ...,
        description="Actuarial calibration data.",
    )
    mitigation_directive: str = Field(
        ...,
        description="Actionable remediation directive linking technical investment to risk mitigation.",
    )
    audit_evidence: Optional[str] = Field(
        default=None,
        description="Direct forensic quote or audit log trace substantiating the vulnerability.",
    )
