"""Canonical Presentation Data Transfer Objects (SR 11-7 Decoupled View Layer).

Provides frozen, immutable, and strictly validated read-models for presentation compilers.
Eliminates side-effects, in-place dictionary mutations, and shadow business engines in adapters.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field


class EpistemicState(StrEnum):
    """Rigorous epistemic classification of an assessed entity or metric."""

    EMPIRICAL_OBSERVED = "EMPIRICAL_OBSERVED"
    LATENT_INFERRED = "LATENT_INFERRED"
    UNASSESSED_OUT_OF_SCOPE = "UNASSESSED_OUT_OF_SCOPE"
    INSUFFICIENT_TELEMETRY = "INSUFFICIENT_TELEMETRY"


class OwnershipType(StrEnum):
    """Custody boundary for risk allocation and deduplication."""

    PRIMARY_CUSTODIAN = "PRIMARY_CUSTODIAN"
    TANGENTIAL_CONTRIBUTOR = "TANGENTIAL_CONTRIBUTOR"


class ProvenanceMetadataDTO(BaseModel):
    """Immutable provenance envelope tracking model version and calibration source."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_version: str = Field(default="2026.Q4.v2")
    calibration_source: str = Field(default="BayesianFairCopulaEngine_v2")
    epistemic_state: EpistemicState = Field(default=EpistemicState.EMPIRICAL_OBSERVED)
    assumptions_registry_id: str = Field(default="REG_CANONICAL_SSOT")


class PresentationFindingDTO(BaseModel):
    """Read-only finding model projecting pre-computed actuarial metrics to presentation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    finding_id: str
    node_id: str
    tower_id: str
    pillar_id: str
    pillar_name: str
    capability_name: str
    finding_narrative: str = Field(default="")
    business_risk_narrative: str = Field(default="")
    ownership_type: OwnershipType = Field(default=OwnershipType.PRIMARY_CUSTODIAN)
    primary_risk_ref: Optional[str] = Field(default=None)
    contributing_towers: Tuple[str, ...] = Field(default_factory=tuple)

    # Pre-computed CMMI maturity
    cmmi_score: Optional[float] = Field(default=None)
    target_cmmi_score: Optional[float] = Field(default=None)
    cmmi_band_label: str = Field(default="UNASSESSED")

    # Pre-computed Open FAIR canonical metrics (None if unquantified)
    tef_annual: Optional[float] = Field(default=None)
    vulnerability_prob: Optional[float] = Field(default=None)
    lef_annual: Optional[float] = Field(default=None)
    sle_mean: Optional[float] = Field(default=None)
    ale_expected: Optional[float] = Field(default=None)
    p90_var: Optional[float] = Field(default=None)
    max_probable_loss: Optional[float] = Field(default=None)
    rto_hours: Optional[float] = Field(default=None)
    toil_frequency_annual: Optional[float] = Field(default=None)
    risk_tier_label: str = Field(default="UNQUANTIFIED")

    # Formatted display representations
    ale_display: str = Field(default="UNQUANTIFIED")
    p90_display: str = Field(default="UNQUANTIFIED")
    sle_display: str = Field(default="UNQUANTIFIED")
    return_period_display: str = Field(default="N/A")

    provenance: ProvenanceMetadataDTO = Field(default_factory=ProvenanceMetadataDTO)


class PresentationPillarDTO(BaseModel):
    """Read-only pillar projection with pre-computed maturity score."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pillar_id: str
    pillar_name: str
    cmmi_score: Optional[float] = Field(default=None)
    cmmi_band_label: str = Field(default="UNASSESSED")
    status_color_token: str = Field(default="grey")
    findings: Tuple[PresentationFindingDTO, ...] = Field(default_factory=tuple)


class PresentationTowerDTO(BaseModel):
    """Read-only tower projection with pre-allocated Euler risk contributions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str
    tower_name: str
    currency_iso: str = Field(default="EUR")
    currency_symbol: str = Field(default="€")
    locale: str = Field(default="en")
    epistemic_state: EpistemicState = Field(default=EpistemicState.EMPIRICAL_OBSERVED)
    overall_cmmi_score: Optional[float] = Field(default=None)
    overall_cmmi_band: str = Field(default="UNASSESSED")
    status_color_token: str = Field(default="grey")

    standalone_ale: Optional[float] = Field(default=None)
    standalone_p90: Optional[float] = Field(default=None)
    standalone_max_loss: Optional[float] = Field(default=None)
    euler_net_ale: Optional[float] = Field(default=None)
    diversification_adjustment: Optional[float] = Field(default=None)
    portfolio_share_pct: Optional[float] = Field(default=None)

    pillars: Tuple[PresentationPillarDTO, ...] = Field(default_factory=tuple)
    all_findings: Tuple[PresentationFindingDTO, ...] = Field(default_factory=tuple)
    provenance: ProvenanceMetadataDTO = Field(default_factory=ProvenanceMetadataDTO)


class ExecutiveFinancialBridgeDTO(BaseModel):
    """Pre-computed ROI, TCO, and capital protection metrics (replaces build_global_report_payload math)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    epistemic_state: EpistemicState = Field(default=EpistemicState.INSUFFICIENT_TELEMETRY)
    annual_revenue: Optional[float] = Field(default=None)
    hourly_downtime_cost: Optional[float] = Field(default=None)
    finops_cash_waste_annual: Optional[float] = Field(default=None)
    operational_downtime_friction_annual: Optional[float] = Field(default=None)
    actuarial_tail_mitigated_min: Optional[float] = Field(default=None)
    actuarial_tail_mitigated_max: Optional[float] = Field(default=None)
    year_1_opex: Optional[float] = Field(default=None)
    total_capex: Optional[float] = Field(default=None)
    annual_value_protected: Optional[float] = Field(default=None)
    three_year_value_protected: Optional[float] = Field(default=None)
    payback_months: Optional[float] = Field(default=None)
    roi_ratio: Optional[float] = Field(default=None)
    provenance: ProvenanceMetadataDTO = Field(default_factory=ProvenanceMetadataDTO)


class PresentationPortfolioDTO(BaseModel):
    """Complete portfolio read-model supplying immutable data to Tomo 1 and Global Synthesis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    currency_iso: str = Field(default="EUR")
    currency_symbol: str = Field(default="€")
    locale: str = Field(default="en")
    corporate_ale: Optional[float] = Field(default=None)
    corporate_p90: Optional[float] = Field(default=None)
    corporate_max_loss: Optional[float] = Field(default=None)
    var_3y_expected: Optional[float] = Field(default=None)
    var_3y_stress: Optional[float] = Field(default=None)
    towers: Tuple[PresentationTowerDTO, ...] = Field(default_factory=tuple)
    financial_bridge: ExecutiveFinancialBridgeDTO = Field(default_factory=ExecutiveFinancialBridgeDTO)
    provenance: ProvenanceMetadataDTO = Field(default_factory=ProvenanceMetadataDTO)
