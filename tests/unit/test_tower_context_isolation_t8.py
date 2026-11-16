"""
Phase E Characterization and Regression Test Suite: TowerContextBuilder Strict Isolation (T8).

Enforces strict domain payload isolation for Tower 8 (Governance & FinOps):
1. Tower 8 must be restricted to strategic governance, portfolio decisions (e.g., VMware May 2027
   contractual renewal), FinOps cost tracking, and software licensing.
2. TowerContextBuilder must strip raw hardware vendor dependencies (NetApp, SimpliVity, Huawei)
   from the T8 context packet.
3. Tower T8 payload in working/molins_fresh_e2e must be free of cross-tower hardware descriptions
   (SimpliVity nodes, NetApp storage arrays, Huawei switching hardware).
"""

from pathlib import Path
import pytest

from assessment_engine.infrastructure.client_intelligence import build_client_context_packet
from assessment_engine.infrastructure.runtime_paths import ROOT


def test_tower_8_context_packet_isolation():
    """1. build_client_context_packet strips hardware dependencies for Tower 8."""
    raw_intel = {
        "version": "3.0",
        "metadata": {},
        "profile": {},
        "business_context": {},
        "client_name": "MOLINS",
        "technology_context": {
            "footprint_summary": {"summary": "SimpliVity hyperconverged nodes and NetApp FAS storage arrays."},
            "vendor_dependencies": ["SimpliVity", "NetApp", "Huawei", "VMware", "Microsoft", "SAP", "Oracle"],
            "technology_drivers": [
                {"name": "VMware License Renewal May 2027"},
                {"name": "SimpliVity Memory Saturation on Node 3"},
                {"name": "FinOps Cloud Cost Optimization"},
            ],
            "operating_constraints": ["24/7 manufacturing operations"],
            "recent_incident_signals": ["Node 3 failover incident"],
        },
    }

    t8_packet = build_client_context_packet(raw_intel, tower_id="T8")
    tech_context = t8_packet.get("technology_context", {})

    # Permitted software and portfolio vendors
    assert "VMware" in tech_context.get("vendor_dependencies", [])
    assert "Microsoft" in tech_context.get("vendor_dependencies", [])

    # Stripped hardware infrastructure vendors
    assert "SimpliVity" not in tech_context.get("vendor_dependencies", [])
    assert "NetApp" not in tech_context.get("vendor_dependencies", [])
    assert "Huawei" not in tech_context.get("vendor_dependencies", [])

    # Incident hardware signals must be stripped for T8
    assert len(tech_context.get("recent_incident_signals", [])) == 0


def test_tower_8_payload_hardware_leakage_cleanliness():
    """2. Tower T8 payload must be free of physical hardware re-descriptions (SimpliVity, NetApp, Huawei)."""
    bp_path = ROOT / "working" / "molins_fresh_e2e" / "T8" / "blueprint_t8_payload.json"
    if not bp_path.exists():
        pytest.skip(f"T8 payload not found at {bp_path}")

    text = bp_path.read_text(encoding="utf-8-sig").lower()
    forbidden_hardware = [
        "simplivity",
        "netapp",
        "huawei",
    ]

    violations = []
    for brand in forbidden_hardware:
        if brand in text:
            violations.append(f"Tower T8 contains unisolated hardware brand: '{brand}'")

    assert not violations, "Tower 8 Context Contamination Invariant violated:\n" + "\n".join(violations)


def test_gate_30_2_stratum_cardinality_projection_for_tower_8():
    """3. GATE-30.2: Tower 8 context contains deterministic stratum_summaries count vectors."""
    raw_intel = {
        "version": "3.0",
        "metadata": {},
        "profile": {},
        "business_context": {},
        "client_name": "MOLINS",
        "asset_telemetry": {"total_hosts": 6},
        "technology_context": {
            "vendor_dependencies": ["SimpliVity", "NetApp", "VMware"],
            "technology_drivers": [{"name": "FinOps Cloud Cost Optimization"}],
        },
    }

    t8_packet = build_client_context_packet(raw_intel, tower_id="T8")
    tech_context = t8_packet.get("technology_context", {})
    summaries = tech_context.get("stratum_summaries", {})

    assert "LOGICAL_COMPUTE_STORAGE" in summaries
    compute_sum = summaries["LOGICAL_COMPUTE_STORAGE"]
    assert compute_sum["verified_asset_count"] == 6
    assert compute_sum["unverified_telemetry_ratio"] > 0.0
    assert compute_sum["portfolio_lifecycle_state"] == "HYBRID_LEGACY_MAINTENANCE"
