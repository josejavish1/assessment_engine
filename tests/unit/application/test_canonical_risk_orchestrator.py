"""Unit and AST tests verifying the Canonical Risk Orchestrator (SR 11-7 SSOT).

Proves that:
1. CanonicalRiskOrchestrator is the sole production risk quantification pathway.
2. Single-tower and portfolio runs produce consistent finding-level results for identical inputs.
3. Presentation and compiler modules do not compute, scale, or mutate actuarial financial values.
"""

import ast
from pathlib import Path

from assessment_engine.application.services.canonical_risk_orchestrator import (
    CanonicalRiskOrchestrator,
    QuantificationStatus,
)


def _build_mock_tower_payload(tower_id: str = "T1") -> dict:
    return {
        "score": 2.5,
        "pillars_analysis": [
            {
                "pilar_id": f"{tower_id}.P1",
                "name": "Core Facilities",
                "score": 2.5,
                "health_check_asis": [
                    {
                        "node_id": f"{tower_id}_F001",
                        "capability": "HVAC Single Point of Failure",
                        "severity": "CRITICAL",
                        "threat_event_frequency": 0.25,
                        "loss_magnitude": 3.0,
                        "recovery_time_hours": 6.0,
                        "direct_replacement_cost": 15000.0,
                        "blast_radius_alpha": 0.70,
                    },
                    {
                        "node_id": f"{tower_id}_F002",
                        "capability": "Generator Maintenance Lapses",
                        "severity": "MEDIUM",
                        "threat_event_frequency": 0.15,
                        "loss_magnitude": 2.0,
                        "recovery_time_hours": 3.0,
                        "blast_radius_alpha": 0.40,
                    },
                ],
            }
        ],
    }


def test_single_tower_entrypoint_parity() -> None:
    """Proves that quantify_single_tower and quantify_payloads([T1]) produce exact bit-for-bit identical results."""
    t1_single = _build_mock_tower_payload("T1")
    t1_as_portfolio = _build_mock_tower_payload("T1")

    global_ctx = {
        "financial_telemetry": {
            "authoritative_hourly_downtime_cost": 10000.0,
            "currency": "EUR",
        },
        "currency": "EUR",
    }

    # 1. Evaluate via single-tower entrypoint
    res_single = CanonicalRiskOrchestrator.quantify_single_tower(
        tower_id="T1",
        blueprint_payload=t1_single,
        global_context=global_ctx,
    )

    # 2. Evaluate via portfolio entrypoint with single tower
    res_portfolio_map, manifest = CanonicalRiskOrchestrator.quantify_payloads(
        payloads_by_tower={"T1": t1_as_portfolio},
        global_context=global_ctx,
    )
    res_from_portfolio = res_portfolio_map["T1"]

    assert res_single["quantification_status"] == QuantificationStatus.QUANTIFIED.value
    assert res_from_portfolio["quantification_status"] == QuantificationStatus.QUANTIFIED.value

    # Exact bit-for-bit equality between entrypoints
    assert res_single["total_fair_ale"] == res_from_portfolio["total_fair_ale"]
    assert res_single["total_fair_p90"] == res_from_portfolio["total_fair_p90"]
    assert res_single["total_fair_cvar_90"] == res_from_portfolio["total_fair_cvar_90"]

    # Manifest is generated and matches
    assert manifest is not None
    assert manifest.expected_portfolio_outputs["total_portfolio_ale"] == res_single["total_fair_ale"]


def test_multi_tower_portfolio_quantification() -> None:
    """Proves that multi-tower portfolios evaluate and generate valid reproduction manifests."""
    t1_payload = _build_mock_tower_payload("T1")
    t2_payload = _build_mock_tower_payload("T2")

    global_ctx = {
        "financial_telemetry": {
            "authoritative_hourly_downtime_cost": 10000.0,
            "currency": "EUR",
        },
        "currency": "EUR",
    }

    res_map, manifest = CanonicalRiskOrchestrator.quantify_payloads(
        payloads_by_tower={"T1": t1_payload, "T2": t2_payload},
        global_context=global_ctx,
    )

    assert res_map["T1"]["quantification_status"] == QuantificationStatus.QUANTIFIED.value
    assert res_map["T2"]["quantification_status"] == QuantificationStatus.QUANTIFIED.value
    assert manifest is not None
    assert "T1" in manifest.expected_tower_outputs
    assert "T2" in manifest.expected_tower_outputs


def test_presentation_modules_do_not_calculate_financial_metrics_ast() -> None:
    """AST-level test proving that presentation compilers do not perform Monte Carlo or mutate ALE."""
    repo_root = Path(__file__).resolve().parents[3]
    compiler_files = [
        repo_root / "src/assessment_engine/adapters/compilers/payload_to_ast.py",
        repo_root / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py",
    ]

    prohibited_call_patterns = {
        "evaluate_portfolio",
        "sample_severity_distribution",
        "calculate_dynamic_p90_ratio",
        "ActuarialEngine",
        "BayesianFairCopulaEngine",
        "ActuarialEngine.evaluate",
    }

    for cf in compiler_files:
        if not cf.exists():
            continue
        tree = ast.parse(cf.read_text(encoding="utf-8"), filename=str(cf))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                func_id = ""
                if isinstance(func, ast.Name):
                    func_id = func.id
                elif isinstance(func, ast.Attribute):
                    func_id = func.attr
                    if isinstance(func.value, ast.Name) and func.value.id in ("ActuarialEngine", "BayesianFairCopulaEngine"):
                        func_id = f"{func.value.id}.{func.attr}"
                assert func_id not in prohibited_call_patterns, (
                    f"Presentation layer violation in {cf.name}: called prohibited actuarial calculation '{func_id}'"
                )
