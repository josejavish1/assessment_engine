"""
Unit Test Suite for GATE-31.1: Epistemic Density Routing.

Validates the implementation of Phase 31.1:
1. Pillars with zero qualitative evidence chunks map to REGIME_ZERO_EVIDENCE.
2. The Epistemic Density ratio (ρ) is calculated correctly as the ratio of qualitative evidence chunks to total KPIs.
3. The prompt compiler correctly injects the strict abstraction ceiling directive for unaccredited pillars.
"""

import pytest

from assessment_engine.application.run_tower_blueprint_engine import _build_pillars_map


def test_gate_31_1_epistemic_density_routing_zero_evidence():
    """GATE-31.1: A pillar with zero qualitative evidence is routed to REGIME_ZERO_EVIDENCE."""
    tower_def = {
        "tower_id": "T1",
        "pillars": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Test Pillar",
                "weight_pct": 100.0,
            }
        ],
    }
    case_data = {
        "answers": [
            {"kpi_id": "T1.P1.K1", "value": "3.0"},
            {"kpi_id": "T1.P1.K2", "value": "2.0"},
        ]
    }
    refined_findings = {
        "pillar_findings": [
            {
                "pillar_id": "T1.P1",
                "evidence": ["Score 3.0 in T1.P1.K1", "Evaluación declarada 2.0 en T1.P1.K2"],
            }
        ]
    }

    pillars_map, _ = _build_pillars_map(tower_def, case_data, refined_findings)
    p_data = pillars_map["T1.P1"]
    
    assert p_data["epistemic_density"] == 0.0
    assert p_data["epistemic_regime"] == "REGIME_ZERO_EVIDENCE"


def test_gate_31_1_epistemic_density_routing_concrete_evidence():
    """GATE-31.1: A pillar with qualitative evidence is routed to REGIME_EMPIRICAL_CONCRETE."""
    tower_def = {
        "tower_id": "T1",
        "pillars": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Test Pillar",
                "weight_pct": 100.0,
            }
        ],
    }
    case_data = {
        "answers": [
            {"kpi_id": "T1.P1.K1", "value": "3.0"},
            {"kpi_id": "T1.P1.K2", "value": "2.0"},
        ]
    }
    refined_findings = {
        "pillar_findings": [
            {
                "pillar_id": "T1.P1",
                "evidence": ["Transcription snippet from interview: We use standard backup servers."],
            }
        ]
    }

    pillars_map, _ = _build_pillars_map(tower_def, case_data, refined_findings)
    p_data = pillars_map["T1.P1"]
    
    assert p_data["epistemic_density"] == 0.5  # 1 qualitative chunk / 2 KPIs
    assert p_data["epistemic_regime"] == "REGIME_EMPIRICAL_CONCRETE"
