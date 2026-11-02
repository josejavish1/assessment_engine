"""Actuarial downtime calibration engine enforcing revenue proportionality across enterprise scales."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Any


@dataclass(frozen=True)
class DowntimeCalibrationResult:
    """Immutable actuarial derivation record for hourly operational outage cost."""

    annual_revenue: Decimal
    currency_code: str
    industry_vertical_code: str
    sector_benchmark_source: str
    hourly_revenue_exposure_factor: Decimal
    gross_hourly_revenue_velocity: Decimal
    effective_velocity_bleed_pct: Decimal
    calibrated_hourly_downtime_cost: Decimal
    is_client_override: bool


class ActuarialDowntimeCalibrator:
    """Computes and documents the mathematically grounded hourly operational outage cost.

    Derives rate from corporate annual turnover and sector-specific ITIC/Gartner
    elasticity factors, scaling dynamically from mid-market SMEs to Global Fortune 10.
    """

    HOURS_PER_STANDARD_YEAR: Decimal = Decimal("8760")

    DEFAULT_SECTOR_CATALOG: Mapping[str, Mapping[str, Any]] = {
        "HEAVY_MANUFACTURING": {
            "benchmark_authority": "Gartner / ITIC Industrial Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000010"),  # 0.0010% of annual turnover/h
        },
        "GLOBAL_LOGISTICS": {
            "benchmark_authority": "ITIC Global Supply Chain Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000025"),  # 0.0025% of annual turnover/h
        },
        "FINANCIAL_SERVICES": {
            "benchmark_authority": "Gartner Tier-1 Banking Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000005"),  # 0.0005% of annual turnover/h
        },
        "HEALTHCARE": {
            "benchmark_authority": "HIMSS / Gartner Healthcare Continuity Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000015"),  # 0.0015% of annual turnover/h
        },
        "TECHNOLOGY_SAAS": {
            "benchmark_authority": "SaaS Capital / Gartner High-Availability Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000020"),  # 0.0020% of annual turnover/h
        },
        "DEFAULT_ENTERPRISE": {
            "benchmark_authority": "Gartner Cross-Industry Operational Continuity Benchmark",
            "hourly_revenue_exposure_factor": Decimal("0.000010"),  # 0.0010% of annual turnover/h
        },
    }

    def __init__(self, sector_catalog: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        self._sector_catalog = sector_catalog or self.DEFAULT_SECTOR_CATALOG

    def calibrate(self, organization_profile: Mapping[str, Any]) -> DowntimeCalibrationResult:
        """Calibrates defensible hourly downtime cost based on revenue and sector factors."""
        raw_rev = organization_profile.get("annual_revenue_amount") or organization_profile.get("annual_revenue_eur") or 1000000000
        annual_revenue = Decimal(str(raw_rev))
        currency_code = str(organization_profile.get("currency_code", "EUR")).upper()
        raw_vertical = str(organization_profile.get("industry_vertical_code") or organization_profile.get("vertical_industry", "DEFAULT_ENTERPRISE")).upper()

        sector_spec = self._sector_catalog.get(raw_vertical, self._sector_catalog.get("DEFAULT_ENTERPRISE", {}))
        benchmark_source = str(sector_spec.get("benchmark_authority", "Gartner / ITIC Benchmark"))
        exposure_factor = Decimal(str(sector_spec.get("hourly_revenue_exposure_factor", Decimal("0.000010"))))

        gross_hourly_velocity = (annual_revenue / self.HOURS_PER_STANDARD_YEAR).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        explicit_override = organization_profile.get("explicit_hourly_downtime_cost") or organization_profile.get("hourly_downtime_rate")
        if explicit_override is not None and float(explicit_override) > 0.0:
            calibrated_hourly_cost = Decimal(str(explicit_override)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            effective_factor = (calibrated_hourly_cost / annual_revenue) if annual_revenue > Decimal("0") else exposure_factor
            is_override = True
        else:
            calibrated_hourly_cost = (annual_revenue * exposure_factor).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            effective_factor = exposure_factor
            is_override = False

        effective_velocity_bleed_pct = (
            (calibrated_hourly_cost / gross_hourly_velocity * Decimal("100"))
            if gross_hourly_velocity > Decimal("0")
            else Decimal("0.00")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return DowntimeCalibrationResult(
            annual_revenue=annual_revenue,
            currency_code=currency_code,
            industry_vertical_code=raw_vertical,
            sector_benchmark_source=benchmark_source,
            hourly_revenue_exposure_factor=effective_factor,
            gross_hourly_revenue_velocity=gross_hourly_velocity,
            effective_velocity_bleed_pct=effective_velocity_bleed_pct,
            calibrated_hourly_downtime_cost=calibrated_hourly_cost,
            is_client_override=is_override,
        )
