# MASTER ARCHITECTURAL EXECUTION PLAN: ACTUARIAL CORE REMEDIATION (COMMIT `41d4c2d` -> `v2.0.0`)

**Document ID**: `ARCH-ACT-2026-Q4-V2`  
**Target Executor**: `gemini-3.8-flash` (Automated Systems Engineering Agent)  
**Author**: `gemini-4-argon` (Supreme Enterprise Architect & Chief Actuarial Examiner)  
**Repository**: `josejavish1/assessment_engine`  
**Base Commit**: `41d4c2d`  
**Strict Execution Policy**: Zero silent fallbacks, zero hardcoded magic numbers in execution paths, zero silent clamping, mandatory cryptographic lineage, 100% deterministic reproduction.

---

## 1. FILE INVENTORY & CHANGE MANIFEST

### 1.1. New Files to Create
1. `engine_config/actuarial/parameter_packs/kernel_calibration_v1.json` — Versioned mathematical hyperparameters for the Bayesian FAIR Copula Engine.
2. `src/assessment_engine/domain/actuarial/parameter_pack_loader.py` — Pydantic v2 schemas, SHA-256 canonical hashing, and singleton/cached loader for `ActuarialParameterPack` and `KernelCalibrationPack`.
3. `tests/unit/domain/actuarial/test_input_resolver.py` — Direct unit test suite for strict input validation, valid zero preservation, PERT ordering, and boolean parsing.
4. `tests/unit/domain/actuarial/test_parameter_pack_loading.py` — Unit tests verifying pack loading, SHA-256 verification, and zero-hardcoding compliance.
5. `tests/unit/domain/actuarial/test_fx_currency_consolidation.py` — Unit tests for multi-currency conversion, missing FX snapshot rejection, and FX lineage recording.

### 1.2. Existing Files to Modify
1. `engine_config/actuarial/parameter_packs/legacy_generic_v1.json` — Ensure complete alignment with `ActuarialParameterPack` schema (all tower defaults, global fallbacks, and baseline constants).
2. `src/assessment_engine/domain/actuarial/context.py` — Enforce strict FX snapshot validation when `source_currency != reporting_currency` and compute `context_sha256`.
3. `src/assessment_engine/domain/actuarial/manifest.py` — Bump `manifest_schema_version="2.0.0"`, `actuarial_model_version="2026.Q4.v2"`, add mandatory pack/context hashes, and implement exact float canonical JSON SHA-256 fingerprinting.
4. `src/assessment_engine/domain/actuarial/input_resolver.py` — Strip all 34 hardcoded numeric literals; inject `ActuarialParameterPack`; enforce strict validation (no silent repair of negative numbers, inverted PERT, out-of-bounds CMMI, or garbage booleans); implement FX normalization and archetype evidence matrix.
5. `src/assessment_engine/domain/actuarial/bayesian_fair_copula_engine.py` — Enforce strict invariants in `FindingTelemetry.__post_init__`; replace 11 hardcoded constructor hyperparameters with `KernelCalibrationPack`; remove silent clamping in simulation loop; rename oversold actuarial properties (`weighted_maturity_adjustment`, `p95_single_event_stress_loss`, `three_year_undiscounted_baseline_expected_loss`).
6. `src/assessment_engine/domain/actuarial/canonical_risk_orchestrator.py` — Require `ActuarialContext` (or explicit `allow_legacy_default_context=True` flag for non-prod tests); inject parameter packs; fix composition status bug across custom/T1 domains.

### 1.3. Dead Code Files to Purge (`git rm`)
Verify zero active imports across `src/` and `tests/` before deletion:
1. `src/assessment_engine/domain/actuarial/actuarial_calibration_engine.py`
2. `src/assessment_engine/domain/actuarial/actuarial_ledger.py`
3. `src/assessment_engine/domain/actuarial/calculators.py`
4. `src/assessment_engine/domain/actuarial/calibration_engine.py`
5. `src/assessment_engine/domain/actuarial/continuous_risk_allocator.py`
6. `src/assessment_engine/domain/actuarial/vectors.py`

---

## 2. COMPLETE DATA CONTRACTS & PYDANTIC SCHEMAS

### 2.1. Parameter Pack & Kernel Calibration Schemas
**File**: `src/assessment_engine/domain/actuarial/parameter_pack_loader.py`

