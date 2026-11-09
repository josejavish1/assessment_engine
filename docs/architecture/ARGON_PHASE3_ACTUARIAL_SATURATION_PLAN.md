---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: editorial
---
```yaml
---
document_id: ARCH-RFC-2026-003
title: "Phase 3 Quantitative Risk Engine: Shared-Fate Actuarial Saturation & Non-Linear Loss Coupling"
author: "gemini-4-argon (Distinguished Staff Architect / Lead Enterprise Ontologist / Chief Quality Gatekeeper)"
status: "APPROVED_FOR_EXECUTION"
target_modules:
  - "TowerPayloadHydrator"
  - "tomo_asis_ast_compiler.py"
compliance_mandates:
  - "Zero Hardcoding (Scale-Invariant $20M to $500B+)"
  - "100% Technical English Codebase (Strict L10n Delegation)"
  - "Strict Actuarial Bound: 0 < ALE_Tower < SLE_max"
  - "Hamilton Largest-Remainder Cent-Level Conservation"
---
```

# Architectural Execution Plan: Phase 3 Non-Linear Actuarial Saturation

## 1. Mathematical Model & Actuarial Proof

### 1.1 The Shared-Fate Anomaly
In an Open FAIR / FAIR-CAM ontology, multiple findings $\{F_1, F_2, \dots, F_n\}$ residing within a single technological or operational tower $T$ share a common underlying asset pool and operational dependency graph. When evaluating Annualized Loss Expectancy ($ALE$), a naive linear summation:

$$ALE_{\text{raw}} = \sum_{k=1}^{n} ALE_k$$

violates fundamental actuarial boundaries because it assumes independent, non-overlapping asset destruction with instantaneous, infinite capital replenishment. In reality, if a tower suffers a catastrophic event equal to its Maximum Single Loss Expectancy ($SLE_{\max}$), the utility of that tower is fully exhausted for the recovery window. Concurrent or overlapping vulnerabilities cannot destroy more value than the total catastrophe ceiling of the shared substrate.

### 1.2 The Concave Exponential Saturation Model (Poisson-Weibull Shared-Fate Coupling)
To resolve this without arbitrary caps, magic numbers, or client-specific thresholds, we model the cumulative hazard rate of the tower's findings as a non-homogeneous Poisson process acting upon a finite asset pool bounded by $SLE_{\max}$.

Let:
* $n \in \mathbb{N}$ be the number of findings in tower $T$.
* $ALE_k > 0$ be the raw, uncoupled Annualized Loss Expectancy of finding $k \in \{1, \dots, n\}$.
* $SLE_k > 0$ be the Single Loss Expectancy of finding $k$.
* $SLE_{\max} = \max_{k \in \{1, \dots, n\}} (SLE_k)$ be the Worst Crisis Single Loss Expectancy for the tower.
* $ALE_{\text{raw}} = \sum_{k=1}^{n} ALE_k$ be the uncoupled linear sum of annual expected losses.

We define the **Effective Coupled Tower ALE** ($ALE_{\text{eff}}$) via the scale-invariant exponential saturation transformation:

$$ALE_{\text{eff}} = SLE_{\max} \cdot \left( 1 - \exp\left( -\frac{ALE_{\text{raw}}}{SLE_{\max}} \right) \right)$$

### 1.3 Formal Mathematical Proof of Invariant Compliance
We must prove that for any enterprise of any financial scale ($SLE_{\max} \in (0, \infty)$) and any positive hazard accumulation ($ALE_{\text{raw}} \in (0, \infty)$), the strict inequality $0 < ALE_{\text{eff}} < SLE_{\max}$ holds unconditionally.

**Proof:**
1. **Strict Positivity ($ALE_{\text{eff}} > 0$):**
   Since $ALE_k > 0$ for any active finding and $SLE_{\max} > 0$, the dimensionless hazard ratio $\lambda = \frac{ALE_{\text{raw}}}{SLE_{\max}}$ satisfies $\lambda > 0$.
   For all $\lambda > 0$, the exponential function satisfies $0 < e^{-\lambda} < 1$.
   Therefore, $1 - e^{-\lambda} > 0$. Since $SLE_{\max} > 0$, the product satisfies $ALE_{\text{eff}} > 0$.

2. **Strict Upper Bound ($ALE_{\text{eff}} < SLE_{\max}$):**
   Because $\lambda = \frac{ALE_{\text{raw}}}{SLE_{\max}}$ is finite ($\lambda < \infty$), $e^{-\lambda}$ is strictly greater than zero ($e^{-\lambda} > 0$).
   Subtracting a strictly positive quantity from $1$ yields:
   $$1 - e^{-\lambda} < 1$$
   Multiplying both sides by the strictly positive scalar $SLE_{\max}$ yields:
   $$SLE_{\max} \cdot (1 - e^{-\lambda}) < SLE_{\max} \implies ALE_{\text{eff}} < SLE_{\max} \quad \blacksquare$$

