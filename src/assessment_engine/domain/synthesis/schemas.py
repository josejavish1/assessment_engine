"""Domain models and schemas for CEGAR Deliverable Synthesis (RFC-009).

Implements Pydantic v2 immutable contracts for candidate synthesis,
counterexample vectors, and formally verified enterprise deliverables.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
import math
from typing import Annotated, Any
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class StrictDomainModel(BaseModel):
    """Base immutable domain model enforcing zero schema drift."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        validate_default=True,
        ser_json_inf_nan="constants",
    )


class OptimizationAxis(str, Enum):
    """Orthogonal strategic vectors spanning the Pareto Frontier."""

    CAPITAL_EFFICIENCY = "CAPITAL_EFFICIENCY"
    OPERATIONAL_RESILIENCE = "OPERATIONAL_RESILIENCE"
    EXECUTION_VELOCITY = "EXECUTION_VELOCITY"


class SeverityLevel(str, Enum):
    """Severity classification of formal counterexample defects."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


class CounterexampleViolation(StrictDomainModel):
    """Formal mathematical, structural, or epistemic defect isolated by the Oracle."""

    rule_id: Annotated[str, Field(min_length=3, max_length=64, pattern=r"^[A-Z0-9_]+$")]
    json_path: Annotated[str, Field(min_length=1, description="RFC 6901 JSON Pointer or JSONPath.")]
    severity: SeverityLevel
    expected_invariant: Annotated[str, Field(min_length=5)]
    actual_value: Annotated[str, Field(min_length=1)]
    remediation_directive: Annotated[str, Field(min_length=10, description="Deterministic instruction.")]


class CounterexampleVector(StrictDomainModel):
    """Aggregate payload of all formal violations for a single synthesis pass."""

    synthesis_attempt: Annotated[int, Field(ge=1, le=2)]
    violations: list[CounterexampleViolation]

    @property
    def is_valid(self) -> bool:
        """Returns True if no counterexample violations exist."""
        return len(self.violations) == 0


class FinancialProjection(StrictDomainModel):
    """FAIR-compliant & FinOps financial allocation node."""

    currency_iso_4217: Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]
    capex_allocation: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)]
    opex_allocation: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)]
    total_cost_of_ownership: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)]
    risk_exposure_p10: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)]
    risk_exposure_p50: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)]
    risk_exposure_p90: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)]

    @field_validator(
        "capex_allocation",
        "opex_allocation",
        "total_cost_of_ownership",
        "risk_exposure_p10",
        "risk_exposure_p50",
        "risk_exposure_p90",
        mode="before",
    )
    @classmethod
    def coerce_decimal(cls, v: Any) -> Decimal:
        """Coerce raw strings or numerical types from LLM JSON Structured Outputs into exact Decimal."""
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        raise ValueError(f"Cannot coerce {type(v)} to Decimal.")


class StrategicOption(StrictDomainModel):
    """Represents a single vertex on the Pareto Frontier."""

    option_id: Annotated[str, Field(pattern=r"^OPT-[A-Z0-9]{4,8}$")]
    primary_axis: OptimizationAxis
    strategy_designation: Annotated[str, Field(min_length=10, max_length=180)]
    architectural_rationale: Annotated[str, Field(min_length=150, max_length=4000)]
    sacrificed_dimension_analysis: Annotated[
        str,
        Field(min_length=100, max_length=2000, description="Explicit engineering trade-off."),
    ]
    financials: FinancialProjection
    supporting_evidence_ids: Annotated[
        list[str],
        Field(min_length=1, description="Foreign keys mapping to the input Evidence Registry."),
    ]
    utility_weights: dict[OptimizationAxis, float]

    @field_validator("utility_weights")
    @classmethod
    def validate_simplex_weights(cls, v: dict[OptimizationAxis, float]) -> dict[OptimizationAxis, float]:
        """Verify weights cover all simplex axes and are bounded within [0.0, 1.0]."""
        required_axes = set(OptimizationAxis)
        if set(v.keys()) != required_axes:
            raise ValueError(f"SIMPLEX_AXIS_ERR: Must contain exactly {required_axes}.")
        for axis, weight in v.items():
            if math.isnan(weight) or math.isinf(weight) or not (0.0 <= weight <= 1.0):
                raise ValueError(f"SIMPLEX_BOUND_ERR: Weight for {axis} ({weight}) outside [0.0, 1.0].")
        total = sum(v.values())
        if not math.isclose(total, 1.0, abs_tol=1e-4):
            raise ValueError(f"SIMPLEX_SUM_ERR: Utility weights must sum to 1.0 (Actual: {total:.6f}).")
        return v


class ExecutiveRoadmapPhase(StrictDomainModel):
    """Time-bounded execution milestone."""

    phase_index: Annotated[int, Field(ge=1, le=12)]
    phase_title: Annotated[str, Field(min_length=5, max_length=120)]
    duration_weeks: Annotated[int, Field(ge=1, le=260)]
    deliverable_artifacts: Annotated[list[str], Field(min_length=1)]
    allocated_budget: Annotated[Decimal, Field(ge=Decimal("0.00"), decimal_places=2)]
    evidence_citations: Annotated[list[str], Field(min_length=1)]

    @field_validator("allocated_budget", mode="before")
    @classmethod
    def coerce_budget_decimal(cls, v: Any) -> Decimal:
        """Coerce budget from raw JSON into exact Decimal."""
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        raise ValueError(f"Cannot coerce {type(v)} to Decimal.")


class CandidateEnterpriseDeliverable(StrictDomainModel):
    """Syntactic Candidate Root for the CEGAR Synthesis Engine (Candidate A_0 / A_1).

    Instantiated safely from LLM Structured Outputs prior to formal semantic verification.
    """

    bcp47_locale: Annotated[str, Field(pattern=r"^[a-z]{2,3}(-[A-Z]{2,3})?$")]
    industry_isic_code: Annotated[str, Field(min_length=1, max_length=10, description="UN ISIC Rev.4 Code")]
    executive_thesis: Annotated[str, Field(min_length=250, max_length=5000)]
    pareto_frontier: Annotated[
        list[StrategicOption],
        Field(min_length=3, max_length=3, description="Exactly 3 orthogonal options spanning Pareto frontier."),
    ]
    selected_equilibrium_option_id: Annotated[str, Field(pattern=r"^OPT-[A-Z0-9]{4,8}$")]
    equilibrium_justification: Annotated[str, Field(min_length=200, max_length=4000)]
    execution_roadmap: Annotated[list[ExecutiveRoadmapPhase], Field(min_length=1, max_length=12)]


class VerifiedEnterpriseDeliverable(CandidateEnterpriseDeliverable):
    """Certified Root Aggregate for the CEGAR Synthesis Engine.

    Emitted if and only if the Deterministic Verification Oracle confirms zero formal violations.
    """

    pass
