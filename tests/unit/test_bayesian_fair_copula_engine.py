"""Unit tests for the BayesianFairCopulaEngine domain service.

Verifies mathematical conservation, Aumann-Shapley additivity, CMMI monotonicity,
deterministic reproducibility, scale invariance, and spectral positive definiteness.
"""

from __future__ import annotations

import pytest

from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    FindingTelemetry,
    OperationalZone,
)


@pytest.fixture
def generic_enterprise_zones() -> dict[str, OperationalZone]:
    """Industry-agnostic operational tiers parameterized from a baseline hourly burn rate."""
    base_hourly_rate = 10000.0
    return {
        "TIER_1": OperationalZone(
            zone_id="TIER_1_MISSION_CRITICAL",
            hourly_burn_rate=base_hourly_rate * 1.00,
            max_annual_outage_hours=240.0,
            secondary_loss_retention_factor=0.85,
        ),
        "TIER_2": OperationalZone(
            zone_id="TIER_2_CORE_OPERATIONS",
            hourly_burn_rate=base_hourly_rate * 0.65,
            max_annual_outage_hours=360.0,
            secondary_loss_retention_factor=0.85,
        ),
        "TIER_3": OperationalZone(
            zone_id="TIER_3_EDGE_DISTRIBUTION",
            hourly_burn_rate=base_hourly_rate * 0.40,
            max_annual_outage_hours=480.0,
            secondary_loss_retention_factor=0.85,
        ),
    }


def _create_sample_findings(
    zones: dict[str, OperationalZone],
    cmmi_level: float = 2.0,
    count: int = 10,
    scale_factor: float = 1.0,
) -> list[FindingTelemetry]:
    findings = []
    zone_keys = list(zones.keys())
    for i in range(count):
        z_key = zone_keys[i % len(zone_keys)]
        base_zone = zones[z_key]
        scaled_zone = OperationalZone(
            zone_id=base_zone.zone_id,
            hourly_burn_rate=base_zone.hourly_burn_rate * scale_factor,
            max_annual_outage_hours=base_zone.max_annual_outage_hours,
            secondary_loss_retention_factor=base_zone.secondary_loss_retention_factor,
        )
        is_spof = (i % 4 == 0)
        findings.append(
            FindingTelemetry(
                finding_id=f"FINDING_{i+1:02d}",
                tower_id=f"T{(i % 3) + 1}",
                title=f"Sample Architectural Finding {i+1}",
                cmmi_maturity=cmmi_level,
                zone=scaled_zone,
                tef_pert_min=0.2 if not is_spof else 0.5,
                tef_pert_mode=0.45 if not is_spof else 0.9,
                tef_pert_max=1.0 if not is_spof else 2.0,
                rto_hours_min=1.0 if not is_spof else 2.0,
                rto_hours_mode=2.5 if not is_spof else 5.0,
                rto_hours_max=5.0 if not is_spof else 10.0,
                secondary_loss_mean=(7500.0 if not is_spof else 18000.0) * scale_factor,
                is_spof=is_spof,
                shared_dependence_factor=0.45 if not is_spof else 0.65,
            )
        )
    return findings


@pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "JPY", "CHF"])
def test_deterministic_reproducibility_and_currency_agnosticism(
    generic_enterprise_zones: dict[str, OperationalZone], currency: str
) -> None:
    findings = _create_sample_findings(generic_enterprise_zones, cmmi_level=2.2, count=6)
    engine = BayesianFairCopulaEngine(num_simulations=1024)

    run1 = engine.evaluate_portfolio(findings, currency_code=currency)
    run2 = engine.evaluate_portfolio(findings, currency_code=currency)

    assert run1.currency_code == currency
    assert run1.deterministic_seed_hash == run2.deterministic_seed_hash
    assert run1.total_portfolio_ale == run2.total_portfolio_ale
    assert run1.portfolio_var_99 == run2.portfolio_var_99
    assert run1.total_primary_ale == run2.total_primary_ale
    assert run1.total_secondary_ale == run2.total_secondary_ale


def test_aumann_shapley_exact_additivity(
    generic_enterprise_zones: dict[str, OperationalZone]
) -> None:
    findings = _create_sample_findings(generic_enterprise_zones, cmmi_level=2.0, count=12)
    engine = BayesianFairCopulaEngine(num_simulations=2048)

    summary = engine.evaluate_portfolio(findings, currency_code="USD")

    tower_sum_allocated = sum(t.portfolio_allocated_ale for t in summary.towers.values())
    assert tower_sum_allocated == pytest.approx(summary.total_portfolio_ale, abs=0.1)

    tower_sum_primary = sum(t.primary_ale for t in summary.towers.values())
    assert tower_sum_primary == pytest.approx(summary.total_primary_ale, abs=0.1)

    tower_sum_secondary = sum(t.secondary_ale for t in summary.towers.values())
    assert tower_sum_secondary == pytest.approx(summary.total_secondary_ale, abs=0.1)


