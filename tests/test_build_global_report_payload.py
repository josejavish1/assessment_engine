import json

from assessment_engine.scripts.build_global_report_payload import build_global_payload


def _write_json(path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _blueprint_payload(tower_code: str, tower_name: str) -> dict:
    return {
        "document_meta": {
            "tower_code": tower_code,
            "tower_name": tower_name,
        },
        "executive_snapshot": {"bottom_line": f"{tower_name} summary"},
        "pillars_analysis": [
            {
                "score": 3.5,
                "target_score": 4.0,
                "health_check_asis": [
                    {
                        "capability": "Capability 1",
                        "finding": "Finding 1",
                        "business_risk": "Risk 1",
                    }
                ],
                "projects_todo": [
                    {
                        "name": "Project 1",
                        "tech_objective": "Objective 1",
                        "business_case": "Outcome 1",
                    }
                ],
            }
        ],
    }


def _legacy_refined_payload() -> dict:
    return {
        "tower_name": "Legacy Tower",
        "sections": {
            "asis": {
                "maturity_summary": {
                    "score_display": "2.5 / 5.0",
                    "maturity_band": "Basico",
                },
                "executive_narrative": "Legacy summary",
            },
            "risks": {
                "risks": [
                    {
                        "risk": "Legacy risk",
                        "impact": "alto",
                        "cause": "Legacy cause",
                        "mitigation_summary": "Legacy mitigation",
                    }
                ]
            },
            "todo": {
                "todo_items": [
                    {
                        "initiative": "Legacy initiative",
                        "objective": "Legacy objective",
                        "priority": "Alta",
                        "expected_outcome": "Legacy outcome",
                    }
                ]
            },
            "tobe": {
                "target_maturity": {"recommended_level": "4.0"},
                "architecture_principles": ["Legacy principle"],
                "operating_model_implications": ["Legacy implication"],
            },
            "conclusion": {"executive_message": "Legacy executive message"},
        },
    }


def test_build_global_payload_marks_mixed_lineage(tmp_path):
    blueprint_dir = tmp_path / "T5"
    blueprint_dir.mkdir()
    _write_json(
        blueprint_dir / "blueprint_t5_payload.json",
        _blueprint_payload("T5", "Resilience"),
    )

    legacy_dir = tmp_path / "T6"
    legacy_dir.mkdir()
    _write_json(
        legacy_dir / "approved_annex_t6.refined.json",
        _legacy_refined_payload(),
    )

    payload = build_global_payload(tmp_path, "client")

    assert payload is not None
    assert payload["_generation_metadata"]["source_version"].startswith(
        "mixed-blueprint-legacy;"
    )
    assert payload["meta"]["version"] == "v2.2 - Blueprint-first Engine (legacy fallback)"
    assert [tower["id"] for tower in payload["heatmap"]] == ["T5", "T6"]


def test_build_global_payload_can_disable_legacy_fallback(tmp_path):
    blueprint_dir = tmp_path / "T5"
    blueprint_dir.mkdir()
    _write_json(
        blueprint_dir / "blueprint_t5_payload.json",
        _blueprint_payload("T5", "Resilience"),
    )

    legacy_dir = tmp_path / "T6"
    legacy_dir.mkdir()
    _write_json(
        legacy_dir / "approved_annex_t6.refined.json",
        _legacy_refined_payload(),
    )

    payload = build_global_payload(
        tmp_path,
        "client",
        allow_legacy_fallback=False,
    )

    assert payload is not None
    assert payload["_generation_metadata"]["source_version"].startswith(
        "blueprint-only;"
    )
    assert payload["meta"]["version"] == "v2.2 - Blueprint-first Engine"
    assert [tower["id"] for tower in payload["heatmap"]] == ["T5"]
