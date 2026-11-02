"""Actuarial downtime calibration engine enforcing revenue proportionality across enterprise scales."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from enum import Enum
import logging
from typing import Mapping, Any

logger = logging.getLogger(__name__)


class TelemetryResolutionError(ValueError):
    """Raised when mandatory actuarial financial telemetry cannot be resolved."""


class RevenueSourceType(str, Enum):
    """Classification of the underlying financial data provenance."""
    VERIFIED_FILING = "VERIFIED_CORPORATE_FILING"
    PARAMETRIC_DERIVATION = "PARAMETRIC_HEADCOUNT_DERIVATION"


class ActuarialRiskRegime(str, Enum):
    """Classifies the domain risk profile based on tail-to-mean loss elasticity."""
    TAIL_VOLATILITY_DOMINANT = "TAIL_VOLATILITY_DOMINANT"
    CHRONIC_FRICTION_DOMINANT = "CHRONIC_FRICTION_DOMINANT"


@dataclass(frozen=True)
class DomainActuarialMetrics:
    """Immutable Data Transfer Object representing calibrated domain risk metrics.
    Strictly decouples internal macro-economic baselines from domain presentation.
    """
    tower_id: str
    currency_code: str
    currency_symbol: str
    composite_hourly_burn_rate: Decimal
    net_annual_downtime_hours: Decimal
    annual_loss_expectancy: Decimal
    p90_stress_downtime_hours: Decimal
    p90_value_at_risk: Decimal
    tail_to_mean_ratio: Decimal
    risk_regime: ActuarialRiskRegime
    target_maturity_score: Decimal


@dataclass(frozen=True)
class CalibratedDowntimeMetrics:
    """Immutable value object containing calibrated actuarial downtime parameters."""
    global_annual_revenue: Decimal
    perimeter_revenue_weight_pct: Decimal
    effective_exposed_revenue: Decimal
    sector_impact_factor: Decimal
    calibrated_hourly_downtime_cost: Decimal
    currency_code: str
    revenue_source: RevenueSourceType
    audited_perimeter_name: str
    industry_vertical_code: str = "DEFAULT_ENTERPRISE"
    sector_benchmark_source: str = "Gartner / ITIC Benchmark"
    gross_hourly_revenue_velocity: Decimal = Decimal("0.0")
    effective_velocity_bleed_pct: Decimal = Decimal("0.0")
    is_client_override: bool = False
    
    @property
    def annual_revenue(self) -> Decimal:
        return self.global_annual_revenue
        
    @property
    def hourly_revenue_exposure_factor(self) -> Decimal:
        return self.sector_impact_factor


DowntimeCalibrationResult = CalibratedDowntimeMetrics


class ActuarialDowntimeCalibrator:
    """Calibrates hourly financial exposure by scaling consolidated corporate revenue
    down to the exact operational footprint of the audited perimeter.
    """

    DEFAULT_OPERATIONAL_HOURS_PER_YEAR: Decimal = Decimal("8760.0")
    TAIL_REGIME_THRESHOLD: Decimal = Decimal("3.0")
    QUANTIZE_CURRENCY: Decimal = Decimal("0.01")
    QUANTIZE_WHOLE_CURRENCY: Decimal = Decimal("1")
    QUANTIZE_HOURS: Decimal = Decimal("0.1")

    @classmethod
    def calibrate_domain_exposure(
        cls,
        tower_id: str,
        currency_code: str,
        currency_symbol: str,
        raw_hourly_burn_rate: float,
        deduplicated_annual_hours: float,
        p90_stress_hours: float,
        current_maturity_score: float,
        configured_target_maturity: float | None = None,
    ) -> DomainActuarialMetrics:
        """Deterministically computes and quantizes actuarial exposure metrics for a given tower."""
        if raw_hourly_burn_rate < 0 or deduplicated_annual_hours < 0 or p90_stress_hours < 0:
            raise ValueError(
                f"Invalid negative actuarial telemetry for tower '{tower_id}': "
                f"rate={raw_hourly_burn_rate}, net_hours={deduplicated_annual_hours}, "
                f"p90_hours={p90_stress_hours}."
            )

        hourly_rate = Decimal(str(raw_hourly_burn_rate)).quantize(
            cls.QUANTIZE_CURRENCY, rounding=ROUND_HALF_UP
        )
        net_hours = Decimal(str(deduplicated_annual_hours)).quantize(
            cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP
        )
        p90_hours = Decimal(str(max(deduplicated_annual_hours, p90_stress_hours))).quantize(
            cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP
        )

        ale_amount = (hourly_rate * net_hours).quantize(
            cls.QUANTIZE_WHOLE_CURRENCY, rounding=ROUND_HALF_UP
        )
        p90_var_amount = (hourly_rate * p90_hours).quantize(
            cls.QUANTIZE_WHOLE_CURRENCY, rounding=ROUND_HALF_UP
        )

        if ale_amount > Decimal("0"):
            tail_ratio = (p90_var_amount / ale_amount).quantize(
                cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP
            )
        else:
            tail_ratio = Decimal("1.0")

        regime = (
            ActuarialRiskRegime.TAIL_VOLATILITY_DOMINANT
            if tail_ratio >= cls.TAIL_REGIME_THRESHOLD
            else ActuarialRiskRegime.CHRONIC_FRICTION_DOMINANT
        )

        maturity_dec = Decimal(str(current_maturity_score))
        if configured_target_maturity is not None:
            target_maturity = Decimal(str(configured_target_maturity)).quantize(
                cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP
            )
        else:
            computed_target = min(Decimal("4.5"), max(Decimal("3.8"), maturity_dec + Decimal("1.5")))
            target_maturity = computed_target.quantize(cls.QUANTIZE_HOURS, rounding=ROUND_HALF_UP)

        return DomainActuarialMetrics(
            tower_id=tower_id,
            currency_code=currency_code,
            currency_symbol=currency_symbol,
            composite_hourly_burn_rate=hourly_rate,
            net_annual_downtime_hours=net_hours,
            annual_loss_expectancy=ale_amount,
            p90_stress_downtime_hours=p90_hours,
            p90_value_at_risk=p90_var_amount,
            tail_to_mean_ratio=tail_ratio,
            risk_regime=regime,
            target_maturity_score=target_maturity,
        )

    DEFAULT_SECTOR_CATALOG: Mapping[str, Mapping[str, Any]] = {
        "HEAVY_MANUFACTURING": {
            "benchmark_authority": "Gartner / ITIC Industrial Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000010"),
            "default_single_site_weight_pct": Decimal("15.0"),
            "revenue_per_employee_benchmark": Decimal("350000.0"),
            "sla_penalty_coefficient": Decimal("0.0845"),
            "labor_recovery_coefficient": Decimal("0.05836"),
        },
        "GLOBAL_LOGISTICS": {
            "benchmark_authority": "ITIC Global Supply Chain Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000025"),
            "default_single_site_weight_pct": Decimal("10.0"),
            "revenue_per_employee_benchmark": Decimal("250000.0"),
            "sla_penalty_coefficient": Decimal("0.1000"),
            "labor_recovery_coefficient": Decimal("0.0600"),
        },
        "FINANCIAL_SERVICES": {
            "benchmark_authority": "Gartner Tier-1 Banking Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000005"),
            "default_single_site_weight_pct": Decimal("30.0"),
            "revenue_per_employee_benchmark": Decimal("850000.0"),
            "sla_penalty_coefficient": Decimal("0.1500"),
            "labor_recovery_coefficient": Decimal("0.0800"),
        },
        "HEALTHCARE": {
            "benchmark_authority": "HIMSS / Gartner Healthcare Continuity Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000015"),
            "default_single_site_weight_pct": Decimal("20.0"),
            "revenue_per_employee_benchmark": Decimal("200000.0"),
            "sla_penalty_coefficient": Decimal("0.1200"),
            "labor_recovery_coefficient": Decimal("0.0700"),
        },
        "TECHNOLOGY_SAAS": {
            "benchmark_authority": "SaaS Capital / Gartner High-Availability Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000020"),
            "default_single_site_weight_pct": Decimal("40.0"),
            "revenue_per_employee_benchmark": Decimal("450000.0"),
            "sla_penalty_coefficient": Decimal("0.1000"),
            "labor_recovery_coefficient": Decimal("0.0500"),
        },
        "DEFAULT_ENTERPRISE": {
            "benchmark_authority": "Gartner Cross-Industry Operational Continuity Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000010"),
            "default_single_site_weight_pct": Decimal("10.0"),
            "revenue_per_employee_benchmark": Decimal("300000.0"),
            "sla_penalty_coefficient": Decimal("0.0845"),
            "labor_recovery_coefficient": Decimal("0.05836"),
        },
    }

    def __init__(self, sector_catalog: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        self._sector_catalog = sector_catalog or self.DEFAULT_SECTOR_CATALOG

    def calibrate(
        self,
        organization_profile: Mapping[str, Any],
        strict_telemetry: bool = False,
    ) -> CalibratedDowntimeMetrics:
        """Executes the actuarial downtime calibration pipeline."""
        currency_code = self._extract_currency(organization_profile)
        perimeter_name = self._extract_perimeter_name(organization_profile)

        global_revenue, rev_source = self._resolve_global_revenue(
            organization_profile=organization_profile,
            sector_benchmarks=self._sector_catalog,
            strict=strict_telemetry,
        )

        perimeter_weight_pct = self._resolve_perimeter_weight_pct(
            organization_profile=organization_profile,
            sector_benchmarks=self._sector_catalog,
        )

        sector_factor = self._resolve_sector_impact_factor(
            organization_profile=organization_profile,
            sector_benchmarks=self._sector_catalog,
        )

        raw_vertical = str(organization_profile.get("industry_vertical_code") or organization_profile.get("vertical_industry", "DEFAULT_ENTERPRISE")).upper()
        sector_spec = self._sector_catalog.get(raw_vertical, self._sector_catalog.get("DEFAULT_ENTERPRISE", {}))
        benchmark_source = str(sector_spec.get("benchmark_authority", "Gartner / ITIC Benchmark"))

        gross_hourly_velocity = (global_revenue / self.DEFAULT_OPERATIONAL_HOURS_PER_YEAR).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Mathematical calculation: Effective Exposed Revenue = Global Revenue * (Weight % / 100)
        weight_ratio = perimeter_weight_pct / Decimal("100.0")
        effective_exposed_revenue = (global_revenue * weight_ratio).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        explicit_override = organization_profile.get("explicit_hourly_downtime_cost")
        if explicit_override is not None and float(explicit_override) > 0.0:
            calibrated_hourly_cost = Decimal(str(explicit_override)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            is_override = True
        else:
            # Base Hourly Cost: from explicit baseline or exposed revenue * sector factor
            raw_base = organization_profile.get("hourly_downtime_rate") or organization_profile.get("hourly_downtime_cost")
            if raw_base is not None and float(raw_base) > 0.0:
                base_hourly = Decimal(str(raw_base))
            else:
                base_hourly = effective_exposed_revenue * sector_factor

            raw_sla = organization_profile.get("sla_penalty_coefficient") or sector_spec.get("sla_penalty_coefficient", Decimal("0.0"))
            raw_labor = organization_profile.get("labor_recovery_coefficient") or sector_spec.get("labor_recovery_coefficient", Decimal("0.0"))
            sla_coef = Decimal(str(raw_sla))
            labor_coef = Decimal(str(raw_labor))

            sla_hourly = base_hourly * sla_coef
            labor_hourly = base_hourly * labor_coef
            
            calibrated_hourly_cost = (base_hourly + sla_hourly + labor_hourly).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            is_override = False

        effective_velocity_bleed_pct = (
            (calibrated_hourly_cost / gross_hourly_velocity * Decimal("100"))
            if gross_hourly_velocity > Decimal("0")
            else Decimal("0.00")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        logger.info(
            "Actuarial calibration complete for perimeter '%s': "
            "GlobalRev=%s %s (Source=%s), Weight=%s%%, ExposedRev=%s %s, HourlyCost=%s %s",
            perimeter_name,
            global_revenue,
            currency_code,
            rev_source.value,
            perimeter_weight_pct,
            effective_exposed_revenue,
            currency_code,
            calibrated_hourly_cost,
            currency_code,
        )

        return CalibratedDowntimeMetrics(
            global_annual_revenue=global_revenue,
            perimeter_revenue_weight_pct=perimeter_weight_pct,
            effective_exposed_revenue=effective_exposed_revenue,
            sector_impact_factor=sector_factor,
            calibrated_hourly_downtime_cost=calibrated_hourly_cost,
            currency_code=currency_code,
            revenue_source=rev_source,
            audited_perimeter_name=perimeter_name,
            sector_benchmark_source=benchmark_source,
            gross_hourly_revenue_velocity=gross_hourly_velocity,
            effective_velocity_bleed_pct=effective_velocity_bleed_pct,
            is_client_override=is_override,
            industry_vertical_code=raw_vertical,
        )

    def _resolve_global_revenue(
        self,
        organization_profile: Mapping[str, Any],
        sector_benchmarks: Mapping[str, Any],
        strict: bool,
    ) -> tuple[Decimal, RevenueSourceType]:
        """Extracts consolidated annual revenue from telemetry without arbitrary hardcoded fallbacks."""
        doc_meta = organization_profile.get("document_meta", {})
        if not isinstance(doc_meta, dict):
            doc_meta = {}
            
        financial_block = organization_profile.get("financial_metrics") or organization_profile.get("financial_telemetry") or {}
        if not isinstance(financial_block, dict):
            financial_block = {}
            
        org_prof = organization_profile.get("organization_profile") or organization_profile
        if not isinstance(org_prof, dict):
            org_prof = organization_profile

        candidate_values = [
            financial_block.get("global_annual_revenue"),
            financial_block.get("consolidated_annual_revenue"),
            financial_block.get("annual_revenue_amount"),
            org_prof.get("consolidated_annual_revenue"),
            org_prof.get("annual_revenue_amount"),
            org_prof.get("annual_revenue"),
            org_prof.get("annual_revenue_eur"),
            doc_meta.get("annual_revenue"),
        ]

        for val in candidate_values:
            if val is not None and str(val).strip() != "":
                try:
                    parsed_rev = Decimal(str(val))
                except (InvalidOperation, ValueError, TypeError) as exc:
                    raise TelemetryResolutionError(
                        f"Malformed monetary value in revenue telemetry: '{val}'"
                    ) from exc

                if parsed_rev <= Decimal("0"):
                    raise TelemetryResolutionError(
                        f"Consolidated revenue must be strictly positive. Received: {parsed_rev}"
                    )
                return parsed_rev, RevenueSourceType.VERIFIED_FILING

        if strict:
            raise TelemetryResolutionError(
                "Missing mandatory 'consolidated_annual_revenue' in organization_profile. "
                "Hardcoded monetary fallbacks are strictly prohibited by actuarial governance."
            )

        # Non-strict fallback: Parametric derivation via verified employee headcount
        headcount = organization_profile.get("employee_headcount")
        raw_vertical = str(organization_profile.get("industry_vertical_code") or organization_profile.get("vertical_industry", "DEFAULT_ENTERPRISE")).upper()
        sector_spec = sector_benchmarks.get(raw_vertical, sector_benchmarks.get("DEFAULT_ENTERPRISE", {}))
        rev_per_employee = sector_spec.get("revenue_per_employee_benchmark")

        if headcount is not None and rev_per_employee is not None:
            try:
                derived_rev = Decimal(str(headcount)) * Decimal(str(rev_per_employee))
                if derived_rev > Decimal("0"):
                    return derived_rev, RevenueSourceType.PARAMETRIC_DERIVATION
            except (InvalidOperation, ValueError, TypeError):
                pass

        raise TelemetryResolutionError(
            "Unable to resolve corporate revenue via direct filing telemetry or parametric headcount derivation."
        )

    def _resolve_perimeter_weight_pct(
        self,
        organization_profile: Mapping[str, Any],
        sector_benchmarks: Mapping[str, Any],
    ) -> Decimal:
        """Resolves the percentage of global corporate revenue sustained by the audited site/perimeter."""
        perimeter_block = organization_profile.get("perimeter_context", {})
        if not isinstance(perimeter_block, dict):
            perimeter_block = {}

        raw_weight = perimeter_block.get("perimeter_revenue_weight_pct")
        if raw_weight is None:
            raw_weight = organization_profile.get("perimeter_revenue_weight_pct")
        if raw_weight is None:
            raw_weight = organization_profile.get("site_revenue_weight_pct")

        if raw_weight is not None:
            try:
                weight_pct = Decimal(str(raw_weight))
            except (InvalidOperation, ValueError, TypeError) as exc:
                raise TelemetryResolutionError(
                    f"Invalid numeric format for 'perimeter_revenue_weight_pct': '{raw_weight}'"
                ) from exc

            if not (Decimal("0.0001") <= weight_pct <= Decimal("100.0")):
                raise TelemetryResolutionError(
                    f"'perimeter_revenue_weight_pct' must be in range (0, 100]. Received: {weight_pct}"
                )
            return weight_pct

        total_facilities = organization_profile.get("total_operational_facilities")
        if total_facilities is not None:
            try:
                facilities_count = int(total_facilities)
                if facilities_count > 0:
                    proportional_weight = (Decimal("100.0") / Decimal(str(facilities_count))).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    return proportional_weight
            except (ValueError, TypeError):
                pass

        raw_vertical = str(organization_profile.get("industry_vertical_code") or organization_profile.get("vertical_industry", "DEFAULT_ENTERPRISE")).upper()
        sector_spec = sector_benchmarks.get(raw_vertical, sector_benchmarks.get("DEFAULT_ENTERPRISE", {}))
        default_node_weight = sector_spec.get("default_single_site_weight_pct")
        if default_node_weight is not None:
            return Decimal(str(default_node_weight))

        raise TelemetryResolutionError(
            "Missing 'perimeter_revenue_weight_pct' and insufficient structural topology telemetry "
            "('total_operational_facilities') to compute site-specific revenue weighting."
        )

    def _resolve_sector_impact_factor(
        self,
        organization_profile: Mapping[str, Any],
        sector_benchmarks: Mapping[str, Any],
    ) -> Decimal:
        """Resolves the hourly sector impact multiplier (alpha_sector)."""
        raw_vertical = str(organization_profile.get("industry_vertical_code") or organization_profile.get("vertical_industry", "DEFAULT_ENTERPRISE")).upper()
        sector_spec = sector_benchmarks.get(raw_vertical, sector_benchmarks.get("DEFAULT_ENTERPRISE", {}))
        
        raw_factor = (
            organization_profile.get("sector_hourly_impact_factor")
            or sector_spec.get("hourly_revenue_exposure_factor")
        )

        if raw_factor is not None:
            factor = Decimal(str(raw_factor))
            if factor <= Decimal("0"):
                raise TelemetryResolutionError("Sector impact factor must be strictly positive.")
            return factor

        op_hours = Decimal(
            str(sector_spec.get("annual_operational_hours", self.DEFAULT_OPERATIONAL_HOURS_PER_YEAR))
        )
        impact_multiplier = Decimal(str(sector_spec.get("operational_interruption_multiplier", "1.0")))

        return (impact_multiplier / op_hours).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _extract_currency(organization_profile: Mapping[str, Any]) -> str:
        """Extracts ISO 4217 currency code from profile telemetry."""
        currency = (
            organization_profile.get("currency_code")
            or organization_profile.get("financial_metrics", {}).get("currency_code")
            or "EUR"
        )
        return str(currency).upper().strip()

    @staticmethod
    def _extract_perimeter_name(organization_profile: Mapping[str, Any]) -> str:
        """Extracts human-readable identifier of the audited facility or perimeter."""
        perimeter = (
            organization_profile.get("perimeter_context", {}).get("perimeter_name")
            or organization_profile.get("audited_site_name")
            or organization_profile.get("facility_identifier")
            or "Primary Audited Operational Perimeter"
        )
        return str(perimeter).strip()
