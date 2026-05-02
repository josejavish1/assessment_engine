import pytest

from assessment_engine.scripts.run_scoring import build_scoring


@pytest.fixture
def mock_case_input():
    """Provides a more realistic, yet simple, case_input.json content."""
    return {
        "case_id": "test_case_01",
        "tower_id": "T1",
        "tower_name": "Test Tower",
        "answers": [
            # Pillar 1: all scores are 2.0
            {"kpi_id": "T1.P1.K1", "value": 2.0},
            {"kpi_id": "T1.P1.K2", "value": 2.0},
            # Pillar 2: all scores are 4.0
            {"kpi_id": "T1.P2.K1", "value": 4.0},
            {"kpi_id": "T1.P2.K2", "value": 4.0},
        ],
    }


@pytest.fixture
def mock_tower_definition():
    """Provides a simplified tower_definition.json with easy-to-calculate weights."""
    return {
        "working_rules": {
            "score_indicator": "mean",
            "score_pillar": "mean",
            "score_tower": "weighted_mean",
        },
        "pillars": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Pillar One",
                "weight_pct": 70,
                "kpis": [{"kpi_id": "T1.P1.K1"}, {"kpi_id": "T1.P1.K2"}],
            },
            {
                "pillar_id": "T1.P2",
                "pillar_name": "Pillar Two",
                "weight_pct": 30,
                "kpis": [{"kpi_id": "T1.P2.K1"}, {"kpi_id": "T1.P2.K2"}],
            },
        ],
        "score_bands": [
            {"min": 1.0, "max": 1.8, "label": "Level 1"},
            {"min": 1.8, "max": 2.6, "label": "Level 2"},
            {"min": 2.6, "max": 3.4, "label": "Level 3"},
            {"min": 3.4, "max": 4.2, "label": "Level 4"},
            {"min": 4.2, "max": 5.0, "label": "Level 5"},
        ],
        "maturity_scale": [],
    }


def test_build_scoring_calculates_weighted_average_correctly(
    mock_case_input, mock_tower_definition
):
    """
    Tests the core logic of build_scoring.
    - Pillar 1 avg should be 2.0.
    - Pillar 2 avg should be 4.0.
    - Tower score should be (2.0 * 0.7) + (4.0 * 0.3) = 1.4 + 1.2 = 2.6.
    """
    # Act
    scoring_output = build_scoring(mock_case_input, mock_tower_definition)

    # Assert
    # 1. Check pillar scores
    pillar_scores = scoring_output["pillar_scores"]
    assert len(pillar_scores) == 2
    assert pillar_scores[0]["pillar_id"] == "T1.P1"
    assert pillar_scores[0]["score_exact"] == 2.0
    assert pillar_scores[1]["pillar_id"] == "T1.P2"
    assert pillar_scores[1]["score_exact"] == 4.0

    # 2. Check final tower score
    assert scoring_output["tower_score_exact"] == pytest.approx(2.6)

    # 3. Check if the correct band was resolved
    assert (
        scoring_output["maturity_band_from_exact"]["label"] == "Level 2"
    )  # FIX: The logic is inclusive of the upper bound for the lower level.


def test_build_scoring_handles_missing_answers_gracefully(
    mock_case_input, mock_tower_definition
):
    """
    Tests that the scoring works even if some answers are missing.
    - Pillar 1 avg should be 2.0.
    - Pillar 2 avg should be 0.
    - Tower score should be (2.0 * 0.7) + (0 * 0.3) = 1.4.
    """
    # Arrange
    mock_case_input["answers"] = [
        {"kpi_id": "T1.P1.K1", "value": 2.0},
        {"kpi_id": "T1.P1.K2", "value": 2.0},
    ]

    # Act
    scoring_output = build_scoring(mock_case_input, mock_tower_definition)

    # Assert
    pillar_scores = scoring_output["pillar_scores"]
    assert pillar_scores[0]["score_exact"] == 2.0
    assert pillar_scores[1]["score_exact"] == 0.0
    assert scoring_output["tower_score_exact"] == pytest.approx(1.4)
    assert scoring_output["maturity_band_from_exact"]["label"] == "Level 1"
