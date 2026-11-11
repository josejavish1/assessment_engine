"""Unit tests for ActuarialInputResolver strict validation and evidence matrix (SR 11-7)."""

from __future__ import annotations

import pytest

from assessment_engine.domain.actuarial.input_resolver import (
    ActuarialInputResolver,
    QuantificationStatus,
)
from assessment_engine.domain.bayesian_fair_copula_engine import OperationalZone
from assessment_engine.domain.models.parameter_lineage import (
    ParameterConfidenceLevel,
    ParameterSourceType,
)
from assessment_engine.domain.taxonomy.archetype_registry import LossArchetypeType


@pytest.fixture
def default_test_zone() -> OperationalZone:
    return OperationalZone(
        zone_id="TEST_ZONE",
        hourly_burn_rate=5000.0,
        max_annual_outage_hours=24.0,
        secondary_loss_retention_factor=0.85,
        catastrophic_recovery_ceiling_hours=24.0,
        emergency_replacement_ratio=0.15,
        tenant_id="TENANT_A",
        legal_entity_id="ENTITY_A",
        operating_site_id="SITE_A",
    )


def test_valid_zero_direct_replacement_cost_preserved(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that direct_replacement_cost=0.0 is preserved as explicit zero and not replaced by pack default."""
    hc = {
        "node_id": "FINDING-001",
        "threat_event_frequency": 0.5,
        "recovery_time_hours": 4.0,
        "direct_replacement_cost": 0.0,
        "cmmi_maturity": 3.0,
    }
    inputs, telemetry, _ = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T1",
        pillar_cmmi=3.0,
        zone=default_test_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
    )
    assert inputs.direct_replacement_cost.effective_value == 0.0
    assert (
        inputs.direct_replacement_cost.source_type
        == ParameterSourceType.ASSESSMENT_PAYLOAD
    )
    assert inputs.direct_replacement_cost.confidence == ParameterConfidenceLevel.HIGH
    assert telemetry.direct_replacement_cost == 0.0


def test_valid_zero_control_effectiveness_alpha_preserved(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that blast_radius_alpha=0.0 is preserved and not overwritten by falsy or."""
    hc = {
        "node_id": "FINDING-002",
        "blast_radius_alpha": 0.0,
    }
    inputs, telemetry, _ = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T1",
        pillar_cmmi=3.0,
        zone=default_test_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
    )
    assert inputs.blast_radius_alpha.effective_value == 0.0
    assert (
        inputs.blast_radius_alpha.source_type == ParameterSourceType.ASSESSMENT_PAYLOAD
    )
    assert telemetry.blast_radius_alpha == 0.0


def test_valid_zero_intra_domain_correlation_rho_preserved(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that shared_dependence_factor=0.0 is preserved and not overwritten by falsy or."""
    hc = {
        "node_id": "FINDING-003",
        "shared_dependence_factor": 0.0,
    }
    inputs, telemetry, _ = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T1",
        pillar_cmmi=3.0,
        zone=default_test_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
    )
    assert inputs.shared_dependence_factor.effective_value == 0.0
    assert (
        inputs.shared_dependence_factor.source_type
        == ParameterSourceType.ASSESSMENT_PAYLOAD
    )
    assert telemetry.shared_dependence_factor == 0.0


def test_valid_zero_audit_k_failures_preserved(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that audit_k_failures=0 is preserved alongside trials count."""
    hc = {
        "node_id": "FINDING-004",
        "audit_k_failures": 0,
        "audit_n_trials": 10,
    }
    inputs, telemetry, _ = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T1",
        pillar_cmmi=3.0,
        zone=default_test_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
    )
    assert inputs.audit_k_failures.effective_value == 0
    assert inputs.audit_n_trials.effective_value == 10
    assert telemetry.audit_k_failures == 0
    assert telemetry.audit_n_trials == 10


def test_negative_tef_raises_value_error(default_test_zone: OperationalZone) -> None:
    """Verifies that negative threat_event_frequency raises ValueError rather than silent fallback."""
    hc = {
        "node_id": "FINDING-ERR-1",
        "threat_event_frequency": -0.5,
    }
    with pytest.raises(ValueError, match="tef_annual"):
        ActuarialInputResolver.resolve_finding_inputs(
            hc=hc,
            tower_id="T1",
            pillar_cmmi=3.0,
            zone=default_test_zone,
            archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
            currency_code="EUR",
        )


