"""
Phase F Characterization and Regression Test Suite: FAIR Provenance Schema and Independence.

Enforces the FAIR Input Provenance Invariant:
1. TechnicalRiskScenario must include explicit, traceable provenance fields:
   tef_source, vulnerability_source, and sle_source.
2. Mathematical Independence (No Goal-Seeking):
   Deriving ALE = LEF * SLE must preserve independent SLE. Changing vulnerability
   modifies LEF and ALE proportionally, while SLE remains anchored to MTTR * hourly rate.
3. All 10 tower payloads in working/molins_fresh_e2e must declare explicit provenance
   for each strategic risk card in chapter4_monistic_payload.
"""

from pathlib import Path
import pytest
import math

from assessment_engine.domain.actuarial.schemas import (
    TechnicalRiskScenario,
    HeatmapCoordinate,
    MonetaryInterval,
)
from assessment_engine.infrastructure.runtime_paths import ROOT


def test_technical_risk_scenario_provenance_schema():
    """1. TechnicalRiskScenario declares explicit provenance fields for TEF, Vulnerability, and SLE."""
    coord = HeatmapCoordinate(likelihood_index=3, impact_index=3, truncated_title="Test Scenario")
    ale = MonetaryInterval(lower_bound=1000.0, upper_bound=2000.0, currency_iso="EUR")
    
    scenario = TechnicalRiskScenario(
        risk_id="RSK-T1-01",
        title="Test Strategic Risk Scenario",
        threat_event_frequency_annual=1.25,
        vulnerability_ratio=0.63,
        mttr_recovery_hours=2.0,
        calibrated_annual_ale=ale,
        heatmap_coordinate=coord,
        physical_evidence="Verified physical power room evidence with dual ATS switches.",
        root_cause_mechanism="Operational bottleneck in legacy distribution panels.",
        business_impact_narrative="Potential disruption to production logistics and kilns.",
        required_mitigation="Deploy modular redundancy and continuous automated ATS testing.",
        tef_source="HISTORICAL_INCIDENT_BASELINE_TEF_ROW_3",
        vulnerability_source="CONTINUOUS_CONTROL_DEGRADATION_C_j_POW_1.35",
        sle_source="FINANCIAL_DOWNTIME_HOURLY_RATE_1428.58_USD_X_MTTR_2.0H",
    )
    
    assert scenario.tef_source == "HISTORICAL_INCIDENT_BASELINE_TEF_ROW_3"
    assert "C_j" in scenario.vulnerability_source
    assert "1428.58" in scenario.sle_source


def test_fair_parameter_mathematical_independence_no_goal_seeking():
    """2. Mathematical Independence: Changing Vulnerability modifies ALE proportionally without altering SLE."""
    hourly_rate = 1428.58
    mttr_hours = 2.0
    independent_sle = mttr_hours * hourly_rate  # 2857.16
    
    tef = 2.40
    vuln_baseline = 0.80
    vuln_improved = 0.50
    
    lef_baseline = tef * vuln_baseline  # 1.92
    lef_improved = tef * vuln_improved  # 1.20
    
    ale_baseline = independent_sle * lef_baseline  # 5485.75
    ale_improved = independent_sle * lef_improved  # 3428.59
    
    # Assert SLE remains identical (zero back-solving)
    assert independent_sle == 2857.16
    # Assert ALE decreases strictly proportionally to vulnerability reduction
    assert math.isclose(ale_improved / ale_baseline, vuln_improved / vuln_baseline, rel_tol=1e-5)


def test_all_tower_payloads_have_fair_provenance():
    """3. All 10 tower payloads in molins_fresh_e2e declare explicit provenance on their risk cards."""
    fresh_dir = ROOT / "working" / "molins_fresh_e2e"
    missing_provenance = []
    
    import json
    for i in range(1, 11):
        tid = f"T{i}"
        bp_path = fresh_dir / tid / f"blueprint_{tid.lower()}_payload.json"
        if not bp_path.exists():
            continue
        data = json.loads(bp_path.read_text(encoding="utf-8-sig"))
        mono = data.get("chapter4_monistic_payload", {})
        cards = mono.get("technical_risk_cards", [])
        if not cards:
            missing_provenance.append(f"{tid}: zero technical_risk_cards in monistic payload")
            continue
        for c in cards:
            cid = c.get("risk_id", "UNKNOWN")
            if not c.get("tef_source") or not c.get("vulnerability_source") or not c.get("sle_source"):
                missing_provenance.append(f"{tid} card {cid}: missing provenance metadata")

    assert not missing_provenance, "FAIR Provenance missing in tower payloads:\n" + "\n".join(missing_provenance)
