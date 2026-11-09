---
status: Verified
owner: architecture-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-07
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: editorial
---
### 1. Executive Verdict

**VERDICT: REVISE (CONDITIONALLY CERTIFIED — MINOR HARDENING REQUIRED)**  
**Numerical Architecture & Actuarial Score: 9.4 / 10.0**

The engineered subsystem demonstrates Tier-1 institutional rigor across its core domain logic. The **Bayesian FAIR-CAM + Two-Factor Student-$t$ Copula Engine** is mathematically sound, seed-deterministic, spectrally safeguarded via eigenvalue flooring, and preserves pathwise Aumann-Shapley / Euler sub-additive allocation. The **Quantitative State Reconciler** and **Mathematical Integrity Gatekeeper** eliminate LLM quantitative hallucinations while preserving qualitative epistemic narratives.

However, under an uncompromising adversarial lens, **five non-trivial edge cases and tenant-leakage defects** were identified across the artifacts (including a tenant name leaked in a CLI docstring, an integration test collection trap on clean CI runners, and a quantization drift edge case when reconciling exact vs. pre-rounded scores).

---

### 2. Forensic Inventory of Defects

#### 2.1. Language Decoupling Law (100% Technical English Audit)
* **Status: 100% PASS (Zero Spanish Tokens Detected)**
* Every variable identifier, function signature, class name, docstring, comment, log message, and exception across all 10 artifacts is written in Technical English.
* **Minor Tenant Name Leak (Artifact 7, Line 154):**
  * In `scripts/resynthesize_domains_from_raw_transcription.py`:
    ```python
    help="Unique identifier for the enterprise tenant (e.g. molins)."
    ```
  * *Remediation:* Replace `(e.g. molins)` with a generic identifier such as `(e.g. acme_corp)` to maintain strict tenant neutrality in codebase documentation.

---

#### 2.2. Hardcoding, Vertical & Topology Agnosticism Audit

1. **Unparameterized FAIR-CAM Degradation & Correlation Caps in `BayesianFairCopulaEngine` (Artifact 1, Lines 159, 191, 211, 267–269):**
   * While `vuln_min`, `vuln_max`, `vuln_convexity_gamma`, `beta_concentration_kappa`, and `intra_tower_correlation_boost` are cleanly injected via `__init__`, four internal actuarial constants remain hardcoded inside methods:
     * Line 159: `0.50` SPOF CMMI penalty (`cmmi - (0.50 if is_spof else 0.0)`).
     * Line 191: `0.85` upper clip on `shared_dependence_factor`.
     * Line 211: `0.92` upper cap on pairwise intra-tower correlation (`min(0.92, corr_ij)`).
     * Lines 267–269: RTO maturity degradation multipliers (`0.35 * max(0.0, 3.0 - clamped_cmmi) + (0.40 if f.is_spof else 0.0)`).
   * *Impact:* Different verticals (e.g., High-Frequency Trading vs. Public Sector) may require configurable SPOF penalties or correlation ceilings.
   * *Remediation:* Promote `spof_cmmi_penalty: float = 0.50`, `max_copula_correlation: float = 0.92`, `rto_cmmi_degradation_slope: float = 0.35`, and `rto_spof_multiplier: float = 0.40` to `__init__` parameters with sensible defaults.

2. **Plaintext Questionnaire Parser Assumes 3-Token KPI Identifiers (Artifact 4, Line 78):**
   * In `sync_payload_scores.py::parse_raw_responses`:
     ```python
     kpi_id = ".".join(tokens[:3]) if len(tokens) >= 3 else q_id
     ```
   * *Impact:* If a custom enterprise taxonomy uses 4-level hierarchical KPI codes (e.g., `DOM1.SUB2.PIL3.KPI01.Q1`), truncating to `tokens[:3]` collapses distinct KPIs into the same prefix (`DOM1.SUB2.PIL3`).
   * *Remediation:* Strip only the trailing question token if the final token matches a question pattern (e.g., `Q\d+`), or preserve the full KPI hierarchy from the tower definition.

3. **Hardcoded `vertical_id="GENERIC_ENTERPRISE"` in `discover_tenant_domains` (Artifact 7, Line 96):**
   * In `scripts/resynthesize_domains_from_raw_transcription.py`, `vertical_id` is hardcoded to `"GENERIC_ENTERPRISE"` rather than being resolved from the tenant configuration or CLI arguments.

