from __future__ import annotations

import json

from assessment_engine.mcp_server import get_tower_state


def _write_json(path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _valid_blueprint_payload() -> dict:
    return {
        "_generation_metadata": {
            "artifact_type": "blueprint_payload",
            "artifact_version": "1.0.0",
        },
        "document_meta": {
            "client_name": "client",
            "tower_name": "Tower 5",
            "tower_code": "T5",
            "financial_tier": "mid",
            "transformation_horizon": "12m",
        },
        "executive_snapshot": {
            "bottom_line": "Tower summary",
            "decisions": ["Decision"],
            "cost_of_inaction": "Cost",
            "structural_risks": ["Risk"],
            "business_impact": "Impact",
            "operational_benefits": ["Benefit"],
            "transformation_complexity": "Media",
        },
        "cross_capabilities_analysis": {
            "common_deficiency_patterns": ["Pattern"],
            "transformation_paradigm": "Paradigm",
            "critical_technical_debt": "Debt",
        },
        "roadmap": [{"wave": "Wave 1", "projects": ["Project 1"]}],
        "external_dependencies": [
            {
                "project": "Project 1",
                "depends_on": "Dependency 1",
                "reason": "Because",
            }
        ],
        "pillars_analysis": [
            {
                "pilar_id": "P1",
                "pilar_name": "Pillar 1",
                "score": 3.5,
                "target_score": 4.0,
                "health_check_asis": [
                    {
                        "capability": "Capability 1",
                        "finding": "Finding 1",
                        "business_risk": "Risk 1",
                    }
                ],
                "target_architecture_tobe": {
                    "vision": "Vision 1",
                    "design_principles": ["Principle 1"],
                },
                "projects_todo": [
                    {
                        "name": "Project 1",
                        "business_case": "Business case 1",
                        "tech_objective": "Objective 1",
                        "deliverables": ["Deliverable 1"],
                        "sizing": "M",
                        "duration": "3 months",
                    }
                ],
            }
        ],
    }


def _valid_annex_payload() -> dict:
    return {
        "_generation_metadata": {
            "artifact_type": "annex_payload",
            "artifact_version": "1.0.0",
        },
        "document_meta": {"tower_code": "T5", "tower_name": "Tower 5"},
        "executive_summary": {
            "global_score": "3.5/5.0",
            "global_band": "Managed",
            "target_maturity": "4.0",
            "headline": "Headline",
            "summary_body": "Summary body",
            "key_business_impacts": ["Impact 1"],
        },
        "domain_introduction": {
            "introduction_paragraph": "Intro",
            "technological_domain": "Domain",
            "domain_objective": "Objective",
            "evaluated_capabilities": ["Capability 1"],
            "included_components": ["Component 1"],
        },
        "pillar_score_profile": {
            "profile_intro": "Intro",
            "scoring_method_note": "Method",
            "pillars": [{"pillar": "Pillar 1", "executive_reading": "Reading"}],
        },
        "sections": {
            "asis": {
                "narrative": "Narrative",
                "strengths": ["Strength"],
                "gaps": ["Gap"],
                "operational_impacts": ["Impact"],
            },
            "tobe": {
                "vision": "Vision",
                "design_principles": ["Principle"],
            },
            "gap": {
                "introduction": "Gap intro",
                "target_capabilities": ["Capability"],
                "gap_rows": [
                    {
                        "pillar": "Pillar 1",
                        "as_is_summary": "As is",
                        "target_state": "Target",
                        "key_gap": "Gap",
                    }
                ],
            },
            "todo": {
                "introduction": "Todo intro",
                "priority_initiatives": [
                    {
                        "sequence": 1,
                        "initiative": "Project 1",
                        "objective": "Objective",
                        "priority": "Alta",
                        "expected_outcome": "Outcome",
                        "dependencies_display": "None",
                    }
                ],
            },
            "risks": {
                "introduction": "Risks intro",
                "risks": [
                    {
                        "risk": "Risk 1",
                        "impact": "High",
                        "probability": "Alta",
                        "mitigation_summary": "Mitigate",
                    }
                ],
            },
            "conclusion": {
                "final_assessment": "Assessment",
                "executive_message": "Message",
                "priority_focus_areas": ["Focus 1"],
                "closing_statement": "Closing",
            },
        },
    }


def test_get_tower_state_prioritizes_canonical_artifacts(tmp_path):
    _write_json(tmp_path / "blueprint_t5_payload.json", _valid_blueprint_payload())
    _write_json(
        tmp_path / "approved_annex_t5.template_payload.json",
        _valid_annex_payload(),
    )
    (tmp_path / "Blueprint_Transformacion_T5_client.docx").write_bytes(b"docx")
    (tmp_path / "annex_t5_client_final.docx").write_bytes(b"docx")

    state = json.loads(get_tower_state(str(tmp_path)))

    assert state["canonical"]["overall_status"] == "complete"
    assert state["canonical"]["blueprint_payload"]["status"] == "valid"
    assert state["canonical"]["blueprint_payload"]["tower_code"] == "T5"
    assert state["canonical"]["annex_payload"]["status"] == "valid"
    assert state["canonical"]["deliverables"]["blueprint_docx"]["status"] == "present"
    assert state["legacy"]["asis"]["status"] == "missing"
    assert state["asis"]["status"] == "missing"


def test_get_tower_state_surfaces_invalid_canonical_payloads(tmp_path):
    _write_json(
        tmp_path / "blueprint_t5_payload.json",
        {"document_meta": {"tower_code": "T5"}},
    )

    state = json.loads(get_tower_state(str(tmp_path)))

    assert state["canonical"]["overall_status"] == "invalid"
    assert state["canonical"]["blueprint_payload"]["status"] == "invalid"
    assert state["canonical"]["annex_payload"]["status"] == "missing"
    assert state["canonical"]["blueprint_payload"]["validation_errors"]


def test_get_tower_state_surfaces_corrupted_canonical_payloads(tmp_path):
    (tmp_path / "blueprint_t5_payload.json").write_bytes(b"\xff\xfe\x00\x00")

    state = json.loads(get_tower_state(str(tmp_path)))

    assert state["canonical"]["overall_status"] == "invalid"
    assert state["canonical"]["blueprint_payload"]["status"] == "error"
    assert "could not be loaded" in state["canonical"]["blueprint_payload"]["message"]
