"""Unit tests for Polymorphic Open FAIR calculators and master engine."""

from __future__ import annotations

from decimal import Decimal
import json
import pytest

from assessment_engine.domain.actuarial.calculators import (
    AvailabilityOutageCalculator,
    CapitalInefficiencyCalculator,
    PolymorphicActuarialEngine,
    ProductivityToilCalculator,
    RegulatoryBreachCalculator,
)
from assessment_engine.domain.actuarial.financial_profile import (
    IndustryArchetype,
    TenantFinancialProfile,
)
from assessment_engine.domain.actuarial.vectors import (
    AvailabilityOutageVector,
    CapitalInefficiencyVector,
    LossVectorEnvelope,
    ProductivityToilVector,
    RegulatoryBreachVector,
)
from assessment_engine.domain.models.telemetry import (
    AvailabilityBaseline,
    CapitalEfficiencyBaseline,
    PolymorphicFinancialTelemetry,
    ProductivityBaseline,
    RegulatoryBaseline,
)


@pytest.fixture
def mock_fintech_telemetry() -> PolymorphicFinancialTelemetry:
    profile = TenantFinancialProfile(
        tenant_id="starling_bank",
        annual_revenue=Decimal("140000000.00"),
        industry_archetype=IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH,
        currency_code="GBP",
        explicit_hourly_burn_override=Decimal("140000.00"),
    )
    return PolymorphicFinancialTelemetry.from_tenant_profile(profile)


def test_availability_outage_monotonicity(mock_fintech_telemetry: PolymorphicFinancialTelemetry) -> None:
    calc = AvailabilityOutageCalculator()
    v1 = calc.calculate_vector(mock_fintech_telemetry, maturity_score=1.0)
    v3 = calc.calculate_vector(mock_fintech_telemetry, maturity_score=3.0)
    v5 = calc.calculate_vector(mock_fintech_telemetry, maturity_score=5.0)

    assert v1.annualized_loss_expectancy > v3.annualized_loss_expectancy > v5.annualized_loss_expectancy
    assert v1.projected_annual_downtime_hours > v5.projected_annual_downtime_hours
    assert v1.revenue_burn_rate_per_hour == 140000.0
    assert v5.annualized_loss_expectancy > 0.0


def test_capital_inefficiency_finops_calculation(mock_fintech_telemetry: PolymorphicFinancialTelemetry) -> None:
    calc = CapitalInefficiencyCalculator()
    v_immature = calc.calculate_vector(mock_fintech_telemetry, maturity_score=1.2)
    v_optimized = calc.calculate_vector(mock_fintech_telemetry, maturity_score=4.8)

    # Inefficient platform loses ~22% of cloud spend; optimized platform loses < 2%
    assert v_immature.annualized_loss_expectancy > v_optimized.annualized_loss_expectancy
    assert v_immature.annualized_loss_expectancy <= mock_fintech_telemetry.capital_efficiency.annual_cloud_infrastructure_spend
    assert v_optimized.inefficiency_leakage_rate_pct < v_immature.inefficiency_leakage_rate_pct


def test_productivity_toil_workplace_calculation(mock_fintech_telemetry: PolymorphicFinancialTelemetry) -> None:
    calc = ProductivityToilCalculator()
    v1 = calc.calculate_vector(mock_fintech_telemetry, maturity_score=1.0)
    v5 = calc.calculate_vector(mock_fintech_telemetry, maturity_score=5.0)

    assert v1.annualized_loss_expectancy > v5.annualized_loss_expectancy
    assert v1.equivalent_fte_capacity_burned > v5.equivalent_fte_capacity_burned
    assert v1.annual_hours_lost_to_toil > v5.annual_hours_lost_to_toil


def test_regulatory_breach_security_calculation(mock_fintech_telemetry: PolymorphicFinancialTelemetry) -> None:
    calc = RegulatoryBreachCalculator()
    v1 = calc.calculate_vector(mock_fintech_telemetry, maturity_score=1.5)
    v5 = calc.calculate_vector(mock_fintech_telemetry, maturity_score=4.5)

    assert v1.annualized_loss_expectancy > v5.annualized_loss_expectancy
    assert v1.loss_event_frequency_annual > v5.loss_event_frequency_annual
    assert v1.statutory_penalty_exposure > v5.statutory_penalty_exposure


def test_polymorphic_engine_tower_dispatch(mock_fintech_telemetry: PolymorphicFinancialTelemetry) -> None:
    # T1 (Facilities) -> Availability Outage
    v_t1 = PolymorphicActuarialEngine.calculate_loss_vector("T1", mock_fintech_telemetry, maturity_score=4.0)
    assert isinstance(v_t1, AvailabilityOutageVector)
    assert v_t1.archetype == "AVAILABILITY_OUTAGE"

    # T8 (FinOps) -> Capital Inefficiency
    v_t8 = PolymorphicActuarialEngine.calculate_loss_vector("T8", mock_fintech_telemetry, maturity_score=4.0)
    assert isinstance(v_t8, CapitalInefficiencyVector)
    assert v_t8.archetype == "CAPITAL_INEFFICIENCY"
    assert v_t8.annual_addressable_waste > 0.0

    # T9 (Workplace) -> Productivity Toil
    v_t9 = PolymorphicActuarialEngine.calculate_loss_vector("T9", mock_fintech_telemetry, maturity_score=4.0)
    assert isinstance(v_t9, ProductivityToilVector)
    assert v_t9.archetype == "PRODUCTIVITY_TOIL"
    assert v_t9.equivalent_fte_capacity_burned > 0.0

    # T6 (Security) -> Regulatory & Breach
    v_t6 = PolymorphicActuarialEngine.calculate_loss_vector("T6", mock_fintech_telemetry, maturity_score=4.0)
    assert isinstance(v_t6, RegulatoryBreachVector)
    assert v_t6.archetype == "REGULATORY_AND_BREACH"
    assert v_t6.statutory_penalty_exposure > 0.0


def test_loss_vector_envelope_json_roundtrip(mock_fintech_telemetry: PolymorphicFinancialTelemetry) -> None:
    v_finops = PolymorphicActuarialEngine.calculate_loss_vector("T8", mock_fintech_telemetry, maturity_score=3.5)
    env = LossVectorEnvelope(vector=v_finops)

    json_str = env.model_dump_json()
    raw_dict = json.loads(json_str)
    assert raw_dict["vector"]["archetype"] == "CAPITAL_INEFFICIENCY"

    # Deserialization reconstitutes the exact concrete CapitalInefficiencyVector subclass
    reconstituted = LossVectorEnvelope.model_validate_json(json_str)
    assert isinstance(reconstituted.vector, CapitalInefficiencyVector)
    assert reconstituted.vector.annual_addressable_waste == v_finops.annual_addressable_waste
