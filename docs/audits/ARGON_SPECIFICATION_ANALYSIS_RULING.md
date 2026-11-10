### 1. Architectural and Actuarial Assessment: Eradicating Model Risk Theater

In Federal Reserve SR 11-7 (Guidance on Model Risk Management), ECB TRIM (Targeted Review of Internal Models), and Solvency II (Article 120–126: Use Test, Data Quality, and Validation Standards), a model fails examination not when its mathematical equations are simplified, but when its **epistemic boundaries are falsified**. 

Commit `37f2bb1098f6443f3bab4b9dd75a918e87c145ce` exhibits classic signs of "compliance theater"—an anti-pattern where a platform claims rigorous empirical calibration, deterministic auditability, and regulatory adherence in its prose and metadata while its underlying execution layer suffers from broken schema contracts, unrecorded parameter mutations, and unverified prior distributions.

This specification enforces four non-negotiable pillars of institutional Model Risk Management (MRM):

1. **Structural Integrity & Boundary Enforcement (Phase 1):** In an enterprise risk engine, silent failures or malformed domain primitives (`AttributeError` masking a `KeyError` on invalid canonical towers like `T99`) invalidate the input validation gate. Simultaneously, rejecting valid dynamic/custom taxonomy extensions (`D_*`, `EDGE_01`) breaks extensibility. Phase 1 restores a strict, bi-modal boundary: rigid enforcement for the canonical taxonomy (`T01`–`T25`) and deterministic fallback routing for non-canonical dynamic domains.
2. **Epistemic Lineage & Override Separation (Phase 2):** Under SR 11-7, every model input must have an auditable provenance trail distinguishing between a *system-estimated prior* (`estimated_value`), an *expert/client override* (`client_override`), and the *value actually injected into the simulation kernel* (`effective_value`). Without this separation, sensitivity analysis and backtesting are impossible because parameter overrides masquerade as baseline model outputs.
3. **Bit-for-Bit / Metric-Bounded Reproducibility (Phase 3):** A stochastic Monte Carlo engine that cannot reproduce a past execution from a persisted state artifact is non-auditable. By capturing the exact PRNG seed derivation (`SHA-256` to 32-bit unsigned integer), the exact hydrated input vector *post-override*, and verifying replay parity within a strict floating-point tolerance ($\epsilon \le 0.01$), the engine achieves deterministic replayability.
4. **Methodological Honesty in Calibration (Phase 4):** Fitting a two-parameter Lognormal ($\mu, \sigma$) or Beta ($\alpha, \beta$) distribution to two or three point estimates (e.g., $P_{10}, P_{50}, P_{90}$ or mean and upper bound) is **algebraic quantile matching**, not **empirical goodness-of-fit** (which requires raw sample arrays and Kolmogorov-Smirnov, Anderson-Darling, or Cramér-von Mises tests). Claiming empirical validation or citing unverified industry reports without raw data is a severe governance violation. Marking unverified provenance as `NEEDS_REVIEW` and `UNCONFIRMED` shifts the burden of proof to the risk owner, protecting the model developer from liability.

---

### 2. Detailed Execution Blueprint

#### Phase 1: Surgical Remediation of `archetype_registry.py`

**Root Cause Analysis:**
In commit `37f2bb1`, `TowerActuarialMapping` was modified or instantiated with missing attributes (`default_cmmi_benchmark`, `vector_alpha_weight`) or incompatible regex patterns (`^T\d{1,2}$`), causing `AttributeError` during object construction or attribute access before `KeyError` could be raised for `T99`, and causing `ValidationError` when hydrating dynamic towers (`D_CLOUD_01`, `EDGE_01`).

**Surgical Code Implementation (`src/assessment_engine/domain/taxonomy/archetype_registry.py`):**

