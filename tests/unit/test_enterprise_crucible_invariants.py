"""Property-based invariant and scale-invariance crucible test suite.

Replaces fake hardcoded scoring with rigorous mathematical property testing
using Hypothesis and stratified stochastic parameter exploration.
Verifies dimensional homogeneity, CMMI clamping invariants, and sector orthogonality.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any, Dict, List

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from assessment_engine.domain.models.shared.financial_profile import (
    IndustryArchetype,
    TenantFinancialProfile,
)
from assessment_engine.domain.coherence_gatekeeper import (
    reconcile_subcontrol_cmmi,
)

CURRENCIES = ["EUR", "USD", "GBP", "JPY", "BRL", "SGD", "CHF", "SAR", "KES", "DKK", "CAD", "AUD"]

SECTOR_PROFILES: List[Dict[str, Any]] = [
    {"name": "Commercial Aviation", "sector_raw": "Commercial Passenger Airline & Flight Ops", "expected_arch": IndustryArchetype.HIGH_TEMPO_COMMERCIAL, "is_fin": False},
    {"name": "Upstream Oil & Gas", "sector_raw": "Oil & Gas Exploration, Drilling & Extraction", "expected_arch": IndustryArchetype.PROCESS_MANUFACTURING_OT, "is_fin": False},
    {"name": "Automotive Manufacturing", "sector_raw": "Automotive JIT Assembly & Robotics", "expected_arch": IndustryArchetype.PROCESS_MANUFACTURING_OT, "is_fin": False},
    {"name": "Cloud Hyperscaler SaaS", "sector_raw": "Multi-Tenant Cloud Observability SaaS", "expected_arch": IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH, "is_fin": True},
    {"name": "Pharmaceutical R&D", "sector_raw": "Clinical Trials & Biomedical Pharma R&D", "expected_arch": IndustryArchetype.LIFE_SAFETY_CRITICAL, "is_fin": False},
    {"name": "Fast-Fashion Retail", "sector_raw": "Omnichannel Apparel Supermarket & Retail", "expected_arch": IndustryArchetype.HIGH_TEMPO_COMMERCIAL, "is_fin": False},
    {"name": "Nuclear & Electric Grid", "sector_raw": "Nuclear Power Generation & Transmission Utility", "expected_arch": IndustryArchetype.PROCESS_MANUFACTURING_OT, "is_fin": False},
    {"name": "Global Reinsurance", "sector_raw": "Corporate Reinsurance & Solvency II Capital", "expected_arch": IndustryArchetype.STANDARD_ENTERPRISE_B2B, "is_fin": True},
    {"name": "Container Shipping", "sector_raw": "Maritime Cargo Logistics & Automated Port Terminals", "expected_arch": IndustryArchetype.DEFERRED_NETWORK_LOGISTICS, "is_fin": False},
    {"name": "Acute Hospital Care", "sector_raw": "Hospital Network ICU & Patient Telemetry", "expected_arch": IndustryArchetype.LIFE_SAFETY_CRITICAL, "is_fin": False},
    {"name": "German CNC Mittelstand", "sector_raw": "Precision Machinery CNC Tooling Foundry", "expected_arch": IndustryArchetype.PROCESS_MANUFACTURING_OT, "is_fin": False},
]


@given(
    revenue=st.decimals(min_value=Decimal("1000000"), max_value=Decimal("200000000000"), places=2),
    currency=st.sampled_from(CURRENCIES),
    archetype=st.sampled_from(list(IndustryArchetype)),
)
@settings(max_examples=50, deadline=None)
def test_property_dimensional_homogeneity_and_scale_invariance(
    revenue: Decimal, currency: str, archetype: IndustryArchetype
) -> None:
    """Verifies dimensional homogeneity: hourly burn must be positive and strictly proportional."""
    profile = TenantFinancialProfile(
        annual_revenue=revenue,
        industry_archetype=archetype,
        currency_code=currency,
    )

    hourly_burn = profile.hourly_downtime_burn
    assert hourly_burn > Decimal("0"), f"Hourly burn must be positive: got {hourly_burn}"

    expected_scale = profile.operational_dependency_factor / profile.operational_hours_per_year
    actual_scale = hourly_burn / revenue
    assert abs(actual_scale - expected_scale) < Decimal("0.0001"), (
        f"Dimensional homogeneity violated for {archetype}: expected {expected_scale}, got {actual_scale}"
    )


@given(
    revenue=st.decimals(min_value=Decimal("5000000"), max_value=Decimal("150000000000"), places=2),
    currency=st.sampled_from(CURRENCIES),
)
@settings(max_examples=30, deadline=None)
def test_property_physical_damage_scaling(revenue: Decimal, currency: str) -> None:
    """Verifies that physical manufacturing damage steps scale smoothly without unbounded spikes."""
    profile = TenantFinancialProfile(
        annual_revenue=revenue,
        industry_archetype=IndustryArchetype.PROCESS_MANUFACTURING_OT,
        currency_code=currency,
    )
    dmg_step = profile.physical_damage_step
    assert dmg_step > Decimal("0"), "Physical damage step must be positive for OT/manufacturing"
    assert dmg_step <= revenue * Decimal("0.002"), (
        f"Physical damage step {dmg_step} exceeded 0.2% of annual revenue {revenue}"
    )


@pytest.mark.parametrize("sector", SECTOR_PROFILES, ids=lambda s: s["name"])
def test_sector_orthogonality_and_archetype_resolution(sector: Dict[str, Any]) -> None:
    """Verifies that raw sector descriptions resolve to the mathematically expected archetypes."""
    resolved = IndustryArchetype.from_str(sector["sector_raw"])
    assert resolved == sector["expected_arch"], (
        f"Sector '{sector['name']}' resolved to {resolved}, expected {sector['expected_arch']}"
    )

    profile = TenantFinancialProfile(
        annual_revenue=Decimal("100000000"),
        industry_archetype=resolved,
        currency_code="EUR",
    )

    if resolved in (IndustryArchetype.STANDARD_ENTERPRISE_B2B, IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH):
        assert profile.revenue_deferral_factor <= Decimal("0.40"), (
            f"Digital/B2B archetype {resolved} has excessive deferral factor {profile.revenue_deferral_factor}"
        )


@given(
    survey_score=st.floats(min_value=3.0, max_value=5.0),
    finding_severity=st.sampled_from(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
)
@settings(max_examples=30, deadline=None)
def test_deterministic_cmmi_clamping_invariants(survey_score: float, finding_severity: str) -> None:
    """Verifies that critical findings deterministically clamp CMMI scores to prevent optimism bias."""
    findings = [{"severity": finding_severity, "finding": "Audited security observation"}]
    clamped_res = reconcile_subcontrol_cmmi(raw_survey_score=survey_score, linked_findings=findings)

    if finding_severity == "CRITICAL":
        assert clamped_res.final_cmmi == 1.25, (
            f"Critical finding did not clamp CMMI to 1.25: got {clamped_res.final_cmmi}"
        )
        assert clamped_res.override_triggered is True
    else:
        assert clamped_res.final_cmmi <= round(survey_score, 2)


def test_stratified_latin_hypercube_crucible_100_enterprises() -> None:
    """Executes a 100-enterprise Latin Hypercube stratification certifying scale invariance across all sectors."""
    log_min = math.log10(5_000_000)
    log_max = math.log10(150_000_000_000)
    slice_width = (log_max - log_min) / 100.0

    for idx in range(100):
        log_rev = log_min + (idx * slice_width) + (0.5 * slice_width)
        rev_dec = Decimal(str(round(10 ** log_rev, 2)))
        sector_cfg = SECTOR_PROFILES[idx % len(SECTOR_PROFILES)]
        currency = CURRENCIES[idx % len(CURRENCIES)]

        resolved_arch = IndustryArchetype.from_str(sector_cfg["sector_raw"])
        profile = TenantFinancialProfile(
            annual_revenue=rev_dec,
            industry_archetype=resolved_arch,
            currency_code=currency,
        )

        hourly_burn = profile.hourly_downtime_burn
        assert hourly_burn > Decimal("0")

        expected_scale = profile.operational_dependency_factor / profile.operational_hours_per_year
        actual_scale = hourly_burn / rev_dec
        assert abs(actual_scale - expected_scale) < Decimal("0.0001")

        if resolved_arch == IndustryArchetype.PROCESS_MANUFACTURING_OT:
            assert Decimal("0") < profile.physical_damage_step <= rev_dec * Decimal("0.002")
