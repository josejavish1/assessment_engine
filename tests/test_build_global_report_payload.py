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


def _multi_pillar_blueprint_payload(tower_code: str, tower_name: str) -> dict:
    payload = _blueprint_payload(tower_code, tower_name)
    payload["pillars_analysis"] = [
        {
            "score": 2.8,
            "target_score": 3.8,
            "health_check_asis": [],
            "projects_todo": [],
        },
        {
            "score": 3.2,
            "target_score": 4.2,
            "health_check_asis": [],
            "projects_todo": [],
        },
    ]
    return payload


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
        "blueprint-only;"
    )
    assert payload["meta"]["version"] == "v2.3 - Blueprint-first Engine"
    assert [tower["id"] for tower in payload["heatmap"]] == ["T5"]


def test_build_global_payload_requires_blueprints(tmp_path):
    legacy_dir = tmp_path / "T6"
    legacy_dir.mkdir()
    _write_json(
        legacy_dir / "approved_annex_t6.refined.json",
        _legacy_refined_payload(),
    )

    payload = build_global_payload(tmp_path, "client")

    assert payload is None


def test_build_global_payload_ignores_legacy_even_when_present(tmp_path):
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
        "blueprint-only;"
    )
    assert payload["meta"]["version"] == "v2.3 - Blueprint-first Engine"
    assert [tower["id"] for tower in payload["heatmap"]] == ["T5"]


def test_build_global_payload_embeds_client_intelligence_summary(tmp_path):
    blueprint_dir = tmp_path / "T5"
    blueprint_dir.mkdir()
    _write_json(
        blueprint_dir / "blueprint_t5_payload.json",
        _blueprint_payload("T5", "Resilience"),
    )
    _write_json(
        tmp_path / "client_intelligence.json",
        {
            "version": "3.0",
            "client_name": "client",
            "metadata": {
                "dossier_id": "client-1",
                "schema_version": "3.0",
                "created_at": "2026-05-01T00:00:00+00:00",
                "modified_at": "2026-05-01T00:00:00+00:00",
                "lang": "es",
                "generated_by": "assessment_engine",
            },
            "profile": {
                "industry": "Telecomunicaciones",
                "financial_tier": "Tier 1",
                "operating_model": "Multipaís",
                "regions": ["EU"],
                "priority_markets": ["España"],
                "business_lines": ["B2B"],
            },
            "regulatory_context": [
                {
                    "name": "NIS2",
                    "applicability": "high",
                    "confidence": {"score": 80, "label": "high", "method": "custom"},
                    "sources": [],
                    "impacted_domains": ["T5"],
                }
            ],
            "business_context": {
                "ceo_agenda": {
                    "summary": "Proteger margen y resiliencia.",
                    "confidence": {"score": 80, "label": "high", "method": "custom"},
                    "sources": [],
                },
                "strategic_priorities": [],
                "business_model_signals": [],
                "active_transformations": [],
                "transformation_horizon": {
                    "stage": "H1",
                    "label": "Brilliant Basics",
                    "rationale": "Reducir complejidad.",
                    "confidence": {"score": 70, "label": "high", "method": "custom"},
                    "sources": [],
                },
                "constraints": [],
            },
            "technology_context": {
                "footprint_summary": {
                    "summary": "Azure dominante.",
                    "confidence": {"score": 60, "label": "medium", "method": "custom"},
                    "sources": [],
                },
                "technology_drivers": [],
                "vendor_dependencies": ["Azure"],
                "operating_constraints": ["Cambios limitados"],
                "recent_incident_signals": [],
            },
            "tower_overrides": {},
            "claims": [],
            "review": {"human_review_status": "pending", "review_notes": []},
            "extensions": {},
        },
    )

    payload = build_global_payload(tmp_path, "client")

    assert payload is not None
    assert payload["intelligence_dossier"]["profile"]["priority_markets"] == ["España"]
    assert payload["intelligence_dossier"]["regulatory_context"] == ["NIS2"]


def test_build_global_payload_averages_target_scores_and_shared_maturity_policy(
    tmp_path,
):
    blueprint_dir = tmp_path / "T5"
    blueprint_dir.mkdir()
    _write_json(
        blueprint_dir / "blueprint_t5_payload.json",
        _multi_pillar_blueprint_payload("T5", "Resilience"),
    )

    payload = build_global_payload(tmp_path, "client")

    assert payload is not None
    assert payload["heatmap"][0]["score"] == "3.0"
    assert payload["heatmap"][0]["band"] == "Básica"
    assert payload["heatmap"][0]["status_color"] == "FFD966"
    assert payload["heatmap"][0]["target_maturity"] == "4.0"
