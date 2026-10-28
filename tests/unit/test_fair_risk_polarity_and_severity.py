import json
import os
import shutil
from pathlib import Path

import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.fair_risk import FairRiskPolicy


def test_fair_risk_anti_negation_and_severity_bounding(tmp_path: Path):
    """Verify that:
    1. Defensive phrases ('protegido contra ransomware') do not trigger TEF=5.
    2. Low severity findings are bounded to TEF <= 2 and LM <= 2.
    3. Positive evidence ('ausencia de vulnerabilidades') is not counted as failures."""
    client_id = "test_polarity_client"
    os.environ["ASSESSMENT_CLIENT_ID"] = client_id

    case_dir = Path(f"working/{client_id}/T2")
    case_dir.mkdir(parents=True, exist_ok=True)
    custom_profile_path = case_dir / "custom_risk_profile.json"
    evidence_ledger_path = case_dir / "evidence_ledger.json"

    custom_profile_path.write_text(
        json.dumps({
            "annual_revenue_eur": 10000000.0,
            "hourly_downtime_cost_eur": 500.0,
        }),
        encoding="utf-8",
    )

    # Evidence stating positive security posture (must NOT count as failure)
    evidence_ledger_path.write_text(
        json.dumps({
            "evidences": [
                {
                    "fragment_id": "ev1",
                    "pillar_ids": ["T2.P1"],
                    "excerpt": "Ausencia de vulnerabilidades críticas y sin incidencias de seguridad en el último trienio.",
                }
            ]
        }),
        encoding="utf-8",
    )

    try:
        graph = EpistemicGraph(client_id=client_id)
        policy = FairRiskPolicy()

        # Low severity finding with defensive context
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
                    "pilar_name": "Platforms",
                    "score": 4.5,
                    "health_check_asis": [
                        {
                            "finding": "Entorno protegido contra ransomware mediante copias inmutables",
                            "impact": "Riesgo residual menor",
                            "severity": "Low",
                        }
                    ],
                }
            ],
        }

        patched = policy.evaluate_and_patch(graph, payload)
        finding = patched["pillars_analysis"][0]["health_check_asis"][0]

        # 1. TEF must be bounded <= 2 due to Low severity and anti-negation protection
        tef_score = finding.get("threat_event_frequency")
        assert tef_score <= 2, f"Expected TEF <= 2 for protected low-severity finding, got {tef_score}"

        # 2. Loss Magnitude must be bounded <= 2
        lm_score = finding.get("loss_magnitude")
        assert lm_score <= 2, f"Expected LM <= 2 for Low severity, got {lm_score}"

        # 3. ALE must reflect low risk (< 5,000 €)
        assert finding["fair_ale_score"] < 5000.0, f"Expected low ALE, got {finding['fair_ale_score']:,.2f} €"
    finally:
        if Path(f"working/{client_id}").exists():
            shutil.rmtree(Path(f"working/{client_id}"))
