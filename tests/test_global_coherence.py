from __future__ import annotations

from assessment_engine.scripts.lib.global_maturity_policy import (
    average_pillar_target,
    band_for_score,
    safe_float,
    status_color_for_score,
)
from tests.artifact_helpers import (
    ROOT,
    load_json,
    require_artifact,
    require_existing_group,
)

SMOKE_DIR = ROOT / "working" / "smoke_ivirma"


def test_global_payload_keeps_heatmap_and_bottom_lines_semantically_aligned() -> None:
    payload = load_json(require_artifact(SMOKE_DIR / "global_report_payload.json"))

    heatmap_by_tower = {tower["id"]: tower for tower in payload["heatmap"]}
    bottom_lines_by_tower = {
        tower["id"]: tower for tower in payload["tower_bottom_lines"]
    }

    assert heatmap_by_tower
    assert set(heatmap_by_tower) == set(bottom_lines_by_tower)

    for tower_id, heatmap_tower in heatmap_by_tower.items():
        bottom_line_tower = bottom_lines_by_tower[tower_id]
        score = safe_float(heatmap_tower.get("score"))

        assert bottom_line_tower["score"] == heatmap_tower["score"]
        assert bottom_line_tower["band"] == heatmap_tower["band"]
        assert bottom_line_tower["status_color"] == heatmap_tower["status_color"]
        assert heatmap_tower["band"] == band_for_score(score)
        assert heatmap_tower["status_color"] == status_color_for_score(score)


def test_global_payload_targets_match_blueprint_target_policy() -> None:
    global_path = require_artifact(SMOKE_DIR / "global_report_payload.json")
    blueprint_paths = sorted(SMOKE_DIR.glob("T*/blueprint_*_payload.json"))
    if not blueprint_paths:
        require_existing_group(
            [], skip_message="No blueprint payloads available for smoke coherence."
        )

    payload = load_json(global_path)
    heatmap_by_tower = {tower["id"]: tower for tower in payload["heatmap"]}

    for blueprint_path in blueprint_paths:
        blueprint = load_json(blueprint_path)
        tower_id = blueprint["document_meta"]["tower_code"]
        if tower_id not in heatmap_by_tower:
            continue
        expected_target = average_pillar_target(
            blueprint["pillars_analysis"], default=4.0
        )
        assert heatmap_by_tower[tower_id]["target_maturity"] == f"{expected_target:.1f}"
