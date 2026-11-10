# golden-path: ignore
"""Typed and versioned parameter lineage contracts for actuarial inputs and outputs (SR 11-7)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ParameterSourceType(StrEnum):
    """Controlled taxonomy for actuarial input parameter sources."""

    ASSESSMENT_PAYLOAD = "ASSESSMENT_PAYLOAD"
    QUESTIONNAIRE = "QUESTIONNAIRE"
    INTERVIEW_TRANSCRIPT = "INTERVIEW_TRANSCRIPT"
    ANNUAL_ACCOUNTS = "ANNUAL_ACCOUNTS"
    EXTERNAL_BENCHMARK = "EXTERNAL_BENCHMARK"
    MODEL_DEFAULT = "MODEL_DEFAULT"
    DERIVED = "DERIVED"
    CLIENT_CONFIRMED = "CLIENT_CONFIRMED"
    UNSPECIFIED = "UNSPECIFIED"


class ParameterConfidenceLevel(StrEnum):
    """Empirical confidence tier in an input parameter."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNASSESSED = "UNASSESSED"


class ParameterValidationStatus(StrEnum):
    """Client and audit confirmation status."""

    UNCONFIRMED = "UNCONFIRMED"
    CLIENT_CONFIRMED = "CLIENT_CONFIRMED"
    CLIENT_OVERRIDDEN = "CLIENT_OVERRIDDEN"


class ParameterProvenanceRecord(BaseModel):
    """Auditable provenance record tracking estimation, overrides, and sources for an actuarial input."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    estimated_value: Any = Field(..., description="Original algorithmic or default estimate")
    effective_value: Any = Field(..., description="Value actually supplied to the simulation kernel")
    unit: str = Field(..., description="Explicit physical or financial unit (e.g., 'hours', 'EUR/h', 'dimensionless')")
    source_type: ParameterSourceType = Field(..., description="Controlled taxonomy source category")
    source_reference: Optional[str] = Field(default=None, description="Verifiable citation, locator, or upstream variable name")
    estimation_method: str = Field(..., description="Specific formula, lookup, or direct-input description")
    confidence: ParameterConfidenceLevel = Field(default=ParameterConfidenceLevel.UNASSESSED)
    validation_status: ParameterValidationStatus = Field(default=ParameterValidationStatus.UNCONFIRMED)
    client_override: bool = Field(default=False, description="True if effective_value diverges from estimated_value due to explicit client instruction")


class DissonanceLineageRecord(BaseModel):
    """Auditable lineage contract for epistemic dissonance adjustments."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: str
    finding_id: str
    claimed_maturity: float = Field(..., ge=1.0, le=5.0)
    empirical_reality_maturity: float = Field(..., ge=1.0, le=5.0)
    dissonance_weight: float = Field(..., ge=0.0, le=1.0)
    transcript_evidence_quote: str = Field(default="")
    impact_vector: str = Field(default="BOTH")


class ActuarialFindingInputs(BaseModel):
    """Complete collection of audited inputs for an individual finding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cmmi_maturity: ParameterProvenanceRecord
    zone_id: ParameterProvenanceRecord
    hourly_burn_rate: ParameterProvenanceRecord
    max_annual_outage_hours: ParameterProvenanceRecord
    secondary_loss_retention_factor: ParameterProvenanceRecord
    catastrophic_recovery_ceiling_hours: ParameterProvenanceRecord
    emergency_replacement_ratio: ParameterProvenanceRecord
    tef_pert_min: ParameterProvenanceRecord
    tef_pert_mode: ParameterProvenanceRecord
    tef_pert_max: ParameterProvenanceRecord
    rto_hours_min: ParameterProvenanceRecord
    rto_hours_mode: ParameterProvenanceRecord
    rto_hours_max: ParameterProvenanceRecord
    secondary_loss_mean: ParameterProvenanceRecord
    is_spof: ParameterProvenanceRecord
    shared_dependence_factor: ParameterProvenanceRecord
    blast_radius_alpha: ParameterProvenanceRecord
    catastrophic_rto_hours: ParameterProvenanceRecord
    direct_replacement_cost: ParameterProvenanceRecord
    audit_k_failures: ParameterProvenanceRecord
    audit_n_trials: ParameterProvenanceRecord
    dissonance_record: Optional[DissonanceLineageRecord] = Field(default=None)


class ActuarialFindingOutputs(BaseModel):
    """Monte Carlo copula simulation outputs for an individual finding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mean_vuln: float
    mean_lef: float
    mean_sle: float
    standalone_ale: float
    portfolio_allocated_ale: float
    var_90: float
    cvar_90: float
    var_95: float
    var_99: float
    cvar_99: float
    worst_crisis_event: float
    worst_crisis_rto_hours: float


class ActuarialInputVector(BaseModel):
    """Complete, immutable parameter lineage record binding inputs, outputs, and identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = Field(default="2.0.0")
    model_version: str = Field(default="2026.Q1.v1")
    finding_id: str
    tower_id: str
    currency_code: str
    inputs: ActuarialFindingInputs
    outputs: ActuarialFindingOutputs
