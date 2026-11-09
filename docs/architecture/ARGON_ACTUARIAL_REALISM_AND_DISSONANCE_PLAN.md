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
# ARCHITECTURAL EXECUTION PLAN: ACTUARIAL REALISM & EPISTEMIC LEDGER INTEGRATION
**Document ID:** ARCH-PLAN-FAIR-004  
**Author:** Distinguished Staff Architect / Lead Enterprise Ontologist / Chief Quality Gatekeeper  
**Target Systems:** `BayesianFairCopulaEngine`, `TowerPayloadHydrator`, `EpistemicLedger`  
**Status:** DESIGN LOCK PENDING APPROVAL  

---

## 1. EXECUTIVE ARCHITECTURAL SUMMARY

The current implementation of the quantitative risk engine contains an unacceptable actuarial anti-pattern: deriving the 95th Percentile (P95 / Tail Risk) by applying an arbitrary scalar (`2.5x`) to the mean Annualized Loss Expectancy (ALE). In risk science, tail risk is governed by the skewness and kurtosis of the Loss Magnitude (LM) distribution, driven by physical operational boundaries—not linear scalars of expected value.

Furthermore, handling "Epistemic Dissonance" (questionnaire vs. transcript contradictions) via arbitrary financial penalties violates the core tenets of Open FAIR and FAIR-CAM. Dissonance is not a direct financial loss; it is an indicator of **Control Efficacy Failure** and **Variance in Operational Resilience**.

This execution plan details the eradication of all static multipliers, the implementation of a bottom-up **Physical Single Loss Expectancy (SLE)** boundary model, and the mathematical wiring of the `EpistemicLedger` to dynamically update Bayesian priors for Vulnerability ($VULN$) and Recovery Time Objective ($RTO$).

---

## 2. MATHEMATICAL & ONTOLOGICAL FOUNDATIONS

### 2.1 Eradicating the `2.5x` Anti-Pattern: The Physical SLE Boundary Model
Under Open FAIR, Loss Magnitude (LM) consists of Primary Loss (Productivity, Replacement, Response) and Secondary Loss (Fines, Judgments, Reputation). To dynamically scale from a $20M SMB to a $500B Global Enterprise without hardcoded ceilings, the engine must anchor to the tenant's **Empirical Financial Telemetry** and the **Physics of the Failure Mode**.

We replace the `2.5x` scalar with the **Physical Maximum Single Loss Expectancy ($SLE_{max}$)**, which serves as the dynamic upper bound ($\gamma$ or $P_{99}$) for the Pert/Log-Normal Loss Magnitude distribution during Monte Carlo or Copula simulation:

$$SLE_{max}^{(z)} = \left( RTO_{empirical}^{(z)} \times R_{hourly}^{(z)} \right) + C_{replacement}^{(z)} + L_{secondary}^{(z)}$$

Where, for a given architectural Zone $(z)$:
1. **$R_{hourly}^{(z)}$ (Hourly Downtime Rate):** Dynamically derived from tenant telemetry:
   $$R_{hourly}^{(z)} = \frac{\text{Annual Revenue} \times \omega^{(z)}}{\text{Operational Hours Per Year}} \times \mu_{margin\_erosion}$$
   *(Where $\omega^{(z)}$ is the topological revenue dependency weight of Zone $z$, and $\mu$ is the vertical-specific operational elasticity factor).*
2. **$RTO_{empirical}^{(z)}$ (Empirical Recovery Time in Hours):** The physical time required to restore operations under a worst-case catastrophic state, bounded by architectural complexity and backup immutability, **not** the client's aspirational SLA.
3. **$C_{replacement}^{(z)}$ (Emergency Replacement & Response Cost):** Derived dynamically from the asset density in Zone $z$ and emergency incident response burn rates (scaled to tenant size/tier).
4. **$L_{secondary}^{(z)}$ (Regulatory & Contractual Exposure):** Calculated via deterministic regulatory curves (e.g., GDPR, NIS2, SEC, PCI-DSS) mapped to the tenant's vertical and global revenue (e.g., $\min(\text{Statutory Cap}, \text{Revenue} \times \text{Statutory } \%)$), weighted by Secondary Loss Event Frequency ($SLEF$).

The $P_{95}$ Tail Risk is then extracted directly from the 95th percentile of the simulated joint distribution (via the Gaussian/Vine Copula), which is naturally bounded and shaped by $SLE_{max}^{(z)}$.

---

### 2.2 Wiring the `EpistemicLedger`: Bayesian Updating of $VULN$ and $RTO$
When a client claims high maturity in a static questionnaire (e.g., *"Backups are immutable and tested; RTO is 4 hours"*) but confesses to severe vulnerabilities in the live interview transcript (e.g., *"Well, the domain admin credentials are shared and we haven't tested bare-metal recovery in two years"*), the `EpistemicLedger` flags a verified dissonance with an immutable forensic quote.

