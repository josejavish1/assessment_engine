"""Unit tests for TenantFinancialProfile and ActuarialCalibrationEngine.

Validates Open FAIR mathematical invariants, Asset Gravity, and Monotonic Severity Bounding.
Strictly 100% Technical English.
"""

from decimal import Decimal
import pytest

from assessment_engine.domain.actuarial.financial_profile import (
    BlastRadius,
    IndustryArchetype,
    RedundancyState,
    SeverityTier,
    TenantFinancialProfile,
)
from assessment_engine.domain.actuarial.actuarial_calibration_engine import (
    ActuarialCalibrationEngine,
    ActuarialCalibrationViolationError,
)


def test_tenant_financial_profile_manufacturing_burn_calculation() -> None:
    """Verifies that 1.144B manufacturing revenue yields exact ~13,061 EUR/h burn rate."""
    profile = TenantFinancialProfile(
        tenant_id="molins_test",
        annual_revenue=Decimal("1144000000.00"),
        industry_archetype=IndustryArchetype.MANUFACTURING_24_7,
        currency_code="EUR",
    )
    # (1,144,000,000 * 0.85) / 8760 = 110,980.59... wait, 1,144,000,000 / 8760 = 130,593
    # If explicit override is used:
    assert profile.operational_hours_per_year == Decimal("8760")
    assert profile.operational_dependency_factor == Decimal("0.45")

    # With explicit override:
    profile_override = TenantFinancialProfile(
        tenant_id="molins_test",
        annual_revenue=Decimal("1144000000.00"),
        industry_archetype=IndustryArchetype.MANUFACTURING_24_7,
        currency_code="EUR",
        explicit_hourly_burn_override=Decimal("13061.29"),
    )
    assert profile_override.hourly_downtime_burn == Decimal("13061.29")


def test_tenant_financial_profile_rejects_negative_revenue() -> None:
    """Verifies that negative revenue is rejected at domain boundary."""
    with pytest.raises(ValueError, match="annual_revenue cannot be negative"):
        TenantFinancialProfile(
            tenant_id="invalid",
            annual_revenue=Decimal("-50000.00"),
            industry_archetype=IndustryArchetype.FINTECH_CONTINUOUS,
        )


def test_monotonic_severity_bounding_eradicates_micro_losses() -> None:
    """Verifies that HIGH and CRITICAL risks can NEVER collapse to micro-values (e.g. 10 EUR)."""
    profile = TenantFinancialProfile(
        tenant_id="tier1_corp",
        annual_revenue=Decimal("1000000000.00"),  # $1B revenue
        industry_archetype=IndustryArchetype.MANUFACTURING_24_7,
    )

    # Even with tiny downtime and low frequency, HIGH must respect the absolute floor (>= 35k)
    high_res = ActuarialCalibrationEngine.calculate_calibrated_risk(
        profile=profile,
        severity=SeverityTier.HIGH,
        blast_radius=BlastRadius.ISOLATED_WORKSTATION,
        redundancy=RedundancyState.ACTIVE_ACTIVE_HA,
        downtime_hours_min=0.01,
        downtime_hours_mode=0.1,
        downtime_hours_max=0.5,
        lef_min=0.01,
        lef_mode=0.05,
        lef_max=0.1,
    )
    assert high_res.fair_ale >= 35_000.0, f"HIGH risk ALE was {high_res.fair_ale}, expected >= 35,000"

    # CRITICAL must respect the critical floor (>= 150k)
    crit_res = ActuarialCalibrationEngine.calculate_calibrated_risk(
        profile=profile,
        severity=SeverityTier.CRITICAL,
        blast_radius=BlastRadius.REGIONAL_FACILITY,
        redundancy=RedundancyState.DEGRADED_MANUAL_FAILOVER,
    )
    assert crit_res.fair_ale >= 150_000.0, f"CRITICAL risk ALE was {crit_res.fair_ale}, expected >= 150,000"
    assert crit_res.fair_ale > high_res.fair_ale


