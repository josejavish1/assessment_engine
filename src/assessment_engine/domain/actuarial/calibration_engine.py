"""Universal Actuarial Telemetry Calibration Engine (UATCE).

Implements closed-form, zero-hardcoded macroeconomic scaling functions across
all operational archetypes under Open FAIR (O-RT / FAIR-CAM / FAIR-MAM).
Strictly 100% Technical English, zero client coupling.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from assessment_engine.domain.actuarial.financial_profile import IndustryArchetype

REPO_ROOT = Path(__file__).resolve().parents[4]
ARCHETYPES_CONFIG_PATH = REPO_ROOT / "engine_config" / "taxonomy_actuarial_archetypes.json"


class ArchetypePriors(BaseModel):
    """Macroeconomic prior distributions and boundary constants for an operational archetype."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    it_spend_intensity_ratio: float = Field(..., gt=0.0, le=0.25)
    default_perimeter_ratio: float = Field(..., gt=0.0, le=1.0)
    buffering_elasticity_beta: float = Field(..., ge=0.10, le=1.0)
    cloud_intensity_gamma: float = Field(..., ge=0.05, le=0.95)
    regulatory_statutory_cap_pct: float = Field(..., ge=0.005, le=0.10)
    base_enforcement_discretion_theta: float = Field(..., ge=0.02, le=0.50)
    cyber_frequency_lambda_base: float = Field(..., ge=0.05, le=1.0)
    calibration_metadata: Optional[Dict[str, Any]] = Field(default=None)


class TenantTelemetryOverrides(BaseModel):
    """Optional factual tenant telemetry to override empirical archetype priors."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scoped_revenue_ratio: Optional[float] = Field(default=None, gt=0.0, le=1.0)
    declared_it_spend_ratio: Optional[float] = Field(default=None, gt=0.0, le=0.25)
    declared_cloud_opex_ratio: Optional[float] = Field(default=None, ge=0.05, le=0.95)
    custom_buffering_factor: Optional[float] = Field(default=None, ge=0.10, le=1.0)


class CalibratedRiskVector(BaseModel):
    """Strongly-typed macroeconomic risk allocation vector across canonical FAIR pillars."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    currency_iso: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    effective_revenue_perimeter: float = Field(..., ge=0.0)
    effective_it_budget: float = Field(..., ge=0.0)
    ale_availability_downtime: float = Field(..., ge=0.0)
    ale_cyber_extortion_breach: float = Field(..., ge=0.0)
    ale_regulatory_sanctions: float = Field(..., ge=0.0)
    ale_structural_capital_waste: float = Field(..., ge=0.0)

    @property
    def total_annualized_loss_expectancy(self) -> float:
        """Closed-form sum of all 4 calibrated FAIR loss pillars."""
        return round(
            self.ale_availability_downtime
            + self.ale_cyber_extortion_breach
            + self.ale_regulatory_sanctions
            + self.ale_structural_capital_waste,
            2,
        )


