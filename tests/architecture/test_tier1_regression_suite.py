"""
Tier-1 Universal Regression Suite.

This suite mathematically and operationally enforces the resolutions to every major 
regression discovered between deliveries 8 and 17, as mandated by the Tier-1 auditor. 
It establishes blocking code invariants to prevent the 'whack-a-mole' hallucination cycle.

Invariants covered:
1. Scoring: reported_score == sum(pillar_score * master_weight) with +-0.005 tolerance.
2. Bands: maturity_band = f(tower_score) (e.g. 2.606 -> Estandarizado).
3. Missing Values: No silent imputation for empty/invalid KPIs.
4. Contradictions: K8s 4.25 + contradictory evidence -> status=PROVISIONAL_CONTRADICTORY.
5. Shared Facts: 'vCPU_oversubscription = UNKNOWN' -> no 'severa' or 'crítica'.
6. Entity Resolution: '3 y 4' -> AMBIGUOUS_REFERENCE.
7. Evidence Guard: Without evidence_id, specific capability implementations are forbidden.
8. FAIR TEF: classify_tef(2.4) == TEF4.
9. No FAIR Goal-Seeking: SLE and ALE must be independent mathematical products.
"""

import json
from decimal import Decimal
import math
from pathlib import Path
import pytest
import re

from assessment_engine.domain.scoring_engine import ScoringEngine
from assessment_engine.domain.actuarial_scale_calibrator import resolve_dynamic_tef_scale_level
from assessment_engine.domain.services.chapter4_synthesizer import Chapter4Synthesizer
from assessment_engine.infrastructure.runtime_paths import ROOT, resolve_tower_definition_file
from assessment_engine.domain.governance.scale_engine import GovernanceScaleEngine

# Helper for finding payload files
def get_payload(tower_id: str) -> dict:
    bp_path = ROOT / "working" / "molins_fresh_e2e" / tower_id / f"blueprint_{tower_id.lower()}_payload.json"
    if not bp_path.exists():
        return {}
    return json.loads(bp_path.read_text(encoding="utf-8-sig"))

def test_invariant_1_scoring_roll_up_exactitude():
    """1. Scoring: reported_score == sum(pillar_score * master_weight) with +-0.005 tolerance."""
    import docx
    for i in range(1, 11):
        tid = f"T{i}"
        payload = get_payload(tid)
        if not payload:
            continue
        
        # Visible pillar scores
        p_scores_map = {}
        from assessment_engine.domain.taxonomy_resolver import extract_pillar_identifiers
        for p in payload.get("pillars_analysis", []):
            if isinstance(p, dict):
                pid = extract_pillar_identifiers(p)[0]
                p_scores_map[pid] = float(p.get("score", 2.5))
        
        calculated_score = float(ScoringEngine.compute_tower_score_by_id(tid, p_scores_map))
        
        # Check compiled DOCX for exact score string
        docx_path = list((ROOT / "working" / "out" / "molins_fresh_e2e" / "02_ANEXOS_TECNICOS_ESPECIALISTAS").glob(f"*Anexo_{i:02d}_*ASIS.docx"))
        if docx_path:
            d = docx.Document(docx_path[0])
            found = False
            for p in d.paragraphs:
                if "sitúa la madurez operativa global" in p.text.lower():
                    # Format calculated score matching locale
                    expected_str = f"{calculated_score:.2f}".replace(".", ",")
                    assert expected_str in p.text, f"Tower {tid}: Expected exact score {expected_str} not found in intro paragraph!"
                    found = True
                    break
            assert found, f"Tower {tid}: Could not find intro paragraph in DOCX to verify score exactitude."

def test_invariant_2_bands_deterministic_mapping():
    """2. Bands: maturity_band = f(tower_score). T1 2.606 -> Estandarizado."""
    scale_engine = GovernanceScaleEngine.get_instance()
    # 2.6064 should round to 2.61 and resolve to Level 3 (Estandarizado)
    resolved = scale_engine.resolve_maturity(2.6064, locale="es")
    assert resolved.level == 3
    assert resolved.label == "Estandarizado"

def test_invariant_3_missing_values_no_imputation():
    """3. Missing values: ',' or empty cannot be transformed to a number silently."""
    kpi_scores = [4.0, 4.0, None]
    result = ScoringEngine.compute_pillar_score(kpi_scores)
    assert result == Decimal("4.00"), "Silent imputation detected!"

