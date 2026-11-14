"""Unit test suite for SurveyScoreHydrator.

Verifies:
1. Arithmetic mean calculation of declared scores per pillar from assessment Excel workbooks.
2. Reliable column detection regardless of column positioning or answer text options.
3. Automated hydration of declared scores into tower blueprints and scoring manifests.
Written in 100% Technical English.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from assessment_engine.application.services.survey_score_hydrator import SurveyScoreHydrator

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_parse_molins_survey_workbook_all_ten_towers() -> None:
    xlsx_path = REPO_ROOT / "source_docs/molins/Preguntas Fast Assessment Molins contestadas cliente.xlsx"
    if not xlsx_path.exists():
        pytest.skip("Molins survey Excel fixture not found.")

    scores = SurveyScoreHydrator.parse_survey_workbook(xlsx_path)

    # Must contain all 10 towers
    assert len(scores) == 10
    for t_idx in range(1, 11):
        t_key = f"T{t_idx}"
        assert t_key in scores
        # Each tower must have pillars P1..P5
        assert len(scores[t_key]) >= 5
        for p_idx in range(1, 6):
            p_key = f"P{p_idx}"
            assert p_key in scores[t_key]
            val = scores[t_key][p_key]
            assert 1.0 <= val <= 5.0

    # Verify known T2 declared scores
    assert scores["T2"]["P1"] == 2.75
    assert scores["T2"]["P2"] == 4.25
    assert scores["T2"]["P3"] == 1.50
    assert scores["T2"]["P4"] == 1.00
    assert scores["T2"]["P5"] == 2.75


def test_hydrate_mock_client_directory(tmp_path: Path) -> None:
    xlsx_path = REPO_ROOT / "source_docs/molins/Preguntas Fast Assessment Molins contestadas cliente.xlsx"
    if not xlsx_path.exists():
        pytest.skip("Molins survey Excel fixture not found.")

    # Create dummy tower dir with blueprint payload
    t2_dir = tmp_path / "T2"
    t2_dir.mkdir(parents=True)
    dummy_payload = {
        "tower_id": "T2",
        "pillars_analysis": [
            {"pillar_id": "T2.P1", "pillar_name": "Pillar 1", "score": 2.75},
            {"pillar_id": "T2.P2", "pillar_name": "Pillar 2", "score": 1.00},
        ]
    }
    bp_file = t2_dir / "blueprint_t2_payload.json"
    with open(bp_file, "w", encoding="utf-8") as f:
        json.dump(dummy_payload, f)

    SurveyScoreHydrator.hydrate_client_directory(xlsx_path, tmp_path)

    # Verify blueprint payload was updated with declared scores
    with open(bp_file, "r", encoding="utf-8") as f:
        updated = json.load(f)

    p1 = updated["pillars_analysis"][0]
    p2 = updated["pillars_analysis"][1]
    assert p1["declared_score"] == 2.75
    assert p2["declared_score"] == 4.25

    # Verify scoring_output.json was generated
    scoring_file = t2_dir / "scoring_output.json"
    assert scoring_file.exists()
    with open(scoring_file, "r", encoding="utf-8") as sf:
        sc_data = json.load(sf)
    assert len(sc_data["pillar_scores"]) >= 2
    assert sc_data["pillar_scores"][1]["score_exact"] == 4.25


def test_assessment_matrix_parser_triggers_survey_score_hydrator(tmp_path: Path) -> None:
    xlsx_path = REPO_ROOT / "source_docs/molins/Preguntas Fast Assessment Molins contestadas cliente.xlsx"
    if not xlsx_path.exists():
        pytest.skip("Molins survey Excel fixture not found.")

    from assessment_engine.application.services.ingestion_service import AssessmentMatrixParserService
    from assessment_engine.infrastructure.storage.workspace_manager import WorkspacePersistenceManager

    ws_mgr = WorkspacePersistenceManager(root_dir=tmp_path)
    client_dir = ws_mgr.resolve_client_dir("test_client")

    t1_dir = client_dir / "T1"
    t1_dir.mkdir(parents=True)
    bp_file = t1_dir / "blueprint_t1_payload.json"
    with open(bp_file, "w", encoding="utf-8") as f:
        json.dump({
            "tower_id": "T1",
            "pillars_analysis": [
                {"pillar_id": "T1.P1", "pillar_name": "Facilities Power", "score": 2.50}
            ]
        }, f)

    parser = AssessmentMatrixParserService(workspace_manager=ws_mgr)
    parser.ingest_assessment_matrix(
        client_slug="test_client",
        source_path=xlsx_path,
        source_filename="test_survey.xlsx",
    )

    with open(bp_file, "r", encoding="utf-8") as f:
        hydrated_bp = json.load(f)

    assert hydrated_bp["pillars_analysis"][0]["declared_score"] == 2.50
    assert (t1_dir / "scoring_output.json").exists()