In FAIR-CAM (Controls Analytics Model), dishonesty or lack of awareness is a failure of **Management System Controls (Decision Making & Visibility)**. It does not create an arbitrary fine; it invalidates the self-reported control efficacy.

We model this mathematically using **Bayesian Prior Shifting** and **RTO Inflation**:

#### A. Vulnerability ($VULN$) Beta Distribution Shift
In Open FAIR, $VULN = P(TC > RS)$, where $TC$ is Threat Capability and $RS$ is Resistance Strength (Control Efficacy). We model $RS$ using a Beta distribution $\text{Beta}(\alpha, \beta)$ bounded on $[0, 1]$.
*   **Questionnaire Prior:** Generates initial shape parameters $(\alpha_0, \beta_0)$ representing high claimed maturity ($\mathbb{E}[RS]$ is high, variance is low).
*   **Epistemic Dissonance Penalty (Likelihood Update):** Each verified dissonance record $d_i \in D_{zone}$ in the `EpistemicLedger` carries a normalized `severity_weight` $w_i \in (0, 1]$. We shift the distribution toward failure (increasing $\beta$, decaying $\alpha$):
    $$\alpha_{posterior} = \alpha_0 \times \prod_{i=1}^{n} (1 - w_i)$$
    $$\beta_{posterior} = \beta_0 + \sum_{i=1}^{n} (\lambda_{scale} \times w_i)$$
*   **Result:** Resistance Strength ($RS$) drops precipitously, and epistemic uncertainty (variance) widens. Consequently, $VULN$ approaches $1.0$, organically increasing Loss Event Frequency ($LEF = TEF \times VULN$) without inventing a single dollar of artificial penalty.

#### B. Empirical RTO Inflation (Dissonance-Driven Friction)
If the dissonance pertains to recovery, architecture, or operational visibility, the aspirational $RTO_{claimed}$ is mathematically invalidated. The empirical maximum recovery time is adjusted toward the physical worst-case bound ($RTO_{catastrophic}$, e.g., full bare-metal rebuild from scratch):

$$RTO_{empirical}^{(z)} = RTO_{claimed}^{(z)} + \left( RTO_{catastrophic}^{(z)} - RTO_{claimed}^{(z)} \right) \times \left( 1 - e^{-\kappa \sum w_i} \right)$$

Where $\kappa$ is the structural friction constant. As verified dissonance accumulates, $RTO_{empirical}^{(z)}$ asymptotically approaches the unmitigated physical rebuild time $RTO_{catastrophic}^{(z)}$, directly feeding the $SLE_{max}^{(z)}$ equation in Section 2.1.

---

## 3. PHASED ARCHITECTURAL EXECUTION PLAN

### PHASE 1: Ontological Data Structures & Contracts (Zero-Hardcoding Foundation)
**Objective:** Establish strict, strongly-typed data contracts in pure Technical English to transport telemetry, physical bounds, and forensic dissonance records into the risk engine.

1.  **Define `TenantFinancialTelemetry` Contract:**
    *   Attributes: `annual_revenue_base`, `currency_iso`, `operational_hours_per_year`, `vertical_classification`, `regulatory_regimes: List[RegulatoryRegime]`, `asset_density_index`.
    *   *Gatekeeper Rule:* Zero default fallback to hardcoded company profiles. Missing telemetry must trigger a deterministic `TelemetryIncompleteError` or invoke a mathematically explicit industry-baseline estimator class.
2.  **Define `EpistemicDissonanceRecord` in `EpistemicLedger`:**
    *   Attributes: `record_id`, `zone_id`, `control_domain`, `claimed_maturity_score`, `empirical_reality_score`, `dissonance_delta`, `severity_weight: float`, `transcript_forensic_quote: str`, `impact_vector: Enum[RESISTANCE_STRENGTH, RECOVERY_TIME, BOTH]`.
3.  **Define `ZonePhysicalBounds` Contract:**
    *   Attributes: `zone_id`, `revenue_dependency_weight`, `rto_claimed_hours`, `rto_catastrophic_hours`, `emergency_replacement_ratio`.

### PHASE 2: `BayesianFairCopulaEngine` Core Refactoring
**Objective:** Eradicate the `2.5x` multiplier, implement the Bayesian $VULN$ updater, and construct the Physical $SLE_{max}$ distribution generator.

1.  **Eradicate Legacy Multiplier:**
    *   Locate and purge all instances of `ale * 2.5` or similar static tail-risk heuristics across the entire engine codebase.
