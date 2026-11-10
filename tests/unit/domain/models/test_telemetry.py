"""Unit tests for multi-dimensional polymorphic financial telemetry."""

from __future__ import annotations

from decimal import Decimal
import pytest
from pydantic import ValidationError

from assessment_engine.domain.actuarial.financial_profile import (
    IndustryArchetype,
    TenantFinancialProfile,
)
from assessment_engine.domain.models.telemetry import (
    AvailabilityBaseline,
    CapitalEfficiencyBaseline,
    PolymorphicFinancialTelemetry,
    ProductivityBaseline,
    RegulatoryBaseline,
)


def test_explicit_telemetry_construction() -> None:
    telemetry = PolymorphicFinancialTelemetry(
        currency_iso="GBP",
        industry_vertical=IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH,
        availability=AvailabilityBaseline(
            hourly_revenue_at_risk=140000.0,
            critical_service_mttr_hours=0.5,
        ),
        capital_efficiency=CapitalEfficiencyBaseline(
            annual_it_opex=12000000.0,
            annual_cloud_infrastructure_spend=5500000.0,
            estimated_unoptimized_spend_ratio=0.25,
        ),
        productivity=ProductivityBaseline(
            total_impacted_ftes=850,
            fully_burdened_hourly_rate=72.0,
            annual_working_hours_per_fte=1920,
        ),
        regulatory=RegulatoryBaseline(
            annual_global_turnover=140000000.0,
            compromised_record_unit_cost=165.0,
            total_pii_records_managed=2500000,
        ),
    )

    assert telemetry.currency_iso == "GBP"
    assert telemetry.capital_efficiency.annual_cloud_infrastructure_spend == 5500000.0
    assert telemetry.productivity.total_impacted_ftes == 850


def test_from_tenant_profile_fintech_derivation() -> None:
    profile = TenantFinancialProfile(
        tenant_id="starling_bank",
        annual_revenue=Decimal("140000000.00"),
        industry_archetype=IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH,
        currency_code="GBP",
        explicit_hourly_burn_override=Decimal("140000.00"),
    )

    telemetry = PolymorphicFinancialTelemetry.from_tenant_profile(profile)

    assert telemetry.currency_iso == "GBP"
    assert telemetry.industry_vertical == IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH
    assert telemetry.availability.hourly_revenue_at_risk == 140000.0

    # IT OPEX derived around 8.5% of 140M = ~11.9M
    assert telemetry.capital_efficiency.annual_it_opex == pytest.approx(11_900_000.0, rel=0.01)
    # Cloud spend derived around 48% of IT OPEX = ~5.7M
    assert telemetry.capital_efficiency.annual_cloud_infrastructure_spend == pytest.approx(5_712_000.0, rel=0.01)

    # FTEs derived around 140M / 380k = ~368
    assert 300 <= telemetry.productivity.total_impacted_ftes <= 450
    assert telemetry.productivity.fully_burdened_hourly_rate == 68.0


def test_from_tenant_profile_manufacturing_derivation() -> None:
    profile = TenantFinancialProfile(
        tenant_id="molins",
        annual_revenue=Decimal("38000000.00"),
        industry_archetype=IndustryArchetype.PROCESS_MANUFACTURING_OT,
        currency_code="EUR",
    )

    telemetry = PolymorphicFinancialTelemetry.from_tenant_profile(profile)

    assert telemetry.currency_iso == "EUR"
    assert telemetry.industry_vertical == IndustryArchetype.PROCESS_MANUFACTURING_OT

    # Manufacturing IT OPEX is lower (2.6% of 38M = ~988k)
    assert telemetry.capital_efficiency.annual_it_opex == pytest.approx(988_000.0, rel=0.01)
    # Cloud spend is lower share (18% of IT OPEX = ~177k)
    assert telemetry.capital_efficiency.annual_cloud_infrastructure_spend == pytest.approx(177_840.0, rel=0.01)


def test_cloud_spend_cannot_exceed_it_opex_validator() -> None:
    with pytest.raises(ValidationError, match="cannot exceed total IT OPEX"):
        PolymorphicFinancialTelemetry(
            currency_iso="USD",
            industry_vertical=IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH,
            availability=AvailabilityBaseline(hourly_revenue_at_risk=1000.0),
            capital_efficiency=CapitalEfficiencyBaseline(
                annual_it_opex=100000.0,
                annual_cloud_infrastructure_spend=150000.0,  # Invalid! Cloud > Total IT OPEX
            ),
            productivity=ProductivityBaseline(
                total_impacted_ftes=10,
                fully_burdened_hourly_rate=50.0,
            ),
            regulatory=RegulatoryBaseline(
                annual_global_turnover=10000000.0,
                total_pii_records_managed=1000,
            ),
        )


def test_hourly_burn_cannot_exceed_annual_turnover() -> None:
    with pytest.raises(ValidationError, match="cannot exceed annual global turnover"):
        PolymorphicFinancialTelemetry(
            currency_iso="USD",
            industry_vertical=IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH,
            availability=AvailabilityBaseline(hourly_revenue_at_risk=2000000.0),  # 2M/hr > 1M/yr
            capital_efficiency=CapitalEfficiencyBaseline(
                annual_it_opex=100000.0,
                annual_cloud_infrastructure_spend=50000.0,
            ),
            productivity=ProductivityBaseline(
                total_impacted_ftes=10,
                fully_burdened_hourly_rate=50.0,
            ),
            regulatory=RegulatoryBaseline(
                annual_global_turnover=1000000.0,
                total_pii_records_managed=1000,
            ),
        )
