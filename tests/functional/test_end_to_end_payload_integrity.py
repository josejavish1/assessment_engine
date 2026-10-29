from __future__ import annotations

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from assessment_engine.domain.schemas.global_report import (
    GlobalReportPayload,
)
from assessment_engine.application.run_executive_refiner import (
    postprocess_refined_findings,
)
from assessment_engine.adapters.render_global_report_from_template import (
    load_payload,
)


def test_baseline_payload_strict_schema_conformance():
    """Verify that the baseline test fixture satisfies the strict GlobalReportPayload contract without fallbacks."""
    fixture_path = Path("tests/test_data/global_report_payload.json")
    assert fixture_path.exists(), "Baseline fixture missing."

    payload_dict = json.loads(fixture_path.read_text(encoding="utf-8-sig"))

    # Strict validation: must not raise ValidationError
    payload = GlobalReportPayload.model_validate(payload_dict)

    # Invariants verification: no empty or synthetic placeholder strings in critical sections
    assert payload.meta.client != "", "Client name must be defined."
    assert payload.executive_summary.headline != "", "Headline cannot be empty."
    assert len(payload.executive_summary.key_business_impacts) >= 1, "Must have business impacts."
    assert len(payload.burning_platform) >= 1, "Must have burning platform issues."
    for bp in payload.burning_platform:
        assert bp.theme != "", "Burning platform theme cannot be empty."
        assert bp.business_risk != "", "Burning platform risk cannot be empty."
        assert len(bp.root_causes) >= 1, "Root causes list cannot be empty."

    assert len(payload.tower_bottom_lines) >= 1, "Must contain tower bottom lines."
    for tbl in payload.tower_bottom_lines:
        assert tbl.id != "", "Tower ID cannot be empty."
        assert tbl.name != "", "Tower name cannot be empty."
        assert tbl.score != "", "Tower score cannot be empty."
        assert tbl.band != "", "Maturity band cannot be empty."

    assert len(payload.execution_roadmap.programs) >= 1, "Execution roadmap must have programs."


def test_render_adapter_load_payload_fails_fast_on_corrupt_data(tmp_path: Path):
    """Verify that load_payload fails fast with ValidationError on corrupt schema data rather than concealing errors."""
    corrupt_payload = {
        "_generation_metadata": {"artifact_type": "global_report_payload"},
        "meta": {"client": "Corrupt Corp"},
        # Missing critical sections: executive_summary, burning_platform, etc.
    }
    corrupt_file = tmp_path / "corrupt_payload.json"
    corrupt_file.write_text(json.dumps(corrupt_payload), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_payload(corrupt_file)


def test_refiner_postprocess_produces_fully_validated_payload():
    """Verify that postprocess_refined_findings yields a dictionary that passes GlobalReportPayload validation."""
    fixture_path = Path("tests/test_data/global_report_payload.json")
    raw_findings = json.loads(fixture_path.read_text(encoding="utf-8-sig"))

    # Simulating a partially structured LLM output (the typical AI drifting payload)
    refined_llm_output = {
        "executive_summary": {
            "headline": "Estrategia Global de Modernización",
            "narrative": "Texto sintetizado de alta dirección.",
            "key_business_impacts": ["Impacto 1", "Impacto 2"]
        },
        "burning_platform": [
            {
                "theme": "Resiliencia Crítica",
                "business_risk": "Pérdida de continuidad",
                "root_causes": ["Causa 1", "Causa 2"]
            }
        ],
        "tower_bottom_lines": [
            {"tower_id": "T1", "bottom_line": "Sistemas críticos estabilizados."}
        ],
        "target_vision": {
            "evolution_principles": [{"principle": "Cloud First", "description": "Priorizar cloud nativo."}],
            "strategic_pillars": [{"pillar": "Seguridad", "description": "Zero Trust perimetral."}],
            "value_proposition": "Transformación tecnológica integral."
        },
        "execution_roadmap": {
            "programs": [{"name": "P1", "description": "Modernización Core"}],
            "horizons": {
                "quick_wins_0_3_months": [
                    {
                        "program": "P1",
                        "title": "Quick Win 1",
                        "business_case": "Caso de negocio validado",
                        "start_month": 1,
                        "duration_months": 3
                    }
                ],
                "year_1_3_12_months": [],
                "year_2_12_24_months": [],
                "year_3_24_36_months": []
            }
        },
        "executive_decisions": ["Aprobar fase 1", "Liberar CAPEX"]
    }

    final_dict = postprocess_refined_findings(refined_llm_output, raw_findings)

    # Must validate cleanly into the canonical schema
    validated = GlobalReportPayload.model_validate(final_dict)
    assert validated.executive_summary.headline == "Estrategia Global de Modernización"
    assert len(validated.executive_decisions.immediate_decisions) == 2
    assert validated.tower_bottom_lines[0].score != ""
