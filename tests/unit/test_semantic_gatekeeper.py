"""Unit tests for OntologicalGatekeeper.

Verifies deterministic semantic firewalling, detection and quarantine of cross-pillar
contaminations (e.g. compute virtualization metrics leaking into Fire Protection),
signal-to-noise ratio handling, and clean pass-through of in-domain findings.
Strictly 100% Technical English, zero hardcoded client data.
"""

from __future__ import annotations

import pytest

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
def gatekeeper() -> OntologicalGatekeeper:
    domain_rules = {
        "T1": DomainTaxonomyRule(
            domain_id="T1",
            name="Physical Facilities & Fire Suppression",
            keywords=("datacenter", "bms", "vesda", "suppression", "humidity", "leak"),
        ),
        "T2": DomainTaxonomyRule(
            domain_id="T2",
            name="Compute & Virtualization",
            keywords=("simplivity", "esxi", "vmware", "hypervisor", "ram", "vcpu"),
        ),
    }

    t1_p4_profile = PillarOntologyProfile(
        pillar_id="T1.P4",
        pillar_name="Fire Protection & Environmental Telemetry",
        tower_id="T1",
        domain_id="T1",
        positive_lexicon={
            "fire",
            "suppression",
            "smoke",
            "vesda",
            "bms",
            "leak",
            "humidity",
            "sensors",
            "gas",
            "extinguishing",
        },
        negative_exclusion_map={
            "T2": {"simplivity", "esxi", "vmware", "hypervisor", "ram", "vcpu"},
        },
    )

    registry = DomainTaxonomyRegistry(
        domain_rules=domain_rules,
        pillar_profiles={"T1.P4": t1_p4_profile},
        short_id_index={"P4": [t1_p4_profile]},
    )
    return OntologicalGatekeeper(registry)


def test_gatekeeper_quarantines_compute_saturation_in_fire_protection(
    gatekeeper: OntologicalGatekeeper,
) -> None:
    contaminated_text = (
        "Exceeding the 50% physical resource safety threshold "
        "(specifically RAM memory and vCPU utilization across clusters 3 and 4) "
        "on the 6 HPE SimpliVity hyperconverged nodes."
    )
    result = gatekeeper.validate_text_for_pillar(contaminated_text, "T1.P4")

    assert result.verdict == ValidationVerdict.QUARANTINED_FOREIGN_DOMAIN
    assert result.detected_foreign_domain_id == "T2"
    assert "simplivity" in result.negative_exclusion_hits
    assert "ram" in result.negative_exclusion_hits


def test_gatekeeper_accepts_valid_fire_protection_text(
    gatekeeper: OntologicalGatekeeper,
) -> None:
    valid_text = (
        "Absence of underfloor water leak and condensation detection sensors, "
        "coupled with lacking integration between the gas extinguishing panel alarms "
        "and the centralized BMS platform."
    )
    result = gatekeeper.validate_text_for_pillar(valid_text, "T1.P4")

    assert result.verdict == ValidationVerdict.VALID_IN_DOMAIN
    assert len(result.negative_exclusion_hits) == 0
    assert "bms" in result.positive_affinity_hits


def test_gatekeeper_sanitizes_mixed_findings(
    gatekeeper: OntologicalGatekeeper,
) -> None:
    findings = [
        {
            "node_id": "T1-P4-HC01",
            "capability": "Workload Absorption Capacity",
            "finding": "Critical RAM memory saturation across SimpliVity and ESXi clusters.",
        },
        {
            "node_id": "T1-P4-HC02",
            "capability": "Environmental & Leak Telemetry",
            "finding": "Missing flood sensors and early VESDA smoke detection across critical zones.",
        },
    ]

    sanitized, quarantined = gatekeeper.sanitize_pillar_findings(
        "T1.P4", findings, tower_id="T1"
    )

    assert len(sanitized) == 1
    assert sanitized[0]["node_id"] == "T1-P4-HC02"
    assert len(quarantined) == 1
    assert quarantined[0].detected_foreign_domain_id == "T2"