```python
from __future__ import annotations

import re
from typing import Dict, Final, Optional
from pydantic import BaseModel, ConfigDict, Field

# Allows canonical T01-T99, Dynamic D_*, and valid alphanumeric custom tower IDs (e.g., EDGE_01)
TOWER_ID_PATTERN: Final[str] = r"^(?:T\d{2}|D_[A-Z0-9_]+|[A-Z][A-Z0-9_]{1,31})$"
CANONICAL_TOWER_REGEX: Final[re.Pattern[str]] = re.compile(r"^T\d{2}$")


class TowerActuarialMapping(BaseModel):
    """Immutable actuarial prior mapping for a canonical or dynamic assessment tower."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str = Field(..., pattern=TOWER_ID_PATTERN)
    tower_name: str = Field(..., min_length=1)
    archetype_id: str = Field(..., min_length=1)
    base_lambda_prior: float = Field(..., gt=0.0, le=100.0)
    severity_mu_prior: float = Field(..., gt=0.0)
    severity_sigma_prior: float = Field(..., gt=0.0)
    default_cmmi_benchmark: float = Field(default=2.5, ge=1.0, le=5.0)
    vector_alpha_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    is_dynamic_fallback: bool = Field(default=False)


# Canonical Registry (T01 through T25 explicitly populated)
CANONICAL_TOWER_MAPPINGS: Final[Dict[str, TowerActuarialMapping]] = {
    "T01": TowerActuarialMapping(
        tower_id="T01",
        tower_name="Identity & Access Management",
        archetype_id="ARCH_IAM_CORE",
        base_lambda_prior=0.42,
        severity_mu_prior=13.8,
        severity_sigma_prior=1.45,
        default_cmmi_benchmark=2.8,
        vector_alpha_weight=0.22,
        is_dynamic_fallback=False,
    ),
    # ... [T02 - T25 preserved with exact existing prior values] ...
}

# Explicit alias mappings for known dynamic/domain-specific extensions
DYNAMIC_ALIAS_MAPPINGS: Final[Dict[str, str]] = {
    "D_IAM": "T01",
    "D_CLOUD": "T04",
    "D_DATA": "T07",
    "D_APPSEC": "T11",
    "D_INFRA": "T15",
}


def get_tower_actuarial_mapping(tower_id: str) -> TowerActuarialMapping:
    """
    Resolve a tower_id to its TowerActuarialMapping.
    
    Rules:
    1. Exact match in CANONICAL_TOWER_MAPPINGS -> return canonical mapping.
    2. Matches '^T\\d{2}$' but not in CANONICAL_TOWER_MAPPINGS (e.g., 'T99') -> raise KeyError.
    3. Prefix or exact match in DYNAMIC_ALIAS_MAPPINGS (e.g., 'D_CLOUD_01') -> clone target canonical
       mapping with the requested tower_id and is_dynamic_fallback=True.
    4. Non-canonical custom identifier matching TOWER_ID_PATTERN (e.g., 'EDGE_01') -> return conservative
       generic fallback mapping with is_dynamic_fallback=True.
    5. Anything else -> raise KeyError.
    """
    if not isinstance(tower_id, str) or not tower_id.strip():
        raise KeyError(f"Invalid empty or non-string tower_id: {tower_id!r}")

    normalized_id = tower_id.strip()

    # 1. Exact Canonical Match
    if normalized_id in CANONICAL_TOWER_MAPPINGS:
        return CANONICAL_TOWER_MAPPINGS[normalized_id]

    # 2. Strict Rejection of Unregistered Canonical IDs (e.g., T99, T00, T26)
    if CANONICAL_TOWER_REGEX.match(normalized_id):
        raise KeyError(
            f"Unregistered canonical tower ID '{normalized_id}'. "
            f"Valid canonical towers are: {sorted(CANONICAL_TOWER_MAPPINGS.keys())}"
        )

    # Validate structural regex before dynamic resolution
    if not re.match(TOWER_ID_PATTERN, normalized_id):
        raise KeyError(f"Malformed tower ID '{normalized_id}' does not match {TOWER_ID_PATTERN}")

    # 3. Dynamic Alias Resolution (D_* prefixes)
    if normalized_id.startswith("D_"):
        for alias_prefix, target_canonical_id in DYNAMIC_ALIAS_MAPPINGS.items():
            if normalized_id == alias_prefix or normalized_id.startswith(f"{alias_prefix}_"):
                base_mapping = CANONICAL_TOWER_MAPPINGS[target_canonical_id]
                return base_mapping.model_copy(
                    update={
                        "tower_id": normalized_id,
                        "tower_name": f"Dynamic Extension ({normalized_id} -> {target_canonical_id})",
                        "is_dynamic_fallback": True,
                    }
                )
        # Generic D_* fallback if no specific domain prefix matched
        return TowerActuarialMapping(
            tower_id=normalized_id,
            tower_name=f"Dynamic Unmapped Domain ({normalized_id})",
            archetype_id="ARCH_DYNAMIC_FALLBACK",
            base_lambda_prior=0.35,
            severity_mu_prior=13.5,
            severity_sigma_prior=1.50,
            default_cmmi_benchmark=2.5,
            vector_alpha_weight=0.15,
            is_dynamic_fallback=True,
        )

    # 4. Generic Non-Canonical Custom Tower Fallback (e.g., EDGE_01)
    return TowerActuarialMapping(
        tower_id=normalized_id,
        tower_name=f"Custom Assessment Domain ({normalized_id})",
        archetype_id="ARCH_GENERIC_FALLBACK",
        base_lambda_prior=0.35,
        severity_mu_prior=13.5,
        severity_sigma_prior=1.50,
        default_cmmi_benchmark=2.5,
        vector_alpha_weight=0.15,
        is_dynamic_fallback=True,
    )
```