```python
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PertDistributionSpec(BaseModel):
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


class TowerDefaultSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str
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
    prior_alpha: float = Field(..., gt=0.0)
    prior_beta: float = Field(..., gt=0.0)
    default_Zone_id: str = Field(default="GLOBAL_DEFAULT_ZONE", min_length=1)


class SeverityMultiplierSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    CRITICAL: float = Field(..., gt=0.0)
    HIGH: float = Field(..., gt=0.0)
    MEDIUM: float = Field(..., gt=0.0)
    LOW: float = Field(..., gt=0.0)


class ActuarialParameterPack(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    pack_id: str = Field(..., min_length=1)
    pack_version: str = Field(..., min_length=1)
    schema_version: Literal["2.0.0"] = "2.0.0"
    base_currency: str = Field(..., min_length=3, max_length=3)
    global_fallbacks: GlobalFallbackSpec
    severity_tef_multipliers: SeverityMultiplierSpec
    towers: Dict[str, TowerDefaultSpec]
    pack_sha256: str = Field(default="")

    def compute_canonical_sha256(self) -> str:
        payload = self.model_dump(exclude={"pack_sha256"}, mode="json")
        canonical_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()


class KernelCalibrationPack(BaseModel):
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
    rto_spof_multiplier: float = Field(..., ge=1.0)
    catastrophic_tail_quantile: float = Field(..., gt=0.5, lt=1.0)
    baseline_horizon_years: int = Field(default=3, ge=1)
    calibration_sha256: str = Field(default="")

    @model_validator(mode="after")
    def validate_bounds(self) -> KernelCalibrationPack:
        if self.vuln_min >= self.vuln_max:
            raise ValueError("vuln_min must be strictly less than vuln_max")
        return self

    def compute_canonical_sha256(self) -> str:
        payload = self.model_dump(exclude={"calibration_sha256"}, mode="json")
        canonical_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()


DEFAULT_PACK_DIR = Path(__file__).resolve().parents[4] / "engine_config" / "actuarial" / "parameter_packs"


@lru_cache(maxsize=16)
def load_actuarial_parameter_pack(pack_path: Optional[Path] = None) -> ActuarialParameterPack:
    target = pack_path or (DEFAULT_PACK_DIR / "legacy_generic_v1.json")
    if not target.exists():
        raise FileNotFoundError(f"Actuarial parameter pack not found at {target}")
    raw_bytes = target.read_bytes()
    raw_data = json.loads(raw_bytes.decode("utf-8"))
    pack = ActuarialParameterPack.model_validate(raw_data)
    computed_hash = pack.compute_canonical_sha256()
    return pack.model_copy(update={"pack_sha256": computed_hash})


@lru_cache(maxsize=16)
def load_kernel_calibration_pack(calibration_path: Optional[Path] = None) -> KernelCalibrationPack:
    target = calibration_path or (DEFAULT_PACK_DIR / "kernel_calibration_v1.json")
    if not target.exists():
        raise FileNotFoundError(f"Kernel calibration pack not found at {target}")
    raw_bytes = target.read_bytes()
    raw_data = json.loads(raw_bytes.decode("utf-8"))
    cal = KernelCalibrationPack.model_validate(raw_data)
    computed_hash = cal.compute_canonical_sha256()
    return cal.model_copy(update={"calibration_sha256": computed_hash})
```

---

### 2.2. JSON Configuration Files

#### 2.2.1. `engine_config/actuarial/parameter_packs/kernel_calibration_v1.json`
```json
{
  "calibration_id": "fair_copula_kernel_std",
  "calibration_version": "2026.Q4.v1",
  "schema_version": "1.0.0",
  "vuln_min": 0.02,
  "vuln_max": 0.95,
  "gamma": 4.0,
  "kappa": 0.35,
  "copula_df": 4,
  "intra_tower_boost": 0.25,
  "secondary_loss_cv": 0.50,
  "spof_cmmi_penalty": 1,
  "max_dependence_loading": 0.35,
  "max_copula_correlation": 0.85,
  "rto_cmmi_degradation_slope": 0.15,
  "rto_spof_multiplier": 1.35,
  "catastrophic_tail_quantile": 0.95,
  "baseline_horizon_years": 3
}
```

#### 2.2.2. `engine_config/actuarial/parameter_packs/legacy_generic_v1.json`
Update to strictly conform to `ActuarialParameterPack` schema v2.0.0, consolidating all tower defaults (`T1` through `T11`) and global fallbacks previously scattered across `canonical_risk_orchestrator.py:118-145` and `input_resolver.py:154-275`.

---

### 2.3. Context & Mandatory FX Contract
**File**: `src/assessment_engine/domain/actuarial/context.py`

