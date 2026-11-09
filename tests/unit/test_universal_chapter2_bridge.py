"""Unit tests for Phase 1: Universal Chapter 2 Bridge in payload_to_ast.py.

Verifies the 4-tier coalescing resolution pipeline for domain objectives,
platform descriptions, and component scoping across arbitrary topologies.
Strictly 100% Technical English and tenant-agnostic.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

from assessment_engine.adapters.compilers.payload_to_ast import (
    resolve_domain_introduction,
)


def test_resolve_domain_introduction_tier2_blueprint_data() -> None:
    blueprint_data: Dict[str, Any] = {
        "tower_id": "T1",
        "domain_introduction": {
            "domain_objective": "Audit datacenter physical infrastructure resilience.",
            "introduction_paragraph": "The evaluated facilities support central production.",
            "included_components": ["Twin data hall rooms", "Dual UPS chains"],
        },
    }

    intro = resolve_domain_introduction(
        blueprint_data=blueprint_data,
        annex_data=None,
        tower_id="T1",
        client_name="Acme Corp",
        meta_lang="en",
    )

    assert intro["domain_objective"] == "Audit datacenter physical infrastructure resilience."
    assert intro["introduction_paragraph"] == "The evaluated facilities support central production."
    assert len(intro["included_components"]) == 2


def test_resolve_domain_introduction_tier4_synthesis_when_missing() -> None:
    # Simulates T3..T10 where domain_introduction is missing from payload
    blueprint_data: Dict[str, Any] = {
        "tower_id": "D_NET",
        "tower_name": "Enterprise Networking & Security",
        "pillars_analysis": [
            {"pillar_id": "P1", "pillar_name": "Core Routing & WAN Interconnect"},
            {"pillar_id": "P2", "pillar_name": "Perimeter Security & Firewall Clusters"},
        ],
        "verified_entities": ["Fortinet FortiGate", "Cisco Catalyst 9300"],
    }

    intro_es = resolve_domain_introduction(
        blueprint_data=blueprint_data,
        annex_data=None,
        tower_id="D_NET",
        client_name="Acme Corp",
        meta_lang="es",
    )

    assert "Enterprise Networking & Security" in intro_es["domain_objective"]
    assert "Acme Corp" in intro_es["domain_objective"]
    assert "Fortinet FortiGate" in intro_es["introduction_paragraph"]
    assert len(intro_es["included_components"]) == 2
    assert "Core Routing & WAN Interconnect" in intro_es["included_components"][0]

    intro_en = resolve_domain_introduction(
        blueprint_data=blueprint_data,
        annex_data=None,
        tower_id="D_NET",
        client_name="Acme Corp",
        meta_lang="en",
    )

    assert "Audit the technical maturity" in intro_en["domain_objective"]
    assert "Enterprise Networking & Security" in intro_en["domain_objective"]
    assert "Acme Corp" in intro_en["domain_objective"]
    assert "Fortinet FortiGate" in intro_en["introduction_paragraph"]
    assert len(intro_en["included_components"]) == 2


def test_resolve_domain_introduction_empty_payload_fallback() -> None:
    intro = resolve_domain_introduction(
        blueprint_data={},
        annex_data=None,
        tower_id="CUSTOM_DOMAIN",
        client_name="Global Enterprise",
        meta_lang="en",
    )

    assert bool(intro["domain_objective"])
    assert bool(intro["introduction_paragraph"])
    assert "CUSTOM_DOMAIN" in intro["domain_objective"]
    assert "Global Enterprise" in intro["domain_objective"]
