# golden-path: ignore
"""Typed and versioned parameter lineage contracts for actuarial inputs and outputs (SR 11-7)."""

from __future__ import annotations

from enum import StrEnum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ScalarValue = Union[float, int, str, bool]


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

    estimated_value: ScalarValue = Field(..., description="Original algorithmic or default estimate")
    effective_value: ScalarValue = Field(..., description="Value actually supplied to the simulation kernel")
    unit: str = Field(..., description="Explicit physical or financial unit (e.g., 'hours', 'EUR/h', 'dimensionless')")
    source_type: ParameterSourceType = Field(default=ParameterSourceType.UNSPECIFIED, description="Controlled taxonomy source category")
    source_reference: Optional[str] = Field(default=None, description="Verifiable citation, locator, or upstream variable name")
    estimation_method: str = Field(..., description="Specific formula, lookup, or direct-input description")
    confidence: ParameterConfidenceLevel = Field(default=ParameterConfidenceLevel.UNASSESSED)
    validation_status: ParameterValidationStatus = Field(default=ParameterValidationStatus.UNCONFIRMED)
    client_override: bool = Field(default=False, description="True if effective_value diverges from estimated_value due to explicit client instruction")

    @model_validator(mode="after")
    def validate_provenance_invariants(self) -> ParameterProvenanceRecord:
        # Invariant 1: client_override == false requires estimated_value == effective_value
        if not self.client_override and self.estimated_value != self.effective_value:
            raise ValueError(
                f"Lineage Invariant Violation: client_override is False but estimated_value ({self.estimated_value}) "
                f"!= effective_value ({self.effective_value})"
            )
        # Invariant 2: CLIENT_OVERRIDDEN requires client_override == true
        if self.validation_status == ParameterValidationStatus.CLIENT_OVERRIDDEN and not self.client_override:
            raise ValueError(
                "Lineage Invariant Violation: validation_status is CLIENT_OVERRIDDEN but client_override is False"
            )
        # Invariant 3: A client-confirmed source requires a compatible validation status
        if self.source_type == ParameterSourceType.CLIENT_CONFIRMED and self.validation_status not in (
            ParameterValidationStatus.CLIENT_CONFIRMED,
            ParameterValidationStatus.CLIENT_OVERRIDDEN,
        ):
            raise ValueError(
                f"Lineage Invariant Violation: source_type is CLIENT_CONFIRMED but validation_status is {self.validation_status}"
            )
        # Invariant 4: ANNUAL_ACCOUNTS, EXTERNAL_BENCHMARK, and CLIENT_CONFIRMED require a non-empty source reference
        if self.source_type in (
            ParameterSourceType.ANNUAL_ACCOUNTS,
            ParameterSourceType.EXTERNAL_BENCHMARK,
            ParameterSourceType.CLIENT_CONFIRMED,
        ):
            if not self.source_reference or not str(self.source_reference).strip():
                raise ValueError(
                    f"Lineage Invariant Violation: source_type {self.source_type} requires a non-empty source_reference"
                )
        # Invariant 5: MODEL_DEFAULT must not be marked client-confirmed
        if self.source_type == ParameterSourceType.MODEL_DEFAULT and self.validation_status == ParameterValidationStatus.CLIENT_CONFIRMED:
            raise ValueError(
                "Lineage Invariant Violation: MODEL_DEFAULT parameter cannot be marked CLIENT_CONFIRMED without explicit override"
            )
        return self


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

    @model_validator(mode="after")
    def validate_input_bounds_and_pert(self) -> ActuarialFindingInputs:
        # Invariant 7: PERT values must satisfy min <= mode <= max
        tef_min = float(self.tef_pert_min.effective_value)
        tef_mode = float(self.tef_pert_mode.effective_value)
        tef_max = float(self.tef_pert_max.effective_value)
        if not (tef_min <= tef_mode <= tef_max):
            raise ValueError(f"PERT Invariant Violation for TEF: expected {tef_min} <= {tef_mode} <= {tef_max}")

        rto_min = float(self.rto_hours_min.effective_value)
        rto_mode = float(self.rto_hours_mode.effective_value)
        rto_max = float(self.rto_hours_max.effective_value)
        if not (rto_min <= rto_mode <= rto_max):
            raise ValueError(f"PERT Invariant Violation for RTO: expected {rto_min} <= {rto_mode} <= {rto_max}")

        # Invariant 8: Strict CMMI bounds [1.0, 5.0]
        cmmi = float(self.cmmi_maturity.effective_value)
        if not (0.99 <= cmmi <= 5.01):
            raise ValueError(f"Domain Bounds Violation: CMMI maturity must be in [1.0, 5.0], got {cmmi}")

        alpha = float(self.blast_radius_alpha.effective_value)
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"Domain Bounds Violation: blast_radius_alpha must be in [0.0, 1.0], got {alpha}")

        rho = float(self.shared_dependence_factor.effective_value)
        if not (0.0 <= rho <= 1.0):
            raise ValueError(f"Domain Bounds Violation: shared_dependence_factor must be in [0.0, 1.0], got {rho}")

        return self


class ActuarialParameterCorrection(BaseModel):
    """Controlled contract for explicit client or analyst parameter corrections."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter_name: str
    original_estimated_value: ScalarValue
    corrected_effective_value: ScalarValue
    user_provided_source: str
    review_identifier: str = Field(default="UNSPECIFIED_REVIEW")
    validation_status: ParameterValidationStatus = Field(default=ParameterValidationStatus.CLIENT_OVERRIDDEN)
    recalculation_occurred: bool = Field(default=True)

    @field_validator("parameter_name")
    def validate_permitted_parameter(cls, v: str) -> str:
        permitted = {
            "cmmi_maturity", "tef_pert_min", "tef_pert_mode", "tef_pert_max",
            "rto_hours_min", "rto_hours_mode", "rto_hours_max",
            "hourly_burn_rate", "secondary_loss_mean", "blast_radius_alpha",
            "direct_replacement_cost", "is_spof"
        }
        if v not in permitted:
            raise ValueError(f"Parameter '{v}' is not in permitted actuarial correction whitelist: {sorted(permitted)}")
        return v


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