```python
from __future__ import annotations

import hashlib
import json
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FxRateSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_id: str = Field(..., min_length=1)
    timestamp_utc: str = Field(..., min_length=1)
    base_currency: str = Field(..., min_length=3, max_length=3)
    rates: Dict[str, float] = Field(..., description="Multiplier to convert 1 unit of key currency into reporting/base currency or vice-versa as standardized below")

    @model_validator(mode="after")
    def validate_positive_rates(self) -> FxRateSnapshot:
        for curr, rate in self.rates.items():
            if len(curr) != 3 or rate <= 0.0:
                raise ValueError(f"Invalid currency code '{curr}' or non-positive FX rate '{rate}'")
        return self


class ActuarialContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    assessment_id: str = Field(..., min_length=1)
    risk_scope: str = Field(..., min_length=1)
    assessment_period: str = Field(..., min_length=1)
    source_currency: str = Field(..., min_length=3, max_length=3)
    reporting_currency: str = Field(..., min_length=3, max_length=3)
    fx_snapshot: Optional[FxRateSnapshot] = None
    random_seed: int = Field(default=42, ge=0)
    n_simulations: int = Field(default=10000, ge=100)

    @model_validator(mode="after")
    def validate_fx_requirements(self) -> ActuarialContext:
        if self.source_currency != self.reporting_currency:
            if self.fx_snapshot is None:
                raise ValueError(
                    f"fx_snapshot is mandatory when source_currency ({self.source_currency}) "
                    f"differs from reporting_currency ({self.reporting_currency})."
                )
            pair_key = f"{self.source_currency}_{self.reporting_currency}"
            if pair_key not in self.fx_snapshot.rates and self.source_currency not in self.fx_snapshot.rates:
                raise ValueError(
                    f"FX rate for converting {self.source_currency} to {self.reporting_currency} "
                    f"is missing in fx_snapshot '{self.fx_snapshot.snapshot_id}'."
                )
        return self

    def get_fx_rate(self, from_currency: Optional[str] = None) -> tuple[float, str]:
        src = (from_currency or self.source_currency).upper()
        dst = self.reporting_currency.upper()
        if src == dst:
            snap_id = self.fx_snapshot.snapshot_id if self.fx_snapshot else "IDENTITY_1_TO_1"
            return 1.0, snap_id
        if self.fx_snapshot is None:
            raise ValueError(f"Cannot convert {src} -> {dst} without fx_snapshot.")
        pair_key = f"{src}_{dst}"
        if pair_key in self.fx_snapshot.rates:
            return float(self.fx_snapshot.rates[pair_key]), self.fx_snapshot.snapshot_id
        if src in self.fx_snapshot.rates and self.fx_snapshot.base_currency.upper() == dst:
            return float(self.fx_snapshot.rates[src]), self.fx_snapshot.snapshot_id
        raise ValueError(f"Missing conversion rate for {src} -> {dst} in snapshot {self.fx_snapshot.snapshot_id}")

    def normalize_monetary_amount(self, amount: float, from_currency: Optional[str] = None) -> tuple[float, float, str]:
        if amount < 0.0:
            raise ValueError(f"Monetary amount cannot be negative: {amount}")
        rate, snap_id = self.get_fx_rate(from_currency)
        return float(amount * rate), rate, snap_id

    def compute_context_sha256(self) -> str:
        payload = self.model_dump(mode="json")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
```

---

### 2.4. Strict `FindingTelemetry` Contract
**File**: `src/assessment_engine/domain/actuarial/bayesian_fair_copula_engine.py`

Update `FindingTelemetry.__post_init__` to enforce strict mathematical invariants without silent clamping:

```python
@dataclass(frozen=True)
class FindingTelemetry:
    finding_id: str
    domain_id: str
    zone_id: str
    tef_annual: float
    direct_replacement_cost: float
    hourly_downtime_cost: float
    rto_min_hours: float
    rto_mode_hours: float
    rto_max_hours: float
    secondary_loss_prob: float
    secondary_loss_mean: float
    cmmi_maturity_level: int
    is_spof: bool
    remediation_capex: float
    control_effectiveness_alpha: float
    intra_domain_correlation_rho: float
    audit_k_failures: Optional[int] = None
    audit_n_trials: Optional[int] = None
    prior_alpha: float = 2.0
    prior_beta: float = 2.0
    site_id: str = "DEFAULT_SITE"

    def __post_init__(self) -> None:
        if not self.finding_id or not self.finding_id.strip():
            raise ValueError("finding_id must be a non-empty string")
        if not self.domain_id or not self.domain_id.strip():
            raise ValueError("domain_id must be a non-empty string")
        if not self.zone_id or not self.zone_id.strip():
            raise ValueError("zone_id must be a non-empty string")
        if not isinstance(self.is_spof, bool):
            raise ValueError(f"is_spof must be strictly a bool, got {type(self.is_spof).__name__}")
        if self.tef_annual <= 0.0:
            raise ValueError(f"tef_annual must be > 0.0, got {self.tef_annual}")
        if self.direct_replacement_cost < 0.0:
            raise ValueError(f"direct_replacement_cost must be >= 0.0, got {self.direct_replacement_cost}")
        if self.hourly_downtime_cost < 0.0:
            raise ValueError(f"hourly_downtime_cost must be >= 0.0, got {self.hourly_downtime_cost}")
        if self.rto_min_hours <= 0.0 or self.rto_mode_hours <= 0.0 or self.rto_max_hours <= 0.0:
            raise ValueError(
                f"RTO PERT parameters must all be > 0.0, got min={self.rto_min_hours}, "
                f"mode={self.rto_mode_hours}, max={self.rto_max_hours}"
            )
        if not (self.rto_min_hours <= self.rto_mode_hours <= self.rto_max_hours):
            raise ValueError(
                f"RTO PERT ordering violated: min ({self.rto_min_hours}) <= mode ({self.rto_mode_hours}) "
                f"<= max ({self.rto_max_hours})"
            )
        if not (0.0 <= self.secondary_loss_prob <= 1.0):
            raise ValueError(f"secondary_loss_prob must be in [0.0, 1.0], got {self.secondary_loss_prob}")
        if self.secondary_loss_mean < 0.0:
            raise ValueError(f"secondary_loss_mean must be >= 0.0, got {self.secondary_loss_mean}")
        if self.secondary_loss_prob == 0.0 and self.secondary_loss_mean > 0.0:
            # Allowed, or if secondary_loss_prob > 0 and mean == 0, valid zero loss
            pass
        if not isinstance(self.cmmi_maturity_level, int) or isinstance(self.cmmi_maturity_level, bool) or not (1 <= self.cmmi_maturity_level <= 5):
            raise ValueError(f"cmmi_maturity_level must be an integer in [1, 5], got {self.cmmi_maturity_level}")
        if self.remediation_capex < 0.0:
            raise ValueError(f"remediation_capex must be >= 0.0, got {self.remediation_capex}")
        if not (0.0 <= self.control_effectiveness_alpha <= 1.0):
            raise ValueError(f"control_effectiveness_alpha must be in [0.0, 1.0], got {self.control_effectiveness_alpha}")
        if not (0.0 <= self.intra_domain_correlation_rho < 1.0):
            raise ValueError(f"intra_domain_correlation_rho must be in [0.0, 1.0), got {self.intra_domain_correlation_rho}")
        if self.prior_alpha <= 0.0 or self.prior_beta <= 0.0:
            raise ValueError(f"Beta prior parameters must be > 0.0, got alpha={self.prior_alpha}, beta={self.prior_beta}")
        if (self.audit_k_failures is None) != (self.audit_n_trials is None):
            raise ValueError("audit_k_failures and audit_n_trials must both be provided or both be None")
        if self.audit_k_failures is not None and self.audit_n_trials is not None:
            if isinstance(self.audit_k_failures, bool) or isinstance(self.audit_n_trials, bool):
                raise ValueError("audit counts must be integers, not booleans")
            if self.audit_k_failures < 0 or self.audit_n_trials <= 0:
                raise ValueError(f"Invalid audit counts: k={self.audit_k_failures} (must be >=0), n={self.audit_n_trials} (must be >0)")
            if self.audit_k_failures > self.audit_n_trials:
                raise ValueError(f"audit_k_failures ({self.audit_k_failures}) cannot exceed audit_n_trials ({self.audit_n_trials})")
```

