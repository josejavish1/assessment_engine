"""Unit tests for the Actuarial Parameter Lineage Contract (SR 11-7 Compliance)."""

import json

import pytest
from pydantic import ValidationError

from assessment_engine.domain.models.parameter_lineage import (
    ActuarialFindingInputs,
    ActuarialFindingOutputs,
    ActuarialInputVector,
    ActuarialParameterCorrection,
    ParameterConfidenceLevel,
    ParameterProvenanceRecord,
    ParameterSourceType,
    ParameterValidationStatus,
)


def _make_dummy_provenance(
    estimated: float = 1.0,
    effective: float = 1.0,
    source: ParameterSourceType = ParameterSourceType.MODEL_DEFAULT,
    confidence: ParameterConfidenceLevel = ParameterConfidenceLevel.LOW,
    status: ParameterValidationStatus = ParameterValidationStatus.UNCONFIRMED,
    override: bool = False,
    unit: str = "hours",
) -> ParameterProvenanceRecord:
    return ParameterProvenanceRecord(
        estimated_value=estimated,
        effective_value=effective,
        unit=unit,
        source_type=source,
        estimation_method="Standard test benchmark",
        confidence=confidence,
        validation_status=status,
        client_override=override,
    )


def _make_dummy_inputs(
    tef_min: float = 0.10,
    tef_mode: float = 0.30,
    tef_max: float = 0.80,
    cmmi: float = 2.5,
) -> ActuarialFindingInputs:
    return ActuarialFindingInputs(
        cmmi_maturity=_make_dummy_provenance(estimated=cmmi, effective=cmmi, unit="cmmi_index"),
        zone_id=_make_dummy_provenance(estimated="TIER_1", effective="TIER_1", unit="zone_key"),
        hourly_burn_rate=_make_dummy_provenance(estimated=5000.0, effective=5000.0, unit="EUR/h"),
        max_annual_outage_hours=_make_dummy_provenance(estimated=24.0, effective=24.0, unit="hours"),
        secondary_loss_retention_factor=_make_dummy_provenance(estimated=1.0, effective=1.0, unit="ratio"),
        catastrophic_recovery_ceiling_hours=_make_dummy_provenance(estimated=48.0, effective=48.0, unit="hours"),
        emergency_replacement_ratio=_make_dummy_provenance(estimated=0.20, effective=0.20, unit="ratio"),
        tef_pert_min=_make_dummy_provenance(estimated=tef_min, effective=tef_min, unit="events/year"),
        tef_pert_mode=_make_dummy_provenance(estimated=tef_mode, effective=tef_mode, unit="events/year"),
        tef_pert_max=_make_dummy_provenance(estimated=tef_max, effective=tef_max, unit="events/year"),
        rto_hours_min=_make_dummy_provenance(estimated=2.0, effective=2.0, unit="hours"),
        rto_hours_mode=_make_dummy_provenance(estimated=6.0, effective=6.0, unit="hours"),
        rto_hours_max=_make_dummy_provenance(estimated=14.0, effective=14.0, unit="hours"),
        secondary_loss_mean=_make_dummy_provenance(estimated=3000.0, effective=3000.0, unit="EUR"),
        is_spof=_make_dummy_provenance(estimated=False, effective=False, unit="boolean"),
        shared_dependence_factor=_make_dummy_provenance(estimated=0.20, effective=0.20, unit="ratio"),
        blast_radius_alpha=_make_dummy_provenance(estimated=0.50, effective=0.50, unit="ratio"),
        catastrophic_rto_hours=_make_dummy_provenance(estimated=24.0, effective=24.0, unit="hours"),
        direct_replacement_cost=_make_dummy_provenance(estimated=0.0, effective=0.0, unit="EUR"),
        audit_k_failures=_make_dummy_provenance(estimated=2, effective=2, unit="count"),
        audit_n_trials=_make_dummy_provenance(estimated=8, effective=8, unit="count"),
    )


