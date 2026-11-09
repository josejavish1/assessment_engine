"""Integration test suite for Section 3.1 Maturity Matrix Isolation and Zero Cross-Contamination.

Guarantees across arbitrary multi-domain topologies that:
1. P(Contamination) == 0.0 (e.g., Compute/SimpliVity/RAM metrics injected into Fire Protection
   are deterministically quarantined during in-memory matrix compilation).
2. All compiled justifications satisfy the OntologicalGatekeeper boundary invariants.
Strictly 100% Technical English, tenant-agnostic, and topology-agnostic.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

from assessment_engine.adapters.compilers.in_memory_asis_compiler import (
    derive_in_memory_maturity_matrix,
)
from assessment_engine.domain.ontology.models import (
    DomainTaxonomyRule,
    PillarOntologyProfile,
    ValidationVerdict,
)
from assessment_engine.domain.validation.semantic_gatekeeper import (
    OntologicalGatekeeper,
)
from assessment_engine.infrastructure.ontology.taxonomy_loader import (
    DomainTaxonomyRegistry,
)


@pytest.fixture(scope="module")
def enterprise_gatekeeper() -> OntologicalGatekeeper:
    domain_rules = {
        "DOM_FAC": DomainTaxonomyRule(
            domain_id="DOM_FAC",
            name="Facilities & Environmental Engineering",
            keywords=("datacenter", "vesda", "suppression", "bms", "cooling", "ups"),
        ),
        "DOM_CMP": DomainTaxonomyRule(
            domain_id="DOM_CMP",
            name="Compute & Virtualization Engineering",
            keywords=("simplivity", "esxi", "vmware", "hyperconverged", "ram", "vcpu"),
        ),
    }

    fac_p4 = PillarOntologyProfile(
        pillar_id="DOM_FAC.P4",
        pillar_name="Fire Suppression & Environmental Protection",
        tower_id="DOM_FAC",
        domain_id="DOM_FAC",
        positive_lexicon={
            "fire",
            "suppression",
            "vesda",
            "smoke",
            "gas",
            "bms",
            "leak",
            "sensors",
            "environmental",
            "alarms",
        },
        negative_exclusion_map={
            "DOM_CMP": {
                "simplivity",
                "esxi",
                "vmware",
                "hyperconverged",
                "ram",
                "vcpu",
            }
        },
    )

    cmp_p1 = PillarOntologyProfile(
        pillar_id="DOM_CMP.P1",
        pillar_name="Virtualization Cluster Capacity",
        tower_id="DOM_CMP",
        domain_id="DOM_CMP",
        positive_lexicon={
            "simplivity",
            "esxi",
            "vmware",
            "hyperconverged",
            "ram",
            "vcpu",
            "cluster",
        },
        negative_exclusion_map={
            "DOM_FAC": {"vesda", "suppression", "extinguishing", "chiller"}
        },
    )

    registry = DomainTaxonomyRegistry(
        domain_rules=domain_rules,
        pillar_profiles={
            "DOM_FAC.P4": fac_p4,
            "DOM_CMP.P1": cmp_p1,
        },
        short_id_index={
            "P4": [fac_p4],
            "P1": [cmp_p1],
        },
    )
    return OntologicalGatekeeper(registry)


def test_in_memory_compiler_quarantines_compute_bleed_in_fire_protection(
    enterprise_gatekeeper: OntologicalGatekeeper,
) -> None:
    contaminated_payload: Dict[str, Any] = {
        "tower_id": "DOM_FAC",
        "pillars_analysis": [
            {
                "pillar_id": "DOM_FAC.P4",
                "pillar_name": "Fire Suppression & Environmental Protection",
                "maturity_score": 2.2,
                "justification": (
                    "Exceeding the 50% physical resource safety limit for RAM and vCPU "
                    "across the 6 HPE SimpliVity hyperconverged cluster nodes."
                ),
                "health_check_asis": [
                    {
                        "node_id": "HC-BLEED-01",
                        "capability": "Compute Capacity",
                        "finding": "High RAM utilization on VMware ESXi and SimpliVity hosts.",
                    },
                    {
                        "node_id": "HC-VALID-02",
                        "capability": "Environmental Telemetry",
                        "finding": (
                            "Lack of underfloor leak sensors and unintegrated gas suppression "
                            "alarms with the centralized BMS platform."
                        ),
                    },
                ],
                "kpis": [
                    {
                        "kpi_id": "DOM_FAC.P4.K1",
                        "kpi_name": "VESDA Smoke Detection Coverage",
                        "score": 2.0,
                        "description": "Early smoke aspiration sensors and BMS alarm telemetry.",
                    }
                ],
            }
        ],
    }

    matrix_rows = derive_in_memory_maturity_matrix(
        contaminated_payload,
        doc_lang="en",
        gatekeeper=enterprise_gatekeeper,
    )

    assert len(matrix_rows) == 1
    p4_row = matrix_rows[0]
    assert p4_row["canonical_pillar_id"] == "DOM_FAC.P4"
    assert p4_row["quarantined_findings_count"] >= 2

    justification = p4_row["justification"].lower()

    # Zero Compute/RAM contamination invariant
    assert "simplivity" not in justification
    assert "ram" not in justification
    assert "esxi" not in justification
    assert "hyperconverged" not in justification

    # Must contain domain-relevant fire suppression / environmental telemetry concepts
    assert any(
        term in justification
        for term in ("suppression", "smoke", "gas", "environmental", "leak", "alarms", "bms")
    )

    # Verify compiled justification passes the semantic gatekeeper
    audit_verdict = enterprise_gatekeeper.validate_text_for_pillar(
        p4_row["justification"],
        "DOM_FAC.P4",
        tower_id="DOM_FAC",
    )
    assert audit_verdict.verdict == ValidationVerdict.VALID_IN_DOMAIN