---

### 2.5. Strict `ActuarialInputResolver` Specification
**File**: `src/assessment_engine/domain/actuarial/input_resolver.py`

#### Key Rules to Implement in `ActuarialInputResolver`:
1. **Constructor Injection**:
   ```python
   def __init__(self, parameter_pack: Optional[ActuarialParameterPack] = None) -> None:
       self.parameter_pack = parameter_pack or load_actuarial_parameter_pack()
   ```
2. **Distinguish `None` (Missing) from Invalid (Explicitly Out-of-Range)**:
   - Never use `val = payload.get("key") or default` because `0.0` or `0` or `False` is falsy in Python!
   - Always check `if raw_val is None:` -> resolve from `self.parameter_pack` and mark source as `PARAMETER_PACK_FALLBACK` with confidence `LOW`.
   - If `raw_val is not None`: validate type and domain strictly. If invalid (e.g., `tef_annual <= 0`, `rto_hours <= 0`, `direct_replacement_cost < 0`, `cmmi < 1` or `cmmi > 5`, `alpha < 0` or `alpha > 1`, `rho < 0` or `rho >= 1`), **raise `ValueError` immediately**.
3. **Strict Boolean Parsing**:
   ```python
   def _parse_strict_bool(raw_val: Any, field_name: str) -> bool:
       if isinstance(raw_val, bool):
           return raw_val
       if isinstance(raw_val, str):
           normalized = raw_val.strip().lower()
           if normalized in ("true", "1", "yes"):
               return True
           if normalized in ("false", "0", "no"):
               return False
       raise ValueError(f"Invalid boolean value for '{field_name}': {raw_val!r}")
   ```
   - Only when `raw_val is None` does `is_spof` default to `False` with `source=PARAMETER_PACK_FALLBACK` and `confidence=LOW`.
   - When `raw_val` is explicitly provided and valid, `source=ASSESSMENT_PAYLOAD` and `confidence=HIGH`.
4. **Strict PERT Resolution**:
   - If `rto_min_hours`, `rto_mode_hours`, `rto_max_hours` are provided in the payload:
     - Validate each is `> 0.0`.
     - Validate `rto_min_hours <= rto_mode_hours <= rto_max_hours`. Do **not** call `sorted([min, mode, max])`. If out of order, raise `ValueError`.
   - If only scalar `rto_hours` is provided (`> 0.0`), derive PERT bounds using documented pack multipliers (e.g., `min = 0.5 * rto_hours`, `mode = rto_hours`, `max = 2.5 * rto_hours`) and record `DERIVED_FROM_SCALAR` with `MEDIUM` confidence.
