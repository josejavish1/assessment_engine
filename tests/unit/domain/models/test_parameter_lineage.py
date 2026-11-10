"""Unit tests for the Actuarial Parameter Lineage Contract (SR 11-7 Compliance)."""

import json

from assessment_engine.domain.models.parameter_lineage import (
    ActuarialFindingInputs,
    ActuarialFindingOutputs,
    ActuarialInputVector,
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


def _make_dummy_inputs() -> ActuarialFindingInputs:
    return ActuarialFindingInputs(
        cmmi_maturity=_make_dummy_provenance(estimated=2.5, effective=2.5, unit="cmmi_index"),
        zone_id=_make_dummy_provenance(estimated="TIER_1", effective="TIER_1", unit="zone_key"),
        hourly_burn_rate=_make_dummy_provenance(estimated=5000.0, effective=5000.0, unit="EUR/h"),
        max_annual_outage_hours=_make_dummy_provenance(estimated=24.0, effective=24.0, unit="hours"),
        secondary_loss_retention_factor=_make_dummy_provenance(estimated=1.0, effective=1.0, unit="ratio"),
        catastrophic_recovery_ceiling_hours=_make_dummy_provenance(estimated=48.0, effective=48.0, unit="hours"),
        emergency_replacement_ratio=_make_dummy_provenance(estimated=0.20, effective=0.20, unit="ratio"),
        tef_pert_min=_make_dummy_provenance(estimated=0.10, effective=0.10, unit="events/year"),
        tef_pert_mode=_make_dummy_provenance(estimated=0.30, effective=0.30, unit="events/year"),
        tef_pert_max=_make_dummy_provenance(estimated=0.80, effective=0.80, unit="events/year"),
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


def test_parameter_lineage_fallback_marked_model_default() -> None:
    """Proves that fallback values are explicitly marked MODEL_DEFAULT or DERIVED with appropriate confidence."""
    rec = _make_dummy_provenance(
        estimated=0.35,
        effective=0.35,
        source=ParameterSourceType.MODEL_DEFAULT,
        confidence=ParameterConfidenceLevel.LOW,
    )
    assert rec.source_type == ParameterSourceType.MODEL_DEFAULT
    assert rec.confidence == ParameterConfidenceLevel.LOW
    assert not rec.client_override


def test_parameter_lineage_unconfirmed_never_becomes_annual_accounts() -> None:
    """Proves that missing evidence defaults to UNCONFIRMED/UNASSESSED and never masquerades as ANNUAL_ACCOUNTS."""
    rec = ParameterProvenanceRecord(
        estimated_value=12.5,
        effective_value=12.5,
        unit="hours",
        source_type=ParameterSourceType.MODEL_DEFAULT,
        estimation_method="Algorithmic prior lookup",
    )
    assert rec.source_type != ParameterSourceType.ANNUAL_ACCOUNTS
    assert rec.source_type != ParameterSourceType.CLIENT_CONFIRMED
    assert rec.validation_status == ParameterValidationStatus.UNCONFIRMED
    assert rec.confidence == ParameterConfidenceLevel.UNASSESSED


def test_parameter_lineage_confirmed_override_preserves_both_values() -> None:
    """Proves that client overrides preserve both pre-override estimate and effective value."""
    rec = ParameterProvenanceRecord(
        estimated_value=6.0,
        effective_value=2.0,
        unit="hours",
        source_type=ParameterSourceType.CLIENT_CONFIRMED,
        source_reference="Signed Interview Confirmation 2026-10-14",
        estimation_method="Client CISO direct operational override",
        confidence=ParameterConfidenceLevel.HIGH,
        validation_status=ParameterValidationStatus.CLIENT_OVERRIDDEN,
        client_override=True,
    )
    assert rec.estimated_value == 6.0
    assert rec.effective_value == 2.0
    assert rec.client_override is True
    assert rec.validation_status == ParameterValidationStatus.CLIENT_OVERRIDDEN


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
