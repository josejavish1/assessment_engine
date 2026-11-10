"""Strategy pattern calculators for Polymorphic Open FAIR Actuarial Risk Modeling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Generic, List, Optional, Type, TypeVar

from assessment_engine.domain.actuarial.vectors import (
    AvailabilityOutageVector,
    BaseEconomicLossVector,
    CapitalInefficiencyVector,
    PolymorphicLossVector,
    ProductivityToilVector,
    RegulatoryBreachVector,
)
from assessment_engine.domain.models.telemetry import PolymorphicFinancialTelemetry
from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
    get_actuarial_archetype_registry,
)

TVector = TypeVar("TVector", bound=BaseEconomicLossVector)


class OpenFairActuarialStrategy(ABC, Generic[TVector]):
    """Abstract Strategy interface for pure, side-effect-free actuarial calculations."""

    @abstractmethod
    def calculate_vector(
        self,
        telemetry: PolymorphicFinancialTelemetry,
        maturity_score: float,
        finding_severity_weights: Optional[List[float]] = None,
    ) -> TVector:
        """Calculates a strongly-typed Open FAIR loss vector for a specific archetype."""
        pass


class AvailabilityOutageCalculator(OpenFairActuarialStrategy[AvailabilityOutageVector]):
    """Calculates operational and transactional availability outage loss vectors."""

    def calculate_vector(
        self,
        telemetry: PolymorphicFinancialTelemetry,
        maturity_score: float,
        finding_severity_weights: Optional[List[float]] = None,
    ) -> AvailabilityOutageVector:
        score = max(1.0, min(5.0, maturity_score))
        # Vulnerability factor: ranges from 1.0 (at maturity 1.0) down to 0.02 (at maturity 5.0)
        vulnerability = max(0.02, ((5.0 - score) / 4.0) ** 1.15)

        # Weight adjustments if granular findings severity weights are provided
        if finding_severity_weights:
            avg_severity = sum(finding_severity_weights) / len(finding_severity_weights)
            vulnerability = min(1.0, vulnerability * (0.8 + 0.4 * avg_severity))

        base_event_freq = 2.2  # Expected threat events per year
        lef = base_event_freq * vulnerability

        # MTTR scales dynamically with maturity: from base_mttr * 0.4 at score 5.0 up to base_mttr * 3.0 at score 1.0
        base_mttr = telemetry.availability.critical_service_mttr_hours
        effective_mttr = base_mttr * (0.40 + 2.60 * ((5.0 - score) / 4.0))
        downtime_hours = round(lef * effective_mttr, 3)

        burn_rate = telemetry.availability.hourly_revenue_at_risk
        single_loss_magnitude = round(burn_rate * effective_mttr, 2)
        ale = round(downtime_hours * burn_rate, 2)

        ci_low = round(ale * 0.40, 2)
        ci_high = round(max(single_loss_magnitude * 1.15, ale * 2.30), 2)

        return AvailabilityOutageVector(
            annualized_loss_expectancy=ale,
            probable_loss_magnitude=single_loss_magnitude,
            loss_event_frequency_annual=round(lef, 3),
            confidence_interval_95_low=ci_low,
            confidence_interval_95_high=ci_high,
            currency_iso=telemetry.currency_iso,
            projected_annual_downtime_hours=downtime_hours,
            revenue_burn_rate_per_hour=burn_rate,
        )


class CapitalInefficiencyCalculator(OpenFairActuarialStrategy[CapitalInefficiencyVector]):
    """Calculates cloud spend drift, unoptimized resources, and software licensing liabilities."""

    def calculate_vector(
        self,
        telemetry: PolymorphicFinancialTelemetry,
        maturity_score: float,
        finding_severity_weights: Optional[List[float]] = None,
    ) -> CapitalInefficiencyVector:
        score = max(1.0, min(5.0, maturity_score))
        benchmark_waste = telemetry.capital_efficiency.estimated_unoptimized_spend_ratio

        # Inefficiency factor: scales with maturity
        maturity_attenuation = max(0.04, ((5.0 - score) / 4.0) ** 1.35)
        leakage_rate = benchmark_waste * maturity_attenuation

        if finding_severity_weights:
            avg_severity = sum(finding_severity_weights) / len(finding_severity_weights)
            leakage_rate = min(0.50, leakage_rate * (0.8 + 0.4 * avg_severity))

        cloud_spend = telemetry.capital_efficiency.annual_cloud_infrastructure_spend
        annual_waste = round(cloud_spend * leakage_rate, 2)

        # Invariant: Waste cannot exceed total cloud spend
        annual_waste = min(annual_waste, cloud_spend)

        ale = annual_waste
        monthly_magnitude = round(ale / 12.0, 2)
        ci_low = round(ale * 0.60, 2)
        ci_high = round(ale * 1.50, 2)

        return CapitalInefficiencyVector(
            annualized_loss_expectancy=ale,
            probable_loss_magnitude=monthly_magnitude,
            loss_event_frequency_annual=12.0,  # 12 monthly billing cycles
            confidence_interval_95_low=ci_low,
            confidence_interval_95_high=ci_high,
            currency_iso=telemetry.currency_iso,
            annual_addressable_waste=annual_waste,
            inefficiency_leakage_rate_pct=round(leakage_rate * 100.0, 2),
        )


class ProductivityToilCalculator(OpenFairActuarialStrategy[ProductivityToilVector]):
    """Calculates workforce cognitive friction, engineering toil, and lost employee hours."""

    def calculate_vector(
        self,
        telemetry: PolymorphicFinancialTelemetry,
        maturity_score: float,
        finding_severity_weights: Optional[List[float]] = None,
    ) -> ProductivityToilVector:
        score = max(1.0, min(5.0, maturity_score))

        hourly_wage = telemetry.productivity.fully_burdened_hourly_rate
        working_hours = telemetry.productivity.annual_working_hours_per_fte
        loaded_annual_salary = hourly_wage * working_hours

        # Derive total IT engineering organization capacity from IT OPEX
        it_opex = telemetry.capital_efficiency.annual_it_opex
        total_it_headcount = max(2.0, (it_opex * 0.35) / max(30_000.0, loaded_annual_salary))

        # Dedicated IT Operations, Service Desk & Runbook capacity (typically 4% to 8% of total IT org)
        it_ops_staff = min(15.0, max(1.5, total_it_headcount * 0.04))

        # Friction rate: scales with maturity (from 35% manual toil at score 1.0 down to 2% at score 5.0)
        toil_fraction = max(0.02, 0.35 * ((5.0 - score) / 4.0))

        if finding_severity_weights:
            avg_severity = sum(finding_severity_weights) / len(finding_severity_weights)
            toil_fraction = min(0.50, toil_fraction * (0.8 + 0.4 * avg_severity))

        fte_burned = round(it_ops_staff * toil_fraction, 2)
        hours_lost = round(fte_burned * working_hours, 1)
        ale = round(hours_lost * hourly_wage, 2)

        ci_low = round(ale * 0.65, 2)
        ci_high = round(ale * 1.45, 2)

        return ProductivityToilVector(
            annualized_loss_expectancy=ale,
            probable_loss_magnitude=round(ale / 12.0, 2),
            loss_event_frequency_annual=12.0,
            confidence_interval_95_low=ci_low,
            confidence_interval_95_high=ci_high,
            currency_iso=telemetry.currency_iso,
            annual_hours_lost_to_toil=hours_lost,
            equivalent_fte_capacity_burned=fte_burned,
        )


class RegulatoryBreachCalculator(OpenFairActuarialStrategy[RegulatoryBreachVector]):
    """Calculates cyber breach exposure, statutory fines (GDPR/DORA), and forensic recovery costs."""

    def calculate_vector(
        self,
        telemetry: PolymorphicFinancialTelemetry,
        maturity_score: float,
        finding_severity_weights: Optional[List[float]] = None,
    ) -> RegulatoryBreachVector:
        score = max(1.0, min(5.0, maturity_score))

        # Annual breach probability: from 18% at score 1.0 down to 0.5% at score 5.0
        annual_breach_prob = max(0.005, 0.18 * ((5.0 - score) / 4.0))

        if finding_severity_weights:
            avg_severity = sum(finding_severity_weights) / len(finding_severity_weights)
            annual_breach_prob = min(0.35, annual_breach_prob * (0.8 + 0.4 * avg_severity))

        turnover = telemetry.regulatory.annual_global_turnover
        max_statutory_fine = min(20_000_000.0, turnover * 0.04)

        b2b_dampener = telemetry.regulatory.b2b_exposure_dampener
        statutory_fine = round(max_statutory_fine * max(0.05, ((5.0 - score) / 4.0)) * b2b_dampener, 2)

        unit_cost = telemetry.regulatory.compromised_record_unit_cost
        sample_records = min(50_000, max(500, round(telemetry.regulatory.total_pii_records_managed * 0.05 * b2b_dampener)))
        forensic_cost = round(sample_records * unit_cost, 2)

        single_loss_magnitude = statutory_fine + forensic_cost
        ale = round(annual_breach_prob * single_loss_magnitude, 2)

        ci_low = round(ale * 0.30, 2)
        ci_high = round(max(single_loss_magnitude, ale * 2.0), 2)

        return RegulatoryBreachVector(
            annualized_loss_expectancy=ale,
            probable_loss_magnitude=single_loss_magnitude,
            loss_event_frequency_annual=round(annual_breach_prob, 4),
            confidence_interval_95_low=ci_low,
            confidence_interval_95_high=ci_high,
            currency_iso=telemetry.currency_iso,
            statutory_penalty_exposure=statutory_fine,
            remediation_and_forensic_cost=forensic_cost,
        )


class PolymorphicActuarialEngine:
    """Master orchestrator dispatching actuarial calculations to the appropriate strategy."""

    _CALCULATORS: ClassVar[Dict[LossArchetypeType, OpenFairActuarialStrategy]] = {
        LossArchetypeType.AVAILABILITY_OUTAGE: AvailabilityOutageCalculator(),
        LossArchetypeType.CAPITAL_INEFFICIENCY: CapitalInefficiencyCalculator(),
        LossArchetypeType.PRODUCTIVITY_TOIL: ProductivityToilCalculator(),
        LossArchetypeType.REGULATORY_AND_BREACH: RegulatoryBreachCalculator(),
    }

    @classmethod
    def calculate_loss_vector(
        cls,
        tower_id: str,
        telemetry: PolymorphicFinancialTelemetry,
        maturity_score: float,
        finding_severity_weights: Optional[List[float]] = None,
    ) -> PolymorphicLossVector:
        """Resolves the tower's loss archetype and executes the corresponding actuarial strategy."""
        registry = get_actuarial_archetype_registry()
        mapping = registry.get_mapping_for_tower(tower_id)

        calculator = cls._CALCULATORS.get(mapping.primary_archetype)
        if not calculator:
            raise KeyError(f"No calculator registered for archetype: {mapping.primary_archetype}")

        return calculator.calculate_vector(
            telemetry=telemetry,
            maturity_score=maturity_score,
            finding_severity_weights=finding_severity_weights,
        )