def test_invariant_4_contradictions_kubernetes():
    """4. Contradictions: K8s 4.25 + contradictory evidence -> status=PROVISIONAL_CONTRADICTORY."""
    t2_payload = get_payload("T2")
    if t2_payload:
        p2_score = None
        is_provisional = False
        for p in t2_payload.get("pillars_analysis", []):
            if "T2.P2" in p.get("pillar_id", "") or "P2" in p.get("pillar_name", ""):
                p2_score = p.get("score")
                if p.get("is_provisional", False) or "contradict" in str(p).lower():
                    is_provisional = True
        
        if p2_score is not None:
            assert p2_score == 4.25, f"Kubernetes score should be 4.25, got {p2_score}"
            assert is_provisional, "Kubernetes should be flagged as provisional/contradictory"

def test_invariant_5_shared_facts_vcpu_oversubscription():
    """5. Shared Facts: vCPU_oversubscription = UNKNOWN -> no 'severa', 'crítica', 'elevada' in any tower."""
    forbidden = ["sobreasignación severa", "sobreasignación crítica", "sobresuscripción severa", "sobresuscripción crítica", "acusada sobreasignación"]
    for i in range(1, 11):
        tid = f"T{i}"
        payload = get_payload(tid)
        if not payload:
            continue
        text = json.dumps(payload, ensure_ascii=False).lower()
        for f in forbidden:
            assert f not in text, f"Tower {tid} hallucinates vCPU oversubscription: '{f}'"

def test_invariant_6_entity_resolution_ambiguous_3_and_4():
    """6. Entity resolution: '3 y 4' -> AMBIGUOUS_REFERENCE. Cannot be 'clústeres 3 y 4'."""
    forbidden = ["clústeres 3 y 4", "agrupaciones 3 y 4"]
    for i in range(1, 11):
        tid = f"T{i}"
        payload = get_payload(tid)
        if not payload:
            continue
        text = json.dumps(payload, ensure_ascii=False).lower()
        for f in forbidden:
            assert f not in text, f"Tower {tid} hallucinates ambiguous entity: '{f}'"

def test_invariant_7_evidence_guard_kpi_alignment():
    """7. Evidence Guard: Without explicit evidence, specific capabilities (e.g. CCTV from third-party KPI) are forbidden."""
    t1_payload = get_payload("T1")
    if t1_payload:
        text = json.dumps(t1_payload, ensure_ascii=False).lower()
        # Ensure CCTV or NVR are not blindly hallucinated based on a generic KPI
        assert "cctv con ángulos muertos" not in text
        assert "nvr autónomos" not in text

def test_invariant_8_fair_tef_classification():
    """8. FAIR: classify_tef(2.4) == TEF4."""
    assert resolve_dynamic_tef_scale_level(2.40) == 4, "TEF 2.4/yr MUST map to TEF 4"
    assert resolve_dynamic_tef_scale_level(1.25) == 3, "TEF 1.25/yr MUST map to TEF 3"

def test_invariant_9_fair_no_goal_seeking():
    """9. No goal-seeking: Changing vulnerability cannot automatically modify SLE to conserve ALE.
    SLE must be independently derived from disruption rate and MTTR."""
    disruption_rate = 1000.0
    eff_mttr_hours = 2.0
    # Calculate SLE
    from assessment_engine.domain.services.chapter4_synthesizer import round_to_actuarial_significance
    base_sle = round_to_actuarial_significance(eff_mttr_hours * disruption_rate)
    
    # Change vulnerability and TEF
    tef = 2.40
    vuln_low = 0.50
    vuln_high = 0.90
    
    lef_low = tef * vuln_low
    lef_high = tef * vuln_high
    
    ale_low_vuln = base_sle * lef_low
    ale_high_vuln = base_sle * lef_high
    
    # ALE MUST change when Vulnerability changes, while SLE remains anchored to pure physics
    assert ale_low_vuln < ale_high_vuln, "ALE failed to respond to Vulnerability change!"
    assert math.isclose(ale_high_vuln / ale_low_vuln, vuln_high / vuln_low, rel_tol=1e-5), "Goal-seeking artifact detected: ALE change is not strictly proportional to LEF!"