---

#### Phase 2: Complete Parameter Lineage Contract

**Architectural Requirement:**
Every actuarial parameter hydrated for a tower or portfolio must carry an explicit, strongly-typed provenance envelope. If a parameter is derived from an unverified prior or heuristic fallback without empirical client confirmation, `validation_status` must be `UNCONFIRMED` or `NEEDS_REVIEW`, and `confidence` must reflect the epistemic state (or be `UNASSESSED`).

**1. Pydantic Lineage Schema (`src/assessment_engine/schemas/parameter_lineage.py`):**

```python
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T", float, int, str, Dict[str, Any])


class ParameterSourceType(str, Enum):
    CANONICAL_PRIOR = "CANONICAL_PRIOR"
    DYNAMIC_FALLBACK_PRIOR = "DYNAMIC_FALLBACK_PRIOR"
    CLIENT_FINANCIAL_STATEMENT = "CLIENT_FINANCIAL_STATEMENT"
    CLIENT_TELEMETRY_EXTRACT = "CLIENT_TELEMETRY_EXTRACT"
    ASSESSOR_EXPERT_OVERRIDE = "ASSESSOR_EXPERT_OVERRIDE"
    DERIVED_COMPUTATION = "DERIVED_COMPUTATION"
    UNSPECIFIED_DEFAULT = "UNSPECIFIED_DEFAULT"


class EstimationMethod(str, Enum):
    QUANTILE_MATCHED_PRIOR = "QUANTILE_MATCHED_PRIOR"
    HEURISTIC_SCALING = "HEURISTIC_SCALING"
    DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
    DETERMINISTIC_FORMULA = "DETERMINISTIC_FORMULA"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    MONTE_CARLO_ESTIMATE = "MONTE_CARLO_ESTIMATE"
    UNASSESSED = "UNASSESSED"


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNASSESSED = "UNASSESSED"


class ValidationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNASSESSED = "UNASSESSED"


class ParameterProvenanceRecord(BaseModel, Generic[T]):
    """Complete SR 11-7 / internal audit lineage wrapper for a single model parameter."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    parameter_name: str = Field(..., min_length=1)
    estimated_value: Optional[T] = Field(
        default=None,
        description="System-calculated or registry-prior value prior to any manual client override.",
    )
    effective_value: T = Field(
        ...,
        description="Final value injected into the mathematical engine after applying overrides.",
    )
    unit: str = Field(..., min_length=1, description="e.g., 'events/year', 'log_EUR', 'EUR', 'ratio', 'CMMI_1_5'")
    source_type: ParameterSourceType
    source_reference: Optional[str] = Field(
        default=None,
        description="Explicit citation, file hash, or registry key. Must be None if unverified.",
    )
    estimation_method: EstimationMethod
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.UNASSESSED)
    validation_status: ValidationStatus = Field(default=ValidationStatus.UNCONFIRMED)
    client_override: Optional[T] = Field(
        default=None,
        description="Explicit override value if supplied by client or assessor; otherwise None.",
    )

    @model_validator(mode="after")
    def verify_override_consistency(self) -> "ParameterProvenanceRecord[T]":
        if self.client_override is not None and self.effective_value != self.client_override:
            raise ValueError(
                f"Parameter '{self.parameter_name}' has client_override={self.client_override} "
                f"but effective_value={self.effective_value} does not match."
            )
        if self.client_override is None and self.estimated_value is not None:
            if self.effective_value != self.estimated_value:
                raise ValueError(
                    f"Parameter '{self.parameter_name}' has no client_override, "
                    f"so effective_value ({self.effective_value}) must equal estimated_value ({self.estimated_value})."
                )
        return self


class TowerParameterLineageEnvelope(BaseModel):
    """Structured container separating input parameter provenance from computed output provenance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str
    inputs: Dict[str, ParameterProvenanceRecord[Any]] = Field(default_factory=dict)
    outputs: Dict[str, ParameterProvenanceRecord[Any]] = Field(default_factory=dict)
```

