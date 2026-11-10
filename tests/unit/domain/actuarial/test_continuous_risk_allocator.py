"""Comprehensive unit tests for ContinuousRiskAllocator covering all 7 Argon edge cases."""

import math
from assessment_engine.domain.actuarial.continuous_risk_allocator import ContinuousRiskAllocator


def test_continuous_risk_allocator_exact_closure() -> None:
    total_ale = 246548.0
    total_sle = 65000.0
    hcs = [
        {"id": "HC1", "capability": "Virtualization", "score": 1.25, "severity": "HIGH", "finding": "RAM saturation"},
        {"id": "HC2", "capability": "Containers", "score": 1.25, "severity": "HIGH", "finding": "Missing CSI driver"},
        {"id": "HC3", "capability": "Cloud", "score": 1.50, "severity": "MEDIUM", "finding": "Manual drift"},
        {"id": "HC4", "capability": "Automation", "score": 1.00, "severity": "CRITICAL", "finding": "Zero IaC"},
        {"id": "HC5", "capability": "Observability", "score": 2.75, "severity": "MEDIUM", "finding": "Tooling silos"},
    ]

    allocated = ContinuousRiskAllocator.allocate_risks(total_ale, total_sle, hcs)

    # 1. Total closure must be exact
    sum_ale = sum(hc["ale"] for hc in allocated)
    assert sum_ale == round(total_ale)

    # 2. Exact SLE closure
    sum_sle = round(sum(hc["sle"] for hc in allocated), 2)
    assert sum_sle == round(total_sle, 2)

    # 3. All ALEs must be distinct (zero identical twins)
    ales = [hc["ale"] for hc in allocated]
    assert len(set(ales)) == len(ales), f"Identical twin ALEs detected: {ales}"

    # 4. Critical risk with low score must receive higher allocation than medium risk with high score
    assert allocated[3]["ale"] > allocated[4]["ale"]


def test_multilingual_severity_mapping() -> None:
    """Verifies that non-English severities (Spanish, German, French) scale properly."""
    total_ale = 100000.0
    total_sle = 30000.0
    hcs = [
        {"id": "HC1", "score": 2.0, "severity": "CRÍTICO"},
        {"id": "HC2", "score": 2.0, "severity": "HOCH"},
        {"id": "HC3", "score": 2.0, "severity": "FAIBLE"},
    ]
    allocated = ContinuousRiskAllocator.allocate_risks(total_ale, total_sle, hcs)
    # CRÍTICO (3.5) > HOCH (2.2) > FAIBLE (0.6)
    assert allocated[0]["ale"] > allocated[1]["ale"] > allocated[2]["ale"]


def test_zero_score_truthiness_trap() -> None:
    """Verifies score=0.0 is preserved as maximum deficit, not converted to 2.5."""
    total_ale = 100000.0
    total_sle = 20000.0
    hcs = [
        {"id": "HC1", "score": 0.0, "severity": "MEDIUM"},  # deficit 5.0
        {"id": "HC2", "score": 2.5, "severity": "MEDIUM"},  # deficit 2.5
    ]
    allocated = ContinuousRiskAllocator.allocate_risks(total_ale, total_sle, hcs)
    # Score 0.0 must receive substantially higher allocation than score 2.5
    assert allocated[0]["ale"] > allocated[1]["ale"] * 1.5


def test_fractional_millions_scale_invariance() -> None:
    """Verifies small or fractional numbers (e.g. 1.45 meaning 1.45M) do not truncate to integer."""
    total_ale = 1.45
    total_sle = 0.50
    hcs = [
        {"id": "HC1", "score": 1.0, "severity": "HIGH"},
        {"id": "HC2", "score": 2.0, "severity": "MEDIUM"},
    ]
    allocated = ContinuousRiskAllocator.allocate_risks(total_ale, total_sle, hcs)
    assert round(sum(hc["ale"] for hc in allocated), 2) == 1.45
    assert all(hc["ale"] > 0 for hc in allocated)


def test_unvalidated_input_coercion_robustness() -> None:
    """Verifies NaN, None, and unparsed strings do not raise uncaught exceptions."""
    total_ale = 50000.0
    total_sle = 10000.0
    hcs = [
        {"id": "HC1", "score": "N/A", "severity": None},
        {"id": "HC2", "score": float("nan"), "severity": "UNKNOWN"},
        {"id": "HC3", "score": 1.5, "severity": "HIGH"},
    ]
    allocated = ContinuousRiskAllocator.allocate_risks(total_ale, total_sle, hcs)
    assert sum(hc["ale"] for hc in allocated) == 50000.0
    assert all(math.isfinite(hc["ale"]) for hc in allocated)
