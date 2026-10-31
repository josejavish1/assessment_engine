"""Domain models and schemas for CEGAR Deliverable Synthesis (RFC-009).

Implements Pydantic v2 immutable contracts for candidate synthesis,
counterexample vectors, and formally verified enterprise deliverables.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
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

    synthesis_attempt: Annotated[int, Field(ge=1, le=10)]
    violations: list[CounterexampleViolation]

    @property
    def is_valid(self) -> bool:
        """Returns True if no counterexample violations exist."""
        return len(self.violations) == 0


def _safe_coerce_to_decimal(v: Any) -> Decimal:
    """Safely coerce numerical types to Decimal, rejecting booleans, NaN, and malformed strings."""
    if isinstance(v, bool):
        raise ValueError("Cannot coerce boolean to Decimal.")
    if isinstance(v, Decimal):
        if v.is_nan() or v.is_infinite():
            raise ValueError("Decimal NaN and Infinity are prohibited.")
        return v
    if isinstance(v, (int, float, str)):
        try:
            dec = Decimal(str(v))
            if dec.is_nan() or dec.is_infinite():
                raise ValueError("Decimal NaN and Infinity are prohibited.")
            return dec
        except (InvalidOperation, ValueError) as err:
            raise ValueError(f"Malformed numerical value '{v}' for Decimal conversion.") from err
    raise ValueError(f"Cannot coerce type {type(v)} to Decimal.")


class FinancialProjection(StrictDomainModel):
    """FAIR-compliant & FinOps financial allocation node."""

    currency_iso_4217: Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]
    capex_allocation: Annotated[Decimal, Field(ge=Decimal("0.00"))]
    opex_allocation: Annotated[Decimal, Field(ge=Decimal("0.00"))]
    total_cost_of_ownership: Annotated[Decimal, Field(ge=Decimal("0.00"))]
    risk_exposure_p10: Annotated[Decimal, Field(ge=Decimal("0.00"))]
    risk_exposure_p50: Annotated[Decimal, Field(ge=Decimal("0.00"))]
    risk_exposure_p90: Annotated[Decimal, Field(ge=Decimal("0.00"))]

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
    def coerce_decimal_field(cls, v: Any) -> Decimal:
        """Coerce raw strings or numerical types into exact Decimal."""
        return _safe_coerce_to_decimal(v)


class SimplexUtilityWeights(StrictDomainModel):
    """Weight assignment for the 3 Pareto optimization axes, structured without additionalProperties."""

    capital_efficiency: Annotated[float, Field(ge=0.0, le=1.0, description="Weight on capital efficiency [0.0, 1.0]")]
    operational_resilience: Annotated[float, Field(ge=0.0, le=1.0, description="Weight on operational resilience [0.0, 1.0]")]
    execution_velocity: Annotated[float, Field(ge=0.0, le=1.0, description="Weight on execution velocity [0.0, 1.0]")]

    def __getitem__(self, item: Any) -> float:
        key = item.value if isinstance(item, OptimizationAxis) else str(item).upper()
        if key == "CAPITAL_EFFICIENCY":
            return self.capital_efficiency
        if key == "OPERATIONAL_RESILIENCE":
            return self.operational_resilience
        if key == "EXECUTION_VELOCITY":
            return self.execution_velocity
        raise KeyError(item)

    def items(self) -> list[tuple[OptimizationAxis, float]]:
        return [
            (OptimizationAxis.CAPITAL_EFFICIENCY, self.capital_efficiency),
            (OptimizationAxis.OPERATIONAL_RESILIENCE, self.operational_resilience),
            (OptimizationAxis.EXECUTION_VELOCITY, self.execution_velocity),
        ]


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
    utility_weights: SimplexUtilityWeights

    @field_validator("utility_weights", mode="before")
    @classmethod
    def coerce_simplex_weights(cls, v: Any) -> SimplexUtilityWeights:
        """Coerce dictionary inputs to SimplexUtilityWeights while validating simplex invariants."""
        if isinstance(v, SimplexUtilityWeights):
            weights_obj = v
        elif isinstance(v, dict):
            ce = float(v.get(OptimizationAxis.CAPITAL_EFFICIENCY, v.get("CAPITAL_EFFICIENCY", v.get("capital_efficiency", 0.0))))
            op = float(v.get(OptimizationAxis.OPERATIONAL_RESILIENCE, v.get("OPERATIONAL_RESILIENCE", v.get("operational_resilience", 0.0))))
            ev = float(v.get(OptimizationAxis.EXECUTION_VELOCITY, v.get("EXECUTION_VELOCITY", v.get("execution_velocity", 0.0))))
            weights_obj = SimplexUtilityWeights(
                capital_efficiency=ce,
                operational_resilience=op,
                execution_velocity=ev,
            )
        else:
            raise ValueError(f"SIMPLEX_TYPE_ERR: Cannot coerce {type(v)} to SimplexUtilityWeights.")

        total = weights_obj.capital_efficiency + weights_obj.operational_resilience + weights_obj.execution_velocity
        if not math.isclose(total, 1.0, abs_tol=1e-4):
            raise ValueError(f"SIMPLEX_SUM_ERR: Utility weights must sum to 1.0 (Actual: {total:.6f}).")
        return weights_obj


class ExecutiveRoadmapPhase(StrictDomainModel):
    """Time-bounded execution milestone."""

    phase_index: Annotated[int, Field(ge=1, le=12)]
    phase_title: Annotated[str, Field(min_length=5, max_length=120)]
    duration_weeks: Annotated[int, Field(ge=1, le=260)]
    deliverable_artifacts: Annotated[list[str], Field(min_length=1)]
    allocated_budget: Annotated[Decimal, Field(ge=Decimal("0.00"))]
    evidence_citations: Annotated[list[str], Field(min_length=1)]

    @field_validator("allocated_budget", mode="before")
    @classmethod
    def coerce_budget_decimal(cls, v: Any) -> Decimal:
        """Coerce budget from raw JSON into exact Decimal."""
        return _safe_coerce_to_decimal(v)


class CandidateEnterpriseDeliverable(StrictDomainModel):
    """Syntactic Candidate Root for the CEGAR Synthesis Engine (Candidate A_0 / A_1).

    Instantiated safely from LLM Structured Outputs prior to formal semantic verification.
    Supports complete IETF BCP-47 language tags (e.g. zh-Hans-CN, es-419, en-US) and UN ISIC Rev.4.
    """

    bcp47_locale: Annotated[
        str,
        Field(
            pattern=r"^[a-z]{2,3}(-[A-Z][a-z]{3})?(-([A-Z]{2}|[0-9]{3}))?$",
            description="Complete IETF BCP-47 tag (e.g. en-US, zh-Hans-CN, es-419, ja-JP)",
        ),
    ]
    industry_isic_code: Annotated[
        str,
        Field(
            pattern=r"^[A-U]?[0-9]{2,4}$",
            description="UN ISIC Rev.4 Sector Code (e.g. C10, 6201, J62, K6419)",
        ),
    ]
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
