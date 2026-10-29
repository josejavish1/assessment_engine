"""Unit tests for the decoupled stages of run_tower_blueprint_engine."""

from __future__ import annotations

import pytest

from assessment_engine.application.run_tower_blueprint_engine import (
    _apply_deterministic_finops,
    _build_pillars_map,
    _calculate_total_fair_ale,
    _cascade_project_rename,
    _map_candidate_initiatives_to_sota_projects,
    _reconcile_orchestrator_roadmap_and_dependencies,
    _remap_canonical_initiatives,
    _resolve_mitigated_risk_context,
    _scrub_client_placeholders,
    _validate_evidence_grounding,
)


def test_validate_evidence_grounding_preserves_verified_evidence():
    """Verify that _validate_evidence_grounding classifies direct vs unverified evidence deterministically."""
    blueprint_analysis = {
        "health_check_asis": [
            {"finding": "F1", "literal_evidence": "Logs confirman caída de enlace"},
            {"finding": "F2", "literal_evidence": ""},
        ]
    }
    p_data = {
        "refined_findings": {
            "gaps": [{"statement": "Obsolescencia de switches principales"}]
        }
    }
    _validate_evidence_grounding(blueprint_analysis, p_data)
    assert (
        blueprint_analysis["health_check_asis"][0]["evidence_grounding_type"]
        == "direct_evidence"
    )
    assert (
        blueprint_analysis["health_check_asis"][1]["evidence_grounding_type"]
        == "verified_gap"
    )
    assert (
        blueprint_analysis["health_check_asis"][1]["literal_evidence"]
        == "Obsolescencia de switches principales"
    )


def test_build_pillars_map_averaging():
    """Verify that _build_pillars_map groups KPI answers and computes arithmetic means."""
    tower_def = {
        "pillars": [
            {"pillar_id": "T1.P1", "pillar_name": "Digital Workplace"},
            {"pillar_id": "T1.P2", "pillar_name": "Collaboration"},
        ]
    }
    case_data = {
        "answers": [
            {"kpi_id": "T1.P1.K1.PR1", "value": 4.0},
            {"kpi_id": "T1.P1.K1.PR2", "value": 2.0},
            {"kpi_id": "T1.P2.K1.PR1", "value": 3.0},
        ]
    }
    refined_findings = {
        "pillar_findings": [
            {"pillar_id": "T1.P1", "gaps": [{"statement": "Obsolescencia de SO"}]}
        ]
    }

    pillars_map = _build_pillars_map(tower_def, case_data, refined_findings)
    assert pillars_map["T1.P1"]["score"] == 3.0
    assert pillars_map["T1.P2"]["score"] == 3.0
    assert "refined_findings" in pillars_map["T1.P1"]


def test_map_candidate_initiatives_horizons_and_sizing():
    """Verify that candidate initiatives map sizing and horizon durations deterministically."""
    initiatives = [
        {"title": "Quick Fix VDI", "horizon": "short-term", "priority": "Alta"},
        {"title": "Long Term Cloud Migration", "horizon": "h3", "priority": "Media"},
        {"title": "Standard Modernization", "horizon": "h2", "priority": "Media"},
    ]

    projects = _map_candidate_initiatives_to_sota_projects(initiatives, max_projects=3)
    assert len(projects) == 3
    assert projects[0]["sizing"] == "S"
    assert "H1" in projects[0]["duration"]
    assert projects[1]["sizing"] == "L"
    assert "H3" in projects[1]["duration"]
    assert projects[2]["sizing"] == "M"
    assert "H2" in projects[2]["duration"]


def test_reconcile_orchestrator_roadmap_and_dependencies():
    """Verify that fuzzy matching reconciles invalid project names in dependencies and roadmap."""
    closing_data = {
        "roadmap": [
            {"wave": "Ola 1", "projects": ["Migracion Cloud", "Proyecto Desconocido"]}
        ],
        "external_dependencies": [
            {"project": "Migracion Cloud", "depends_on": "Plataforma Base"}
        ],
        "design_principles": ["P1", "P2"],
    }
    valid_names = ["Migración Cloud SOTA", "Plataforma Base de Datos"]

    _reconcile_orchestrator_roadmap_and_dependencies(closing_data, valid_names)
    assert len(closing_data["roadmap"][0]["projects"]) > 0


def test_cascade_project_rename_and_scrub():
    """Verify that project renaming propagates across roadmap and dependencies, and placeholders are scrubbed."""
    payload = {
        "roadmap": [{"projects": ["Old Name", "Other Proj"]}],
        "external_dependencies": [{"project": "Old Name", "depends_on": "None"}],
    }
    _cascade_project_rename(payload, "Old Name", "New Renamed Project")
    assert payload["roadmap"][0]["projects"][0] == "New Renamed Project"
    assert payload["external_dependencies"][0]["project"] == "New Renamed Project"

    nested_dict = {"title": "Informe para [Cliente]", "sub": ["Ref: [CLIENTE]"]}
    scrubbed = _scrub_client_placeholders(nested_dict, "Acme Corp")
    assert scrubbed["title"] == "Informe para Acme Corp"
    assert scrubbed["sub"][0] == "Ref: Acme Corp"


def test_calculate_total_fair_ale():
    """Verify that total ALE is extracted directly or summed from pillar health checks."""
    payload1 = {"total_fair_ale": 250000.0}
    assert _calculate_total_fair_ale(payload1) == 250000.0

    payload2 = {
        "total_fair_ale": 0.0,
        "pillars_analysis": [
            {
                "health_check_asis": [
                    {"fair_ale_score": 50000.0},
                    {"fair_ale_score": 75000.0},
                ]
            }
        ],
    }
    assert _calculate_total_fair_ale(payload2) == 125000.0