**2. Hydration Logic in `tower_payload_hydrator.py`:**

```python
def build_tower_parameter_lineage(
    tower_id: str,
    mapping: TowerActuarialMapping,
    raw_payload: Dict[str, Any],
    computed_outputs: Optional[Dict[str, float]] = None,
) -> TowerParameterLineageEnvelope:
    """
    Construct the complete parameter lineage envelope for a single tower.
    Never invents sources or confirmation status.
    """
    overrides = raw_payload.get("actuarial_overrides") or {}
    prior_source_type = (
        ParameterSourceType.DYNAMIC_FALLBACK_PRIOR
        if mapping.is_dynamic_fallback
        else ParameterSourceType.CANONICAL_PRIOR
    )
    prior_validation = (
        ValidationStatus.NEEDS_REVIEW
        if mapping.is_dynamic_fallback
        else ValidationStatus.UNCONFIRMED
    )

    def _make_input_record(
        param_name: str,
        estimated_val: float,
        unit: str,
        override_key: str,
        default_method: EstimationMethod = EstimationMethod.QUANTILE_MATCHED_PRIOR,
    ) -> ParameterProvenanceRecord[float]:
        override_val = overrides.get(override_key)
        has_override = override_val is not None
        effective_val = float(override_val) if has_override else float(estimated_val)

        return ParameterProvenanceRecord[float](
            parameter_name=param_name,
            estimated_value=float(estimated_val),
            effective_value=effective_val,
            unit=unit,
            source_type=(
                ParameterSourceType.ASSESSOR_EXPERT_OVERRIDE
                if has_override
                else prior_source_type
            ),
            source_reference=(
                raw_payload.get("override_source_reference")
                if has_override
                else f"archetype_registry:{mapping.tower_id}:{mapping.archetype_id}"
            ),
            estimation_method=(
                EstimationMethod.MANUAL_OVERRIDE if has_override else default_method
            ),
            confidence=ConfidenceLevel.UNASSESSED,
            validation_status=(
                ValidationStatus.NEEDS_REVIEW if has_override else prior_validation
            ),
            client_override=float(override_val) if has_override else None,
        )

    inputs_dict: Dict[str, ParameterProvenanceRecord[Any]] = {
        "base_lambda": _make_input_record(
            "base_lambda", mapping.base_lambda_prior, "events/year", "base_lambda"
        ),
        "severity_mu": _make_input_record(
            "severity_mu", mapping.severity_mu_prior, "log_EUR", "severity_mu"
        ),
        "severity_sigma": _make_input_record(
            "severity_sigma", mapping.severity_sigma_prior, "log_EUR_std", "severity_sigma"
        ),
        "cmmi_benchmark": _make_input_record(
            "cmmi_benchmark",
            mapping.default_cmmi_benchmark,
            "CMMI_1_5",
            "cmmi_benchmark",
            default_method=EstimationMethod.HEURISTIC_SCALING,
        ),
    }

    outputs_dict: Dict[str, ParameterProvenanceRecord[Any]] = {}
    if computed_outputs:
        for out_key, out_val in computed_outputs.items():
            outputs_dict[out_key] = ParameterProvenanceRecord[float](
                parameter_name=out_key,
                estimated_value=float(out_val),
                effective_value=float(out_val),
                unit="EUR" if "loss" in out_key or "cvar" in out_key or "aal" in out_key else "scalar",
                source_type=ParameterSourceType.DERIVED_COMPUTATION,
                source_reference=f"simulation_kernel:{tower_id}",
                estimation_method=EstimationMethod.MONTE_CARLO_ESTIMATE,
                confidence=ConfidenceLevel.UNASSESSED,
                validation_status=ValidationStatus.UNCONFIRMED,
                client_override=None,
            )

    return TowerParameterLineageEnvelope(
        tower_id=tower_id,
        inputs=inputs_dict,
        outputs=outputs_dict,
    )
```

