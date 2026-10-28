"""Unit tests for building global report consolidated payloads."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from assessment_engine.application.build_global_report_payload import (
    _aggregate_tower_blueprints,
    build_global_payload,
)


def test_aggregate_tower_blueprints_execution(tmp_path: Path):
    """Verify that _aggregate_tower_blueprints processes blueprint JSON files."""
    bp_source = Path("tests/test_data/blueprint_t2_payload.json")
    assert bp_source.exists(), "Source blueprint fixture missing."

    t2_dir = tmp_path / "T2"
    t2_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bp_source, t2_dir / "blueprint_t2_payload.json")

    blueprint_files = list(tmp_path.glob("T*/blueprint_*_payload.json"))
    (
        towers_data,
        strategic_risks,
        all_initiatives,
        all_principles,
        all_implications,
        blueprint_towers,
    ) = _aggregate_tower_blueprints(blueprint_files)

    assert len(towers_data) == 1
    assert towers_data[0]["id"] == "T2"
    assert "score" in towers_data[0]
    assert len(strategic_risks) > 0
    assert len(all_initiatives) > 0
    assert "T2" in blueprint_towers


def test_build_global_payload_full_pipeline(tmp_path: Path):
    """Verify that build_global_payload aggregates blueprints and client intelligence."""
    bp_source = Path("tests/test_data/blueprint_t2_payload.json")
    t2_dir = tmp_path / "T2"
    t2_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bp_source, t2_dir / "blueprint_t2_payload.json")

    client_intel = {
        "version": "3.0",
        "client_name": "Test Client",
        "profile": {"industry": "Energy & Utilities"},
        "business_context": {"transformation_horizon": {"stage": "H2"}},
    }
    (tmp_path / "client_intelligence.json").write_text(
        json.dumps(client_intel), encoding="utf-8"
    )

    result = build_global_payload(tmp_path, "Test Client")
    assert result is not None
    assert "meta" in result
    assert "executive_summary" in result
    assert "tower_bottom_lines" in result
    assert "heatmap" in result
    assert "board_memo" in result
