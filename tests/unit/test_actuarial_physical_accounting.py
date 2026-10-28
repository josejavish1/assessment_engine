import json
import os
import shutil
from pathlib import Path

import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.fair_risk import FairRiskPolicy


def test_actuarial_physical_accounting_breakdown(tmp_path: Path):
    """Verify that every finding receives an auditable physical loss breakdown
    (downtime hours, lucro cesante, SRE intervention cost) and natural language accounting trace."""
    client_id = "test_accounting_client"
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id

    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"
    evidence_ledger_path = case_dir / "evidence_ledger.json"

    annual_revenue = 25000000.0  # 25M €
    hourly_cost = (annual_revenue * 0.5) / 8760.0  # ~1,426.94 €/h

    custom_profile_path.write_text(
        json.dumps({
            "annual_revenue_eur": annual_revenue,
            "digital_dependency_factor": 0.5,
            "hourly_downtime_cost_eur": hourly_cost,
            "hourly_rate_sre_eur": 45.0,
            "capability_calibrations": {
                "OBSERVABILITY": {
                    "typology": "OPERATIONAL_FRICTION",
                    "exposure_factor": 0.8,
                }
            },
        }),
        encoding="utf-8",
    )

    evidence_ledger_path.write_text(
        json.dumps({
            "evidences": [
                {
                    "fragment_id": "ev_gap_1",
                    "pillar_ids": ["T2.P1"],
                    "supports": ["gap", "risk"],
                    "excerpt": "Lack of centralized tracing and distributed APM across microservices.",
                },
                {
                    "fragment_id": "ev_asis_1",
                    "pillar_ids": ["T2.P1"],
                    "supports": ["asis"],
                    "excerpt": "Basic Prometheus server deployed on a single instance.",
                },
            ]
        }),
        encoding="utf-8",
    )

    try:
        graph = EpistemicGraph(client_id=client_id)
        policy = FairRiskPolicy()

        payload = {
            "document_meta": {
                "client_name": client_id,
                "tower_code": "T2",
                "tower_name": "Platforms",
                "tower_id": "T2",
            },
            "pillars_analysis": [
                {
                    "pilar_id": "T2.P1",
                    "pilar_name": "Observability Foundation",
                    "score": 2.2,
                    "gaps": [{"statement": "Missing APM tracing across services"}],
                    "strengths": [{"statement": "Prometheus active"}],
                    "health_check_asis": [
                        {
                            "finding": "High latency in tracing production incidents without APM",
                            "impact": "Extended MTTR during customer transaction failures",
                            "capability": "OBSERVABILITY",
                            "severity": "Medium",
                        }
                    ],
                }
            ],
        }

        patched = policy.evaluate_and_patch(graph, payload)
        finding = patched["pillars_analysis"][0]["health_check_asis"][0]

        # 1. Physical loss breakdown must be present
        assert "physical_loss_breakdown" in finding
        breakdown = finding["physical_loss_breakdown"]
        assert breakdown["downtime_hours"] > 0
        assert breakdown["hourly_downtime_cost_eur"] == round(hourly_cost, 2)
        assert breakdown["lucro_cesante_eur"] > 0
        assert breakdown["sre_cost_eur"] > 0
        assert breakdown["direct_incident_cost_eur"] > 0

        # 2. Auditable plain-text justification must be present
        assert "audit_justification" in finding
        assert "Pérdida primaria contable estimada" in finding["audit_justification"]
        assert (
            "1.426,94 €" in finding["audit_justification"]
            or "1,426.94 €" in finding["audit_justification"]
            or "1426.94" in finding["audit_justification"]
        )

        # 3. Typology must be OPERATIONAL_FRICTION (TCO) without any Spanish keywords
        assert finding["is_operational_friction"] is True
        assert finding["typology"] == "OPERATIONAL_FRICTION"
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))
