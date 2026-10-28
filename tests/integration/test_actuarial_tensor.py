import json
import os
import shutil
from pathlib import Path

import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine


def test_actuarial_tensor_pnl_revenue_scaling():
    """Verify that Loss Magnitude scales proportionally to annual revenue and digital dependency,
    rather than falling back to an unanchored static constant (150,000 €/h)."""
    client_id = "test_pnl_scaling_client"
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id
    os.environ["ASSESSMENT_INDUSTRY"] = "Retail & Commerce"

    # Setup custom risk profile with specific annual revenue and digital dependency
    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"

    annual_revenue = 50_000_000.0  # 50M €
    digital_dependency = 0.5  # 50% revenue dependent on digital platforms
    expected_hourly_cost = (annual_revenue * digital_dependency) / 8760.0  # ~2,853.88 €/h

    custom_profile_path.write_text(
        json.dumps({
            "annual_revenue_eur": annual_revenue,
            "digital_dependency_factor": digital_dependency,
            "hourly_downtime_cost_eur": expected_hourly_cost,
        }),
        encoding="utf-8",
    )

    try:
        graph = EpistemicGraph(client_id=client_id)
        engine = SovereignPolicyEngine(graph)

        payload = {
            "document_meta": {
                "client_name": "RetailCo",
                "tower_code": "T2",
                "tower_name": "Platforms",
                "tower_id": "T2",
            },
            "pillars_analysis": [
                {
                    "pilar_id": "T2.P1",
                    "pilar_name": "Store Platforms",
                    "projects_todo": [],
                    "health_check_asis": [
                        {
                            "finding": "Caída del sistema de cobro en tiendas físicas",
                            "impact": "Indisponibilidad de terminales de punto de venta (TPV)",
                            "capability": "POS_OPERATIONS",
                        }
                    ],
                }
            ],
        }

        compiled = engine.compile(payload)
        finding = compiled["pillars_analysis"][0]["health_check_asis"][0]

        # The calculated Loss Magnitude max and P90 must be scaled relative to the 50M revenue (hourly ~2.8k),
        # not the 150k/h fallback (which would produce ~7.2M max).
        assert finding["fair_max_score"] < 500_000.0, (
            f"Expected P&L scaled max loss < 500k € for a 50M € retailer, got {finding['fair_max_score']:,.2f} €"
        )
        assert finding["fair_ale_score"] < 100_000.0, (
            f"Expected scaled ALE < 100k €, got {finding['fair_ale_score']:,.2f} €"
        )
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))


def test_actuarial_tensor_ontology_driven_typology():
    """Verify that operational friction (TCO, P=1.0) is classified via capability metadata/ontology,
    and does not fail when finding text is written in English or lacks exact Spanish keywords."""
    client_id = "test_ontology_typology_client"
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id

    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"

    custom_profile_path.write_text(
        json.dumps({
            "capability_calibrations": {
                "CLOUD_PROVISIONING": {
                    "typology": "OPERATIONAL_FRICTION",
                    "annual_waste_eur": 45000.0,
                }
            }
        }),
        encoding="utf-8",
    )

    try:
        graph = EpistemicGraph(client_id=client_id)
        engine = SovereignPolicyEngine(graph)

        # Finding text in English without any Spanish keywords ("ticket", "manual", "retraso", etc.)
        payload = {
            "document_meta": {
                "client_name": "GlobalTech",
                "tower_code": "T2",
                "tower_name": "Cloud Platforms",
                "tower_id": "T2",
            },
            "pillars_analysis": [
                {
                    "pilar_id": "T2.P1",
                    "pilar_name": "Infrastructure as Code",
                    "projects_todo": [],
                    "health_check_asis": [
                        {
                            "finding": "Unautomated staging workspace deployment pipeline",
                            "impact": "Engineers spend recurring unbudgeted hours waiting for workspace readiness",
                            "capability": "CLOUD_PROVISIONING",
                        }
                    ],
                }
            ],
        }

        compiled = engine.compile(payload)
        finding = compiled["pillars_analysis"][0]["health_check_asis"][0]

        # Must be recognized as OPERATIONAL_FRICTION (TCO) with probability = 1.0 (ALE equal to annual waste)
        # instead of stochastic CATASTROPHIC_SYSTEMIC:
        is_friction = finding.get("is_operational_friction") is True or finding.get("typology") == "OPERATIONAL_FRICTION"
        assert is_friction, (
            "Expected CLOUD_PROVISIONING to be classified as OPERATIONAL_FRICTION via ontology metadata"
        )
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))


def test_actuarial_tensor_bounded_internal_vulnerability():
    """Verify that an internal, isolated component with a low maturity score (e.g. 2.0)
    does not mathematically collapse to a catastrophic vulnerability (p_vuln >= 0.80)
    when the component has zero external internet exposure."""
    client_id = "test_internal_vuln_client"
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id

    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"

    custom_profile_path.write_text(
        json.dumps({
            "capability_calibrations": {
                "AIR_GAPPED_ARCHIVE": {
                    "exposure_vector": "INTERNAL_ISOLATED",
                    "exposure_factor": 0.1,
                }
            }
        }),
        encoding="utf-8",
    )

    try:
        graph = EpistemicGraph(client_id=client_id)
        engine = SovereignPolicyEngine(graph)

        payload = {
            "document_meta": {
                "client_name": "SecBank",
                "tower_code": "T2",
                "tower_name": "Core Platforms",
                "tower_id": "T2",
            },
            "pillars_analysis": [
                {
                    "pilar_id": "T2.P1",
                    "pilar_name": "Offline Archive",
                    "current_maturity": 2.0,  # Low maturity
                    "projects_todo": [],
                    "health_check_asis": [
                        {
                            "finding": "Backup offline conservado en cinta magnética sin automatización",
                            "impact": "Proceso lento de recuperación en auditorías",
                            "capability": "AIR_GAPPED_ARCHIVE",
                        }
                    ],
                }
            ],
        }

        compiled = engine.compile(payload)
        finding = compiled["pillars_analysis"][0]["health_check_asis"][0]

        # Vulnerability must be conditioned on exposure; for an air-gapped system, p_vuln must not exceed 0.50:
        p_vuln = finding.get("p_vuln", 1.0)
        assert p_vuln < 0.50, (
            f"Expected bounded vulnerability (< 0.50) for air-gapped internal system with maturity 2.0, got {p_vuln:.4f}"
        )
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))
