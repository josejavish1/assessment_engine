"""Unit test suite for the Constitutional Pre-flight Actuarial CFO Audit Gate."""

from __future__ import annotations

from decimal import Decimal
import pytest

from assessment_engine.domain.cfo_actuarial_gate import (
    ActuarialAuditGateViolationError,
    ActuarialAuditPolicy,
    CfoActuarialGate,
)


def test_scenario_realism_mttr_floor() -> None:
    gate = CfoActuarialGate()
    # 1.0h is below the 1.5h operational recovery floor
    with pytest.raises(ActuarialAuditGateViolationError, match="below the configured operational recovery floor"):
        gate.verify_scenario_realism(
            mttr_hours=1.0,
            hourly_rate=15000.0,
            parts_cost=5000.0,
            sle=20000.0,
            lef=0.3,
            ale=6000.0,
        )


def test_scenario_realism_cold_rebuild_floor() -> None:
    gate = CfoActuarialGate()
    # Cold rebuild requires at least 4.0h
    with pytest.raises(ActuarialAuditGateViolationError, match="below the configured operational recovery floor"):
        gate.verify_scenario_realism(
            mttr_hours=2.5,
            hourly_rate=10000.0,
            parts_cost=2000.0,
            sle=27000.0,
            lef=0.2,
            ale=5400.0,
            is_cold_rebuild=True,
        )


def test_scenario_realism_parametric_sle_mismatch() -> None:
    gate = CfoActuarialGate()
    # Expected SLE = (2.5 * 10000) + 5000 = 30000, but provided 45000
    with pytest.raises(ActuarialAuditGateViolationError, match="Parametric SLE mismatch"):
        gate.verify_scenario_realism(
            mttr_hours=2.5,
            hourly_rate=10000.0,
            parts_cost=5000.0,
            sle=45000.0,
            lef=0.2,
            ale=6000.0,
        )


def test_scenario_realism_parametric_ale_mismatch() -> None:
    gate = CfoActuarialGate()
    # SLE = 30000, LEF = 0.2 -> Expected ALE = 6000, but provided 12000
    with pytest.raises(ActuarialAuditGateViolationError, match="Parametric ALE mismatch"):
        gate.verify_scenario_realism(
            mttr_hours=2.5,
            hourly_rate=10000.0,
            parts_cost=5000.0,
            sle=30000.0,
            lef=0.2,
            ale=12000.0,
        )


def test_probabilistic_tone_filter_forbidden_tokens() -> None:
    gate = CfoActuarialGate()
    bad_narratives = [
        "A single node failure guarantees a full cluster outage.",
        "The architecture is 100% certain to fail under peak load.",
        "A power transient inevitably causes database corruption.",
        "This configuration will inevitably result in prolonged downtime.",
    ]
    for text in bad_narratives:
        with pytest.raises(ActuarialAuditGateViolationError, match="forbidden deterministic certainty token"):
            gate.verify_probabilistic_tone(text)


def test_probabilistic_tone_filter_custom_tokens() -> None:
    gate = CfoActuarialGate()
    # Test custom dynamic localized tokens injected at runtime
    custom_tokens = ["garantiza", "100% seguro", "inevitablemente causará"]
    with pytest.raises(ActuarialAuditGateViolationError, match="forbidden deterministic certainty token"):
        gate.verify_probabilistic_tone(
            "Esta configuracion garantiza un fallo catastrofico.",
            custom_forbidden_tokens=custom_tokens,
        )


def test_probabilistic_tone_filter_passes_on_calibrated_hypotheses() -> None:
    gate = CfoActuarialGate()
    good_text = (
        "Under unmitigated operating conditions, elevated thermal gradients increase "
        "the statistical probability of protective shutdown on cooling compressors."
    )
    # Should not raise
    gate.verify_probabilistic_tone(good_text)


def test_portfolio_double_counting_detection() -> None:
    gate = CfoActuarialGate()
    scenarios = [
        {
            "mttr_hours": 2.5,
            "hourly_downtime_cost": 10000.0,
            "parts_cost": 5000.0,
            "sle_amount": 30000.0,
            "aro_frequency": 0.2,
            "ale_amount": 6000.0,
            "primary_cascade_domain_id": "CLIMATE_COMPRESSOR",
            "is_deduplicated": False,
        },
        {
            "mttr_hours": 2.5,
            "hourly_downtime_cost": 10000.0,
            "parts_cost": 5000.0,
            "sle_amount": 30000.0,
            "aro_frequency": 0.2,
            "ale_amount": 6000.0,
            "primary_cascade_domain_id": "CLIMATE_COMPRESSOR",
            "is_deduplicated": False,  # Duplicate domain without deduplication flag!
        },
    ]
    with pytest.raises(ActuarialAuditGateViolationError, match="Double-counted cascade domain"):
        gate.verify_portfolio(scenarios, annual_enterprise_revenue=10000000.0)


def test_portfolio_revenue_ceiling_exceeded() -> None:
    gate = CfoActuarialGate()
    # Revenue = 1,000,000 EUR. Max allowed ALE = 150,000 EUR.
    # Provided portfolio ALE = 200,000 EUR.
    scenarios = [
        {
            "mttr_hours": 4.0,
            "hourly_downtime_cost": 25000.0,
            "parts_cost": 0.0,
            "sle_amount": 100000.0,
            "aro_frequency": 2.0,
            "ale_amount": 200000.0,
            "primary_cascade_domain_id": "DOM_01",
            "is_deduplicated": False,
        }
    ]
    with pytest.raises(ActuarialAuditGateViolationError, match="exceeds CFO credibility ceiling"):
        gate.verify_portfolio(scenarios, annual_enterprise_revenue=1000000.0)


def test_portfolio_verification_passes_on_grounded_data() -> None:
    gate = CfoActuarialGate()
    scenarios = [
        {
            "mttr_hours": 2.5,
            "hourly_downtime_cost": 15000.0,
            "parts_cost": 7500.0,
            "sle_amount": 45000.0,
            "aro_frequency": 0.36,
            "ale_amount": 16200.0,
            "primary_cascade_domain_id": "HVAC_CHILLER",
            "is_deduplicated": False,
            "narrative_hypothesis": "Absence of cold aisle containment elevates server exhaust thermal gradients.",
        },
        {
            "mttr_hours": 2.0,
            "hourly_downtime_cost": 12000.0,
            "parts_cost": 6000.0,
            "sle_amount": 30000.0,
            "aro_frequency": 0.25,
            "ale_amount": 7500.0,
            "primary_cascade_domain_id": "POWER_ATS",
            "is_deduplicated": False,
            "narrative_hypothesis": "Battery string degradation elevates risk of unconditioned power transient during transfer.",
        },
    ]
    # Revenue = 50,000,000 EUR. Total ALE = 23,700 EUR (< 7.5M EUR ceiling).
    gate.verify_portfolio(scenarios, annual_enterprise_revenue=50000000.0)


def test_actuarial_audit_policy_immutability() -> None:
    """Verify that ActuarialAuditPolicy is immutable and raises FrozenInstanceError on modification."""
    import dataclasses

    policy = ActuarialAuditPolicy()
    assert policy.min_hot_swap_mttr_hours == Decimal("1.5")

    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.tolerance = Decimal("10.0")  # type: ignore[misc]

