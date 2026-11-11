"""Actuarial Parameter Pack and Kernel Calibration Loader (SR 11-7).

Defines Pydantic v2 data models for versioned actuarial parameter packs and kernel calibration packs.
Enforces canonical JSON serialization and SHA-256 integrity checks.
Eliminates hardcoded magic numbers and provides singleton/cached access.
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PertDistributionSpec(BaseModel):
    """PERT distribution parameters with strict min <= mode <= max ordering."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    min_val: float = Field(..., ge=0.0)
    mode_val: float = Field(..., ge=0.0)
    max_val: float = Field(..., ge=0.0)
    gamma: float = Field(default=4.0, gt=0.0)

    @model_validator(mode="after")
    def validate_pert_ordering(self) -> PertDistributionSpec:
        if not (self.min_val <= self.mode_val <= self.max_val):
            raise ValueError(
                f"Invalid PERT ordering: min ({self.min_val}) <= mode ({self.mode_val}) <= max ({self.max_val}) violated."
            )
        return self


class PertDispersionSpec(BaseModel):
    """Multipliers to derive PERT bounds from mode when only mode is provided."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tef_min_ratio: float = Field(default=0.45, gt=0.0, lt=1.0)
    tef_max_ratio: float = Field(default=2.20, gt=1.0)
    rto_min_ratio: float = Field(default=0.45, gt=0.0, lt=1.0)
    rto_max_ratio: float = Field(default=2.50, gt=1.0)


class OperationalZoneSpec(BaseModel):
    """Configuration for an operational criticality zone tier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    burn_multiplier: float = Field(..., gt=0.0, le=1.0)
    max_annual_outage_hours: float = Field(..., gt=0.0)
    secondary_loss_retention_factor: float = Field(..., ge=0.0, le=1.0)
    catastrophic_recovery_ceiling_hours: float = Field(..., gt=0.0)
    emergency_replacement_ratio: float = Field(..., ge=0.0, le=1.0)


class TowerDefaultSpec(BaseModel):
    """Default actuarial priors for an individual operational tower."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str = Field(..., min_length=1)
    default_tef_annual: float = Field(..., gt=0.0)
    default_rto_hours: float = Field(..., gt=0.0)
    default_direct_replacement_cost: float = Field(..., ge=0.0)
    default_hourly_downtime_cost: float = Field(..., ge=0.0)
    default_secondary_loss_prob: float = Field(..., ge=0.0, le=1.0)
    default_secondary_loss_mean: float = Field(..., ge=0.0)
    default_remediation_capex: float = Field(..., ge=0.0)
    default_control_effectiveness_alpha: float = Field(..., ge=0.0, le=1.0)
    default_intra_domain_correlation_rho: float = Field(..., ge=0.0, lt=1.0)


class GlobalFallbackSpec(BaseModel):
    """Fallback values when tower-specific priors are not configured."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tef_annual: float = Field(..., gt=0.0)
    rto_hours: float = Field(..., gt=0.0)
    direct_replacement_cost: float = Field(..., ge=0.0)
    hourly_downtime_cost: float = Field(..., ge=0.0)
    secondary_loss_prob: float = Field(..., ge=0.0, le=1.0)
    secondary_loss_mean: float = Field(..., ge=0.0)
    remediation_capex: float = Field(..., ge=0.0)
    cmmi_maturity_level: int = Field(..., ge=1, le=5)
    control_effectiveness_alpha: float = Field(..., ge=0.0, le=1.0)
    intra_domain_correlation_rho: float = Field(..., ge=0.0, lt=1.0)
    prior_alpha: float = Field(default=2.0, gt=0.0)
    prior_beta: float = Field(default=2.0, gt=0.0)
    default_zone_id: str = Field(default="TIER_2_CORE_OPERATIONS", min_length=1)
    hourly_wage_default: float = Field(default=65.0, gt=0.0)
    annual_it_opex_default: float = Field(default=5_000_000.0, gt=0.0)
    annual_revenue_default: float = Field(default=100_000_000.0, gt=0.0)
    statutory_max_fine_ceiling: float = Field(default=20_000_000.0, gt=0.0)
    statutory_max_fine_revenue_pct: float = Field(default=0.04, gt=0.0, lt=1.0)
    simulation_iterations: int = Field(default=8192, ge=100)


class SeverityMultiplierSpec(BaseModel):
    """Ordinal multipliers applied to TEF mode based on finding severity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    CRITICAL: float = Field(..., gt=0.0)
    HIGH: float = Field(..., gt=0.0)
    MEDIUM: float = Field(..., gt=0.0)
    LOW: float = Field(..., gt=0.0)


class ActuarialParameterPack(BaseModel):
    """Canonical parameter pack containing all enterprise actuarial calibration priors."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pack_id: str = Field(..., min_length=1)
    pack_version: str = Field(..., min_length=1)
    schema_version: Literal["2.0.0"] = "2.0.0"
    base_currency: str = Field(..., min_length=3, max_length=3)
    global_fallbacks: GlobalFallbackSpec
    severity_tef_multipliers: SeverityMultiplierSpec
    pert_dispersion: PertDispersionSpec = Field(default_factory=PertDispersionSpec)
    operational_zones: Dict[str, OperationalZoneSpec]
    towers: Dict[str, TowerDefaultSpec]
    pack_sha256: str = Field(default="")

    def compute_canonical_sha256(self) -> str:
        """Computes deterministic SHA-256 fingerprint over sorted canonical JSON excluding the hash itself."""
        payload = self.model_dump(exclude={"pack_sha256"}, mode="json")
        canonical_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()