2.  **Implement `_apply_epistemic_dissonance_to_priors()`:**
    *   Ingest `List[EpistemicDissonanceRecord]` for the target zone.
    *   Compute posterior $(\alpha_{posterior}, \beta_{posterior})$ for Resistance Strength ($RS$).
    *   Compute $RTO_{empirical}^{(z)}$ using the asymptotic exponential decay formula.
    *   Record the exact mathematical delta in an internal `ActuarialAuditTrace` object (linking the shift in $VULN$ and $RTO$ directly to the `record_id` and `transcript_forensic_quote`).
3.  **Implement `_compute_physical_sle_bounds()`:**
    *   Calculate $R_{hourly}^{(z)}$ from `TenantFinancialTelemetry` and `ZonePhysicalBounds`.
    *   Calculate $SLE_{max}^{(z)}$ using $RTO_{empirical}^{(z)}$, $R_{hourly}^{(z)}$, $C_{replacement}^{(z)}$, and dynamic regulatory exposure $L_{secondary}^{(z)}$.
4.  **Update Copula Simulation Pipeline:**
    *   Parameterize the marginal Loss Magnitude distribution (Modified PERT or Log-Normal) using $SLE_{mode}$ (expected event) and $SLE_{max}^{(z)}$ (physical ceiling).
    *   Execute the Copula simulation to correlate risks across zones.
    *   Extract `ale_mean`, `sle_median`, and `tail_risk_p95` directly from the simulated empirical cumulative distribution function (ECDF) using `numpy.percentile(simulated_losses, 95)`.

### PHASE 3: `TowerPayloadHydrator` Integration & Audit Trail Wiring
**Objective:** Hydrate the downstream consumption payloads (UI Towers, Executive Reports, API responses) with the new actuarial metrics and forensic audit trails, ensuring 100% localization separation.

1.  **Refactor Payload Hydration Logic:**
    *   Map `tail_risk_p95` and `physical_sle_max` directly from the engine's ECDF output into the Tower payload.
    *   Expose the `epistemic_audit_trail` array in the payload. For every zone where dissonance shifted the risk curve, the payload must expose:
        *   `dissonance_detected: bool`
        *   `claimed_rto_hours` vs. `empirical_rto_hours`
        *   `prior_vulnerability_mean` vs. `posterior_vulnerability_mean`
        *   `forensic_evidence_quotes: List[str]`
2.  **Enforce Strict Localization Separation:**
    *   Ensure `TowerPayloadHydrator` emits strictly language-agnostic semantic keys (e.g., `ERR_DISSONANCE_RTO_INFLATION`, `METRIC_PHYSICAL_SLE_MAX`).
    *   Delegate all human-readable narrative rendering to the presentation layer via `locales.json`.

### PHASE 4: Chief Quality Gatekeeper Verification & Invariant Testing
**Objective:** Prove mathematical soundness, scale invariance, and codebase purity before merging.

1.  **Lexical & Static Analysis Gate (Zero Spanish / Zero Hardcoding):**
    *   Execute automated AST (Abstract Syntax Tree) and regex sweeps across all `.py` files to guarantee zero Spanish tokens, comments, or string literals, and zero magic numbers (`2.5`, hardcoded EUR/USD figures, or tenant names).
2.  **Scale-Invariance Property-Based Testing (Hypothesis):**
    *   Run property-based tests simulating tenants from $20M to $500B in revenue across 5 verticals.
    *   **Invariant 1:** $SLE_{max}$ and $P_{95}$ must scale monotonically with revenue and $RTO_{empirical}$, never exceeding physical theoretical maximums.
    *   **Invariant 2:** Injecting an `EpistemicDissonanceRecord` with `severity_weight > 0` must strictly satisfy:
        $$VULN_{posterior} > VULN_{prior} \quad \text{and} \quad RTO_{empirical} > RTO_{claimed}$$
    *   **Invariant 3:** If `EpistemicLedger` contains zero dissonance records ($\sum w_i = 0$), $RTO_{empirical}$ must equal $RTO_{claimed}$ and $(\alpha_{posterior}, \beta_{posterior}) = (\alpha_0, \beta_0)$.
3.  **Forensic Traceability Gate:**
    *   Verify that every basis-point increase in $VULN$ or hour increase in $RTO$ caused by transcript contradictions can be traced back via `record_id` to an exact, immutable quote in the `EpistemicLedger`.

---

## 4. ARCHITECTURAL SIGN-OFF
This plan eliminates heuristic guesswork, establishes true Open FAIR / FAIR-CAM compliance, and turns qualitative interview contradictions into rigorous, defensible actuarial adjustments. 

**Awaiting authorization to proceed to Phase 1 implementation.**