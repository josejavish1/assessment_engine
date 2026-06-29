import numpy as np

from assessment_engine.infrastructure.mcda_sensitivity_engine import (
    MCDASensitivityEngine,
)


def test_mcda_utility_function_bounds():
    # Test lower bound clipping
    crit = np.array([-50.0])
    comp = np.array([-50.0])
    feas = np.array([-50.0])
    res = MCDASensitivityEngine.mcda_utility_function(crit, comp, feas)
    assert res[0] == 3.0

    # Test upper bound clipping
    crit = np.array([200.0])
    comp = np.array([200.0])
    feas = np.array([200.0])
    res = MCDASensitivityEngine.mcda_utility_function(crit, comp, feas)
    assert res[0] == 5.0

    # Test standard mathematical evaluation
    # Target = 3.0 + 2.0 * ((50*0.4 + 50*0.4 + 50*0.2) / 100) = 3.0 + 2.0 * (50 / 100) = 4.0
    crit = np.array([50.0])
    comp = np.array([50.0])
    feas = np.array([50.0])
    res = MCDASensitivityEngine.mcda_utility_function(crit, comp, feas)
    assert round(res[0], 2) == 4.0


def test_generate_truncated_normal():
    # Verify that Truncated Normal strictly obeys bounds and preserves mean
    mean = 95.0
    std = 15.0
    low = 0.0
    high = 100.0
    size = 10000

    samples = MCDASensitivityEngine._generate_truncated_normal(
        mean, std, low, high, size
    )
    assert len(samples) == size
    assert np.all(samples >= low)
    assert np.all(samples <= high)
    # The mean of truncated normal at 95 with std 15 should be around 88-92
    assert 80.0 <= np.mean(samples) <= 97.0


def test_run_sensitivity_analysis_convergence():
    engine = MCDASensitivityEngine()
    result = engine.run_sensitivity_analysis(
        base_criticality=60.0,
        base_compliance=50.0,
        base_feasibility=70.0,
        N=10000,
        uncertainty_range=10.0,
    )

    # 1. Structural Assertions
    assert "statistics" in result
    assert "decision_instability_indices" in result
    assert "sobol_indices" in result
    assert "audits" in result

    stats = result["statistics"]
    assert "mean_target_score" in stats
    assert "std_deviation" in stats
    assert "confidence_interval_95" in stats
    assert "sample_variance" in stats

    assert 3.0 <= stats["mean_target_score"] <= 5.0
    assert stats["std_deviation"] >= 0.0

    ci_lower, ci_upper = stats["confidence_interval_95"]
    assert ci_lower <= ci_upper
    assert 3.0 <= ci_lower <= 5.0
    assert 3.0 <= ci_upper <= 5.0

    # 2. Decision Instability Index Assertions
    dii = result["decision_instability_indices"]
    assert "dii_threshold_03_pct" in dii
    assert "dii_threshold_05_pct" in dii
    assert 0.0 <= dii["dii_threshold_03_pct"] <= 100.0
    assert 0.0 <= dii["dii_threshold_05_pct"] <= 100.0
    assert dii["dii_threshold_05_pct"] <= dii["dii_threshold_03_pct"]

    # 3. Sensitivity Indices Assertions (Sobol Indices boundaries)
    indices = result["sobol_indices"]
    for param in [
        "business_criticality",
        "regulatory_compliance",
        "implementation_feasibility",
    ]:
        assert param in indices
        assert 0.0 <= indices[param]["first_order"] <= 1.0
        assert 0.0 <= indices[param]["total_order"] <= 1.0
        assert indices[param]["first_order"] <= indices[param]["total_order"]

    # 4. Audits Assertions
    audits = result["audits"]
    assert audits["stability_status"] in [
        "Stable / Robust",
        "Highly Sensitive",
        "Unstable / Volatile",
    ]
    assert audits["dominant_parameter"] in [
        "business_criticality",
        "regulatory_compliance",
        "implementation_feasibility",
    ]
    assert 0.0 <= audits["dominant_influence_pct"] <= 100.0
    assert audits["fuzzing_iterations"] == 10000
