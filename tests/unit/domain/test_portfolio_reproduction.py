"""Unit and integration tests verifying portfolio reproduction and scoped zone integrity."""

from dataclasses import replace

import pytest

from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    FindingTelemetry,
    OperationalZone,
    create_reproduction_manifest,
    replay_portfolio_simulation,
)


def _build_test_telemetry() -> list[FindingTelemetry]:
    z1 = OperationalZone(
        zone_id="TIER_1_MISSION_CRITICAL",
        hourly_burn_rate=12500.0,
        max_annual_outage_hours=24.0,
        secondary_loss_retention_factor=0.90,
        tenant_id="TENANT_A",
        operating_site_id="SITE_MADRID",
    )
    z2 = OperationalZone(
        zone_id="TIER_2_CORE_OPERATIONS",
        hourly_burn_rate=6500.0,
        max_annual_outage_hours=48.0,
        secondary_loss_retention_factor=0.75,
        tenant_id="TENANT_A",
        operating_site_id="SITE_MADRID",
    )

    f1 = FindingTelemetry(
        finding_id="T1_F001",
        tower_id="T1",
        title="Active-Active Storage Partition Failure",
        cmmi_maturity=2.2,
        zone=z1,
        tef_pert_min=0.10,
        tef_pert_mode=0.35,
        tef_pert_max=0.90,
        rto_hours_min=2.0,
        rto_hours_mode=5.5,
        rto_hours_max=16.0,
        secondary_loss_mean=18000.0,
        is_spof=True,
    )
    f2 = FindingTelemetry(
        finding_id="T4_F001",
        tower_id="T4",
        title="Industrial SCADA Gateway Bypass",
        cmmi_maturity=2.8,
        zone=z2,
        tef_pert_min=0.05,
        tef_pert_mode=0.20,
        tef_pert_max=0.55,
        rto_hours_min=1.0,
        rto_hours_mode=4.0,
        rto_hours_max=12.0,
        secondary_loss_mean=25000.0,
        is_spof=False,
    )
    return [f1, f2]


def test_deterministic_portfolio_reproduction_end_to_end() -> None:
    """Verifies that a simulated portfolio reproduces bit-for-bit across all metrics."""
    engine = BayesianFairCopulaEngine(num_simulations=2048)
    findings = _build_test_telemetry()
    summary = engine.evaluate_portfolio(findings, currency_code="EUR")

    manifest = create_reproduction_manifest(
        engine=engine,
        findings=findings,
        summary=summary,
        currency_code="EUR",
    )

    result = replay_portfolio_simulation(manifest, currency_tolerance=0.01)
    assert result["verified"] is True
    assert result["seed_hash"] == summary.deterministic_seed_hash
    assert result["total_portfolio_ale"] == summary.total_portfolio_ale
    assert result["portfolio_var_90"] == summary.portfolio_var_90


def test_changing_retention_factor_changes_deterministic_seed() -> None:
    """Proves that secondary_loss_retention_factor is part of the deterministic fingerprint."""
    engine = BayesianFairCopulaEngine(num_simulations=1024)
    findings_1 = _build_test_telemetry()
    findings_2 = _build_test_telemetry()

    # Modify retention factor on finding 1
    z_mod = OperationalZone(
        zone_id="TIER_1_MISSION_CRITICAL",
        hourly_burn_rate=12500.0,
        max_annual_outage_hours=24.0,
        secondary_loss_retention_factor=0.50,  # Changed from 0.90
        tenant_id="TENANT_A",
        operating_site_id="SITE_MADRID",
    )
    findings_2[0] = replace(findings_2[0], zone=z_mod)

    _, hash_1 = engine._compute_deterministic_seed(findings_1, currency_code="EUR")
    _, hash_2 = engine._compute_deterministic_seed(findings_2, currency_code="EUR")

    assert hash_1 != hash_2, "Changing secondary_loss_retention_factor MUST change the seed hash!"


def test_changing_inaction_horizon_changes_deterministic_seed() -> None:
    """Proves that inaction_horizon_years is part of the deterministic fingerprint."""
    engine_1 = BayesianFairCopulaEngine(num_simulations=1024, inaction_horizon_years=3.0)
    engine_2 = BayesianFairCopulaEngine(num_simulations=1024, inaction_horizon_years=5.0)
    findings = _build_test_telemetry()

    _, hash_1 = engine_1._compute_deterministic_seed(findings, currency_code="EUR")
    _, hash_2 = engine_2._compute_deterministic_seed(findings, currency_code="EUR")

    assert hash_1 != hash_2, "Changing inaction_horizon_years MUST change the seed hash!"


def test_conflicting_parameters_for_same_scoped_zone_fail_loudly() -> None:
    """Proves that two findings in the same scoped zone with different parameters fail validation."""
    engine = BayesianFairCopulaEngine(num_simulations=512)
    findings = _build_test_telemetry()
    summary = engine.evaluate_portfolio(findings, currency_code="EUR")
    manifest = create_reproduction_manifest(
        engine=engine,
        findings=findings,
        summary=summary,
        currency_code="EUR",
    )

    manifest_dict = manifest.model_dump()
    # Tamper with finding 2: assign it to the SAME scoped zone as finding 1 but with different hourly burn
    manifest_dict["findings_telemetry"][1]["zone_id"] = "TIER_1_MISSION_CRITICAL"
    manifest_dict["findings_telemetry"][1]["tenant_id"] = "TENANT_A"
    manifest_dict["findings_telemetry"][1]["operating_site_id"] = "SITE_MADRID"
    manifest_dict["findings_telemetry"][1]["hourly_burn_rate"] = 99999.0  # Conflict!

    with pytest.raises(ValueError, match="Conflicting parameters detected for scoped zone"):
        replay_portfolio_simulation(manifest_dict)
