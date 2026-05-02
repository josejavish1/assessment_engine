from __future__ import annotations

import argparse
import json

from assessment_engine.scripts import build_case_input


def test_build_case_input_includes_context_and_client_intelligence(
    monkeypatch, tmp_path
) -> None:
    tower_id = "T5"
    tower_dir = tmp_path / "engine_config" / "towers" / tower_id
    tower_dir.mkdir(parents=True)
    (tower_dir / f"tower_definition_{tower_id}.json").write_text(
        json.dumps(
            {
                "tower_name": "Resilience",
                "purpose": "Purpose",
                "working_rules": {
                    "score_question": "avg",
                    "score_indicator": "avg",
                    "score_pillar": "avg",
                    "score_tower": "avg",
                    "display_rounding": 1,
                    "reporting_rule": "standard",
                    "tobe_default_rule": "target",
                },
                "pillars": [
                    {
                        "pillar_id": "T5.P1",
                        "pillar_name": "Pilar 1",
                        "kpis": [
                            {
                                "kpi_id": "T5.P1.K1",
                                "kpi_name": "KPI 1",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    context_path = tmp_path / "context.txt"
    context_path.write_text(
        "Contexto real del cliente con prioridades claras.", encoding="utf-8"
    )
    responses_path = tmp_path / "responses.txt"
    responses_path.write_text("T5.P1.K1.PR1: 3.5\n", encoding="utf-8")
    intel_path = tmp_path / "working" / "client" / "client_intelligence.json"
    intel_path.parent.mkdir(parents=True)
    intel_path.write_text(
        json.dumps(
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
                    "industry": "Telecom",
                    "financial_tier": "Tier 1",
                    "operating_model": "Multipaís",
                    "regions": ["EU"],
                    "priority_markets": ["España"],
                    "business_lines": ["B2B"],
                },
                "regulatory_context": [],
                "business_context": {
                    "ceo_agenda": {
                        "summary": "Blindar resiliencia.",
                        "confidence": {
                            "score": 80,
                            "label": "high",
                            "method": "custom",
                        },
                        "sources": [],
                    },
                    "strategic_priorities": [],
                    "business_model_signals": [],
                    "active_transformations": [],
                    "transformation_horizon": {
                        "stage": "H1",
                        "label": "Brilliant Basics",
                        "rationale": "Reducir complejidad.",
                        "confidence": {
                            "score": 70,
                            "label": "high",
                            "method": "custom",
                        },
                        "sources": [],
                    },
                    "constraints": [],
                },
                "technology_context": {
                    "footprint_summary": {
                        "summary": "Azure dominante.",
                        "confidence": {
                            "score": 60,
                            "label": "medium",
                            "method": "custom",
                        },
                        "sources": [],
                    },
                    "technology_drivers": [],
                    "vendor_dependencies": ["Azure"],
                    "operating_constraints": ["Ventanas de cambio limitadas"],
                    "recent_incident_signals": [],
                },
                "tower_overrides": {
                    "T5": {
                        "target_maturity": 4.4,
                        "business_criticality": {
                            "score": 85,
                            "label": "high",
                            "method": "custom",
                        },
                        "regulatory_pressure": {
                            "score": 80,
                            "label": "high",
                            "method": "custom",
                        },
                        "change_urgency": {
                            "score": 75,
                            "label": "high",
                            "method": "custom",
                        },
                        "constraints": ["No interrumpir operación"],
                        "related_claim_ids": [],
                    }
                },
                "claims": [],
                "review": {"human_review_status": "pending", "review_notes": []},
                "extensions": {},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(build_case_input, "ROOT", tmp_path)
    monkeypatch.setattr(
        build_case_input,
        "resolve_client_intelligence_path",
        lambda _client_slug: intel_path,
    )

    payload = build_case_input.build_case_input(
        argparse.Namespace(
            client="client",
            tower=tower_id,
            context_file=str(context_path),
            responses_file=str(responses_path),
        )
    )

    assert payload["target_maturity_default"] == 4.4
    assert payload["context_summary"].startswith("Contexto real del cliente")
    assert payload["client_context"]["profile"]["industry"] == "Telecom"
    assert payload["client_context"]["tower_context"]["target_maturity"] == 4.4
