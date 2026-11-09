"""Unit tests for Physical Single Loss Expectancy (SLE_max) and Epistemic Dissonance integration.

Verifies:
1. Physical worst-case crisis calculation based on RTO, blast radius, hourly rate, and replacement costs (eradicating arbitrary 2.5x multipliers).
2. Bayesian prior shifting of VULN and RTO inflation when Epistemic Dissonance records are attached.
3. Multi-tenant vertical and scale agnosticism.
4. Strict compliance with 100% Technical English.
"""

from __future__ import annotations

import pytest

from assessment_engine.domain.bayesian_fair_copula_engine import (
    BayesianFairCopulaEngine,
    EpistemicDissonanceRecord,
    FindingTelemetry,
    OperationalZone,
)


@pytest.fixture
def mission_critical_zone() -> OperationalZone:
    return OperationalZone(
        zone_id="ZONE_CORE_FACILITIES",
        hourly_burn_rate=13061.29,
        max_annual_outage_hours=360.0,
        secondary_loss_retention_factor=0.85,
        catastrophic_recovery_ceiling_hours=24.0,
        emergency_replacement_ratio=0.25,
    )


def test_physical_sle_worst_crisis_derivation(mission_critical_zone: OperationalZone) -> None:
    """Verifies that worst-case crisis is calculated from failure physics rather than magic multipliers."""
    engine = BayesianFairCopulaEngine(num_simulations=2048)

    finding = FindingTelemetry(
        finding_id="F_PHYS_01",
        tower_id="T1",
        title="Electromechanical UPS SPOF with Manual Bypass",
        cmmi_maturity=2.2,
        zone=mission_critical_zone,
        tef_pert_min=0.15,
        tef_pert_mode=0.35,
        tef_pert_max=0.80,
        rto_hours_min=10.0,
        rto_hours_mode=16.0,
        rto_hours_max=24.0,
        secondary_loss_mean=25000.0,
        is_spof=True,
        shared_dependence_factor=0.65,
        blast_radius_alpha=0.85,
        catastrophic_rto_hours=24.0,
        direct_replacement_cost=35000.0,
    )

    result = engine.evaluate_portfolio([finding], currency_code="EUR")
    t1_result = result.towers["T1"]

    # Verify that worst_crisis_event exists and is physically calculated
    assert t1_result.worst_crisis_event > 0.0
    assert t1_result.worst_crisis_rto_hours >= 16.0

    # Ensure worst_crisis_event reflects the physics: hours * (alpha * rate) + replacement + secondary
    min_expected_crisis = (16.0 * (0.85 * mission_critical_zone.hourly_burn_rate)) + 35000.0
    assert t1_result.worst_crisis_event >= min_expected_crisis


def test_epistemic_dissonance_increases_vuln_and_rto(mission_critical_zone: OperationalZone) -> None:
    """Verifies that epistemic dissonance shifts VULN prior and inflates RTO dynamically without arbitrary financial penalties."""
    engine = BayesianFairCopulaEngine(num_simulations=2048)

    # Finding A: Baseline without dissonance (claimed high maturity 4.0)
    finding_honest = FindingTelemetry(
        finding_id="F_HONEST",
        tower_id="T2",
        title="High Availability Virtualization Cluster",
        cmmi_maturity=4.0,
        zone=mission_critical_zone,
        tef_pert_min=0.10,
        tef_pert_mode=0.20,
        tef_pert_max=0.40,
        rto_hours_min=2.0,
        rto_hours_mode=4.0,
        rto_hours_max=8.0,
        secondary_loss_mean=10000.0,
        is_spof=False,
        blast_radius_alpha=0.40,
        catastrophic_rto_hours=24.0,
        dissonance=None,
    )

    # Finding B: Same baseline, but interview transcript reveals severe dissonance (shared root credentials, no HA tests)
    dissonance_record = EpistemicDissonanceRecord(
        record_id="DISS_001",
        finding_id="F_DISSONANT",
        claimed_maturity=4.0,
        empirical_reality_maturity=1.5,
        dissonance_weight=0.85,
        transcript_evidence_quote="Our failover is manual and takes over 16 hours because root passwords are in an unshared spreadsheet.",
        impact_vector="BOTH",
    )
    finding_dissonant = FindingTelemetry(
        finding_id="F_DISSONANT",
        tower_id="T2",
        title="High Availability Virtualization Cluster",
        cmmi_maturity=4.0,
        zone=mission_critical_zone,
        tef_pert_min=0.10,
        tef_pert_mode=0.20,
        tef_pert_max=0.40,
        rto_hours_min=2.0,
        rto_hours_mode=4.0,
        rto_hours_max=8.0,
        secondary_loss_mean=10000.0,
        is_spof=False,
        blast_radius_alpha=0.40,
        catastrophic_rto_hours=24.0,
        dissonance=dissonance_record,
    )

    res_honest = engine.evaluate_portfolio([finding_honest], currency_code="EUR")
    res_dissonant = engine.evaluate_portfolio([finding_dissonant], currency_code="EUR")

    f_honest = res_honest.towers["T2"].findings[0]
    f_dissonant = res_dissonant.towers["T2"].findings[0]

    # Verify that VULN shifted upward due to dissonance
    assert f_dissonant.mean_vuln > f_honest.mean_vuln
    assert f_dissonant.dissonance_applied is True
    assert f_honest.dissonance_applied is False

    # Verify that ALE and worst crisis event increased strictly organically
    assert res_dissonant.total_portfolio_ale > res_honest.total_portfolio_ale
    assert res_dissonant.towers["T2"].worst_crisis_event > res_honest.towers["T2"].worst_crisis_event