def test_zero_or_negative_rto_raises_value_error(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that non-positive RTO hours raise ValueError rather than silent fallback."""
    for invalid_rto in [0.0, -4.0]:
        hc = {
            "node_id": "FINDING-ERR-2",
            "recovery_time_hours": invalid_rto,
        }
        with pytest.raises(ValueError, match="rto_hours"):
            ActuarialInputResolver.resolve_finding_inputs(
                hc=hc,
                tower_id="T1",
                pillar_cmmi=3.0,
                zone=default_test_zone,
                archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
                currency_code="EUR",
            )


def test_inverted_pert_raises_value_error_without_reordering(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that inverted PERT bounds raise ValueError rather than silent auto-reordering."""
    hc = {
        "node_id": "FINDING-ERR-3",
        "threat_event_frequency": 4.0,
        "tef_pert_min": 10.0,
        "tef_pert_max": 8.0,
    }
    with pytest.raises(ValueError, match="PERT ordering violated"):
        ActuarialInputResolver.resolve_finding_inputs(
            hc=hc,
            tower_id="T1",
            pillar_cmmi=3.0,
            zone=default_test_zone,
            archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
            currency_code="EUR",
        )


def test_cmmi_out_of_bounds_raises_value_error(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that CMMI maturity outside [1.0, 5.0] raises ValueError."""
    for invalid_cmmi in [0.5, 6.0]:
        hc = {
            "node_id": "FINDING-ERR-4",
            "cmmi_maturity": invalid_cmmi,
        }
        with pytest.raises(ValueError, match="cmmi_maturity"):
            ActuarialInputResolver.resolve_finding_inputs(
                hc=hc,
                tower_id="T1",
                pillar_cmmi=3.0,
                zone=default_test_zone,
                archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
                currency_code="EUR",
            )


def test_k_failures_greater_than_n_trials_raises_value_error(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that audit_k_failures > audit_n_trials raises ValueError rather than mutating n."""
    hc = {
        "node_id": "FINDING-ERR-5",
        "audit_k_failures": 12,
        "audit_n_trials": 10,
    }
    with pytest.raises(ValueError, match="cannot exceed"):
        ActuarialInputResolver.resolve_finding_inputs(
            hc=hc,
            tower_id="T1",
            pillar_cmmi=3.0,
            zone=default_test_zone,
            archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
            currency_code="EUR",
        )


def test_garbage_boolean_is_spof_raises_value_error(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that invalid boolean string raises ValueError."""
    hc = {
        "node_id": "FINDING-ERR-6",
        "is_spof": "garbage_string",
    }
    with pytest.raises(ValueError, match="is_spof"):
        ActuarialInputResolver.resolve_finding_inputs(
            hc=hc,
            tower_id="T1",
            pillar_cmmi=3.0,
            zone=default_test_zone,
            archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
            currency_code="EUR",
        )


def test_missing_material_parameter_downgrades_status_to_estimated_low_confidence(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that omitting replacement cost when TEF/RTO are explicit yields ESTIMATED_LOW_CONFIDENCE."""
    hc = {
        "node_id": "FINDING-ESTIMATED",
        "threat_event_frequency": 0.5,
        "recovery_time_hours": 4.0,
        "cmmi_maturity": 3.0,
        # direct_replacement_cost is omitted -> falls back to pack
    }
    _, _, status = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T1",
        pillar_cmmi=3.0,
        zone=default_test_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
    )
    assert status == QuantificationStatus.ESTIMATED_LOW_CONFIDENCE


def test_valid_explicit_finding_produces_quantified_status(
    default_test_zone: OperationalZone,
) -> None:
    """Verifies that an explicitly observed finding with all material inputs produces QUANTIFIED."""
    hc = {
        "node_id": "FINDING-QUANTIFIED",
        "threat_event_frequency": 0.5,
        "recovery_time_hours": 4.0,
        "direct_replacement_cost": 25000.0,
        "cmmi_maturity": 3.5,
    }
    _, _, status = ActuarialInputResolver.resolve_finding_inputs(
        hc=hc,
        tower_id="T1",
        pillar_cmmi=3.5,
        zone=default_test_zone,
        archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
        currency_code="EUR",
    )
    assert status == QuantificationStatus.QUANTIFIED