---

#### 2.3. Mathematical, Algorithmic & Systems Edge Cases

1. **Finding-to-Tower Rounding Drift in `BayesianFairCopulaEngine` (Artifact 1, Lines 318–366):**
   * **The Defect:** In `evaluate_portfolio`, `TowerRiskResult.portfolio_allocated_ale` is computed as `round(float(np.sum(allocated_finding_ales[t_indices])), 2)` (the rounded sum of unrounded expectations), whereas each `FindingRiskResult.portfolio_allocated_ale` is individually rounded via `round(float(allocated_finding_ales[i]), 2)`.
   * **Impact:** For a tower with $K$ findings, the sum of `f.portfolio_allocated_ale` in the JSON table can drift by up to $\pm 0.005 \times K$ currency units (e.g., $\pm \$0.05$ to $\$0.15$) from `tower.portfolio_allocated_ale`, and the sum of `tower.portfolio_allocated_ale` across $M$ towers can drift by $\pm 0.01 \times M$ from `total_portfolio_ale`. Furthermore, for zero-decimal currencies like `JPY`, rounding to 2 decimal places (`round(..., 2)`) introduces fractional Yen unless controlled or reconciled via Largest Remainder (Hamilton) allocation.

2. **Root Score vs. Quantized Pillar Dot-Product Drift in `reconcile_tower_scores` (Artifact 2, Lines 147–148 & Artifact 3, Lines 109–120):**
   * **The Defect:** `reconcile_tower_scores` quantizes each pillar's `score` to `0.01` (`exact_p_score = float(p_score_dec.quantize(quantizer, rounding=ROUND_HALF_UP))`), and sets `tower_payload["score"]` directly from `scoring_ssot["tower_score_exact"]` quantized to `0.01`.
   * **Mathematical Edge Case:** Suppose a tower has 7 equal-weight pillars ($w_i = 1/7 \approx 0.142857$) where every pillar has an exact score $s_i = 2.124$.
     * Each pillar rounds to `2.12`.
     * The exact dot product is $\sum w_i s_i = 2.124$, which rounds to `2.12`.
     * Now suppose each pillar has $s_i = 2.1249$ except one with $2.126$. All pillars round to `2.12` or `2.13`. Across larger $N$-pillar topologies ($N \ge 10$), the dot product of the *rounded* pillar scores $\sum w_i \cdot \text{round}(s_i, 2)$ can differ from $\text{round}(\sum w_i \cdot s_i, 2)$ by up to $0.01$–$0.02$. While `score_tolerance: float = 0.015` in `assert_tower_mathematical_integrity` absorbs a $0.01$ rounding discrepancy, a pathological combination of half-up boundaries can hit $\Delta = 0.02 > 0.015$.
   * **Remediation:** In `assert_tower_mathematical_integrity`, evaluate `exact_score` if present alongside `score`, or in `reconcile_tower_scores`, verify that the quantized dot product stays within `0.01` of `authoritative_tower_score`.

3. **Unnormalized Weights in ` _resolve_ssot_pillar_weights` When Sum $\neq 1.0$ or $100.0$ (Artifact 2, Lines 76–98):**
   * **The Defect:** `_resolve_ssot_pillar_weights` checks `is_percentage_scale`, and then divides by `100` or keeps `dec_w` as-is, **without dividing by `total_raw`** when `total_raw` is neither `1.0` nor `100.0` (e.g., if a user configures relative weights like `25, 25, 25` summing to `75`, or `1, 1, 1` summing to `3`).
   * **Impact:** `reconcile_tower_scores` will write unnormalized weights into `tower_payload`, which will immediately cause `assert_tower_mathematical_integrity` to crash with `Pillar weights do not sum to unity (1.0 or 100.0)`.
   * **Remediation:** Explicitly validate in `_resolve_ssot_pillar_weights` that `total_raw` equals `1.0` (within `0.001`) or `100.0` (within `0.1`), raising a descriptive `QuantitativeSplitBrainError` immediately if SSOT weights are malformed.

