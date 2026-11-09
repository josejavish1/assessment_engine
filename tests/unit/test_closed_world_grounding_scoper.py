"""Unit tests for Phase 4: Closed-World Grounding and Domain-Isolated Executive Summary Directives.

Verifies:
1. Strict prohibition of ungrounded measurement instruments and manual paper procedures.
2. Domain-isolated executive summary scoping directives.
3. Injection of literal client questionnaire statements into KPI scoping prompts.
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
    """Pure domain test double implementing TaxonomyRegistryPort."""

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
def scoper() -> OntologicalPromptScoper:
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
    }

    fac_p1 = PillarOntologyProfile(
        pillar_id="D_FAC.P1",
        pillar_name="Electrical Power & Capacity",
        tower_id="D_FAC",
        domain_id="D_FAC",
        positive_lexicon={"power", "ups", "generator", "ats"},
        negative_exclusion_map={"D_CMP": {"simplivity", "esxi", "ram"}},
    )

    registry = InMemoryTaxonomyRegistry(
        domain_rules=domain_rules,
        pillar_profiles={"D_FAC.P1": fac_p1},
    )
    return OntologicalPromptScoper(registry)


def test_closed_world_grounding_directive_forbids_invented_tools(
    scoper: OntologicalPromptScoper,
) -> None:
    directive = scoper.build_closed_world_grounding_directive(
        client_name="Global Enterprise",
        domain_name="Core Datacenter Facilities",
    )

    assert "CLOSED-WORLD EPISTEMIC GROUNDING MANDATE" in directive
    assert "clamp meters" in directive
    assert "handheld thermal cameras" in directive
    assert "PROHIBITION OF INVENTED INSTRUMENTATION" in directive
    assert "PROHIBITION OF INVENTED MANUAL PROCEDURES" in directive
    assert "paper forms, handwritten signatures" in directive


def test_executive_summary_scoping_directive_isolates_primary_domain(
    scoper: OntologicalPromptScoper,
) -> None:
    directive = scoper.build_executive_summary_scoping_directive(
        tower_id="D_FAC",
        tower_name="Core Facilities & Power",
        domain_archetype="INFRASTRUCTURE_PHYSICAL",
    )

    assert "EXECUTIVE SUMMARY SCOPING & DOMAIN ISOLATION MANDATE" in directive
    assert "[INFRASTRUCTURE_PHYSICAL]" in directive
    assert "CROSS-DOMAIN DEPENDENCIES AS SECONDARY CONTEXT ONLY" in directive
    assert "strictly FORBIDDEN from making foreign domain issues the primary headline risk" in directive


def test_pillar_scoping_directive_injects_client_questionnaire_answers(
    scoper: OntologicalPromptScoper,
) -> None:
    tower_def: Dict[str, Any] = {
        "tower_id": "D_FAC",
        "tower_name": "Core Facilities & Power",
        "client_name": "Global Enterprise",
        "pillars": [
            {
                "pillar_id": "D_FAC.P1",
                "pillar_name": "Electrical Power & Capacity",
                "kpis": [
                    {
                        "kpi_id": "D_FAC.P1.K4",
                        "kpi_name": "Available Electrical Capacity Telemetry",
                        "description": "Continuous monitoring of load vs breaker thresholds.",
                    }
                ],
            }
        ],
    }

    questionnaire_answers = {
        "D_FAC.P1.K4": {
            "score": 1,
            "response_text": "Available power capacity is unknown and no branch monitoring exists.",
        }
    }

    directive = scoper.build_pillar_scoping_directive(
        tower_id="D_FAC",
        tower_definition=tower_def,
        questionnaire_answers=questionnaire_answers,
    )

    assert "D_FAC.P1.K4" in directive
    assert "Client Declared Score: 1/5" in directive
    assert 'Client Factual Statement: "Available power capacity is unknown and no branch monitoring exists."' in directive
    assert "CLOSED-WORLD EPISTEMIC GROUNDING MANDATE" in directive