3. **Asymptotic Consistency (First-Order Taylor Expansion for Low Risk):**
   Using the Maclaurin series $e^{-\lambda} = 1 - \lambda + \frac{\lambda^2}{2!} - \dots$, for towers with small cumulative risk ($\lambda \ll 1$):
   $$ALE_{\text{eff}} \approx SLE_{\max} \cdot \left( 1 - \left(1 - \frac{ALE_{\text{raw}}}{SLE_{\max}}\right) \right) = ALE_{\text{raw}}$$
   Thus, the transformation behaves linearly when risk is low and smoothly saturates toward the asymptote $SLE_{\max}$ as vulnerability density increases. It requires **zero hardcoded constants** and is **100% scale-invariant**.

### 1.4 Proportional Attribution & Conservation Law
To preserve mathematical traceability down to individual findings inside the AST and UI tables, each finding $k$ is assigned a **Coupled Finding ALE** ($ALE'_{k}$) proportional to its contribution to the raw hazard:

$$ALE'_{k} = ALE_{\text{eff}} \cdot \left( \frac{ALE_k}{ALE_{\text{raw}}} \right)$$

To guarantee exact cent-level (or integer-unit) reconciliation where $\sum_{k=1}^{n} \text{round}(ALE'_k) == \text{round}(ALE_{\text{eff}})$, the **Hamilton (Largest Remainder) Method** is applied over the vector $[ALE'_1, ALE'_2, \dots, ALE'_n]$.

---

## 2. Step-by-Step Implementation Plan

### Phase 3.1: Mathematical Core & Hamilton Allocator Integration
**Target:** Quantitative Risk Utility / Core Math Layer (invoked by `TowerPayloadHydrator`)

1. **Implement `compute_saturated_tower_ale(raw_ales: list[Decimal], sles: list[Decimal]) -> tuple[Decimal, list[Decimal]]`:**
   * Accept arbitrary-precision `Decimal` or `float` vectors representing finding-level $ALE_k$ and $SLE_k$.
   * Handle the degenerate edge case: if `not raw_ales` or $\sum ALE_k == 0$ or $\max(SLE_k) == 0$, return `(Decimal('0.00'), [Decimal('0.00')] * len(raw_ales))`.
   * Compute $SLE_{\max} = \max(sles)$ and $ALE_{\text{raw}} = \sum(raw\_ales)$.
   * Compute $\lambda = ALE_{\text{raw}} / SLE_{\max}$ in IEEE 754 double precision (`math.exp(-float(lambda_ratio))`), then cast the saturation factor back to `Decimal`.
   * Guard against floating-point underflow at extreme $\lambda$ (e.g., $\lambda > 35$ where `1.0 - math.exp(-lambda)` might evaluate to `1.0` in 64-bit float):
     * Enforce an IEEE-754 epsilon ceiling on the saturation factor: `saturation_factor = min(1.0 - math.exp(-lambda_val), 1.0 - 1e-12)`, ensuring strict compliance with $ALE_{\text{eff}} < SLE_{\max}$ even under pathological inputs.
2. **Apply Hamilton Largest-Remainder Distribution:**
   * Quantize $ALE_{\text{eff}}$ to the target currency precision (e.g., `0.01` for cents or `1` for whole currency units, matching existing AST conventions).
   * Calculate exact unrounded shares: $S_k = ALE_{\text{eff\_quantized}} \times \frac{ALE_k}{ALE_{\text{raw}}}$.
   * Extract integer/cent floors $\lfloor S_k \rfloor$ and fractional remainders $r_k = S_k - \lfloor S_k \rfloor$.
   * Distribute the discrepancy $\Delta = ALE_{\text{eff\_quantized}} - \sum \lfloor S_k \rfloor$ one minimal quantum at a time to findings sorted by descending $r_k$ (using original finding index as a deterministic tie-breaker).

### Phase 3.2: `TowerPayloadHydrator` Refactoring
**Target:** `TowerPayloadHydrator` class

1. **Intercept Linear Aggregation:**
   * Locate the tower-level reduction step where finding metrics are rolled up into the tower summary payload.
   * Retain `raw_ale_sum` as an internal diagnostic telemetry field (`_telemetry_uncoupled_ale`) if needed for auditability, but replace the primary tower `ale` attribute with $ALE_{\text{eff}}$.
2. **Hydrate Finding-Level Coupled ALEs:**
   * Replace each finding's standalone `ale` in the hydrated payload with its Hamilton-apportioned coupled value $ALE'_k$, ensuring that any downstream table summing finding rows arrives at the exact tower $ALE_{\text{eff}}$.
3. **Enterprise Rollup Consistency:**
   * Update the global enterprise ALE accumulator to sum the saturated tower $ALE_{\text{eff}}$ values across all towers:
     $$ALE_{\text{Enterprise}} = \sum_{T} ALE_{\text{eff}, T}$$
   * Re-run the Hamilton allocator on any percentage-of-total-risk weights across towers so tower risk shares sum to exactly `100.00%`.

### Phase 3.3: AST Compiler Integration (`tomo_asis_ast_compiler.py`)
**Target:** `tomo_asis_ast_compiler.py`

1. **AST Node Binding Verification:**
   * Ensure all AST nodes representing tower financial exposure bind strictly to the saturated metrics emitted by `TowerPayloadHydrator`.
   * Remove any legacy inline `sum(f.ale for f in tower.findings)` comprehensions inside the AST compiler that would bypass the hydrator's saturation logic.
2. **Linguistic & Localization Hygiene (100% Technical English Mandate):**
   * Audit `tomo_asis_ast_compiler.py` and `TowerPayloadHydrator` for any residual Spanish identifiers, comments, docstrings, or exception messages.
   * Ensure all human-facing labels (e.g., table headers, narrative templates explaining shared-fate saturation) are resolved exclusively via keys in `locales.json` (e.g., `risk_engine.shared_fate_saturation_note`).

---

## 3. Empirical Verification on Anomalous Towers

Applying the exponential saturation equation $ALE_{\text{eff}} = SLE_{\max} \cdot \left(1 - e^{-ALE_{\text{raw}} / SLE_{\max}}\right)$ to the anomalous towers cited in the problem statement yields:

| Tower ID | $ALE_{\text{raw}}$ (EUR/yr) | $SLE_{\max}$ (EUR) | Hazard Ratio ($\lambda$) | Saturation Factor ($1 - e^{-\lambda}$) | Coupled $ALE_{\text{eff}}$ (EUR/yr) | Invariant $ALE_{\text{eff}} < SLE_{\max}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **T5 (Operational Continuity)** | $422,886$ | $323,683$ | $1.30648$ | $0.72922$ | **$236,036$** | `236,036 < 323,683` (**PASS**) |
| **T2 (Compute)** | $366,850$ | $290,042$ | $1.26482$ | $0.71771$ | **$208,165$** | `208,165 < 290,042` (**PASS**) |
| **T7 (Peripheral/Other)** | $105,072$ | $102,721$ | $1.02289$ | $0.64045$ | **$65,787$** | `65,787 < 102,721` (**PASS**) |

---

## 4. Quality Gate Probes & Automated Test Assertions

Before any commit is cleared by the Quality Gatekeeper, the following automated test suite (`tests/quality_gates/test_phase3_actuarial_invariants.py`) must pass with 100% compliance:

### Probe 1: Universal Actuarial Ceiling Invariant (`assert_ale_strictly_below_sle`)
```python
def test_actuarial_ceiling_invariant(compiled_enterprise_ast):
    """Certifies 0 < ALE_Tower < SLE_max across 100% of active towers."""
    for tower in compiled_enterprise_ast.towers:
        if len(tower.findings) > 0:
            assert tower.ale_eff > 0, f"Tower {tower.id} has non-positive ALE."
            assert tower.ale_eff < tower.sle_max, (
                f"Actuarial breach in Tower {tower.id}: "
                f"ALE ({tower.ale_eff}) >= SLE_max ({tower.sle_max})"
            )
```

### Probe 2: Hamilton Conservation Identity (`assert_hamilton_conservation`)
```python
def test_hamilton_cent_conservation(compiled_enterprise_ast):
    """Certifies that coupled finding ALEs sum exactly to the Tower ALE with zero rounding drift."""
    for tower in compiled_enterprise_ast.towers:
        finding_ale_sum = sum(f.coupled_ale for f in tower.findings)
        assert finding_ale_sum == tower.ale_eff, (
            f"Conservation failure in Tower {tower.id}: "
            f"Sum of findings ({finding_ale_sum}) != Tower ALE ({tower.ale_eff})"
        )
```

### Probe 3: Scale-Invariance Property-Based Fuzzing (`assert_scale_invariance`)
```python
@pytest.mark.parametrize("revenue_scale", [2e7, 5e8, 1e10, 5e11])  # $20M to $500B
@pytest.mark.parametrize("finding_count", [1, 2, 5, 15, 50])
def test_scale_invariance_across_enterprise_tiers(revenue_scale, finding_count):
    """Verifies invariant holds across 4 orders of magnitude of enterprise valuation and arbitrary finding density."""
    sle_max = Decimal(str(revenue_scale * 0.015))
    sles = [sle_max * Decimal(str(0.5 + 0.5 * (i / finding_count))) for i in range(1, finding_count + 1)]
    raw_ales = [sle * Decimal("0.85") for sle in sles]  # High frequency to force raw sum >> SLE_max

    ale_eff, coupled_ales = compute_saturated_tower_ale(raw_ales, sles)
    assert Decimal("0") < ale_eff < sle_max
    assert sum(coupled_ales) == ale_eff
```

### Probe 4: Static AST Linguistic Gate (`assert_zero_spanish_tokens`)
```python
def test_codebase_strict_english_compliance():
    """Parses Python AST and token streams to forbid non-English identifiers, docstrings, or comments."""
    target_files = ["TowerPayloadHydrator.py", "tomo_asis_ast_compiler.py"]
    forbidden_patterns = re.compile(r"\b(torre|hallazgo|riesgo|impacto|perdida|anual|crisis|horas|tabla)\b", re.IGNORECASE)
    for file_path in target_files:
        content = Path(file_path).read_text(encoding="utf-8")
        matches = forbidden_patterns.findall(content)
        assert not matches, f"Linguistic mandate violation in {file_path}: found forbidden tokens {set(matches)}"
```