"""Authoritative Domain Ontology and Bipartite RAGE Gatekeeper Module (RFC-024).

Provides bijective mapping between Technical Towers and Regulatory/Industry Profiles,
ensuring boot-time formal verification of evaluation coverage.
"""

from __future__ import annotations

from assessment_engine.infrastructure.ontology.exceptions import (
    OntologyError,
    OntologyIntegrityError,
)
from assessment_engine.infrastructure.ontology.models import (
    CanonicalControlId,
    ControlBenchmarkMapping,
    FrameworkId,
    IndustryProfile,
    KpiDefinition,
    OrganizationTier,
    PillarDefinition,
    Polarity,
    QuantitativeBenchmark,
    RegulatoryCitation,
    TowerDefinition,
)
from assessment_engine.infrastructure.ontology.registry import OntologyRegistry

__all__ = [
    "CanonicalControlId",
    "ControlBenchmarkMapping",
    "FrameworkId",
    "IndustryProfile",
    "KpiDefinition",
    "OntologyError",
    "OntologyIntegrityError",
    "OntologyRegistry",
    "OrganizationTier",
    "PillarDefinition",
    "Polarity",
    "QuantitativeBenchmark",
    "RegulatoryCitation",
    "TowerDefinition",
]