---

#### Phase 3: Deterministic Portfolio Reproduction Manifest & Replay Architecture

**Architectural Requirement:**
Immediately following `evaluate_portfolio()`, the engine must serialize a self-contained `PortfolioReproductionManifest`. A pure function `replay_portfolio_simulation(manifest)` must reconstruct the exact simulation inputs from the manifest, derive the identical 32-bit PRNG seed, execute the unaltered mathematical kernel, and verify that all risk metrics (AAL, VaR95, VaR99, CVaR99) match the recorded outputs within an absolute tolerance of $\le 0.01$. Furthermore, any prose in the dossier generator claiming external certification or full SR 11-7 compliance must be excised and replaced with factual descriptions of the reproduction manifest.

**1. Manifest Schema & Replay Function (`src/assessment_engine/actuarial/reproduction_manifest.py`):**

```python
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class RecordedPortfolioMetrics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_annual_loss: float
    var_95: float
    var_99: float
    cvar_99: float
    diversification_benefit: float


class PortfolioReproductionManifest(BaseModel):
    """Self-contained deterministic reproduction contract for a portfolio simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_version: str = Field(default="1.0.0")
    generated_at_utc: str
    seed_material_string: str = Field(
        ..., description="Canonical JSON string or identifier hashed to derive the PRNG seed."
    )
    seed_sha256_hex: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    derived_prng_seed: int = Field(..., ge=0, le=2**32 - 1)
    n_simulations: int = Field(..., gt=0)
    copula_family: str
    correlation_matrix: List[List[float]]
    tower_effective_inputs: List[Dict[str, Any]] = Field(
        ..., description="Ordered list of effective tower parameters injected into evaluate_portfolio."
    )
    recorded_metrics: RecordedPortfolioMetrics


def derive_deterministic_seed(seed_material: str) -> tuple[str, int]:
    """Derive a SHA-256 hex digest and a 32-bit unsigned integer seed from canonical string material."""
    digest_hex = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
    seed_int = int(digest_hex[:8], 16)
    return digest_hex, seed_int


def build_portfolio_reproduction_manifest(
    seed_material: str,
    n_simulations: int,
    copula_family: str,
    correlation_matrix: List[List[float]],
    tower_effective_inputs: List[Dict[str, Any]],
    evaluation_result: Dict[str, Any],
) -> PortfolioReproductionManifest:
    """Build the reproduction manifest immediately after evaluate_portfolio() completes."""
    digest_hex, seed_int = derive_deterministic_seed(seed_material)
    return PortfolioReproductionManifest(
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        seed_material_string=seed_material,
        seed_sha256_hex=digest_hex,
        derived_prng_seed=seed_int,
        n_simulations=n_simulations,
        copula_family=copula_family,
        correlation_matrix=correlation_matrix,
        tower_effective_inputs=tower_effective_inputs,
        recorded_metrics=RecordedPortfolioMetrics(
            expected_annual_loss=float(evaluation_result["expected_annual_loss"]),
            var_95=float(evaluation_result["var_95"]),
            var_99=float(evaluation_result["var_99"]),
            cvar_99=float(evaluation_result["cvar_99"]),
            diversification_benefit=float(evaluation_result.get("diversification_benefit", 0.0)),
        ),
    )


def replay_portfolio_simulation(
    manifest: PortfolioReproductionManifest | Dict[str, Any],
    tolerance: float = 0.01,
) -> Dict[str, Any]:
    """
    Re-execute evaluate_portfolio() using only the state recorded in the manifest.
    Asserts exact seed derivation equality and metric parity within `tolerance` (<= 0.01).
    """
    from assessment_engine.actuarial.portfolio_engine import evaluate_portfolio

    parsed_manifest = (
        manifest
        if isinstance(manifest, PortfolioReproductionManifest)
        else PortfolioReproductionManifest.model_validate(manifest)
    )

    recomputed_hex, recomputed_seed = derive_deterministic_seed(
        parsed_manifest.seed_material_string
    )
    if recomputed_hex != parsed_manifest.seed_sha256_hex:
        raise ValueError(
            f"Seed hash mismatch during replay: expected {parsed_manifest.seed_sha256_hex}, "
            f"got {recomputed_hex}"
        )
    if recomputed_seed != parsed_manifest.derived_prng_seed:
        raise ValueError(
            f"Derived integer seed mismatch: expected {parsed_manifest.derived_prng_seed}, "
            f"got {recomputed_seed}"
        )

    replayed_result = evaluate_portfolio(
        tower_inputs=parsed_manifest.tower_effective_inputs,
        n_simulations=parsed_manifest.n_simulations,
        copula_family=parsed_manifest.copula_family,
        correlation_matrix=parsed_manifest.correlation_matrix,
        random_seed=recomputed_seed,
    )

    metric_keys = [
        "expected_annual_loss",
        "var_95",
        "var_99",
        "cvar_99",
        "diversification_benefit",
    ]
    recorded_dict = parsed_manifest.recorded_metrics.model_dump()
    deltas: Dict[str, float] = {}

    for key in metric_keys:
        recorded_val = float(recorded_dict[key])
        replayed_val = float(replayed_result.get(key, 0.0))
        delta = abs(replayed_val - recorded_val)
        deltas[key] = delta
        if delta > tolerance:
            raise AssertionError(
                f"Replay parity failure for '{key}': recorded={recorded_val:.6f}, "
                f"replayed={replayed_val:.6f}, delta={delta:.6f} > tolerance={tolerance}"
            )

    return {
        "verified": True,
        "seed_sha256_hex": recomputed_hex,
        "derived_prng_seed": recomputed_seed,
        "max_abs_delta": max(deltas.values()) if deltas else 0.0,
        "metric_deltas": deltas,
        "replayed_metrics": {k: float(replayed_result.get(k, 0.0)) for k in metric_keys},
    }
```

