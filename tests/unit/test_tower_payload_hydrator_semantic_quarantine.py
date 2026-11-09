"""Unit tests verifying that TowerPayloadHydrator sanitizes payloads with OntologicalGatekeeper

prior to disk persistence (Phase 5).
Strictly 100% Technical English and tenant-agnostic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import pytest

from assessment_engine.application.services.tower_payload_hydrator import (
    TowerPayloadHydrator,
)
from assessment_engine.domain.ontology.models import (
    DomainTaxonomyRule,
    PillarOntologyProfile,
    TaxonomyRegistryPort,
)
from assessment_engine.domain.validation.semantic_gatekeeper import (
    OntologicalGatekeeper,
)


class InMemoryTaxonomyRegistry(TaxonomyRegistryPort):
    """Pure domain test double implementing TaxonomyRegistryPort without infrastructure imports."""

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
def mock_gatekeeper() -> OntologicalGatekeeper:
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

    fac_p4 = PillarOntologyProfile(
        pillar_id="D_FAC.P4",
        pillar_name="Fire Suppression & Environmental Telemetry",
        tower_id="D_FAC",
        domain_id="D_FAC",
        positive_lexicon={"fire", "suppression", "vesda", "smoke", "bms", "leak"},
        negative_exclusion_map={"D_CMP": {"simplivity", "esxi", "vmware", "ram", "vcpu"}},
    )

    registry = InMemoryTaxonomyRegistry(
        domain_rules=domain_rules,
        pillar_profiles={"D_FAC.P4": fac_p4},
    )
    return OntologicalGatekeeper(registry)


def test_hydrator_sanitizes_findings_and_persists_clean_json(
    tmp_path: Path,
    mock_gatekeeper: OntologicalGatekeeper,
) -> None:
    client_slug = "synthetic_enterprise"
    client_dir = tmp_path / "working" / client_slug
    client_dir.mkdir(parents=True, exist_ok=True)

    fac_dir = client_dir / "D_FAC"
    fac_dir.mkdir(parents=True, exist_ok=True)

    raw_payload: Dict[str, Any] = {
        "tower_code": "D_FAC",
        "tower_name": "Facilities & Environmental",
        "pillars_analysis": [
            {
                "pillar_id": "D_FAC.P4",
                "pillar_name": "Fire Suppression & Environmental Telemetry",
                "score": 4.0,
                "asis_architecture_description": (
                    "Fire suppression relies on VESDA sensors and gas extinguishing. "
                    "However, HPE SimpliVity RAM saturation limits recovery."
                ),
                "health_check_asis": [
                    {
                        "node_id": "HC-01",
                        "capability": "Compute Capacity",
                        "finding": "High RAM saturation on HPE SimpliVity nodes.",
                    },
                    {
                        "node_id": "HC-02",
                        "capability": "Environmental Leakage",
                        "finding": "Missing water leak detection probes under raised floor.",
                    },
                ],
            }
        ],
    }

    payload_file = fac_dir / "blueprint_d_fac_payload.json"
    payload_file.write_text(json.dumps(raw_payload), encoding="utf-8")

    global_payload: Dict[str, Any] = {
        "meta": {"client": client_slug, "currency": "EUR"},
        "financial_telemetry": {"annual_revenue": 50_000_000.0},
    }

    hydrated_map = TowerPayloadHydrator.load_and_hydrate_all_towers(
        repo_root=tmp_path,
        global_payload=global_payload,
        doc_lang="en",
        target_towers=["D_FAC"],
        persist_to_disk=True,
        gatekeeper=mock_gatekeeper,
    )

    assert "D_FAC" in hydrated_map
    hydrated_fac = hydrated_map["D_FAC"]
    p4 = hydrated_fac["pillars_analysis"][0]

    # In-memory assertion: Contaminated finding was quarantined
    findings = p4["health_check_asis"]
    assert len(findings) == 1
    assert findings[0]["node_id"] == "HC-02"
    assert "simplivity" not in findings[0]["finding"].lower()

    # In-memory assertion: Description had contaminated sentence removed
    assert "simplivity" not in p4["asis_architecture_description"].lower()

    # Disk assertion: Persisted JSON file is clean of SimpliVity/RAM
    persisted_json = json.loads(payload_file.read_text(encoding="utf-8"))
    persisted_p4 = persisted_json["pillars_analysis"][0]
    persisted_findings = persisted_p4["health_check_asis"]
    assert len(persisted_findings) == 1
    assert "simplivity" not in persisted_findings[0]["finding"].lower()
    assert "simplivity" not in persisted_p4["asis_architecture_description"].lower()
