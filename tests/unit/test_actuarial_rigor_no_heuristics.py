import json
import os
import shutil
from pathlib import Path

import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.evolution.epistemic_distiller import EpistemicDistiller
from assessment_engine.infrastructure.policies.fair_risk import FairRiskPolicy


def test_fair_risk_secondary_fine_not_clamped_to_downtime():
    """Verify that statutory regulatory fines under NIS2/GDPR are NOT artificially clamped
    to 8 hours of internal IT downtime (hourly * 8.0)."""
    client_id = "test_statutory_client"
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id

    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"

    # Small client (hourly cost = 200 €/h) with 2,000,000 € statutory fine cap
    custom_profile_path.write_text(
        json.dumps({
            "annual_revenue_eur": 5000000.0,
            "hourly_downtime_cost_eur": 200.0,
            "reg_max_fine_eur": 2000000.0,
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
                    "pilar_name": "Platform Foundation",
                    "score": 1.5,  # Low score triggers high fine probability
                    "health_check_asis": [
                        {
                            "finding": "Breach of NIS2 multi-factor and logging mandate",
                            "impact": "Exposed critical control failure under Art 34",
                            "severity": "Critical",
                        }
                    ],
                }
            ],
        }

        patched = policy.evaluate_and_patch(graph, payload)
        finding = patched["pillars_analysis"][0]["health_check_asis"][0]

        # The maximum possible loss (fair_max_score) must exceed 8 hours of downtime (1,600 €)
        # by an order of magnitude, reflecting true regulatory exposure.
        assert finding["fair_max_score"] > 5000.0, (
            f"Expected statutory fine exposure > 5,000 €, but got {finding['fair_max_score']:,.2f} €"
        )
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))


def test_epistemic_distiller_sector_aligned_leaders():
    """Verify that sector 'energy' defaults to industrial/energy leaders, NOT payment gateways (Stripe/Adyen)."""
    distiller = EpistemicDistiller()
    # Empty response forcing seed/fallback extraction
    dossier = distiller._parse_json_response(
        raw_text="{}",
        task="SCADA Telemetry Integration",
        sector="energy",
        queries=["industrial energy SCADA"],
    )

    assert "Stripe" not in dossier.leaders_analyzed
    assert "Schneider Electric" in dossier.leaders_analyzed or "Siemens Energy" in dossier.leaders_analyzed
