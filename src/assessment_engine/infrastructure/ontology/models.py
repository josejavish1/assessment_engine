"""Authoritative Pydantic domain models for ontology and normative benchmarks."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

CanonicalControlId = Annotated[
    str,
    StringConstraints(pattern=r"^CTRL-[A-Z0-9]+(-[A-Z0-9]+)+$", min_length=10, max_length=64),
]

FrameworkId = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z0-9_]+$", min_length=2, max_length=32),
]


class StrictBaseModel(BaseModel):
    """Base model enforcing zero-tolerance for extra fields, NaN/Inf, or implicit mutations."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        allow_inf_nan=False,
        str_strip_whitespace=True,
    )


class Polarity(str, Enum):
    """Evaluation directionality for key performance indicators."""

    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    TARGET_RANGE = "TARGET_RANGE"


class KpiDefinition(StrictBaseModel):
    """Technical metric definition mapped to canonical controls."""

    kpi_id: str = Field(..., pattern=r"^KPI-[A-Z0-9_-]+$")
    name_i18n_key: str = Field(
        ..., min_length=1, description="Pointer to translation catalog key, zero hardcoded text."
    )
    unit: str = Field(
        ...,
        min_length=1,
        description="Standardized measurement unit (e.g. 'percentage', 'minutes', 'hours').",
    )
    polarity: Polarity
    canonical_control_ids: tuple[CanonicalControlId, ...] = Field(
        ..., min_length=1, description="Every KPI must map to at least one canonical control."
    )

    @model_validator(mode="after")
    def verify_unique_control_references(self) -> KpiDefinition:
        """Disallow duplicate canonical control references within a single KPI."""
        if len(set(self.canonical_control_ids)) != len(self.canonical_control_ids):
            raise ValueError(
                f"KPI '{self.kpi_id}' contains duplicate canonical_control_ids."
            )
        return self


class PillarDefinition(StrictBaseModel):
    """Architectural domain group aggregating technical KPIs."""

    pillar_id: str = Field(..., pattern=r"^PIL-[A-Z0-9_-]+$")
    name_i18n_key: str = Field(..., min_length=1)
    weight: float = Field(..., gt=0.0, le=1.0)
    kpis: tuple[KpiDefinition, ...] = Field(..., min_length=1)


class TowerDefinition(StrictBaseModel):
    """Authoritative technical tower catalog."""

    tower_id: str = Field(..., pattern=r"^T[0-9]+_[A-Z0-9_]+$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    name_i18n_key: str = Field(..., min_length=1)
    pillars: tuple[PillarDefinition, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def verify_unique_pillar_and_kpi_ids(self) -> TowerDefinition:
        """Ensure no duplicate pillar IDs or KPI IDs exist within a single tower."""
        seen_pillars: set[str] = set()
        seen_kpis: set[str] = set()
        for pillar in self.pillars:
            if pillar.pillar_id in seen_pillars:
                raise ValueError(
                    f"Duplicate pillar_id '{pillar.pillar_id}' in tower '{self.tower_id}'."
                )
            seen_pillars.add(pillar.pillar_id)
            for kpi in pillar.kpis:
                if kpi.kpi_id in seen_kpis:
                    raise ValueError(
                        f"Duplicate kpi_id '{kpi.kpi_id}' in tower '{self.tower_id}'."
                    )
                seen_kpis.add(kpi.kpi_id)
        return self


class RegulatoryCitation(StrictBaseModel):
    """Binding reference to external compliance or standards framework."""

    framework_id: FrameworkId = Field(
        ..., description="e.g. DORA, ISO27001_2022, NIST_CSF_2, SOC2, HIPAA"
    )
    clause_id: str = Field(..., min_length=1, description="e.g. 'Article 11.2', 'A.8.15'")
    enforcement_level: Literal["MANDATORY", "ADVISORY", "BEST_PRACTICE"]
    evidence_requirement_i18n_key: str = Field(..., min_length=1)


class QuantitativeBenchmark(StrictBaseModel):
    """Actuarial quantitative target brackets for control evaluation."""

    tier_1_global_leader: float
    industry_median: float
    minimum_acceptable: float
    tolerance_delta: float = Field(default=0.0, ge=0.0)

    @model_validator(mode="after")
    def verify_monotonic_thresholds(self) -> QuantitativeBenchmark:
        """Ensure thresholds follow monotonic progression (ascending or descending)."""
        is_ascending = self.minimum_acceptable <= self.industry_median <= self.tier_1_global_leader
        is_descending = self.tier_1_global_leader <= self.industry_median <= self.minimum_acceptable
        if not (is_ascending or is_descending):
            raise ValueError(
                "QuantitativeBenchmark thresholds must be monotonically ordered "
                f"(got leader={self.tier_1_global_leader}, median={self.industry_median}, "
                f"min={self.minimum_acceptable})."
            )
        return self


class ControlBenchmarkMapping(StrictBaseModel):
    """Bipartite binding linking a canonical control to thresholds and regulations."""

    control_id: CanonicalControlId
    criticality_weight: float = Field(..., gt=0.0, le=1.0)
    quantitative_thresholds: QuantitativeBenchmark
    regulatory_citations: tuple[RegulatoryCitation, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def verify_unique_citations(self) -> ControlBenchmarkMapping:
        """Prevent duplicate regulatory clause citations within the same control mapping."""
        seen: set[tuple[str, str]] = set()
        for citation in self.regulatory_citations:
            key = (citation.framework_id, citation.clause_id)
            if key in seen:
                raise ValueError(
                    f"Duplicate citation ({citation.framework_id}, '{citation.clause_id}') "
                    f"in control '{self.control_id}'."
                )
            seen.add(key)
        return self


class OrganizationTier(str, Enum):
    """Target organizational scale archetype."""

    MID_MARKET = "MID_MARKET"
    ENTERPRISE = "ENTERPRISE"
    GLOBAL_TIER_1 = "GLOBAL_TIER_1"


class IndustryProfile(StrictBaseModel):
    """Industry vertical configuration defining benchmark thresholds and citations."""

    profile_id: str = Field(..., pattern=r"^PROF-[A-Z0-9_]+$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    industry_vertical: str = Field(
        ..., min_length=1, description="e.g. FINANCIAL_SERVICES, HEALTHCARE, SAAS, MANUFACTURING"
    )
    target_tier: OrganizationTier
    applicable_towers: tuple[str, ...] = Field(
        ..., min_length=1, description="Explicit list of Tower IDs applicable to this profile."
    )
    control_mappings: tuple[ControlBenchmarkMapping, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def verify_unique_applicable_towers(self) -> IndustryProfile:
        """Disallow duplicate tower IDs in applicable_towers list."""
        if len(set(self.applicable_towers)) != len(self.applicable_towers):
            raise ValueError(
                f"Profile '{self.profile_id}' contains duplicate entries in applicable_towers."
            )
        return self