5. **Mandatory FX Conversion & Lineage**:
   - Every monetary field (`direct_replacement_cost`, `hourly_downtime_cost`, `secondary_loss_mean`, `remediation_capex`):
     - Determine input currency: if resolved from explicit payload, use `context.source_currency` (or finding-level `currency` override if present); if resolved from `parameter_pack`, use `self.parameter_pack.base_currency`.
     - Call `converted_amount, fx_rate, fx_snapshot_id = context.normalize_monetary_amount(raw_amount, from_currency=input_currency)`.
     - Store `original_currency=input_currency`, `reporting_currency=context.reporting_currency`, `fx_rate=fx_rate`, and `fx_snapshot_id=fx_snapshot_id` inside `ParameterLineageEntry`.
6. **Archetype Evidence Matrix (`QuantificationStatus`)**:
   - Define material parameters required for `QUANTIFIED`:
     - `tef_annual` (or explicit `rto` + frequency evidence)
     - `rto_hours` (or full PERT triplet)
     - At least one primary loss driver (`direct_replacement_cost` or `hourly_downtime_cost`)
     - `cmmi_maturity_level`
   - Status evaluation rules per finding:
     - If **all** material parameters come from `ASSESSMENT_PAYLOAD` (or `EMPIRICAL_TELEMETRY`), finding status = `QUANTIFIED`.
     - If **any** material parameter falls back to `PARAMETER_PACK_FALLBACK` (even if TEF and RTO are explicit, e.g., cost or CMMI came from pack), finding status = `ESTIMATED_LOW_CONFIDENCE`.
     - If an unrecognized/custom domain has no tower entry in `parameter_pack` and lacks explicit material inputs, finding status = `INSUFFICIENT_EVIDENCE`.

---

### 2.6. Manifest v2.0.0 & Exact Canonical Vector Fingerprinting
**File**: `src/assessment_engine/domain/actuarial/manifest.py`

```python
class ParameterLineageEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter_name: str
    resolved_value: Union[float, int, bool, str]
    source: str
    confidence: str
    original_currency: Optional[str] = None
    reporting_currency: Optional[str] = None
    fx_rate: Optional[float] = None
    fx_snapshot_id: Optional[str] = None


class ActuarialExecutionManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_schema_version: Literal["2.0.0"] = "2.0.0"
    actuarial_model_version: Literal["2026.Q4.v2"] = "2026.Q4.v2"
    assessment_id: str = Field(..., min_length=1)
    risk_scope: str = Field(..., min_length=1)
    assessment_period: str = Field(..., min_length=1)
    parameter_pack_id: str = Field(..., min_length=1)
    parameter_pack_version: str = Field(..., min_length=1)
    parameter_pack_sha256: str = Field(..., min_length=64, max_length=64)
    kernel_calibration_id: str = Field(..., min_length=1)
    kernel_calibration_version: str = Field(..., min_length=1)
    kernel_calibration_sha256: str = Field(..., min_length=64, max_length=64)
    context_sha256: str = Field(..., min_length=64, max_length=64)
    input_vector_fingerprint_sha256: str = Field(..., min_length=64, max_length=64)
    quantification_status: str
    finding_lineage: Dict[str, Dict[str, ParameterLineageEntry]]
```

#### Exact Canonical Vector Fingerprinting Function:
Do **not** use `f"{val:.2f}"` or `f"{val:.4f}"` when computing `input_vector_fingerprint_sha256`. Serialize exact IEEE 754 float values along with pack and context hashes:
```python
def compute_exact_vector_fingerprint(
    telemetry_vector: Sequence[FindingTelemetry],
    parameter_pack_sha256: str,
    kernel_calibration_sha256: str,
    context_sha256: str,
) -> str:
    sorted_items = sorted(
        telemetry_vector,
        key=lambda t: (t.site_id, t.domain_id, t.zone_id, t.finding_id),
    )
    canonical_payload = {
        "parameter_pack_sha256": parameter_pack_sha256,
        "kernel_calibration_sha256": kernel_calibration_sha256,
        "context_sha256": context_sha256,
        "vector": [dataclasses.asdict(item) for item in sorted_items],
    }
    encoded = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
```

---

## 3. STEP-BY-STEP IMPLEMENTATION SEQUENCE (PHASES 1 TO 7)

### PHASE 1: Dead Code Purge & Hygiene Verification
1. **Action**: Run `grep -rn` across `src/` and `tests/` for references to the 6 legacy modules:
   - `actuarial_calibration_engine`
   - `actuarial_ledger`
   - `calculators`
   - `calibration_engine`
   - `continuous_risk_allocator`
   - `vectors`
2. **Action**: Remove any unused re-exports in `src/assessment_engine/domain/actuarial/__init__.py` and delete the 6 files.
3. **Pitfall to Avoid**: Do not delete `bayesian_fair_copula_engine.py`, `canonical_risk_orchestrator.py`, `input_resolver.py`, `context.py`, or `manifest.py`.
4. **Verification Command**:
   ```bash
   pytest -q
   ```

---