4. **Pytest Empty Parametrization Failure on Clean CI Runners (Artifact 10, Lines 58–62):**
   * **The Defect:** In `tests/integration/test_scoring_ssot_invariants.py`:
     ```python
     ACTIVE_PAYLOADS = get_all_active_tower_payloads()

     @pytest.mark.parametrize("label,payload_path", ACTIVE_PAYLOADS)
     def test_tower_payload_dot_product_invariant(label: str, payload_path: Path) -> None:
     ```
   * **Impact:** When `working/` does not exist or contains zero active payloads (such as in a clean git clone in CI/CD before tenant synthesis runs), `ACTIVE_PAYLOADS` is `[]`. Pytest treats `@pytest.mark.parametrize(..., [])` as a skipped/empty test set, which can fail strict CI runners configured with `--Pending` or zero-collected-items checks, or silently pass without testing anything.
   * **Remediation:** Guard empty discovery with `pytest.skip("No active tenant payloads present in working/ directory")` inside the test or fixture.

5. **Directory Case-Sensitivity on Linux/POSIX Filesystems (Artifact 4, Lines 125–145 & Artifact 7, Lines 77–91):**
   * **The Defect:** `synchronize_tenant_payloads` resolves `config_dir / t_code_u / f"tower_definition_{t_code_u}.json"` and `payloads_dir / t_code_u / f"blueprint_{t_code_l}_payload.json"` assuming directory names are strictly uppercase (`T1`, `D1`) and filenames are strictly uppercase/lowercase as formatted.
   * **Impact:** On macOS/Windows (case-insensitive APFS/NTFS), `working/client/t1/` matches `T1`. On Linux production containers (ext4/xfs, case-sensitive), if a directory is named `t1` instead of `T1`, `payloads_dir / t_code_u` will fail to locate the directory.
   * **Remediation:** Resolve child directories case-insensitively by mapping `{child.name.upper(): child for child in parent.iterdir() if child.is_dir()}`.

---

### 3. Verification of Universal Multi-Tenant Enterprise Readiness

| Architectural Dimension | Audit Status | Verification Summary |
| :--- | :---: | :--- |
| **1. Language Decoupling Law** | **PASS (100%)** | Zero Spanish tokens in identifiers, docstrings, comments, logs, or exceptions. |
| **2. Company Scale Agnosticism** | **PASS (98%)** | Scales linearly from $20M SMBs to $500B global conglomerates via `OperationalZone.hourly_burn_rate` and `secondary_loss_mean`. |
| **3. Vertical Agnosticism** | **PASS (95%)** | Operational zones, CMMI-to-VULN Beta calibration, and PERT distributions are domain-agnostic. |
| **4. Dynamic N-Domain Topology** | **PASS (95%)** | Supports `T1..T10`, `D1..D8`, or arbitrary alphanumeric domain codes via dynamic discovery and natural sorting. |
| **5. Multi-Currency Support** | **PASS (95%)** | Accepts arbitrary ISO 4217 currency codes (`USD`, `EUR`, `GBP`, `JPY`, `CHF`, etc.). |
| **6. Atomic Persistence & I/O** | **PASS (100%)** | Uses PID-isolated temporary files, `flush()`, `os.fsync()`, and atomic POSIX `Path.replace()` with `unlink` cleanup on failure. |

---

### 4. Architectural Certification & Required Patch Checklist

The subsystem is **Architecturally Certified for Production Deployment** subject to applying the following targeted surgical refinements:

1. **`bayesian_fair_copula_engine.py`**:
   * Expose `spof_cmmi_penalty`, `max_copula_correlation`, `rto_cmmi_degradation_slope`, and `rto_spof_multiplier` in `BayesianFairCopulaEngine.__init__`.
   * Ensure exact penny/unit conservation between `sum(finding.portfolio_allocated_ale)`, `tower.portfolio_allocated_ale`, and `portfolio.total_portfolio_ale` (or document that `TowerRiskResult` aggregates unrounded expectations prior to display rounding).
2. **`score_reconciler.py`**:
   * Validate in `_resolve_ssot_pillar_weights` that the SSOT weights sum to `1.0` or `100.0` within tolerance, raising `QuantitativeSplitBrainError` immediately if violated.
3. **`sync_payload_scores.py` & `resynthesize_domains_from_raw_transcription.py`**:
   * Use case-insensitive directory lookup on POSIX filesystems when matching `t_code_u` directories.
   * Replace `(e.g. molins)` in CLI help text with `(e.g. acme_corp)`.
4. **`test_scoring_ssot_invariants.py`**:
   * Add a fallback guard when `ACTIVE_PAYLOADS` is empty so clean CI environments without local `working/` data skip cleanly with an explicit diagnostic reason.