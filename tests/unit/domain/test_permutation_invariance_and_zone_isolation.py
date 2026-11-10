"""Tests verifying complete permutation invariance and scoped zone isolation (Phase 1)."""

import pytest

from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    FindingTelemetry,
    OperationalZone,
)


def _build_multi_site_telemetry() -> tuple[FindingTelemetry, FindingTelemetry, FindingTelemetry]:
    # Site 1 - Madrid
    z_madrid = OperationalZone(
        zone_id="TIER_1_CORE",
        hourly_burn_rate=10000.0,
        max_annual_outage_hours=24.0,
        tenant_id="CORP_X",
        legal_entity_id="ENTITY_ES",
        operating_site_id="SITE_MADRID",
    )
    # Site 2 - London (same zone_id "TIER_1_CORE", different burn rate & site!)
    z_london = OperationalZone(
        zone_id="TIER_1_CORE",
        hourly_burn_rate=25000.0,
        max_annual_outage_hours=12.0,
        tenant_id="CORP_X",
        legal_entity_id="ENTITY_UK",
        operating_site_id="SITE_LONDON",
    )
    # Site 1 - Madrid Secondary
    z_madrid_sec = OperationalZone(
        zone_id="TIER_2_OPS",
        hourly_burn_rate=4000.0,
        max_annual_outage_hours=48.0,
        tenant_id="CORP_X",
        legal_entity_id="ENTITY_ES",
        operating_site_id="SITE_MADRID",
    )

    f1 = FindingTelemetry(
        finding_id="F_MADRID_01",
        tower_id="T1",
        title="Madrid DC UPS Battery Aging",
        cmmi_maturity=2.4,
        zone=z_madrid,
        tef_pert_min=0.10,
        tef_pert_mode=0.30,
        tef_pert_max=0.75,
        rto_hours_min=2.0,
        rto_hours_mode=5.0,
        rto_hours_max=12.0,
        secondary_loss_mean=12000.0,
        is_spof=True,
    )
    f2 = FindingTelemetry(
        finding_id="F_LONDON_01",
        tower_id="T1",
        title="London Trading Floor Gateway Flapping",
        cmmi_maturity=3.1,
        zone=z_london,
        tef_pert_min=0.05,
        tef_pert_mode=0.15,
        tef_pert_max=0.40,
        rto_hours_min=1.0,
        rto_hours_mode=3.0,
        rto_hours_max=8.0,
        secondary_loss_mean=50000.0,
        is_spof=False,
    )
    f3 = FindingTelemetry(
        finding_id="F_MADRID_02",
        tower_id="T2",
        title="Madrid Logistics ERP Desynchronization",
        cmmi_maturity=2.0,
        zone=z_madrid_sec,
        tef_pert_min=0.20,
        tef_pert_mode=0.45,
        tef_pert_max=1.10,
        rto_hours_min=4.0,
        rto_hours_mode=8.0,
        rto_hours_max=24.0,
        secondary_loss_mean=8000.0,
        is_spof=True,
    )
    return f1, f2, f3


def test_complete_permutation_invariance() -> None:
    """Proves that passing findings in reversed or shuffled order produces identical outputs bit-for-bit."""
    engine = BayesianFairCopulaEngine(num_simulations=1024)
    f1, f2, f3 = _build_multi_site_telemetry()

    forward_list = [f1, f2, f3]
    reversed_list = [f3, f2, f1]
    shuffled_list = [f2, f3, f1]

    res_forward = engine.evaluate_portfolio(forward_list, currency_code="EUR")
    res_reversed = engine.evaluate_portfolio(reversed_list, currency_code="EUR")
    res_shuffled = engine.evaluate_portfolio(shuffled_list, currency_code="EUR")

    # Seed hashes must be exactly identical
    assert res_forward.deterministic_seed_hash == res_reversed.deterministic_seed_hash
    assert res_forward.deterministic_seed_hash == res_shuffled.deterministic_seed_hash

    # Portfolio metrics must be exactly equal
    assert res_forward.total_portfolio_ale == res_reversed.total_portfolio_ale == res_shuffled.total_portfolio_ale
    assert res_forward.portfolio_var_90 == res_reversed.portfolio_var_90 == res_shuffled.portfolio_var_90
    assert res_forward.portfolio_cvar_90 == res_reversed.portfolio_cvar_90 == res_shuffled.portfolio_cvar_90

    # Tower-level metrics must be exactly equal
    assert res_forward.towers["T1"].portfolio_allocated_ale == res_reversed.towers["T1"].portfolio_allocated_ale
    assert res_forward.towers["T2"].portfolio_allocated_ale == res_reversed.towers["T2"].portfolio_allocated_ale


def test_scoped_zones_do_not_collide_across_sites() -> None:
    """Proves that distinct sites sharing zone_id='TIER_1_CORE' do not overwrite each other."""
    engine = BayesianFairCopulaEngine(num_simulations=512)
    f1, f2, _ = _build_multi_site_telemetry()

    # Both findings share zone_id="TIER_1_CORE" but have different sites and rates
    res = engine.evaluate_portfolio([f1, f2], currency_code="EUR")

    # London has higher burn rate (25k vs 10k) and higher secondary loss
    # If they collided, one would overwrite the other
    f_res_map = {f.finding_id: f for f in res.towers["T1"].findings}
    assert "F_MADRID_01" in f_res_map
    assert "F_LONDON_01" in f_res_map
    assert f_res_map["F_LONDON_01"].portfolio_allocated_ale > 0.0
    assert f_res_map["F_MADRID_01"].portfolio_allocated_ale > 0.0


def test_conflicting_parameters_in_same_scoped_zone_fail_before_simulation() -> None:
    """Proves that two findings in the exact same scoped zone with different burn rates fail validation."""
    engine = BayesianFairCopulaEngine(num_simulations=512)
    z_a = OperationalZone(
        zone_id="TIER_1_CORE",
        hourly_burn_rate=10000.0,
        max_annual_outage_hours=24.0,
        tenant_id="CORP_X",
        legal_entity_id="ENTITY_ES",
        operating_site_id="SITE_MADRID",
    )
    z_b_conflict = OperationalZone(
        zone_id="TIER_1_CORE",
        hourly_burn_rate=99999.0,  # Conflict!
        max_annual_outage_hours=24.0,
        tenant_id="CORP_X",
        legal_entity_id="ENTITY_ES",
        operating_site_id="SITE_MADRID",
    )
    f1 = FindingTelemetry(
        finding_id="F1",
        tower_id="T1",
        title="F1",
        cmmi_maturity=2.5,
        zone=z_a,
        tef_pert_min=0.1,
        tef_pert_mode=0.2,
        tef_pert_max=0.3,
        rto_hours_min=1.0,
        rto_hours_mode=2.0,
        rto_hours_max=3.0,
        secondary_loss_mean=1000.0,
    )
    f2 = FindingTelemetry(
        finding_id="F2",
        tower_id="T1",
        title="F2",
        cmmi_maturity=2.5,
        zone=z_b_conflict,
        tef_pert_min=0.1,
        tef_pert_mode=0.2,
        tef_pert_max=0.3,
        rto_hours_min=1.0,
        rto_hours_mode=2.0,
        rto_hours_max=3.0,
        secondary_loss_mean=1000.0,
    )

    with pytest.raises(ValueError, match="Conflicting parameters detected for scoped zone"):
        engine.evaluate_portfolio([f1, f2], currency_code="EUR")