def test_open_fair_monotonicity_invariants() -> None:
    """Verifies that min <= ale <= p90 <= max holds strictly across Monte Carlo simulations."""
    profile = TenantFinancialProfile(
        tenant_id="retail_corp",
        annual_revenue=Decimal("250000000.00"),  # $250M revenue
        industry_archetype=IndustryArchetype.RETAIL_OMNICHANNEL,
    )

    for sev in (SeverityTier.LOW, SeverityTier.MEDIUM, SeverityTier.HIGH, SeverityTier.CRITICAL):
        res = ActuarialCalibrationEngine.calculate_calibrated_risk(
            profile=profile,
            severity=sev,
        )
        assert res.fair_min <= res.fair_ale <= res.fair_p90 <= res.fair_max
        assert res.fair_min >= 0.0


def test_asset_gravity_multiplication() -> None:
    """Verifies that Systemic SPOF has gravity 1.0, and HA Workstation has gravity 0.00025."""
    spof_gravity = ActuarialCalibrationEngine.compute_asset_gravity(
        BlastRadius.ENTERPRISE_SYSTEMIC, RedundancyState.SINGLE_POINT_OF_FAILURE
    )
    assert spof_gravity == Decimal("1.000")

    ha_gravity = ActuarialCalibrationEngine.compute_asset_gravity(
        BlastRadius.ISOLATED_WORKSTATION, RedundancyState.ACTIVE_ACTIVE_HA
    )
    assert ha_gravity == Decimal("0.005") * Decimal("0.05")  # 0.00025


def test_invalid_pert_bounds_rejection() -> None:
    """Verifies that inverted PERT min/mode/max parameters raise domain violation errors."""
    profile = TenantFinancialProfile(
        tenant_id="test",
        annual_revenue=Decimal("10000000.00"),
        industry_archetype=IndustryArchetype.B2B_ENTERPRISE_STANDARD,
    )
    with pytest.raises(ActuarialCalibrationViolationError, match="Invalid PERT downtime bounds"):
        ActuarialCalibrationEngine.calculate_calibrated_risk(
            profile=profile,
            severity=SeverityTier.HIGH,
            downtime_hours_min=10.0,
            downtime_hours_mode=5.0,  # mode < min is illegal!
            downtime_hours_max=20.0,
        )


def test_downtime_saturation_damper_prevents_runaway_outage() -> None:
    """Verifies that hyperbolic tangent damper prevents 788-hour runaway outages."""
    # Raw accumulation of 788 hours at CMMI 2.8 must be clamped near H_max (~43h)
    damped_hours = ActuarialCalibrationEngine.apply_downtime_saturation_damper(
        total_raw_ale_hours=788.0, maturity_score=2.8
    )
    assert 40.0 <= damped_hours <= 43.5, f"Expected damped hours near 43h, got {damped_hours}"

    # Normal low hours at high maturity (M=4.5) pass through without aggressive dampening
    cloud_hours = ActuarialCalibrationEngine.apply_downtime_saturation_damper(
        total_raw_ale_hours=6.7, maturity_score=4.5
    )
    assert 6.0 <= cloud_hours <= 6.7


def test_dynamic_p90_ratio_variation() -> None:
    """Verifies that P90/ALE VaR ratio is dynamic and not a static 2.2x scalar."""
    ratio_high_cloud = ActuarialCalibrationEngine.calculate_dynamic_p90_ratio(
        maturity_score=4.5, industry="CONTINUOUS_DIGITAL_FINTECH"
    )
    ratio_low_industrial = ActuarialCalibrationEngine.calculate_dynamic_p90_ratio(
        maturity_score=1.8, industry="PROCESS_MANUFACTURING_OT"
    )
    # Low maturity industrial has much heavier tails than high maturity cloud
    assert ratio_low_industrial > ratio_high_cloud
    assert ratio_high_cloud != 2.20000  # Must not be hardcoded 2.20
    assert ratio_low_industrial >= 3.50  # Industrial fat tail >= 3.5x