class UniversalActuarialCalibrationEngine:
    """Universal Actuarial Telemetry Calibration Engine (UATCE).

    Enforces cross-vertical parameterization invariance across all global industries.
    """

    MITIGATION_DECAY_CONSTANT: float = 1.85
    MATURITY_SCALE_MAX: float = 5.0
    MATURITY_SCALE_MIN: float = 1.0

    _priors_cache: Optional[Dict[str, ArchetypePriors]] = None

    @classmethod
    def load_priors(cls) -> Dict[str, ArchetypePriors]:
        """Loads and caches declarative archetype priors from engine configuration."""
        if cls._priors_cache is None:
            if not ARCHETYPES_CONFIG_PATH.exists():
                raise FileNotFoundError(f"Missing archetype config at {ARCHETYPES_CONFIG_PATH}")
            with open(ARCHETYPES_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            raw_arch = data.get("operational_archetypes", {})
            cache: Dict[str, ArchetypePriors] = {}
            for k, v in raw_arch.items():
                cache[k] = ArchetypePriors(
                    it_spend_intensity_ratio=float(v["it_spend_intensity_ratio"]),
                    default_perimeter_ratio=float(v["default_perimeter_ratio"]),
                    buffering_elasticity_beta=float(v["buffering_elasticity_beta"]),
                    cloud_intensity_gamma=float(v["cloud_intensity_gamma"]),
                    regulatory_statutory_cap_pct=float(v["regulatory_statutory_cap_pct"]),
                    base_enforcement_discretion_theta=float(v["base_enforcement_discretion_theta"]),
                    cyber_frequency_lambda_base=float(v["cyber_frequency_lambda_base"]),
                    calibration_metadata=v.get("calibration_metadata"),
                )
            cls._priors_cache = cache
        return cls._priors_cache

    @classmethod
    def compute_calibrated_ale(
        cls,
        gross_annual_revenue: float,
        archetype: IndustryArchetype,
        maturity_scores: Dict[str, float],
        uncalibrated_base_downtime_loss: float = 0.0,
        currency_iso: str = "USD",
        overrides: Optional[TenantTelemetryOverrides] = None,
    ) -> CalibratedRiskVector:
        """Computes calibrated multi-pillar ALE vector across any industry scale."""
        if gross_annual_revenue <= 0.0:
            raise ValueError(f"gross_annual_revenue must be positive, got {gross_annual_revenue}")

        priors_registry = cls.load_priors()
        arch_key = archetype.value if hasattr(archetype, "value") else str(archetype)

        # Fallback to standard enterprise B2B if not found
        priors = priors_registry.get(arch_key) or priors_registry["STANDARD_ENTERPRISE_B2B"]
        telemetry = overrides or TenantTelemetryOverrides()

        # 1. Operational Scope & Perimeter Calibration (Omega)
        omega = (
            telemetry.scoped_revenue_ratio
            if telemetry.scoped_revenue_ratio is not None
            else priors.default_perimeter_ratio
        )
        omega = max(0.05, min(1.0, omega))
        effective_revenue = gross_annual_revenue * omega

        # 2. IT Spend & Cloud Topology Calibration (Gamma)
        it_intensity = (
            telemetry.declared_it_spend_ratio
            if telemetry.declared_it_spend_ratio is not None
            else priors.it_spend_intensity_ratio
        )
        effective_it_budget = effective_revenue * it_intensity

        gamma = (
            telemetry.declared_cloud_opex_ratio
            if telemetry.declared_cloud_opex_ratio is not None
            else priors.cloud_intensity_gamma
        )
        gamma = max(0.05, min(0.95, gamma))

        # 3. Maturity Deficits: d_i in [0.0, 1.0] where 0 is perfect maturity (5.0)
        m_avail = max(1.0, min(5.0, maturity_scores.get("availability", 2.5)))
        m_cyber = max(1.0, min(5.0, maturity_scores.get("cybersecurity", 2.5)))
        m_gov = max(1.0, min(5.0, maturity_scores.get("governance", 2.5)))
        m_finops = max(1.0, min(5.0, maturity_scores.get("finops_architecture", 2.5)))

        deficit_cyber = (cls.MATURITY_SCALE_MAX - m_cyber) / 4.0
        deficit_gov = (cls.MATURITY_SCALE_MAX - m_gov) / 4.0
        deficit_finops = (cls.MATURITY_SCALE_MAX - m_finops) / 4.0

        # 4. Pillar I: Operational Availability & Business Interruption (Beta-damped)
        beta = (
            telemetry.custom_buffering_factor
            if telemetry.custom_buffering_factor is not None
            else priors.buffering_elasticity_beta
        )
        beta = max(0.10, min(1.0, beta))

        if uncalibrated_base_downtime_loss <= 0.0:
            # Derive uncalibrated base from gross annual revenue before perimeter damping
            gross_hourly_rate = gross_annual_revenue / 8760.0
            deficit_avail = (cls.MATURITY_SCALE_MAX - m_avail) / 4.0
            uncalibrated_base_downtime_loss = gross_hourly_rate * 24.0 * deficit_avail

        ale_availability = uncalibrated_base_downtime_loss * beta * omega

        # 5. Pillar II: Cyber Extortion, Incident Response & Forensics
        lambda_cyber = priors.cyber_frequency_lambda_base * (0.40 + 1.20 * deficit_cyber)
        incident_severity_ratio = 0.045 * (0.50 + 0.50 * beta)
        ale_cyber = effective_it_budget * lambda_cyber * incident_severity_ratio * (1.0 + deficit_cyber)

        # 6. Pillar III: Regulatory & Supervisory Sanctions (Theta-damped)
        theta_effective = priors.base_enforcement_discretion_theta * math.exp(
            -cls.MITIGATION_DECAY_CONSTANT * ((m_gov - cls.MATURITY_SCALE_MIN) / 4.0)
        )
        statutory_ceiling = effective_revenue * priors.regulatory_statutory_cap_pct
        breach_probability_joint = lambda_cyber * 0.15 * deficit_gov
        ale_regulatory = statutory_ceiling * theta_effective * breach_probability_joint

        # 7. Pillar IV: Structural Capital & Cloud FinOps Waste (Gamma-damped)
        cloud_waste_rate = 0.22 * gamma * deficit_finops
        onprem_inefficiency_rate = 0.065 * (1.0 - gamma) * deficit_finops
        ale_capital_waste = effective_it_budget * (cloud_waste_rate + onprem_inefficiency_rate)

        return CalibratedRiskVector(
            currency_iso=currency_iso.upper(),
            effective_revenue_perimeter=round(effective_revenue, 2),
            effective_it_budget=round(effective_it_budget, 2),
            ale_availability_downtime=round(ale_availability, 2),
            ale_cyber_extortion_breach=round(ale_cyber, 2),
            ale_regulatory_sanctions=round(ale_regulatory, 2),
            ale_structural_capital_waste=round(ale_capital_waste, 2),
        )