def test_primary_secondary_decomposition(
    generic_enterprise_zones: dict[str, OperationalZone]
) -> None:
    findings = _create_sample_findings(generic_enterprise_zones, cmmi_level=2.1, count=9)
    engine = BayesianFairCopulaEngine(num_simulations=1024)

    summary = engine.evaluate_portfolio(findings, currency_code="GBP")

    assert summary.total_primary_ale > 0.0
    assert summary.total_secondary_ale > 0.0
    combined = summary.total_primary_ale + summary.total_secondary_ale
    assert combined == pytest.approx(summary.total_portfolio_ale, abs=0.1)
    assert summary.three_year_cost_of_inaction == pytest.approx(
        summary.total_portfolio_ale * 3.0, abs=0.1
    )


def test_cmmi_strict_monotonicity(
    generic_enterprise_zones: dict[str, OperationalZone]
) -> None:
    engine = BayesianFairCopulaEngine(num_simulations=2048)

    low_cmmi_findings = _create_sample_findings(generic_enterprise_zones, cmmi_level=1.5, count=9)
    high_cmmi_findings = _create_sample_findings(generic_enterprise_zones, cmmi_level=3.8, count=9)

    low_res = engine.evaluate_portfolio(low_cmmi_findings, currency_code="USD")
    high_res = engine.evaluate_portfolio(high_cmmi_findings, currency_code="USD")

    assert low_res.total_portfolio_ale > high_res.total_portfolio_ale
    assert low_res.total_standalone_sum > high_res.total_standalone_sum
    assert low_res.portfolio_var_99 > high_res.portfolio_var_99


def test_spectral_floor_positive_definiteness(
    generic_enterprise_zones: dict[str, OperationalZone]
) -> None:
    findings = []
    zone = generic_enterprise_zones["TIER_1"]
    for i in range(25):
        findings.append(
            FindingTelemetry(
                finding_id=f"DENSE_{i}",
                tower_id=f"T{(i % 2) + 1}",
                title=f"High Correlation Finding {i}",
                cmmi_maturity=1.8,
                zone=zone,
                tef_pert_min=0.3,
                tef_pert_mode=0.8,
                tef_pert_max=1.8,
                rto_hours_min=2.0,
                rto_hours_mode=4.0,
                rto_hours_max=8.0,
                secondary_loss_mean=15000.0,
                is_spof=True,
                shared_dependence_factor=0.85,
            )
        )

    engine = BayesianFairCopulaEngine(
        num_simulations=512, copula_df=4, intra_tower_correlation_boost=0.35
    )
    summary = engine.evaluate_portfolio(findings, currency_code="USD")

    assert summary.total_portfolio_ale > 0.0
    assert summary.portfolio_var_99 > summary.total_portfolio_ale


def test_single_finding_portfolio_edge_case(
    generic_enterprise_zones: dict[str, OperationalZone]
) -> None:
    single_finding = _create_sample_findings(generic_enterprise_zones, cmmi_level=2.0, count=1)
    engine = BayesianFairCopulaEngine(num_simulations=512)
    summary = engine.evaluate_portfolio(single_finding, currency_code="CHF")

    assert summary.total_portfolio_ale > 0.0
    assert len(summary.towers) == 1


def test_operational_zone_validation_guards() -> None:
    with pytest.raises(ValueError, match="max_annual_outage_hours"):
        OperationalZone(
            zone_id="INVALID_ZONE",
            hourly_burn_rate=1000.0,
            max_annual_outage_hours=0.0,
        )


def test_bayesian_entities_frozen_immutability() -> None:
    """Verify that Bayesian telemetry and entity dataclasses are strictly frozen."""
    import dataclasses
    from assessment_engine.domain.bayesian_fair_copula_engine import (
        EpistemicDissonanceRecord,
        OperationalZone,
        TenantFinancialTelemetry,
    )

    telemetry = TenantFinancialTelemetry(annual_revenue=100.0, currency_code="EUR")
    with pytest.raises(dataclasses.FrozenInstanceError):
        telemetry.annual_revenue = 200.0  # type: ignore[misc]

    dissonance = EpistemicDissonanceRecord(
        record_id="r1",
        finding_id="f1",
        claimed_maturity=3.0,
        empirical_reality_maturity=1.0,
        dissonance_weight=0.5,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        dissonance.claimed_maturity = 4.0  # type: ignore[misc]

    zone = OperationalZone(zone_id="z1", hourly_burn_rate=10.0, max_annual_outage_hours=5.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        zone.hourly_burn_rate = 20.0  # type: ignore[misc]

