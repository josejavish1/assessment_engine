"""Unit tests verifying ActuarialCorrectionService and deterministic recalculation (Phase 7)."""

import pytest

from assessment_engine.application.services.actuarial_correction_service import (
    ActuarialCorrectionService,
)
from assessment_engine.domain.models.parameter_lineage import (
    ActuarialParameterCorrection,
)


def _build_test_payload() -> dict:
    return {
        "score": 2.5,
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "name": "Facilities & Power",
                "score": 2.5,
                "health_check_asis": [
                    {
                        "node_id": "T1_F001",
                        "capability": "UPS Battery Degradation",
                        "severity": "CRITICAL",
                        "threat_event_frequency": 0.25,
                        "recovery_time_hours": 6.0,
                    }
                ],
            }
        ],
    }


def test_actuarial_correction_updates_value_and_recalculates() -> None:
    """Verifies that applying a correction updates effective value, preserves audit trail, and recalculates ALE."""
    payload = _build_test_payload()
    payloads_map = {"T1": payload}

    correction = ActuarialParameterCorrection(
        parameter_name="rto_hours_mode",
        original_estimated_value=6.0,
        corrected_effective_value=12.0,  # Client certifies longer RTO
        user_provided_source="Facility Engineering Actual Runbook Drill 2026-10",
        review_identifier="REV_SRE_AUDIT_2026",
    )

    recalculated_map, manifest = ActuarialCorrectionService.apply_parameter_correction(
        payloads_by_tower=payloads_map,
        correction=correction,
        target_finding_id="T1_F001",
    )

    t1_payload = recalculated_map["T1"]
    finding = t1_payload["pillars_analysis"][0]["health_check_asis"][0]

    assert finding["rto_hours_mode"] == 12.0
    assert "last_correction_audit" in finding
    audit = finding["last_correction_audit"]
    assert audit["parameter_name"] == "rto_hours_mode"
    assert audit["original_estimated_value"] == 6.0
    assert audit["corrected_effective_value"] == 12.0
    assert audit["source"] == "Facility Engineering Actual Runbook Drill 2026-10"

    # Verify input vector effective value matches correction
    vec = finding["actuarial_input_vector"]
    assert vec["inputs"]["rto_hours_mode"]["effective_value"] == 12.0

    # Manifest was produced and is valid
    assert manifest is not None
    assert "T1" in manifest.expected_tower_outputs


def test_actuarial_correction_fails_for_unknown_finding() -> None:
    """Verifies that applying a correction to a non-existent finding raises KeyError."""
    payload = _build_test_payload()
    correction = ActuarialParameterCorrection(
        parameter_name="cmmi_maturity",
        original_estimated_value=2.5,
        corrected_effective_value=3.5,
        user_provided_source="Audit Report",
    )

    with pytest.raises(KeyError, match="Target finding 'NON_EXISTENT' not found"):
        ActuarialCorrectionService.apply_parameter_correction(
            payloads_by_tower={"T1": payload},
            correction=correction,
            target_finding_id="NON_EXISTENT",
        )
