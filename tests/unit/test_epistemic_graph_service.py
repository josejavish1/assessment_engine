from assessment_engine.infrastructure.epistemic_graph_service import (
    EpistemicGraphService,
)


def test_epistemic_graph_perfect_state():
    service = EpistemicGraphService()
    # If all towers are perfect (5.0, i.e., 0.0 risk), there should be absolutely no propagated risk
    intrinsic = {f"T{i}": 5.0 for i in range(1, 11)}
    propagated = service.propagate_risk(intrinsic)

    for t_id, m in propagated.items():
        assert m == 5.0


def test_epistemic_graph_risk_cascade():
    service = EpistemicGraphService()

    # Base case: moderate maturities (all at 4.5)
    intrinsic_base = {f"T{i}": 4.5 for i in range(1, 11)}
    propagated_base = service.propagate_risk(intrinsic_base)

    # Let's fail T6 (Identity & Access Management) completely: set to 3.0 (1.0 risk)
    # T6 -> T5 is an edge. Thus, T5 should be heavily dragged down by T6's failure!
    # T5 -> T2 is another edge. So T2 should also be dragged down in cascade!
    failed_intrinsic = intrinsic_base.copy()
    failed_intrinsic["T6"] = 3.0

    propagated_failed = service.propagate_risk(failed_intrinsic)

    # Assertions
    # T6 failed intrinsically
    assert propagated_failed["T6"] == 3.0

    # T5 (SOC Operations) was dragged down by its parent T6
    assert propagated_failed["T5"] < propagated_base["T5"]

    # T2 (OT Substation Systems) was dragged down by its grandparent T6 via T5!
    assert propagated_failed["T2"] < propagated_base["T2"]

    # T9 (Physical Security) is not a descendant of T6, so its propagated score should not be affected by T6
    assert propagated_failed["T9"] == propagated_base["T9"]


def test_single_point_of_failure():
    service = EpistemicGraphService()

    intrinsic = {f"T{i}": 4.5 for i in range(1, 11)}
    spof, impact = service.get_single_point_of_failure(intrinsic)

    # T6 or T3 are high in the dependency hierarchy. Let's make sure an SPOF is resolved.
    assert spof in [f"T{i}" for i in range(1, 11)]
    assert impact > 0.0


def test_declarative_policy_loading():
    # Load default profile
    default_service = EpistemicGraphService(industry_profile="default")
    # Load retail profile (where edge weights should differ)
    retail_service = EpistemicGraphService(industry_profile="retail")

    # In default, T6 -> T5 edge weight is 0.60
    # In retail, T6 -> T5 edge weight is 0.50
    assert default_service.graph["T6"]["T5"]["weight"] == 0.60
    assert retail_service.graph["T6"]["T5"]["weight"] == 0.50

    # Load critical infrastructure
    ci_service = EpistemicGraphService(
        industry_profile="Energy & Critical Infrastructure"
    )
    assert ci_service.graph["T6"]["T5"]["weight"] == 0.75
    assert ci_service.graph["T5"]["T2"]["weight"] == 0.85


def test_counterfactual_intervention_simulation():
    service = EpistemicGraphService(industry_profile="critical_infrastructure")

    # Baseline: T6 (IAM) is weak (3.0), which drags down T5 and T2
    intrinsic = {f"T{i}": 4.5 for i in range(1, 11)}
    intrinsic["T6"] = 3.0

    # Simulate raising T6 to perfect 5.0
    intervention = {"T6": 5.0}
    result = service.simulate_counterfactual_intervention(intrinsic, intervention)

    assert "baseline_propagated" in result
    assert "counterfactual_propagated" in result
    assert "global_improvement_delta" in result
    assert "cascading_benefits" in result

    # Check cascading benefits: T5 and T2 should have experienced significant maturity increases!
    benefits = result["cascading_benefits"]
    assert "T5" in benefits
    assert "T2" in benefits
    assert "T1" in benefits

    assert result["global_improvement_delta"] > 0.0


def test_critical_propagation_paths():
    service = EpistemicGraphService(industry_profile="critical_infrastructure")
    paths = service.get_critical_propagation_paths()

    assert len(paths) > 0
    # The paths should be sorted by highest risk transfer potential first
    for i in range(len(paths) - 1):
        assert (
            paths[i]["cumulative_risk_transfer"]
            >= paths[i + 1]["cumulative_risk_transfer"]
        )

    # Verify keys
    assert "path" in paths[0]
    assert "source" in paths[0]
    assert "sink" in paths[0]
    assert "cumulative_risk_transfer" in paths[0]


