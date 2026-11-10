"""Integration test verifying migration of legacy payloads to canonical actuarial contracts."""

from assessment_engine.application.services.canonical_risk_orchestrator import (
    CanonicalRiskOrchestrator,
    QuantificationStatus,
)


def test_legacy_payload_migration_to_canonical_contract() -> None:
    """Verifies that an unquantified legacy payload is safely upgraded to canonical outputs and typed lineage."""
    legacy_payload = {
        "score": 2.2,
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "name": "Facilities & Power",
                "score": 2.2,
                "health_check_asis": [
                    {
                        "node_id": "LEGACY_001",
                        "capability": "UPS Battery Degradation",
                        "severity": "HIGH",
                        "threat_event_frequency": 0.40,
                        "loss_magnitude": 3.0,
                        # Missing modern actuarial vector, RTO, or copula metrics
                    }
                ],
            }
        ],
    }

    upgraded = CanonicalRiskOrchestrator.quantify_single_tower(
        tower_id="T1",
        blueprint_payload=legacy_payload,
        global_context={
            "financial_telemetry": {
                "authoritative_hourly_downtime_cost": 8000.0,
                "currency": "EUR",
            }
        },
    )

    assert (
        upgraded["quantification_status"]
        == QuantificationStatus.ESTIMATED_LOW_CONFIDENCE.value
    )
    assert upgraded["total_fair_ale"] > 0.0
    assert upgraded["total_fair_p90"] >= upgraded["total_fair_ale"]
    assert upgraded["total_fair_cvar_90"] >= upgraded["total_fair_p90"]

    # Verify finding contract was upgraded
    finding = upgraded["pillars_analysis"][0]["health_check_asis"][0]
    assert (
        finding["quantification_status"]
        == QuantificationStatus.ESTIMATED_LOW_CONFIDENCE.value
    )
    assert finding["fair_ale_score"] > 0.0
    assert "actuarial_input_vector" in finding

    vector = finding["actuarial_input_vector"]
    assert vector["currency_code"] == "EUR"
    assert "inputs" in vector and "outputs" in vector
    assert vector["inputs"]["cmmi_maturity"]["effective_value"] == 2.2
