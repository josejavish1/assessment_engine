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
    assert derive_maturity_band(4.5) in ["Optimizado", "Optimized", "Líder"]
    assert truncate_text("A" * 300, limit=100).endswith("...")
    assert unique_list(["A", "B", "A", "C"], limit=2) == ["A", "B"]
    assert infer_initiative_priority({"priority": "Alta"}, 0) in ["Crítica", "Critical", "Alta", "High"]


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

    assert enriched.generation_metadata.run_id == "test_run_123"
    assert enriched.document_meta["report_variant"] == "short"
    assert enriched.executive_summary.global_score != ""
