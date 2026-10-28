import pytest

from assessment_engine.infrastructure.client_intelligence import (
    get_target_maturity,
    infer_related_towers,
)


def test_infer_related_towers_covers_all_ten_towers():
    """Verify that infer_related_towers includes mapping for T1 (Strategy), T4 (Data & AI), and T10 (Apps),
    ensuring comprehensive coverage across all 10 enterprise IT towers."""
    # T1 Strategy
    t1_matches = infer_related_towers("Iniciativa de arquitectura empresarial y soberanía digital")
    assert "T1" in t1_matches

    # T4 Data & AI
    t4_matches = infer_related_towers("Despliegue de plataforma lakehouse y gobernanza dama con ia")
    assert "T4" in t4_matches

    # T10 Core Applications
    t10_matches = infer_related_towers("Modernización de aplicaciones monolito y desacople de mainframe")
    assert "T10" in t10_matches


def test_get_target_maturity_case_insensitivity():
    """Verify that get_target_maturity handles uppercase, lowercase, and missing towers reliably."""
    data = {
        "version": "2.0",
        "profile": {},
        "business_context": {},
        "tower_overrides": {
            "T4": {"target_maturity": 4.5},
            "t1": {"target_maturity": 3.8},
        },
    }

    assert get_target_maturity(data, "T4") == 4.5
    assert get_target_maturity(data, "t4") == 4.5
    assert get_target_maturity(data, "T1") == 3.8
    assert get_target_maturity(data, "T2", default=4.0) == 4.0
