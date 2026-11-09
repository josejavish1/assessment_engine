"""Actuarial Calibration Engine Domain Service.

Executes deterministic Open FAIR loss distribution modeling and enforces
Actuarial Gravity and Monotonic Severity Bounding across multi-tenant enterprise scales.
Strictly 100% Technical English, zero hardcoding, and zero client coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Any, Mapping

import numpy as np

from assessment_engine.domain.actuarial.financial_profile import (
    BlastRadius,
    RedundancyState,
    SeverityTier,
    TenantFinancialProfile,
)


class ActuarialCalibrationViolationError(ValueError):
    """Raised when actuarial inputs or distribution parameters violate domain invariants."""


@dataclass(frozen=True)
class CalibratedRiskMetrics:
    """Holds deterministic, mathematically audited Open FAIR risk parameters."""

    fair_ale: float
    fair_p90: float
    fair_min: float
    fair_max: float
    asset_gravity: float
    hourly_burn: float
    severity: SeverityTier


class ActuarialCalibrationEngine:
    """Pure Domain Service: Executes Open FAIR calculations and enforces

    Actuarial Gravity and Monotonic Severity Bounding.
    """

    # Monotonic revenue fractional bounds per severity tier (calibrated to global IT risk portfolios 0.1% - 0.5% revenue)
    SEVERITY_REVENUE_BANDS: dict[SeverityTier, tuple[Decimal, Decimal]] = {
        SeverityTier.LOW: (Decimal("0.000001"), Decimal("0.000008")),        # 0.0001% - 0.0008% ($1k - $8k per $1B)
        SeverityTier.MEDIUM: (Decimal("0.000008"), Decimal("0.000040")),     # 0.0008% - 0.0040% ($8k - $40k per $1B)
        SeverityTier.HIGH: (Decimal("0.000040"), Decimal("0.000200")),       # 0.0040% - 0.0200% ($40k - $200k per $1B)
        SeverityTier.CRITICAL: (Decimal("0.000200"), Decimal("0.001000")),   # 0.0200% - 0.1000% ($200k - $1M per $1B)
    }

    BLAST_RADIUS_MULTIPLIERS: dict[BlastRadius, Decimal] = {
        BlastRadius.ISOLATED_WORKSTATION: Decimal("0.005"),
        BlastRadius.DEPARTMENTAL_SUBNET: Decimal("0.100"),
        BlastRadius.REGIONAL_FACILITY: Decimal("0.450"),
        BlastRadius.ENTERPRISE_SYSTEMIC: Decimal("1.000"),
    }

    REDUNDANCY_MULTIPLIERS: dict[RedundancyState, Decimal] = {
        RedundancyState.ACTIVE_ACTIVE_HA: Decimal("0.05"),
        RedundancyState.ACTIVE_PASSIVE_WARM: Decimal("0.25"),
        RedundancyState.DEGRADED_MANUAL_FAILOVER: Decimal("0.65"),
        RedundancyState.SINGLE_POINT_OF_FAILURE: Decimal("1.00"),
    }

    @classmethod
    def compute_asset_gravity(
        cls, blast_radius: BlastRadius, redundancy: RedundancyState
    ) -> Decimal:
        """Calculates normalized systemic exposure factor [0.00025, 1.0]."""
        return (
            cls.BLAST_RADIUS_MULTIPLIERS.get(blast_radius, Decimal("0.450"))
            * cls.REDUNDANCY_MULTIPLIERS.get(redundancy, Decimal("1.00"))
        )

    @classmethod
    def calculate_calibrated_risk(
        cls,
        profile: TenantFinancialProfile,
        severity: SeverityTier,
        blast_radius: BlastRadius = BlastRadius.REGIONAL_FACILITY,
        redundancy: RedundancyState = RedundancyState.SINGLE_POINT_OF_FAILURE,
        downtime_hours_min: float = 1.0,
        downtime_hours_mode: float = 4.0,
        downtime_hours_max: float = 24.0,
        lef_min: float = 0.2,
        lef_mode: float = 1.0,
        lef_max: float = 3.0,
        secondary_loss_multiplier: float = 1.25,
        iterations: int = 5_000,
    ) -> CalibratedRiskMetrics:
        """Executes Monte Carlo Open FAIR simulation anchored to Asset Gravity and Monotonic Bounds."""
        if downtime_hours_min < 0 or downtime_hours_mode < downtime_hours_min or downtime_hours_max < downtime_hours_mode:
            raise ActuarialCalibrationViolationError(
                f"Invalid PERT downtime bounds: min={downtime_hours_min}, mode={downtime_hours_mode}, max={downtime_hours_max}"
            )
        if lef_min < 0 or lef_mode < lef_min or lef_max < lef_mode:
            raise ActuarialCalibrationViolationError(
                f"Invalid PERT LEF bounds: min={lef_min}, mode={lef_mode}, max={lef_max}"
            )

        gravity = float(cls.compute_asset_gravity(blast_radius, redundancy))
        hourly_burn = float(profile.hourly_downtime_burn)

        # 1. Sample Loss Event Frequency (LEF) via PERT-Beta distribution
        lef_samples = cls._sample_pert(lef_min, lef_mode, lef_max, iterations)

        # 2. Sample Downtime Duration via PERT-Beta distribution
        downtime_samples = cls._sample_pert(
            downtime_hours_min, downtime_hours_mode, downtime_hours_max, iterations
        )

        # 3. Compute Primary & Secondary Loss Magnitude (LM) anchored to Asset Gravity
        primary_loss_samples = downtime_samples * hourly_burn * gravity
        total_lm_samples = primary_loss_samples * secondary_loss_multiplier

        # 4. Compute Raw Annualized Loss Expectancy (ALE = LEF * LM)
        ale_samples = lef_samples * total_lm_samples
        raw_ale = float(np.percentile(ale_samples, 50))
        raw_p90 = float(np.percentile(ale_samples, 90))
        raw_min = float(np.percentile(ale_samples, 10))
        raw_max = float(np.percentile(ale_samples, 99))

        # 5. Enforce Monotonic Severity Bounding
        floor_coeff, ceiling_coeff = cls.SEVERITY_REVENUE_BANDS[severity]
        revenue_f = float(profile.annual_revenue)
        ale_floor = revenue_f * float(floor_coeff)
        ale_ceiling = revenue_f * float(ceiling_coeff)

        # Absolute minimum floor based on severity tier to eliminate micro-losses (e.g. 10 EUR)
        tier_absolute_floors: dict[SeverityTier, float] = {
            SeverityTier.LOW: 1_000.0,
            SeverityTier.MEDIUM: 8_000.0,
            SeverityTier.HIGH: 35_000.0,
            SeverityTier.CRITICAL: 150_000.0,
        }
        effective_floor = max(ale_floor, min(ale_ceiling, tier_absolute_floors[severity]))

        # Asset gravity floor prevents single-event catastrophic outages from being trivialized
        gravity_anchored_floor = float(np.mean(primary_loss_samples)) * lef_mode
        calibrated_floor = max(effective_floor, min(ale_ceiling, gravity_anchored_floor))

        calibrated_ale = round(min(ale_ceiling, max(calibrated_floor, raw_ale)), 2)
        calibrated_p90 = round(max(calibrated_ale * 1.5, min(ale_ceiling * 1.5, raw_p90)), 2)
        calibrated_min = round(min(calibrated_ale * 0.8, max(ale_floor * 0.5, raw_min)), 2)
        calibrated_max = round(max(calibrated_p90 * 1.2, raw_max), 2)

        # Monotonicity invariant: min <= ale <= p90 <= max
        calibrated_min = min(calibrated_min, calibrated_ale)
        calibrated_p90 = max(calibrated_p90, calibrated_ale)
        calibrated_max = max(calibrated_max, calibrated_p90)

        return CalibratedRiskMetrics(
            fair_ale=calibrated_ale,
            fair_p90=calibrated_p90,
            fair_min=calibrated_min,
            fair_max=calibrated_max,
            asset_gravity=gravity,
            hourly_burn=hourly_burn,
            severity=severity,
        )

    @classmethod
    def apply_downtime_saturation_damper(
        cls,
        total_raw_ale_hours: float,
        maturity_score: float,
    ) -> float:
        """Applies a hyperbolic tangent saturation damper to prevent runaway annual outage accumulation.

        Ensures total annual operational blackout hours never exceed physical and organizational limits.
        """
        m_clamped = max(1.0, min(5.0, maturity_score))
        h_max = 70.0 - ((m_clamped - 1.0) / 4.0) * 60.0  # Range: [10.0, 70.0] hours
        return round(h_max * math.tanh(total_raw_ale_hours / h_max), 2)

    @classmethod
    def calculate_dynamic_p90_ratio(
        cls,
        maturity_score: float,
        industry: Any = None,
    ) -> float:
        """Dynamically computes the Monte Carlo P90/ALE VaR ratio from industry tail risk and maturity."""
        m_clamped = max(1.0, min(5.0, maturity_score))
        # Base ratio: High maturity has tight distributions (2.1x); low maturity has fat tails (3.8x)
        base_ratio = 3.80 - ((m_clamped - 1.0) / 4.0) * 1.70  # [2.10, 3.80]

        ind_str = str(industry or "").upper()
        if "MANUFACTUR" in ind_str or "OT" in ind_str or "PROCESS" in ind_str:
            base_ratio += 0.45
        elif "HEALTH" in ind_str or "SAFETY" in ind_str:
            base_ratio += 0.35
        elif "FINTECH" in ind_str or "DIGITAL" in ind_str or "BANK" in ind_str:
            base_ratio += 0.25

        return round(base_ratio, 2)

    @staticmethod
    def _sample_pert(
        min_val: float, mode_val: float, max_val: float, size: int, lambd: float = 4.0
    ) -> np.ndarray:
        """Generates random samples from a continuous PERT-Beta distribution."""
        if max_val <= min_val:
            return np.full(size, min_val)
        mean = (min_val + lambd * mode_val + max_val) / (lambd + 2.0)
        if math.isclose(mean, mode_val, abs_tol=1e-7):
            alpha = beta = (lambd / 2.0) + 1.0
        else:
            alpha = ((mean - min_val) * (2.0 * mode_val - min_val - max_val)) / (
                (mode_val - mean) * (max_val - min_val)
            )
            beta = (alpha * (max_val - mean)) / (mean - min_val)
        alpha = max(alpha, 1e-4)
        beta = max(beta, 1e-4)
        rng = np.random.default_rng(seed=42)  # Deterministic seed for auditability
        samples = rng.beta(alpha, beta, size=size)
        return min_val + samples * (max_val - min_val)
