"""Domain schemas for Open FAIR conditional risk ontology and causal chain modeling."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, condecimal, confloat, model_validator


class RiskOwnershipType(str, Enum):
    PRIMARY_CUSTODIAN = "PRIMARY_CUSTODIAN"
    TANGENTIAL_CONTRIBUTOR = "TANGENTIAL_CONTRIBUTOR"


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
    single_loss_magnitude_base: condecimal(ge=Decimal("0.00")) = Field(
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
    hourly_operational_impact: Optional[condecimal(ge=Decimal("0.00"))] = Field(
        default=None,
        description="Hourly burn rate during partial or total business interruption.",
    )


class ConditionalLossEvent(BaseModel):
    """An end-to-end defensible risk scenario grounded in empirical Open FAIR physics."""

    event_id: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9_.\-]+$",
        description="Standardized risk identifier (e.g., RSK-01, RVS-05, RVS01, T1.R01).",
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
        ...,
        min_length=1,
        max_length=16,
        description="ISO 4217 Currency Code or currency symbol (e.g., EUR, USD, JPY, GBP, €, $).",
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
    ownership_type: RiskOwnershipType = Field(
        default=RiskOwnershipType.PRIMARY_CUSTODIAN,
        description="Defines whether this tower owns the financial loss or contributes tangentially."
    )
    primary_risk_ref: Optional[str] = Field(
        default=None,
        description="The canonical ID of the primary risk event if this is a tangential contributor (e.g., 'T1-R01')."
    )
    contributing_towers: List[str] = Field(
        default_factory=list,
        description="List of tower identifiers that tangentially contribute to this primary risk."
    )

    @model_validator(mode="after")
    def validate_cross_tower_topology(self) -> "ConditionalLossEvent":
        """Validate cross-tower relationship references against canonical topology."""
        clean_ref = (self.primary_risk_ref or "").strip()
        if not clean_ref:
            self.primary_risk_ref = None

        if self.ownership_type == RiskOwnershipType.TANGENTIAL_CONTRIBUTOR:
            if not self.primary_risk_ref:
                raise ValueError(
                    f"Ontological Violation in {self.event_id}: "
                    "TANGENTIAL_CONTRIBUTOR must explicitly define a valid 'primary_risk_ref'."
                )
            if self.contributing_towers:
                raise ValueError(
                    f"Ontological Violation in {self.event_id}: "
                    "TANGENTIAL_CONTRIBUTOR cannot declare 'contributing_towers'."
                )
        elif self.ownership_type == RiskOwnershipType.PRIMARY_CUSTODIAN:
            if self.primary_risk_ref is not None:
                raise ValueError(
                    f"Ontological Violation in {self.event_id}: "
                    "PRIMARY_CUSTODIAN cannot reference a 'primary_risk_ref'."
                )
        return self
