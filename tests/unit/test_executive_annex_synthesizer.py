"""Unit tests for executive annex synthesis derivation algorithms."""

from __future__ import annotations

import json
from pathlib import Path

from assessment_engine.application.run_executive_annex_synthesizer import (
    average,
    derive_focus_areas,
    derive_gap_rows,
    derive_maturity_band,
    derive_priority_initiatives,
    derive_risks,
    enrich_annex_payload,
    infer_initiative_priority,
    truncate_text,
    unique_list,
)
from assessment_engine.domain.schemas.annex_synthesis import AnnexPayload
from assessment_engine.domain.schemas.blueprint import BlueprintPayload


def test_basic_utility_helpers():
    """Verify numeric averaging, string truncation, and unique list pruning."""
    assert average([3.0, 5.0]) == 4.0
    assert average([]) == 0.0
    assert derive_maturity_band(4.5) in ["Optimizado", "Optimized", "Líder", "Optimizing", "Optimized and Resilient", "Advanced"]
    assert truncate_text("A" * 300, limit=100).endswith("...")
    assert unique_list(["A", "B", "A", "C"], limit=2) == ["A", "B"]
    assert infer_initiative_priority({"priority": "Alta"}, "es") in ["Crítica", "Critical", "Alta", "High"]


def test_derivations_from_blueprint_fixture():
    """Verify that gap rows, risks, initiatives, and focus areas derive from canonical blueprint."""
    bp_source = Path("tests/test_data/blueprint_t2_payload.json")
    assert bp_source.exists(), "Blueprint fixture missing."

    data = json.loads(bp_source.read_text(encoding="utf-8-sig"))
    blueprint = BlueprintPayload.model_validate(data)

    caps, gap_rows = derive_gap_rows(blueprint)
    assert len(caps) > 0
    assert len(gap_rows) > 0

    risks = derive_risks(blueprint)
    assert len(risks) > 0

    initiatives = derive_priority_initiatives(blueprint)
    assert len(initiatives) > 0

    focus_areas = derive_focus_areas(blueprint)
    assert len(focus_areas) > 0


def test_enrich_annex_payload_full_flow(tmp_path: Path):
    """Verify that enrich_annex_payload integrates blueprint scores and metadata into AnnexPayload."""
    bp_source = Path("tests/test_data/blueprint_t2_payload.json")
    data = json.loads(bp_source.read_text(encoding="utf-8-sig"))
    blueprint = BlueprintPayload.model_validate(data)

    annex_source = Path("tests/test_data/approved_annex_t2.template_payload.json")
    annex_data = json.loads(annex_source.read_text(encoding="utf-8-sig"))
    annex_payload = AnnexPayload.model_validate(annex_data)

    radar_chart = tmp_path / "radar.png"
    radar_chart.write_text("fake_png")

    enriched = enrich_annex_payload(
        result_payload=annex_payload,
        blueprint=blueprint,
        radar_chart_path=radar_chart,
        run_id="test_run_123",
    )

    assert enriched.generation_metadata is not None
    assert enriched.generation_metadata.run_id == "test_run_123"
    assert enriched.document_meta["report_variant"] == "short"
    assert enriched.executive_summary.global_score != ""


def test_enrich_annex_payload_multilingual_currency_invariance(tmp_path: Path):
    """Verify that enrich_annex_payload respects currency from blueprint metadata across global currencies."""
    bp_source = Path("tests/test_data/blueprint_t2_payload.json")
    base_bp_data = json.loads(bp_source.read_text(encoding="utf-8-sig"))
    annex_source = Path("tests/test_data/approved_annex_t2.template_payload.json")
    base_annex_data = json.loads(annex_source.read_text(encoding="utf-8-sig"))

    radar_chart = tmp_path / "radar.png"
    radar_chart.write_text("fake_png")

    for currency_token in ["$", "£", "R$", "¥", "CHF", "€"]:
        bp_data = dict(base_bp_data)
        bp_data["document_meta"] = dict(bp_data.get("document_meta", {}))
        bp_data["document_meta"]["currency"] = currency_token
        bp_data["document_meta"]["currency_symbol"] = currency_token

        bp = BlueprintPayload.model_validate(bp_data)
        annex_payload = AnnexPayload.model_validate(dict(base_annex_data))

        enriched = enrich_annex_payload(
            result_payload=annex_payload,
            blueprint=bp,
            radar_chart_path=radar_chart,
            run_id="test_curr_run",
        )

        summary_str = str(enriched.executive_summary)
        assert currency_token in summary_str, f"Currency {currency_token} not preserved in executive summary"

