"""Unit tests for DomainTaxonomyRegistry and taxonomy loader.

Verifies dynamic configuration loading, positive lexicon indexing,
multi-topology support (arbitrary domain IDs), and zero short-ID collision.
Strictly 100% Technical English and topology-agnostic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from assessment_engine.infrastructure.ontology.taxonomy_loader import (
    DomainTaxonomyRegistry,
)


@pytest.fixture()
def synthetic_config_env(tmp_path: Path) -> tuple[Path, Path]:
    """Creates a vertical-agnostic, multi-domain ontology and tower configuration fixture."""
    ontology_data = {
        "domain_taxonomy_rules": {
            "D_FACILITIES": {
                "name": "Physical Facilities & Environmental Control",
                "categories": ["facilities", "hvac", "fire_suppression"],
                "keywords": ["datacenter", "cooling", "ups", "generator", "vesda", "bms"],
            },
            "D_COMPUTE": {
                "name": "Compute & Hyperconverged Virtualization",
                "categories": ["compute_virtualization"],
                "keywords": ["hypervisor", "cluster", "vcpu", "ram", "overcommit"],
            },
        },
        "canonical_entities": [
            {
                "canonical_name": "SimpliVity",
                "category": "compute_virtualization",
                "acronyms": ["hpe simplivity"],
            },
            {
                "canonical_name": "VMware ESXi",
                "category": "compute_virtualization",
                "acronyms": ["esxi", "vsphere"],
            },
            {
                "canonical_name": "FM-200 Suppression",
                "category": "fire_suppression",
                "acronyms": ["fm200"],
            },
        ],
    }

    ontology_file = tmp_path / "global_tech_ontology.yaml"
    ontology_file.write_text(yaml.safe_dump(ontology_data), encoding="utf-8")

    towers_dir = tmp_path / "towers"
    towers_dir.mkdir()

    facilities_def = {
        "tower_id": "D_FACILITIES",
        "tower_name": "Physical Facilities & Environmental Control",
        "pillars": [
            {
                "pillar_id": "D_FACILITIES.P1",
                "pillar_name": "Power & Cooling Redundancy",
                "kpis": [
                    {
                        "kpi_id": "K1",
                        "kpi_name": "Thermal SLA Compliance",
                        "description": "Precision cooling and chiller redundancy metrics.",
                    }
                ],
            },
            {
                "pillar_id": "D_FACILITIES.P4",
                "pillar_name": "Fire Suppression & Environmental Telemetry",
                "kpis": [
                    {
                        "kpi_id": "K2",
                        "kpi_name": "Early Smoke Detection Coverage",
                        "description": "VESDA aspiration sensors and gas suppression integration with BMS.",
                    }
                ],
            },
        ],
    }

    compute_def = {
        "tower_id": "D_COMPUTE",
        "tower_name": "Compute & Hyperconverged Virtualization",
        "pillars": [
            {
                "pillar_id": "D_COMPUTE.P4",
                "pillar_name": "Hyperconverged Cluster Capacity",
                "kpis": [
                    {
                        "kpi_id": "K1",
                        "kpi_name": "Memory & CPU Host Utilization",
                        "description": "RAM and CPU allocation across ESXi and SimpliVity nodes.",
                    }
                ],
            }
        ],
    }

    (towers_dir / "tower_definition_d_facilities.json").write_text(
        json.dumps(facilities_def), encoding="utf-8"
    )
    (towers_dir / "tower_definition_d_compute.json").write_text(
        json.dumps(compute_def), encoding="utf-8"
    )

    return ontology_file, towers_dir


def test_dynamic_topology_indexing(synthetic_config_env: tuple[Path, Path]) -> None:
    ontology_file, towers_dir = synthetic_config_env
    registry = DomainTaxonomyRegistry.from_config_directories(
        ontology_file=ontology_file,
        towers_config_dir=towers_dir,
    )

    indexed = registry.list_indexed_pillars()
    assert indexed == ["D_COMPUTE.P4", "D_FACILITIES.P1", "D_FACILITIES.P4"]


def test_cross_domain_negative_exclusions_include_short_acronyms(
    synthetic_config_env: tuple[Path, Path],
) -> None:
    ontology_file, towers_dir = synthetic_config_env
    registry = DomainTaxonomyRegistry.from_config_directories(
        ontology_file=ontology_file,
        towers_config_dir=towers_dir,
    )

    fire_profile = registry.get_profile("D_FACILITIES.P4")
    assert fire_profile is not None
    compute_exclusions = fire_profile.negative_exclusion_map.get("D_COMPUTE")
    assert compute_exclusions is not None
    assert "simplivity" in compute_exclusions
    assert "esxi" in compute_exclusions
    assert "ram" in compute_exclusions


def test_contextual_short_id_lookup_prevents_cross_tower_collision(
    synthetic_config_env: tuple[Path, Path],
) -> None:
    ontology_file, towers_dir = synthetic_config_env
    registry = DomainTaxonomyRegistry.from_config_directories(
        ontology_file=ontology_file,
        towers_config_dir=towers_dir,
    )

    p4_facilities = registry.get_profile("P4", tower_id="D_FACILITIES")
    p4_compute = registry.get_profile("P4", tower_id="D_COMPUTE")

    assert p4_facilities is not None
    assert p4_compute is not None
    assert p4_facilities.pillar_id == "D_FACILITIES.P4"
    assert p4_compute.pillar_id == "D_COMPUTE.P4"