def _make_dummy_outputs() -> ActuarialFindingOutputs:
    return ActuarialFindingOutputs(
        mean_vuln=0.32,
        mean_lef=0.25,
        mean_sle=15000.0,
        standalone_ale=3750.0,
        portfolio_allocated_ale=2950.0,
        var_90=7800.0,
        cvar_90=12400.0,
        var_95=10500.0,
        var_99=18000.0,
        cvar_99=22500.0,
        worst_crisis_event=45000.0,
        worst_crisis_rto_hours=18.0,
    )


def test_parameter_lineage_explicit_inputs_survive_unchanged() -> None:
    """Proves that explicit inputs are faithfully preserved in effective_value."""
    rec = _make_dummy_provenance(
        estimated=4.5,
        effective=4.5,
        source=ParameterSourceType.ASSESSMENT_PAYLOAD,
        confidence=ParameterConfidenceLevel.MEDIUM,
    )
    assert rec.estimated_value == 4.5
    assert rec.effective_value == 4.5
    assert rec.source_type == ParameterSourceType.ASSESSMENT_PAYLOAD


def test_parameter_lineage_override_false_requires_equal_values() -> None:
    """Invariant 1: client_override == False requires estimated_value == effective_value."""
    with pytest.raises(ValidationError, match="client_override is False but estimated_value"):
        ParameterProvenanceRecord(
            estimated_value=10.0,
            effective_value=5.0,
            unit="hours",
            source_type=ParameterSourceType.MODEL_DEFAULT,
            estimation_method="Default lookup",
            client_override=False,
        )


def test_parameter_lineage_provenance_requires_reference() -> None:
    """Invariant 4: ANNUAL_ACCOUNTS, EXTERNAL_BENCHMARK, and CLIENT_CONFIRMED require a non-empty source_reference."""
    with pytest.raises(ValidationError, match="requires a non-empty source_reference"):
        ParameterProvenanceRecord(
            estimated_value=1000.0,
            effective_value=1000.0,
            unit="EUR",
            source_type=ParameterSourceType.ANNUAL_ACCOUNTS,
            source_reference="",
            estimation_method="Annual reports",
        )


def test_parameter_lineage_pert_ordering_enforced() -> None:
    """Invariant 7: PERT values must satisfy min <= mode <= max."""
    with pytest.raises(ValidationError, match="PERT Invariant Violation for TEF"):
        _make_dummy_inputs(tef_min=0.80, tef_mode=0.30, tef_max=0.10)


def test_parameter_lineage_cmmi_bounds_enforced() -> None:
    """Invariant 8: CMMI maturity must be in [1.0, 5.0]."""
    with pytest.raises(ValidationError, match="CMMI maturity must be in"):
        _make_dummy_inputs(cmmi=0.50)


def test_parameter_correction_contract() -> None:
    """Verifies that client parameter corrections enforce whitelist and audit metadata."""
    corr = ActuarialParameterCorrection(
        parameter_name="hourly_burn_rate",
        original_estimated_value=13061.29,
        corrected_effective_value=11500.0,
        user_provided_source="Corporate Controller Signed Audit Note",
        review_identifier="REV_2026_Q4_001",
    )
    assert corr.parameter_name == "hourly_burn_rate"
    assert corr.corrected_effective_value == 11500.0
    assert corr.recalculation_occurred is True

    with pytest.raises(ValidationError, match="not in permitted actuarial correction whitelist"):
        ActuarialParameterCorrection(
            parameter_name="forbidden_custom_variable",
            original_estimated_value=1.0,
            corrected_effective_value=2.0,
            user_provided_source="Test",
        )


def test_parameter_lineage_json_roundtrip_preserves_contract() -> None:
    """Proves that complete ActuarialInputVector survives serialization/deserialization."""
    vector = ActuarialInputVector(
        finding_id="T1_F001",
        tower_id="T1",
        currency_code="EUR",
        inputs=_make_dummy_inputs(),
        outputs=_make_dummy_outputs(),
    )
    raw_json = vector.model_dump_json()
    reconstituted = ActuarialInputVector.model_validate(json.loads(raw_json))
    assert reconstituted == vector
    assert reconstituted.outputs.var_90 == 7800.0
    assert reconstituted.inputs.tef_pert_mode.effective_value == 0.30