---

#### Phase 4: Honest Calibration Lineage in `fit_actuarial_priors.py`

**Root Cause Analysis:**
`fit_actuarial_priors.py` solves for distribution parameters $(\mu, \sigma)$ or $(\alpha, \beta)$ from target quantiles (e.g., $\mu = \ln(P_{50})$ and $\sigma = (\ln(P_{90}) - \ln(P_{50})) / \Phi^{-1}(0.90)$), yet labels the output in `CALIBRATION_FITTING_LINEAGE.json` as an "empirical goodness-of-fit calibration" backed by named external datasets that are not present in the repository.

**Surgical Remediation (`scripts/fit_actuarial_priors.py` & `CALIBRATION_FITTING_LINEAGE.json`):**

```python
from __future__ import annotations

import math
from typing import Any, Dict
from scipy.stats import norm


def fit_lognormal_from_quantiles(p50: float, p90: float) -> Dict[str, Any]:
    """
    Compute Lognormal (mu, sigma) parameters via analytic quantile matching
    from a median (P50) and 90th percentile (P90) point estimate.

    NOTE: This is algebraic quantile matching on two target points.
    It is NOT an empirical maximum-likelihood fit on raw loss observations,
    and no goodness-of-fit test (e.g., KS or Anderson-Darling) can be computed
    from two points.
    """
    if p50 <= 0.0 or p90 <= p50:
        raise ValueError(f"Invalid quantiles for lognormal matching: p50={p50}, p90={p90}")

    z_90 = float(norm.ppf(0.90))
    mu = math.log(p50)
    sigma = (math.log(p90) - mu) / z_90

    return {
        "mu": round(mu, 6),
        "sigma": round(sigma, 6),
        "input_quantiles": {"p50": p50, "p90": p90},
        "fitting_methodology": "ANALYTIC_QUANTILE_MATCHING",
        "empirical_sample_size": None,
        "goodness_of_fit_statistic": None,
        "goodness_of_fit_p_value": None,
        "source_verification_status": "NEEDS_REVIEW",
        "validation_status": "UNCONFIRMED",
        "epistemic_limitations": (
            "Parameters are algebraically solved from two target quantiles (P50, P90). "
            "No raw empirical loss dataset is bundled in this repository; external benchmark "
            "references require independent verification before regulatory or client reliance."
        ),
    }
```

