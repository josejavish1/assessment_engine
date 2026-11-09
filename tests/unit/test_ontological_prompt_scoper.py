"""Unit tests for OntologicalPromptScoper (Phase 6).

Verifies dynamic prompt compilation of official KPI rubrics, boundary directives,
round-robin foreign exclusion fairness, hierarchical sub-pillar IDs, and prompt sanitization
using a pure in-memory TaxonomyRegistryPort test double (zero infrastructure imports).
Strictly 100% Technical English and tenant-agnostic.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

import pytest

from assessment_engine.domain.ontology.models import (
    DomainTaxonomyRule,
    PillarOntologyProfile,
    TaxonomyRegistryPort,
)
from assessment_engine.domain.prompts.ontological_prompt_scoper import (
    OntologicalPromptScoper,
)


class InMemoryTaxonomyRegistry(TaxonomyRegistryPort):
    """Pure domain test double implementing TaxonomyRegistryPort without infrastructure dependencies."""

    def __init__(
        self,
        domain_rules: Mapping[str, DomainTaxonomyRule],
        pillar_profiles: Mapping[str, PillarOntologyProfile],
    ) -> None:
        self._domain_rules = dict(domain_rules)
        self._pillar_profiles = {k.upper(): v for k, v in pillar_profiles.items()}

    def get_profile(
        self, pillar_id: str, tower_id: Optional[str] = None
    ) -> Optional[PillarOntologyProfile]:
        norm_id = pillar_id.strip().upper()
        if norm_id in self._pillar_profiles:
            return self._pillar_profiles[norm_id]
        if tower_id:
            composite = f"{tower_id.strip().upper()}.{norm_id}"
            if composite in self._pillar_profiles:
                return self._pillar_profiles[composite]
        return None

    def get_domain_rule(self, domain_id: str) -> Optional[DomainTaxonomyRule]:
        return self._domain_rules.get(domain_id.strip().upper())

    def list_indexed_pillars(self) -> list[str]:
        return sorted(self._pillar_profiles.keys())


@pytest.fixture()
def sample_registry() -> TaxonomyRegistryPort:
    domain_rules = {
        "D_FAC": DomainTaxonomyRule(
            domain_id="D_FAC",
            name="Physical Facilities & Environmental Control",
            keywords=("datacenter", "cooling", "ups", "bms", "vesda", "suppression"),
        ),
        "D_CMP": DomainTaxonomyRule(
            domain_id="D_CMP",
            name="Compute Virtualization & Capacity",
            keywords=("simplivity", "esxi", "vmware", "ram", "vcpu"),
        ),
        "D_NET": DomainTaxonomyRule(
            domain_id="D_NET",
            name="Enterprise Networking & Routing",
            keywords=("bgp", "ospf", "vlan", "sdwan", "firewall"),
        ),
    }

    fac_p4 = PillarOntologyProfile(
        pillar_id="D_FAC.P4",
        pillar_name="Fire Suppression & Environmental Telemetry",
        tower_id="D_FAC",
        domain_id="D_FAC",
        positive_lexicon={"fire", "suppression", "vesda", "smoke", "bms", "leak"},
        negative_exclusion_map={
            "D_CMP": {"simplivity", "esxi", "vmware", "ram", "vcpu"},
            "D_NET": {"bgp", "ospf", "vlan", "sdwan", "firewall"},
        },
    )

    fac_sub_pillar = PillarOntologyProfile(
        pillar_id="D_FAC.P4.1",
        pillar_name="Aspiration Smoke Sensors",
        tower_id="D_FAC",
        domain_id="D_FAC",
        positive_lexicon={"vesda", "aspiration"},
        negative_exclusion_map={"D_CMP": {"esxi"}},
    )

    return InMemoryTaxonomyRegistry(
        domain_rules=domain_rules,
        pillar_profiles={
            "D_FAC.P4": fac_p4,
            "D_FAC.P4.1": fac_sub_pillar,
        },
    )


def test_prompt_scoper_compiles_kpi_rubrics_and_exclusions(
    sample_registry: TaxonomyRegistryPort,
) -> None:
    scoper = OntologicalPromptScoper(sample_registry)

    fac_tower_def: Dict[str, Any] = {
        "tower_id": "D_FAC",
        "pillars": [
            {
                "pillar_id": "P4",
                "pillar_name": "Fire Suppression & Environmental Telemetry",
                "kpis": [
                    {
                        "kpi_id": "K1",
                        "kpi_name": "Early Smoke Detection Coverage",
                        "description": "VESDA aspiration systems\nacross critical rooms.",
                    },
                    {
                        "kpi_id": "K2",
                        "kpi_name": "Automatic Gas Extinguishing",
                        "description": "Clean agent discharge testing and maintenance.",
                    },
                ],
            },
            {
                "pillar_id": "P4.1",  # Hierarchical sub-pillar ID with dot
                "pillar_name": "Aspiration Smoke Sensors",
                "kpis": ["K1.1: Sub-floor laser chamber calibration"],
            },
        ],
    }

    directive = scoper.build_pillar_scoping_directive("D_FAC", fac_tower_def)

    assert "MANDATORY ONTOLOGICAL BOUNDARIES" in directive
    assert "PILLAR [D_FAC.P4]: Fire Suppression & Environmental Telemetry" in directive
    assert "PILLAR [D_FAC.P4.1]: Aspiration Smoke Sensors" in directive
    assert "K1: Early Smoke Detection Coverage (VESDA aspiration systems across critical rooms.)" in directive
    assert "K2: Automatic Gas Extinguishing" in directive
    assert "FORBIDDEN CONCEPTS" in directive
    assert "'simplivity'" in directive or "'esxi'" in directive
    assert "ISOLATION INVARIANT" in directive
    assert "foreign domains (D_CMP, D_NET)" in directive


def test_prompt_scoper_round_robin_prevents_alphabetical_starvation(
    sample_registry: TaxonomyRegistryPort,
) -> None:
    scoper = OntologicalPromptScoper(sample_registry)

    fac_tower_def: Dict[str, Any] = {
        "tower_id": "D_FAC",
        "pillars": [{"pillar_id": "D_FAC.P4", "pillar_name": "Fire Suppression"}],
    }

    directive = scoper.build_pillar_scoping_directive(
        "D_FAC", fac_tower_def, max_forbidden_terms_per_pillar=4
    )

    assert "FORBIDDEN CONCEPTS" in directive
    assert any(term in directive for term in ("'simplivity'", "'esxi'", "'ram'", "'vcpu'", "'vmware'"))
    assert any(term in directive for term in ("'bgp'", "'firewall'", "'ospf'", "'sdwan'", "'vlan'"))


def test_prompt_scoper_handles_empty_definitions(
    sample_registry: TaxonomyRegistryPort,
) -> None:
    scoper = OntologicalPromptScoper(sample_registry)
    assert scoper.build_pillar_scoping_directive("D_FAC", {}) == ""
    assert scoper.build_pillar_scoping_directive("D_FAC", {"pillars": []}) == ""
    assert scoper.build_pillar_scoping_directive("D_FAC", {"pillars": [{}]}) == ""
