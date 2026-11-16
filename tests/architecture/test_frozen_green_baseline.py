"""
Frozen Green Baseline Characterization Test Suite.

Protects all certified GREEN components from regression during the Stabilization Phase:
A. ScoringEngine exact weighted roll-ups across all 10 towers.
B. MaturityBandEngine strict boundaries and transitions.
C. MissingValueEngine fail-closed behavior for malformed/missing KPIs.
D. Kubernetes contradiction handling (4.25* provisional state without artificial degradation).
E. FAIR TEF discrete scale classification.
F. Framework naming standard (Fast Assessment, never CMMI).
G. Actuarial claims consistency (Zero unbacked P90/CVaR Monte Carlo assertions).
"""

from decimal import Decimal
import json
import math
from pathlib import Path
import pytest

from assessment_engine.domain.scoring_engine import ScoringEngine
from assessment_engine.domain.governance.scale_engine import GovernanceScaleEngine
from assessment_engine.domain.actuarial_scale_calibrator import resolve_dynamic_tef_scale_level
from assessment_engine.domain.taxonomy_resolver import extract_pillar_identifiers
from assessment_engine.infrastructure.runtime_paths import ROOT

# Certified Green Expected Scores for Baseline Iteration 18
EXPECTED_TOWER_SCORES = {
    "T1": 2.61,
    "T2": 2.47,
    "T3": 2.56,
    "T4": 3.32,
    "T5": 2.20,
    "T6": 2.82,
    "T7": 2.43,
    "T8": 2.45,
    "T9": 3.19,
    "T10": 2.40,
}


def _get_tower_payload(tower_id: str) -> dict:
    bp_path = ROOT / "working" / "molins_fresh_e2e" / tower_id / f"blueprint_{tower_id.lower()}_payload.json"
    if not bp_path.exists():
        pytest.skip(f"Payload for {tower_id} not found at {bp_path}")
    return json.loads(bp_path.read_text(encoding="utf-8-sig"))


@pytest.mark.parametrize("tower_id,expected_score", EXPECTED_TOWER_SCORES.items())
def test_frozen_component_a_scoring_exactitude(tower_id: str, expected_score: float):
    """Component A: reported_score == sum(pillar_score * master_weight) with +-0.005 tolerance.

    Guarantees no fallbacks to unweighted simple arithmetic means exist.
    """
    payload = _get_tower_payload(tower_id)
    
    p_scores_map = {}
    for p in payload.get("pillars_analysis", []):
        if isinstance(p, dict):
            pid = extract_pillar_identifiers(p)[0]
            p_scores_map[pid] = float(p.get("score", 2.5))
            
    computed = float(ScoringEngine.compute_tower_score_by_id(tower_id, p_scores_map))
    assert math.isclose(computed, expected_score, abs_tol=0.005), (
        f"ScoringEngine regression on {tower_id}: expected {expected_score}, got {computed}"
    )


def test_frozen_component_b_maturity_band_boundaries():
    """Component B: MaturityBandEngine boundary behavior across discrete tiers."""
    scale_engine = GovernanceScaleEngine.get_instance()
    
    # Tier 1: 1.00 - 1.79 (Inicial)
    res_1_00 = scale_engine.resolve_maturity(1.00, locale="es")
    assert res_1_00.level == 1 and res_1_00.label == "Inicial"
    res_1_79 = scale_engine.resolve_maturity(1.79, locale="es")
    assert res_1_79.level == 1 and res_1_79.label == "Inicial"
    
    # Tier 2: 1.80 - 2.59 (Básico)
    res_1_80 = scale_engine.resolve_maturity(1.80, locale="es")
    assert res_1_80.level == 2 and res_1_80.label == "Básico"
    res_2_59 = scale_engine.resolve_maturity(2.59, locale="es")
    assert res_2_59.level == 2 and res_2_59.label == "Básico"
    
    # Tier 3: 2.60 - 3.39 (Estandarizado)
    res_2_60 = scale_engine.resolve_maturity(2.60, locale="es")
    assert res_2_60.level == 3 and res_2_60.label == "Estandarizado"
    res_3_39 = scale_engine.resolve_maturity(3.39, locale="es")
    assert res_3_39.level == 3 and res_3_39.label == "Estandarizado"
    
    # Tier 4: 3.40 - 4.19 (Optimizado)
    res_3_40 = scale_engine.resolve_maturity(3.40, locale="es")
    assert res_3_40.level == 4 and res_3_40.label == "Optimizado"
    res_4_19 = scale_engine.resolve_maturity(4.19, locale="es")
    assert res_4_19.level == 4 and res_4_19.label == "Optimizado"
    
    # Tier 5: 4.20 - 5.00 (Avanzado)
    res_4_20 = scale_engine.resolve_maturity(4.20, locale="es")
    assert res_4_20.level == 5 and res_4_20.label == "Avanzado"
    res_5_00 = scale_engine.resolve_maturity(5.00, locale="es")
    assert res_5_00.level == 5 and res_5_00.label == "Avanzado"