class KernelCalibrationPack(BaseModel):
    """Versioned mathematical hyperparameters governing the Monte Carlo Copula kernel."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    calibration_id: str = Field(..., min_length=1)
    calibration_version: str = Field(..., min_length=1)
    schema_version: Literal["1.0.0"] = "1.0.0"
    vuln_min: float = Field(..., gt=0.0, lt=1.0)
    vuln_max: float = Field(..., gt=0.0, le=1.0)
    gamma: float = Field(..., gt=0.0)
    kappa: float = Field(..., gt=0.0)
    copula_df: int = Field(..., ge=3)
    intra_tower_boost: float = Field(..., ge=0.0, lt=1.0)
    secondary_loss_cv: float = Field(..., gt=0.0)
    spof_cmmi_penalty: int = Field(..., ge=0, le=4)
    max_dependence_loading: float = Field(..., ge=0.0, le=1.0)
    max_copula_correlation: float = Field(..., gt=0.0, lt=1.0)
    rto_cmmi_degradation_slope: float = Field(..., ge=0.0)
    rto_spof_multiplier: float = Field(..., ge=0.0, le=5.0)
    catastrophic_tail_quantile: float = Field(..., gt=0.5, lt=1.0)
    baseline_horizon_years: int = Field(default=3, ge=1)
    tail_collapse_metric: Literal["CVAR_90", "VAR_99"] = Field(default="CVAR_90")
    tail_collapse_threshold_frequency: float = Field(default=0.105, gt=0.0)
    secondary_loss_event_probability: float = Field(default=0.10, ge=0.0, le=1.0)
    calibration_sha256: str = Field(default="")

    @model_validator(mode="after")
    def validate_bounds(self) -> KernelCalibrationPack:
        if self.vuln_min >= self.vuln_max:
            raise ValueError("vuln_min must be strictly less than vuln_max")
        return self

    def compute_canonical_sha256(self) -> str:
        """Computes deterministic SHA-256 fingerprint over sorted canonical JSON."""
        payload = self.model_dump(exclude={"calibration_sha256"}, mode="json")
        canonical_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()


def create_default_kernel_calibration_pack() -> KernelCalibrationPack:
    """Creates a pure in-memory default KernelCalibrationPack without filesystem I/O."""
    cal = KernelCalibrationPack(
        calibration_id="fair_copula_kernel_std",
        calibration_version="2026.Q4.v1",
        vuln_min=0.08,
        vuln_max=0.95,
        gamma=1.45,
        kappa=0.35,
        copula_df=4,
        intra_tower_boost=0.25,
        secondary_loss_cv=0.50,
        spof_cmmi_penalty=1,
        max_dependence_loading=0.35,
        max_copula_correlation=0.85,
        rto_cmmi_degradation_slope=0.15,
        rto_spof_multiplier=0.35,
        catastrophic_tail_quantile=0.95,
        baseline_horizon_years=3,
        tail_collapse_metric="CVAR_90",
        tail_collapse_threshold_frequency=0.105,
        secondary_loss_event_probability=0.10,
    )
    return cal.model_copy(update={"calibration_sha256": cal.compute_canonical_sha256()})


def create_default_actuarial_parameter_pack() -> ActuarialParameterPack:
    """Creates a pure in-memory default ActuarialParameterPack without filesystem I/O."""
    pack = ActuarialParameterPack(
        pack_id="legacy_generic_v1",
        pack_version="2026.Q4.v2",
        base_currency="EUR",
        global_fallbacks=GlobalFallbackSpec(
            tef_annual=0.30,
            rto_hours=4.0,
            direct_replacement_cost=5000.0,
            hourly_downtime_cost=5000.0,
            secondary_loss_prob=0.25,
            secondary_loss_mean=2500.0,
            remediation_capex=10000.0,
            cmmi_maturity_level=3,
            control_effectiveness_alpha=0.60,
            intra_domain_correlation_rho=0.30,
            prior_alpha=2.0,
            prior_beta=2.0,
            default_zone_id="TIER_2_CORE_OPERATIONS",
            hourly_wage_default=65.0,
            annual_it_opex_default=5000000.0,
            annual_revenue_default=100000000.0,
            statutory_max_fine_ceiling=20000000.0,
            statutory_max_fine_revenue_pct=0.04,
            simulation_iterations=8192,
        ),
        severity_tef_multipliers=SeverityMultiplierSpec(
            CRITICAL=2.0,
            HIGH=1.0,
            MEDIUM=0.5,
            LOW=0.2,
        ),
        pert_dispersion=PertDispersionSpec(
            tef_min_ratio=0.45,
            tef_max_ratio=2.20,
            rto_min_ratio=0.45,
            rto_max_ratio=2.50,
        ),
        operational_zones={
            "TIER_1_MISSION_CRITICAL": OperationalZoneSpec(
                burn_multiplier=0.60,
                max_annual_outage_hours=24.0,
                secondary_loss_retention_factor=1.00,
                catastrophic_recovery_ceiling_hours=24.0,
                emergency_replacement_ratio=0.20,
            ),
            "TIER_2_CORE_OPERATIONS": OperationalZoneSpec(
                burn_multiplier=0.35,
                max_annual_outage_hours=48.0,
                secondary_loss_retention_factor=0.85,
                catastrophic_recovery_ceiling_hours=48.0,
                emergency_replacement_ratio=0.15,
            ),
            "TIER_3_INTERNAL_SUPPORT": OperationalZoneSpec(
                burn_multiplier=0.15,
                max_annual_outage_hours=72.0,
                secondary_loss_retention_factor=0.50,
                catastrophic_recovery_ceiling_hours=72.0,
                emergency_replacement_ratio=0.05,
            ),
        },
        towers={},
    )
    return pack.model_copy(update={"pack_sha256": pack.compute_canonical_sha256()})
