"""Ontological Domain Models and Data Contracts.

Defines immutable data classes, thresholds, and enumerations for taxonomy indexation,
cross-pillar boundary validation, and KPI-causal maturity matrix compilation.
Strictly 100% Technical English, vertical-agnostic, and multi-tenant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Protocol, Set, Tuple


class ValidationVerdict(str, Enum):
    """Categorical verdict returned by the semantic gatekeeper."""

    VALID_IN_DOMAIN = "VALID_IN_DOMAIN"
    QUARANTINED_FOREIGN_DOMAIN = "QUARANTINED_FOREIGN_DOMAIN"
    QUARANTINED_POLARITY_MISMATCH = "QUARANTINED_POLARITY_MISMATCH"
    INSUFFICIENT_SIGNAL = "INSUFFICIENT_SIGNAL"


class FindingPolarity(str, Enum):
    """Polarity classification for an architectural finding or capability."""

    STRENGTH = "STRENGTH"
    BREACH = "BREACH"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class GatekeeperThresholds:
    """Configurable mathematical parameters governing semantic boundary enforcement."""

    min_token_length: int = 3
    allowed_short_acronyms: FrozenSet[str] = field(
        default_factory=lambda: frozenset(
            {"ai", "ml", "db", "vm", "ip", "dr", "ha", "ot", "it", "io", "os", "dc", "ram", "cpu", "san", "nas", "bms", "ups", "pdu", "iam", "pam", "soc"}
        )
    )
    foreign_dominance_ratio_threshold: float = 0.5
    hard_quarantine_foreign_hit_count: int = 2
    smoothing_epsilon: float = 1e-4
    default_valid_confidence: float = 1.0
    fallback_neutral_confidence: float = 0.5


@dataclass(frozen=True)
class EvaluatedKPI:
    """Represents a single evaluated Key Performance Indicator with mathematical metrics."""

    kpi_id: str
    pillar_id: str
    name: str
    score: float
    weight: float = 1.0
    observed_value: Optional[str] = None
    target_benchmark: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class DomainTaxonomyRule:
    """Taxonomic specification for an architectural domain category."""

    domain_id: str
    name: str
    categories: Tuple[str, ...] = field(default_factory=tuple)
    keywords: Tuple[str, ...] = field(default_factory=tuple)
    canonical_entities: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PillarOntologyProfile:
    """Resolved runtime profile for an individual pillar containing positive and exclusionary lexicons."""

    pillar_id: str
    pillar_name: str
    tower_id: str
    domain_id: str
    positive_lexicon: Set[str] = field(default_factory=set)
    negative_exclusion_map: Dict[str, Set[str]] = field(default_factory=dict)


class TaxonomyRegistryPort(Protocol):
    """Port interface for querying pillar ontological profiles (Dependency Inversion)."""

    def get_profile(
        self,
        pillar_id: str,
        tower_id: Optional[str] = None,
    ) -> Optional[PillarOntologyProfile]:
        """Retrieves a pillar profile by canonical ID or contextual (tower_id, short_id)."""
        ...

    def get_domain_rule(self, domain_id: str) -> Optional[DomainTaxonomyRule]:
        """Retrieves a domain taxonomy rule by domain identifier."""
        ...

    def list_indexed_pillars(self) -> List[str]:
        """Returns sorted list of all unique canonical pillar identifiers indexed."""
        ...


@dataclass(frozen=True)
class OntologicalValidationResult:
    """Audit result returned when validating candidate narrative text against a pillar's domain boundary."""

    verdict: ValidationVerdict
    target_pillar_id: str
    detected_foreign_domain_id: Optional[str] = None
    positive_affinity_hits: List[str] = field(default_factory=list)
    negative_exclusion_hits: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    reason: str = ""

    @property
    def detected_foreign_pillar_id(self) -> Optional[str]:
        """Backwards-compatible alias for detected_foreign_domain_id."""
        return self.detected_foreign_domain_id


@dataclass(frozen=True)
class MaturityMatrixRow:
    """Section 3.1 table row representing a single pillar's KPI-causal maturity and justification."""

    pillar_id: str
    pillar_name: str
    maturity_score: float
    maturity_level_label: str
    primary_strength: str
    critical_breach: str
    justification: str
    supporting_strength_kpi_ids: List[str] = field(default_factory=list)
    supporting_breach_kpi_ids: List[str] = field(default_factory=list)
    quarantined_findings_count: int = 0