def test_frozen_component_c_missing_values_no_imputation():
    """Component C: Empty, null, or malformed values are ignored without silent imputation to 3.0."""
    # Case with valid numbers and None/empty values
    kpi_scores_with_null = [4.0, 4.0, None]
    res_null = ScoringEngine.compute_pillar_score(kpi_scores_with_null)
    assert res_null == Decimal("4.00"), "Silent imputation detected on None value!"

    # Case where all values are invalid/missing
    res_empty = ScoringEngine.compute_pillar_score([])
    assert res_empty == Decimal("0.00"), "Expected fail-closed 0.00 on empty inputs!"


def test_frozen_component_d_kubernetes_contradiction_preservation():
    """Component D: Kubernetes retains 4.25* provisional score without being crushed to 1.0."""
    t2_payload = _get_tower_payload("T2")
    k8s_pillar = None
    for p in t2_payload.get("pillars_analysis", []):
        if "T2.P2" in str(p.get("pillar_id")) or "P2" in str(p.get("pillar_name")):
            k8s_pillar = p
            break

    assert k8s_pillar is not None, "T2.P2 (Kubernetes) pillar missing from T2 payload!"
    assert k8s_pillar.get("score") == 4.25, f"Expected K8s score 4.25, found {k8s_pillar.get('score')}"

    # Verify overall T2 score is 2.47 (not crushed to 1.85 from 1.0 down-clamp)
    p_scores_map = {
        extract_pillar_identifiers(p)[0]: float(p.get("score", 2.5))
        for p in t2_payload.get("pillars_analysis", [])
        if isinstance(p, dict)
    }
    t2_score = float(ScoringEngine.compute_tower_score_by_id("T2", p_scores_map))
    assert math.isclose(t2_score, 2.47, abs_tol=0.005), f"T2 score corrupted: got {t2_score}"


def test_frozen_component_e_fair_tef_classification():
    """Component E: Discrete FAIR Threat Event Frequency (TEF) categorization."""
    assert resolve_dynamic_tef_scale_level(0.05) == 1, "0.05 events/yr must map to TEF 1 (<0.1)"
    assert resolve_dynamic_tef_scale_level(0.30) == 2, "0.30 events/yr must map to TEF 2 (0.1 - 0.5)"
    assert resolve_dynamic_tef_scale_level(1.25) == 3, "1.25 events/yr must map to TEF 3 (0.5 - 2.0)"
    assert resolve_dynamic_tef_scale_level(2.40) == 4, "2.40 events/yr must map to TEF 4 (2.0 - 10.0)"
    assert resolve_dynamic_tef_scale_level(12.0) == 5, "12.0 events/yr must map to TEF 5 (>10.0)"


def test_frozen_component_f_framework_naming_integrity():
    """Component F: Fast Assessment maturity framework branding, zero CMMI claims."""
    locales_path = ROOT / "engine_config" / "locales.json"
    locales_data = json.loads(locales_path.read_text(encoding="utf-8"))

    es_locales = locales_data.get("es", {})
    # Verify official methodology naming template
    framework_str = es_locales.get("cmmi_scale_title", "")
    assert "Fast Assessment" in framework_str, "Fast Assessment framework branding missing!"
    intro_diag = es_locales.get("intro_ch3_technical_diagnosis_asymmetric", "")
    assert "Fast Assessment" in intro_diag, "Fast Assessment branding missing in diagnosis intro!"
    assert "CMMI" not in intro_diag, "Forbidden CMMI certification claim detected in framework template!"


def test_frozen_component_g_disclaimer_actuarial_purity():
    """Component G: Disclaimers do not claim uncalculated Monte Carlo distributions."""
    locales_path = ROOT / "engine_config" / "locales.json"
    locales_data = json.loads(locales_path.read_text(encoding="utf-8"))
    
    disc_es = locales_data.get("es", {}).get("disclaimer_text_2", "")
    disc_en = locales_data.get("en", {}).get("disclaimer_text_2", "")
    
    # Forbidden ungrounded simulation claims
    assert "simulaciones estocásticas de monte carlo" not in disc_es.lower()
    assert "stochastic monte carlo simulations" not in disc_en.lower()
    assert "p90 / cvar" not in disc_es.lower()
    assert "p90 / cvar" not in disc_en.lower()