def test_calculate_risk_centrality():
    service = EpistemicGraphService(industry_profile="critical_infrastructure")
    # Volatilities from Phase 1 Monte Carlo (T2 has the highest volatility)
    std_devs = {
        "T1": 0.05,
        "T2": 0.174,
        "T3": 0.08,
        "T4": 0.12,
        "T5": 0.15,
        "T6": 0.06,
        "T7": 0.04,
        "T8": 0.09,
        "T9": 0.05,
        "T10": 0.11,
    }
    centrality = service.calculate_risk_centrality(std_devs)

    # 1. Structural Assertions
    assert len(centrality) == 10
    total_score = sum(centrality.values())
    # Should sum to approximately 1.0 (some rounding float errors may occur, so allow 0.95 to 1.05)
    assert 0.95 <= total_score <= 1.05

    # 2. Risk Centrality Bounds
    for t_id in [f"T{i}" for i in range(1, 11)]:
        assert t_id in centrality
        assert 0.0 <= centrality[t_id] <= 1.0

    # T2 should be the most central risk node because it is highly volatile and has critical dependencies
    max_tower = max(centrality, key=centrality.get)
    assert max_tower == "T2"


def test_epistemic_graph_service_loopy_propagation():
    # Verify that the loopy contraction map algorithm successfully converges on cyclic networks
    service = EpistemicGraphService(industry_profile="critical_infrastructure")

    # Intrinsic maturities: T3 and T5 form a cycle (T3 <-> T5)
    intrinsic = {f"T{i}": 4.5 for i in range(1, 11)}
    # Fail T3 (Core Networks)
    intrinsic["T3"] = 3.0

    propagated = service.propagate_risk(intrinsic)

    # 1. Verification of cyclic propagation
    assert propagated["T3"] == 3.0
    # T5 should be dragged down because T3 -> T5
    assert propagated["T5"] < 4.5
    # T3 should also experience feedback drag from T5, but since its intrinsic is 3.0 (minimum), it stays 3.0.
    # What if we fail T5 instead? Let us verify.
    intrinsic_t5 = {f"T{i}": 4.5 for i in range(1, 11)}
    intrinsic_t5["T5"] = 3.2
    prop_t5 = service.propagate_risk(intrinsic_t5)

    # T3 is dragged down by T5 (T5 -> T3 is an active edge!)
    assert prop_t5["T3"] < 4.5


def test_backpropagate_audit_feedback():
    # Verify that Causal Backpropagation minimizes prediction error (MSE) between targets and actuals
    from pathlib import Path

    # Back up the pristine policy file before testing backpropagation
    policy_file = (
        Path(__file__).resolve().parent.parent.parent
        / "engine_config"
        / "policies"
        / "epistemic_dependencies.json"
    )
    pristine_content = (
        policy_file.read_text(encoding="utf-8-sig") if policy_file.exists() else None
    )

    try:
        service = EpistemicGraphService(industry_profile="critical_infrastructure")

        # Let's create a mismatch between intrinsic target recommendations and actual audited scores
        intrinsic = {f"T{i}": 4.5 for i in range(1, 11)}

        # Actual real-world audited scores have a severe drop in child towers T2 and T5
        audited = {f"T{i}": 4.5 for i in range(1, 11)}
        audited["T2"] = 3.2
        audited["T5"] = 3.4

        # 1st Epoch
        res1 = service.backpropagate_audit_feedback(intrinsic, audited, lr=0.1)
        mse_1 = res1["epoch_mse"]
        assert mse_1 > 0.0

        # Check that some weights actually changed
        updated = res1["updated_weights"]
        assert len(updated) > 0
        for update in updated:
            assert 0.05 <= update["weight_new"] <= 0.95

        # 2nd Epoch
        res2 = service.backpropagate_audit_feedback(intrinsic, audited, lr=0.1)
        mse_2 = res2["epoch_mse"]

        # Verification of continuous learning: the Mean Squared Error MUST decrease!
        assert mse_2 < mse_1
    finally:
        # Restore the pristine policy file to guarantee 100% test isolation and zero side effects on disk
        if pristine_content is not None:
            policy_file.write_text(pristine_content, encoding="utf-8-sig")
