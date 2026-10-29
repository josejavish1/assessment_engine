from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.domain.schemas.global_report import (
    GlobalReportPayload,
)
from assessment_engine.application.run_executive_refiner import (
    postprocess_refined_findings,
)


def test_postprocess_ensures_strict_global_report_payload_compliance():
    """Verify that postprocess_refined_findings maps, coerces, and completes all fields so that
    the resulting dictionary strictly validates into GlobalReportPayload without ValidationError."""
    fixture_path = Path("tests/test_data/global_report_payload.json")
    assert fixture_path.exists(), "Baseline fixture missing."
    raw_findings = json.loads(fixture_path.read_text(encoding="utf-8-sig"))

    # Simulating a drifting LLM response with common format deviations:
    # 1. tower_id instead of id, missing name, numeric score
    # 2. immediate_decisions as flat strings instead of dicts
    # 3. evolution_principles / strategic_pillars with title instead of principle/pillar
    # 4. burning_platform root_causes as single string or missing fields
    refined_llm_output = {
        "executive_summary": {
            "headline": "Estrategia Global de Modernización",
            "narrative": "Texto sintetizado de alta dirección.",
            "key_business_impacts": ["Impacto 1", "Impacto 2"],
        },
        "burning_platform": [
            {
                "theme": "Resiliencia Crítica",
                "business_risk": "Pérdida de continuidad",
                "root_causes": ["Causa 1", "Causa 2"],
            }
        ],
        "tower_bottom_lines": [
            {"tower_id": "T1", "bottom_line": "Sistemas críticos estabilizados."}
        ],
        "target_vision": {
            "value_proposition": "Transformación tecnológica integral.",
            "evolution_principles": [
                {"title": "Cloud First", "description": "Priorizar cloud nativo."}
            ],
            "strategic_pillars": [
                {"title": "Seguridad", "description": "Zero Trust perimetral."}
            ],
        },
        "execution_roadmap": {
            "programs": [{"name": "P1", "description": "Modernización Core"}],
            "horizons": {
                "quick_wins_0_3_months": [
                    {
                        "program_id": "P1",
                        "title": "Quick Win 1",
                        "objective": "Caso de negocio validado",
                        "start_month": 1,
                        "duration_months": 3,
                    }
                ],
                "year_1_3_12_months": [],
                "year_2_12_24_months": [],
                "year_3_24_36_months": [],
            },
        },
        "executive_decisions": ["Aprobar fase 1", "Liberar CAPEX"],
    }

    final_dict = postprocess_refined_findings(refined_llm_output, raw_findings)

    # Must pass Pydantic validation cleanly
    validated = GlobalReportPayload.model_validate(final_dict)

    assert validated.executive_summary.headline == "Estrategia Global de Modernización"
    assert len(validated.executive_decisions.immediate_decisions) == 2
    assert validated.executive_decisions.immediate_decisions[0].decision == "Aprobar fase 1"
    assert validated.tower_bottom_lines[0].id == "T1"
    assert isinstance(validated.tower_bottom_lines[0].score, str)
    assert validated.tower_bottom_lines[0].name != ""
