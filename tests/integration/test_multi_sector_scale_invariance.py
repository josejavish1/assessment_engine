import json
import os
import shutil
from pathlib import Path

import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine


def test_scale_invariance_startup_small_business():
    """Verify that a small startup (Revenue: 3M €) produces proportional losses,
    and regulatory fines are capped by statutory turnover percentage (e.g. 4% = 120,000 €)
    instead of assigning an unanchored fixed 10M € or 150k €/h."""
    client_id = "test_startup_client"
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id
    os.environ["ASSESSMENT_INDUSTRY"] = "SaaS & AI Services"

    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"

    annual_revenue = 3_000_000.0  # 3M € startup
    digital_dependency = 0.6
    expected_hourly = (annual_revenue * digital_dependency) / 8760.0  # ~205.48 €/h

    custom_profile_path.write_text(
        json.dumps({
            "annual_revenue_eur": annual_revenue,
            "digital_dependency_factor": digital_dependency,
            "hourly_downtime_cost_eur": expected_hourly,
            "regulatory_framework": "GDPR",
            "regulatory_fine_cap_ratio": 0.04,  # Max 4% of global turnover
            "capability_calibrations": {
                "AUTH_SERVICE": {
                    "typology": "OPERATIONAL_FRICTION",
                    "annual_waste_eur": 12000.0,
                }
            },
        }),
        encoding="utf-8",
    )

    try:
        graph = EpistemicGraph(client_id=client_id)
        engine = SovereignPolicyEngine(graph)

        payload = {
            "document_meta": {
                "client_name": "AIStartup",
                "tower_code": "T2",
                "tower_name": "API Platforms",
                "tower_id": "T2",
            },
            "pillars_analysis": [
                {
                    "pilar_id": "T2.P1",
                    "pilar_name": "Auth Infrastructure",
                    "current_maturity": 2.2,
                    "projects_todo": [],
                    "health_check_asis": [
                        {
                            "finding": "Microservice latency breach in user login",
                            "impact": "Transient disruption to subscriber authentication",
                            "capability": "AUTH_SERVICE",
                        }
                    ],
                }
            ],
        }

        compiled = engine.compile(payload)
        finding = compiled["pillars_analysis"][0]["health_check_asis"][0]

        # 1. Operational friction loss must not exceed 10% of annual revenue (300k €),
        # completely avoiding the 150k fixed cap or 2M+ catastrophic numbers:
        assert finding["fair_max_score"] < 50_000.0, (
            f"Startup max loss must scale to turnover; expected < 50k €, got {finding['fair_max_score']:,.2f} €"
        )
        assert finding["fair_ale_score"] < 20_000.0, (
            f"Startup ALE must scale to turnover; expected < 20k €, got {finding['fair_ale_score']:,.2f} €"
        )
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))


def test_sector_invariance_arbitrary_industry():
    """Verify that any uncataloged industry (e.g. 'Aquaculture & Marine Biotech')
    is processed cleanly without hardcoded branch matching ('Energy', 'Critical Infrastructure')
    and resolves declarative scale invariants gracefully."""
    client_id = "test_marine_client"
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id
    os.environ["ASSESSMENT_INDUSTRY"] = "Aquaculture & Marine Biotech"

    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"

    annual_revenue = 45_000_000.0  # 45M € Mid-Market
    custom_profile_path.write_text(
        json.dumps({
            "annual_revenue_eur": annual_revenue,
            "digital_dependency_factor": 0.3,
            "hourly_downtime_cost_eur": (annual_revenue * 0.3) / 8760.0,
        }),
        encoding="utf-8",
    )

    try:
        graph = EpistemicGraph(client_id=client_id)
        engine = SovereignPolicyEngine(graph)

        payload = {
            "document_meta": {
                "client_name": "AquaBio Holdings",
                "tower_code": "T2",
                "tower_name": "Telemetry Platforms",
                "tower_id": "T2",
            },
            "pillars_analysis": [
                {
                    "pilar_id": "T2.P1",
                    "pilar_name": "Sensor Fabric",
                    "current_maturity": 2.5,
                    "projects_todo": [],
                    "health_check_asis": [
                        {
                            "finding": "Desconexión de sondas térmicas en jaulas oceánicas",
                            "impact": "Pérdida de telemetría de biomasa marina",
                            "capability": "OCEAN_TELEMETRY",
                        }
                    ],
                }
            ],
        }

        compiled = engine.compile(payload)
        finding = compiled["pillars_analysis"][0]["health_check_asis"][0]

        # The calculation must complete without throwing errors and produce sensible bounded metrics:
        assert finding.get("fair_ale_score", 0.0) > 0.0, "ALE score must be positive"
        assert finding.get("fair_max_score", 0.0) > finding.get("fair_min_score", 0.0), (
            "Max score must exceed min score"
        )
        assert finding["fair_max_score"] < 1_000_000.0, (
            f"Expected max loss bounded for 45M € business, got {finding['fair_max_score']:,.2f} €"
        )
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))