### PHASE 2: Parameter Pack & Kernel Calibration Pack Infrastructure
1. **Action**: Create `engine_config/actuarial/parameter_packs/kernel_calibration_v1.json` and update `engine_config/actuarial/parameter_packs/legacy_generic_v1.json`.
2. **Action**: Create `src/assessment_engine/domain/actuarial/parameter_pack_loader.py` implementing `ActuarialParameterPack`, `KernelCalibrationPack`, `load_actuarial_parameter_pack()`, and `load_kernel_calibration_pack()`.
3. **Pitfall to Avoid**: Ensure `compute_canonical_sha256()` excludes the hash field itself (`pack_sha256` / `calibration_sha256`) so the hash calculation is idempotent.
4. **Verification Command**:
   ```bash
   pytest tests/unit/domain/actuarial/test_parameter_pack_loading.py -q
   ```

---

### PHASE 3: Context FX Enforcement & Manifest v2.0.0 Upgrade
1. **Action**: Update `src/assessment_engine/domain/actuarial/context.py`:
   - Enforce `validate_fx_requirements` model validator when `source_currency != reporting_currency`.
   - Implement `normalize_monetary_amount()` and `compute_context_sha256()`.
   - Remove default values on `risk_scope` and `assessment_period` in `ActuarialContext` (or require them explicitly on construction).
2. **Action**: Update `src/assessment_engine/domain/actuarial/manifest.py`:
   - Set `manifest_schema_version: Literal["2.0.0"] = "2.0.0"` and `actuarial_model_version: Literal["2026.Q4.v2"] = "2026.Q4.v2"`.
   - Add mandatory `parameter_pack_id`, `parameter_pack_version`, `parameter_pack_sha256`, `kernel_calibration_id`, `kernel_calibration_version`, `kernel_calibration_sha256`, and `context_sha256`.
   - Replace rounded float string formatting in fingerprinting with `compute_exact_vector_fingerprint()`.
3. **Verification Command**:
   ```bash
   pytest tests/unit/domain/actuarial/test_fx_currency_consolidation.py -q
   ```

---

### PHASE 4: Strict `ActuarialInputResolver` Refactoring
1. **Action**: Refactor `src/assessment_engine/domain/actuarial/input_resolver.py`:
   - Remove all 34 hardcoded numeric literals (`0.30`, `4.0`, `0.60`, tower dictionaries, etc.).
   - Inject `ActuarialParameterPack`.
   - Replace all falsy `or` checks (`payload.get("direct_replacement_cost") or default`) with explicit `is None` checks so `0.0` and `0` are preserved as `ASSESSMENT_PAYLOAD` (`HIGH` confidence).
   - Reject negative values (`tef_annual <= 0`, `rto <= 0`, costs `< 0`), out-of-range CMMI (`< 1` or `> 5`), out-of-range `alpha` (`< 0` or `> 1`), out-of-range `rho` (`< 0` or `>= 1`), `k_failures > n_trials`, inverted PERT (`min > mode` or `mode > max`), and invalid boolean strings by raising `ValueError`.
   - Convert all monetary fields via `context.normalize_monetary_amount()` and populate FX lineage (`original_currency`, `reporting_currency`, `fx_rate`, `fx_snapshot_id`).
   - Implement the Archetype Evidence Matrix: any finding using `PARAMETER_PACK_FALLBACK` on a material parameter receives `ESTIMATED_LOW_CONFIDENCE`, never `QUANTIFIED`.
2. **Pitfall to Avoid**: Do not confuse `direct_replacement_cost = 0.0` (valid zero) with `tef_annual = 0.0` (invalid frequency; TEF and RTO must be strictly `> 0.0`).
3. **Verification Command**:
   ```bash
   pytest tests/unit/domain/actuarial/test_input_resolver.py -q
   ```

---

### PHASE 5: Kernel Calibration Injection, Invariant Enforcement & Semantic Honesty
1. **Action**: Update `src/assessment_engine/domain/actuarial/bayesian_fair_copula_engine.py`:
   - Add strict validation in `FindingTelemetry.__post_init__` (Section 2.4).
   - Update `BayesianFairCopulaEngine.__init__` to accept `calibration_pack: Optional[KernelCalibrationPack] = None` (loading `load_kernel_calibration_pack()` by default) and source all 13 hyperparameters (`vuln_min`, `vuln_max`, `gamma`, `kappa`, `copula_df`, `intra_tower_boost`, `secondary_loss_cv`, `spof_cmmi_penalty`, `max_dependence_loading`, `max_copula_correlation`, `rto_cmmi_degradation_slope`, `rto_spof_multiplier`, `catastrophic_tail_quantile`) from `self.calibration_pack`.
   - Remove silent clamping in the Monte Carlo kernel (`max(0.0, replacement_cost)` and discarding negative secondary losses). Because `FindingTelemetry.__post_init__` and lognormal/PERT parameterization guarantee non-negativity, assert non-negativity instead of silently clamping.
   - Rename oversold metric fields/keys in kernel output dataclasses and dicts:
     - `maturity_discount_factor` -> `weighted_maturity_adjustment`
     - `var_95_ tail_loss` / `catastrophic_var_95` -> `p95_single_event_stress_loss`
     - `three_year_npv_loss` / `discounted_3yr_loss` -> `three_year_undiscounted_baseline_expected_loss`
     *(If backward-compatible aliases are needed for external JSON consumers, expose them as `@property` with a `DeprecationWarning`, while canonical dicts use the honest names).*