**Resulting `CALIBRATION_FITTING_LINEAGE.json` Structure:**
```json
{
  "schema_version": "2.0.0",
  "calibration_mode": "ANALYTIC_QUANTILE_MATCHING",
  "external_validation_status": "UNCONFIRMED",
  "regulatory_certification": null,
  "global_epistemic_notice": "Priors in this artifact are derived via algebraic quantile matching against configured target percentiles. Raw empirical loss microdata is not present in the repository. All external benchmark references are marked NEEDS_REVIEW until backed by auditable primary data extracts.",
  "towers": {
    "T01": {
      "archetype_id": "ARCH_IAM_CORE",
      "fitting_methodology": "ANALYTIC_QUANTILE_MATCHING",
      "empirical_sample_size": null,
      "goodness_of_fit_statistic": null,
      "source_reference": null,
      "source_verification_status": "NEEDS_REVIEW",
      "validation_status": "UNCONFIRMED",
      "parameters": {
        "base_lambda_prior": 0.42,
        "severity_mu_prior": 13.8,
        "severity_sigma_prior": 1.45
      }
    }
  }
}
```

---

### 3. The Strategic Imperative: Why Epistemic Honesty is the Ultimate Artifact of Power

When a Tier-1 Principal Model Risk Reviewer (at a G-SIB, Big-4 Actuarial Practice, or regulatory supervisory team) audits a quantitative cyber-risk engine, their primary adversarial heuristic is simple: **locate the gap between what the documentation claims and what the code actually proves.**

1. **Defensibility Under Adversarial Audit:** If a platform claims "Empirical Goodness-of-Fit Calibration" and "SR 11-7 Certified Compliance" while `fit_actuarial_priors.py` merely executes `sigma = (log(p90) - log(p50)) / 1.28155`, an examiner immediately classifies the entire system as **High Model Risk / Governance Failure**. Conversely, when the system explicitly outputs `"fitting_methodology": "ANALYTIC_QUANTILE_MATCHING"`, `"empirical_sample_size": null`, and `"validation_status": "UNCONFIRMED"`, the examiner cannot fault the model's integrity—because the model itself has transparently declared its exact mathematical nature and evidentiary boundaries.
2. **Clear Allocation of Fiduciary Liability:** By separating `estimated_value` (the registry prior) from `client_override` and `effective_value`, and tagging unverified priors as `UNCONFIRMED` or `NEEDS_REVIEW`, the architecture creates an immutable audit trail. When an engagement team or client CISO overrides a frequency or severity parameter—or chooses to accept an unconfirmed baseline prior—that decision is cryptographically locked into the `PortfolioReproductionManifest` and the `TowerParameterLineageEnvelope`.
3. **Immutable Mathematical Parity:** Preserving the core actuarial mathematics (Poisson event generation, Student-t / Gaussian copula dependency structures, Rockafellar-Uryasev CVaR optimization) while wrapping them in a deterministic SHA-256 seed-replay contract proves that the stochastic engine is not a "black box." Any stakeholder can take the JSON manifest from a boardroom dossier, execute `replay_portfolio_simulation(manifest)`, and verify that every euro of VaR and CVaR reproduces within $\le 0.01$.

Executing this specification without shortcuts transforms `assessment_engine` from a fragile prototype into an audit-grade quantitative platform whose primary strength is its verifiable truth.