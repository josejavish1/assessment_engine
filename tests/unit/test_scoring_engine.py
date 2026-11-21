import pytest
from decimal import Decimal
from assessment_engine.domain.scoring_engine import ScoringEngine

def test_compute_pillar_score():
    scores = [4.0, 5.0, 4.0]
    result = ScoringEngine.compute_pillar_score(scores)
    assert result == Decimal("4.33")

def test_compute_pillar_score_with_missing():
    scores = [4.0, None, 5.0, 0.0]
    result = ScoringEngine.compute_pillar_score(scores)
    assert result == Decimal("4.50")

def test_compute_tower_score_exact_weights():
    # Example T1: 24/20/16/22/18
    p_scores = [Decimal("3.0"), Decimal("4.0"), Decimal("2.0"), Decimal("3.0"), Decimal("5.0")]
    p_weights = [Decimal("24"), Decimal("20"), Decimal("16"), Decimal("22"), Decimal("18")]
    
    # Calculation:
    # (3*0.24) + (4*0.20) + (2*0.16) + (3*0.22) + (5*0.18)
    # 0.72 + 0.80 + 0.32 + 0.66 + 0.90 = 3.40
    
    result = ScoringEngine.compute_tower_score(p_scores, p_weights)
    assert result == Decimal("3.40")

def test_compute_tower_score_invalid_weights():
    p_scores = [Decimal("3.0"), Decimal("4.0")]
    p_weights = [Decimal("50"), Decimal("40")] # sum 90
    
    with pytest.raises(ValueError, match="Pillar weights must sum to 1.0 or 100"):
        ScoringEngine.compute_tower_score(p_scores, p_weights)

def test_compute_tower_score_with_excluded_pillar_renormalization():
    # 5 pillars: 4 active with score 4.0, 1 excluded with 0.0
    p_scores = [Decimal("4.0"), Decimal("4.0"), Decimal("4.0"), Decimal("4.0"), Decimal("0.0")]
    p_weights = [Decimal("20"), Decimal("20"), Decimal("20"), Decimal("20"), Decimal("20")]

    result = ScoringEngine.compute_tower_score(p_scores, p_weights)
    # The active 4 pillars must re-normalize to 25% each, preserving the 4.00 score without zero dilution
    assert result == Decimal("4.00")

def test_generate_audit_trail():
    tower_id = "T1"
    kpi_ledger = {
        "K1": 3.0, "K2": 4.0, "K3": 5.0
    }
    pillar_defs = [
        {
            "pillar_id": "P1",
            "pillar_name": "Facilities",
            "weight_pct": 100,
            "kpis": [
                {"kpi_id": "K1"},
                {"kpi_id": "K2"},
                {"kpi_id": "K3"}
            ]
        }
    ]
    
    trail = ScoringEngine.generate_audit_trail(tower_id, kpi_ledger, pillar_defs)
    assert trail["tower_id"] == "T1"
    assert len(trail["pillars"]) == 1
    assert trail["pillars"][0]["computed_score"] == 4.00
    assert trail["global"]["computed_tower_score"] == 4.00
    assert trail["global"]["maturity_level"] == 4
    # Label should be optimized/advanced based on our scale