2. **Verification Command**:
   ```bash
   pytest -k "kernel or copula or invariance" -q
   ```

---

### PHASE 6: `CanonicalRiskOrchestrator` Context Enforcement & Status Composition Fix
1. **Action**: Update `src/assessment_engine/domain/actuarial/canonical_risk_orchestrator.py`:
   - Remove the 23 hardcoded tower default literals.
   - Make `context: ActuarialContext` mandatory in production execution (`orchestrate(findings, context)`). Raise `ValueError("ActuarialContext is mandatory for canonical risk orchestration")` if `context is None`.
   - Inject `parameter_pack` and `calibration_pack` into resolver, kernel, and manifest builder.
   - **Fix Status Composition Bug**:
     When aggregating finding-level statuses into portfolio-level `quantification_status`:
     - Empty findings -> `NOT_QUANTIFIED`
     - Any finding `INSUFFICIENT_EVIDENCE` -> portfolio status is `INSUFFICIENT_EVIDENCE` (previously, mixing a custom domain with `INSUFFICIENT_EVIDENCE` and a `T1` finding fell through to `NOT_QUANTIFIED`).
     - Else if any finding is `ESTIMATED_LOW_CONFIDENCE` -> portfolio status is `ESTIMATED_LOW_CONFIDENCE`.
     - Else if all findings are `QUANTIFIED` -> portfolio status is `QUANTIFIED`.
2. **Action**: Update existing tests that call `CanonicalRiskOrchestrator` without a context to pass an explicit `ActuarialContext` fixture.
3. **Verification Command**:
   ```bash
   pytest -q
   ```

---

### PHASE 7: AST Numeric Literal Audit & Full Regression Gate
1. **Action**: Run an AST inspection script across `input_resolver.py`, `bayesian_fair_copula_engine.py`, and `canonical_risk_orchestrator.py` to verify that only trivial mathematical constants (`0`, `0.0`, `1`, `1.0`, `2`, `100.0`) remain in code, and all domain/actuarial parameters originate from `ActuarialParameterPack` or `KernelCalibrationPack`.
2. **Verification Command**:
   ```bash
   pytest -v
   ```

---

## 4. COMPREHENSIVE UNIT TEST SPECIFICATIONS

### 4.1. `tests/unit/domain/actuarial/test_input_resolver.py`
Must implement the following 12 test functions:
1. `test_valid_zero_direct_replacement_cost_preserved`: Passes `direct_replacement_cost=0.0`, verifies resolved value is `0.0` (not pack default), `source == "ASSESSMENT_PAYLOAD"`, `confidence == "HIGH"`.
2. `test_valid_zero_control_effectiveness_alpha_preserved`: Passes `control_effectiveness_alpha=0.0`, verifies it is **not** overwritten by `0.60` via falsy `or`.
3. `test_valid_zero_intra_domain_correlation_rho_preserved`: Passes `intra_domain_correlation_rho=0.0`, verifies it is **not** overwritten by `0.30`.
4. `test_valid_zero_audit_k_failures_preserved`: Passes `audit_k_failures=0, audit_n_trials=10`, verifies `k=0, n=10` preserved.
5. `test_negative_tef_raises_value_error`: Passes `tef_annual=-0.5`, asserts `pytest.raises(ValueError, match="tef_annual")`.
6. `test_zero_or_negative_rto_raises_value_error`: Passes `rto_hours=0.0` and `rto_hours=-4.0`, asserts `pytest.raises(ValueError, match="rto")`.
7. `test_inverted_pert_raises_value_error_without_reordering`: Passes `rto_min_hours=10.0, rto_mode_hours=4.0, rto_max_hours=8.0`, asserts `pytest.raises(ValueError, match="PERT ordering")`.
8. `test_cmmi_out_of_bounds_raises_value_error`: Passes `cmmi_maturity_level=0` and `cmmi_maturity_level=6`, asserts `pytest.raises(ValueError, match="cmmi_maturity_level")`.
9. `test_k_failures_greater_than_n_trials_raises_value_error`: Passes `audit_k_failures=12, audit_n_trials=10`, asserts `pytest.raises(ValueError)` instead of mutating `n_trials`.
10. `test_garbage_boolean_is_spof_raises_value_error`: Passes `is_spof="garbage"`, asserts `pytest.raises(ValueError, match="is_spof")`.
11. `test_missing_material_parameter_downgrades_status_to_estimated_low_confidence`: Provides explicit `tef_annual` and `rto_hours`, omits `direct_replacement_cost` and `hourly_downtime_cost` (resolved from pack), asserts status is `ESTIMATED_LOW_CONFIDENCE` (never `QUANTIFIED`).
12. `test_finding_telemetry_post_init_rejects_direct_invalid_construction`: Directly instantiates `FindingTelemetry` with negative cost or inverted PERT and asserts `pytest.raises(ValueError)`.

---

