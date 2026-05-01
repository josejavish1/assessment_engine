import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from assessment_engine.scripts.render_web_presentation import generate_web_dashboard

# El directorio 'working' ahora se encuentra desde la raíz del proyecto
WORKING_DIR = Path("working")


def _build_valid_global_report_payload(client_id: str) -> dict:
    return {
        "_generation_metadata": {
            "artifact_type": "global_report_payload",
            "artifact_version": "1.0.0",
        },
        "meta": {
            "client": client_id,
            "date": "2026-05-01",
            "version": "v1",
            "global_score_display": "3.1",
        },
        "executive_summary": {
            "headline": "Test Headline",
            "narrative": "Summary...",
            "key_business_impacts": ["Impact 1"],
        },
        "burning_platform": [
            {
                "theme": "Risk",
                "business_risk": "Risk summary",
                "root_causes": ["Cause 1"],
            }
        ],
        "heatmap": [{"id": "T1", "name": "Test Tower 1", "score": "3.5"}],
        "tower_bottom_lines": [
            {
                "id": "T1",
                "name": "Test Tower 1",
                "score": "3.5",
                "band": "Managed",
                "status_color": "93C47D",
                "bottom_line": "Bottom line",
            }
        ],
        "target_vision": {
            "value_proposition": "Value",
            "evolution_principles": [{"principle": "P1", "description": "D1"}],
            "strategic_pillars": [{"pillar": "SP1", "description": "SD1"}],
            "architecture_principles": [{"principle": "AP1", "description": "AD1"}],
            "operating_model_implications": [
                {"area": "People", "description": "Desc..."}
            ],
        },
        "execution_roadmap": {
            "programs": [{"name": "Program 1", "description": "Desc"}],
            "horizons": {
                "quick_wins_0_3_months": [],
                "year_1_3_12_months": [],
                "year_2_12_24_months": [],
                "year_3_24_36_months": [],
            },
            "proactive_proposals": [],
        },
        "executive_decisions": {
            "immediate_decisions": [
                {
                    "decision_type": "D",
                    "action_required": "A",
                    "impact_if_delayed": "I",
                }
            ]
        },
        "visuals": {},
        "gtm_strategy": {},
        "stakeholder_matrix": [],
    }


def _build_valid_blueprint_payload() -> dict:
    return {
        "_generation_metadata": {
            "artifact_type": "blueprint_payload",
            "artifact_version": "1.0.0",
        },
        "document_meta": {
            "client_name": "web_test_client_real",
            "tower_name": "Test Tower 1",
            "tower_code": "T1",
            "financial_tier": "mid",
            "transformation_horizon": "12m",
        },
        "executive_snapshot": {
            "bottom_line": "BP Summary",
            "decisions": ["Decision 1"],
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

@pytest.fixture
def setup_real_test_data():
    client_id = "web_test_client_real"
    test_dir = WORKING_DIR / client_id
    test_dir.mkdir(parents=True, exist_ok=True)

    global_report_data = _build_valid_global_report_payload(client_id)
    (test_dir / "global_report_payload.json").write_text(json.dumps(global_report_data))

    blueprint_dir = test_dir / "T1"
    blueprint_dir.mkdir(exist_ok=True)
    blueprint_data = _build_valid_blueprint_payload()
    (blueprint_dir / "blueprint_T1_payload.json").write_text(json.dumps(blueprint_data))
    
    yield client_id
    
    import shutil
    shutil.rmtree(test_dir)

def test_generate_web_dashboard_with_real_files(setup_real_test_data):
    client_id = setup_real_test_data
    output_html_path = WORKING_DIR / client_id / "presentation" / "index.html"
    
    # La lógica del script original usa una ruta relativa a __file__, 
    # por lo que no necesita mocks si la estructura de directorios es correcta.
    generate_web_dashboard(client_id)

    assert output_html_path.exists(), "El fichero index.html no fue creado."
    content = output_html_path.read_text(encoding="utf-8")
    assert len(content) > 5000, f"El contenido del HTML es demasiado pequeño ({len(content)} bytes)."
    assert '"headline": "Test Headline"' in content, "El 'headline' no fue inyectado."


def test_generate_web_dashboard_fails_on_invalid_global_payload(setup_real_test_data):
    client_id = setup_real_test_data
    invalid_payload = {
        "meta": {"client": client_id, "date": "2026-05-01", "version": "v1"},
        "executive_summary": {
            "headline": "Missing required sections",
            "narrative": "Summary...",
            "key_business_impacts": ["Impact 1"],
        },
        "burning_platform": [],
        "heatmap": [],
    }
    (WORKING_DIR / client_id / "global_report_payload.json").write_text(
        json.dumps(invalid_payload)
    )

    with pytest.raises(ValidationError):
        generate_web_dashboard(client_id)