### 4.2. `tests/unit/domain/actuarial/test_parameter_pack_loading.py`
Must implement the following 5 test functions:
1. `test_load_legacy_generic_v1_pack_succeeds_and_computes_sha256`: Loads default pack, asserts `len(pack.pack_sha256) == 64`, verifies all expected towers (`T1`–`T11`) exist.
2. `test_load_kernel_calibration_v1_succeeds_and_computes_sha256`: Loads default kernel calibration pack, verifies all 13 hyperparameters match specification and `len(cal.calibration_sha256) == 64`.
3. `test_parameter_pack_mutation_changes_manifest_and_vector_fingerprint`: Modifies a tower default cost in a copy of `ActuarialParameterPack`, runs orchestrator, verifies `parameter_pack_sha256` and `input_vector_fingerprint_sha256` both change.
4. `test_exact_float_fingerprinting_detects_sub_cent_perturbation`: Perturbs `direct_replacement_cost` from `1000.00001` to `1000.00002` (which rounded to `.2f` or `.4f` would collide), asserts `compute_exact_vector_fingerprint()` produces distinct SHA-256 digests.
5. `test_custom_plus_t1_domain_status_composition`: Combines an unquantified custom domain finding (`INSUFFICIENT_EVIDENCE`) with a valid `T1` finding (`QUANTIFIED`), asserts portfolio status is `INSUFFICIENT_EVIDENCE` (not `NOT_QUANTIFIED`).

---

### 4.3. `tests/unit/domain/actuarial/test_fx_currency_consolidation.py`
Must implement the following 5 test functions:
1. `test_mismatched_currencies_without_fx_snapshot_raises_validation_error`: Instantiates `ActuarialContext(source_currency="USD", reporting_currency="EUR", fx_snapshot=None)`, asserts `pytest.raises(ValidationError)`.
2. `test_mismatched_currencies_with_missing_pair_in_snapshot_raises_error`: Provides `FxRateSnapshot` with only `GBP_EUR` when `source_currency="USD"`, asserts `pytest.raises(ValidationError)`.
3. `test_monetary_inputs_converted_before_vector_creation`: Runs resolver with `source_currency="USD"`, `reporting_currency="EUR"`, `USD_EUR=0.90`, `direct_replacement_cost=100000.0`. Verifies `FindingTelemetry.direct_replacement_cost == 90000.0`.
4. `test_parameter_pack_fallback_converted_from_pack_base_currency`: When `source_currency="GBP"`, `reporting_currency="EUR"`, and `pack.base_currency="USD"`, a fallback cost from the parameter pack is converted using `USD -> EUR` rate, while an explicit finding cost is converted using `GBP -> EUR` rate.
5. `test_fx_lineage_recorded_in_manifest`: Verifies `manifest.finding_lineage[finding_id]["direct_replacement_cost"]` contains `original_currency="USD"`, `reporting_currency="EUR"`, `fx_rate=0.90`, and `fx_snapshot_id="ECB_2026_Q4"`.

---

## 5. FAILURE PREVENTION CHECKLIST FOR `gemini-3.8-flash`

1. **FAILURE MODE 1: Using Python truthiness (`or`) for numeric fallbacks**
   - *Symptom*: Writing `alpha = payload.get("alpha") or pack.default_alpha`, which turns a valid `0.0` into `0.60`.
   - *Preemption*: **NEVER** use `or` for numeric or boolean resolution. Exclusively use `val = payload.get("key"); if val is None: ...`.
2. **FAILURE MODE 2: Accepting `bool` as `int` in Python**
   - *Symptom*: In Python, `isinstance(True, int)` is `True` and `1 <= True <= 5` evaluates to `True`, allowing `cmmi_maturity_level=True` or `audit_n_trials=True`.
   - *Preemption*: Always check `if isinstance(val, bool) or not isinstance(val, int): raise ValueError(...)` when validating integer fields (`cmmi_maturity_level`, `audit_k_failures`, `audit_n_trials`).
3. **FAILURE MODE 3: Breaking the 18 existing kernel/invariance/orchestrator tests**
   - *Symptom*: Making `ActuarialContext` mandatory causes existing unit tests that call `orchestrate(findings)` without a context or with a minimal fixture to fail with `TypeError` or `ValidationError`.
   - *Preemption*: Inspect all existing test files under `tests/` during Phase 6 and update their test fixtures to pass a valid `ActuarialContext` (with `source_currency="EUR", reporting_currency="EUR"`) and verify all 18 existing tests pass alongside the 22 new tests.
4. **FAILURE MODE 4: Circular hash dependency in `ActuarialParameterPack`**
   - *Symptom*: Including `pack_sha256` inside the dictionary serialized by `compute_canonical_sha256()`, causing the hash of a loaded pack to differ from its raw JSON hash.
   - *Preemption*: Always call `self.model_dump(exclude={"pack_sha256"}, mode="json")` before serializing to canonical JSON.
5. **FAILURE MODE 5: Leaving residual magic numbers in default arguments**
   - *Symptom*: Leaving `def __init__(self, vuln_min: float = 0.02, ...)` in `BayesianFairCopulaEngine`.
   - *Preemption*: The constructor of `BayesianFairCopulaEngine` must take `calibration_pack: Optional[KernelCalibrationPack] = None` and read every hyperparameter from `self.calibration_pack`. No float literals allowed in `__init__` signatures.