# ENTERPRISE ARCHITECTURAL DIRECTIVE: POLYMORPHIC ACTUARIAL AST ENGINE

**Author**: `gemini-4-argon` (Principal Enterprise Architect & Supreme Actuarial Arbiter)  
**Target Component**: `src/assessment_engine/adapters/compilers/payload_to_ast.py` (and associated domain/config layers)  
**Architectural Pattern**: Gang of Four (GoF) Strategy Pattern + Abstract Factory + Strict I18N Externalization  
**Compliance Standard**: Open FAIR™ (Factor Analysis of Information Risk) & Clean Architecture  

---

## 1. EXECUTIVE ARCHITECTURAL VISION

The current implementation of Section 4 (*Actuarial Quantification*) in `payload_to_ast.py` exhibits a **Single-Receptor Monolithic Anti-Pattern**. By forcing all 10 technology domains through an "Hourly Server Downtime" financial model, the engine loses C-Suite credibility when evaluating domains governed by non-outage economic receptors—specifically **Cybersecurity (T6)**, **Cloud FinOps (T8)**, and **Digital Workplace/Agile Delivery (T7, T9)**.

To elevate this platform to the **#1 Global Tier-1 Enterprise Standard**, we will decouple the actuarial narrative generation from the AST compiler using a **Polymorphic Strategy Pattern**. Every domain will be dynamically routed to its canonical Open FAIR™ Economic Receptor. All narrative strings, mathematical formulas, and vector labels will be 100% externalized into `engine_config/locales.json`, ensuring absolute zero hardcoding, multi-currency agnosticism, vertical independence, and seamless 6-language localization.

---

## 2. THE 4 OPEN FAIR™ ECONOMIC RECEPTOR STRATEGIES

We establish an explicit, immutable taxonomy mapping the 10 Technology Domains to 4 canonical Economic Receptors:

1. **`AVAILABILITY_OUTAGE` (Domains: T1, T2, T3, T4, T5, T10)**
   * **Actuarial Nature**: Operational disruption, SLA breaches, and transactional revenue halt.
   * **Primary Loss Vectors**:
     * *Vector Alpha*: Direct Revenue & SLA Penalty Loss (Transactional Downtime).
     * *Vector Beta*: Engineering War-Room & Emergency Recovery Labor.
     * *Vector Gamma*: Brand Equity Erosion & Customer Churn SLA Credits.
2. **`CAPITAL_INEFFICIENCY` (Domain: T8 - Cloud FinOps & Unit Economics)**
   * **Actuarial Nature**: Value leakage, unoptimized cloud spend, idle resource allocation, and architectural over-provisioning.
   * **Primary Loss Vectors**:
     * *Vector Alpha*: Unutilized Compute/Storage & Zombie Infrastructure Waste.
     * *Vector Beta*: Sub-optimal Commitment Discounts & Spot-Instance Misses.
     * *Vector Gamma*: Architectural Re-work & FinOps Governance Remediation Cost.
3. **`PRODUCTIVITY_TOIL` (Domains: T7 - SDLC/DevEx, T9 - Digital Workplace)**
   * **Actuarial Nature**: Human capital friction, cognitive load, deployment wait-states, and endpoint/tooling latency.
   * **Primary Loss Vectors**:
     * *Vector Alpha*: Aggregate Engineering/Employee Idle Time & Context-Switching Friction.
     * *Vector Beta*: Delayed Time-to-Market (Opportunity Cost of Feature Velocity).
     * *Vector Gamma*: Manual Remediation Toil & Support Ticket Escalation Overhead.
4. **`REGULATORY_AND_BREACH` (Domain: T6 - Cybersecurity & Zero Trust)**
   * **Actuarial Nature**: Confidentiality/Integrity compromise, data exfiltration, extortion, and statutory non-compliance (GDPR, SEC, DORA, HIPAA).
   * **Primary Loss Vectors**:
     * *Vector Alpha*: Statutory Regulatory Fines & Legal Liability Settlements.
     * *Vector Beta*: Incident Response, Forensics, & Extortion/Ransom Containment.
     * *Vector Gamma*: Mandatory Notification, Credit Monitoring, & Reputational Churn.

---

## 3. ARCHITECTURAL DESIGN DIMENSIONS

### Dimension 1: Zero Hardcoding & I18N Independence (`engine_config/locales.json`)

No English, Spanish, or mathematical prose will exist inside Python files. The Python layer will act purely as a **Data-Binding Hydrator**. 

We will introduce a new polymorphic namespace within `locales.json` across all 6 supported languages (`en`, `es`, `pt`, `fr`, `de`, `it`):

```json
{
  "en": {
    "annex_ch4_receptors": {
      "AVAILABILITY_OUTAGE": {
        "methodology_intro": "Actuarial exposure for {domain_name} is modeled via the Open FAIR™ Availability & Service Disruption receptor...",
        "formula_expression": "ALE = LEF × (Downtime_Duration × Hourly_Burn_Rate + Recovery_Toil + SLA_Penalties)",
        "vector_alpha_label": "Direct Transactional & SLA Downtime Loss",
        "vector_alpha_desc": "Financial impact of service unavailability across {affected_assets} critical assets...",
        "vector_beta_label": "Emergency War-Room & Recovery Labor",
        "vector_beta_desc": "Unplanned engineering toil required to restore state and resolve root causes...",
        "vector_gamma_label": "Downstream Churn & Reputational Attrition",
        "vector_gamma_desc": "Secondary commercial erosion resulting from prolonged systemic instability...",
        "prioritization_rationale": "Remediation sequence is strictly ordered by MTTR reduction and Blast Radius containment..."
      },
      "CAPITAL_INEFFICIENCY": { "...": "..." },
      "PRODUCTIVITY_TOIL": { "...": "..." },
      "REGULATORY_AND_BREACH": { "...": "..." }
    }
  }
}
```
* Architectural Guarantee: Every string uses standard Python `.format(**context)` placeholders populated exclusively from validated domain payload metrics and currency formatters.

---

### Dimension 2: Polymorphic AST Construction (GoF Strategy Pattern)

We will eliminate conditional branching (`if/elif/else` per domain) inside `payload_to_ast.py`. Instead, we will create a dedicated strategy module: `src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py`.

#### Class Hierarchy Specification:
1. **`ActuarialReceptorContext` (Frozen Dataclass / Value Object)**:
   * Encapsulates the calibrated financial metrics (`total_fair_ale`, `vector_alpha_amount`, `vector_beta_amount`, `vector_gamma_amount`), currency symbols, locale dictionary reference, and domain metadata.
2. **`IActuarialReceptorStrategy` (Abstract Base Class)**:
   * Defines the strict contract required by the AST compiler:
     * `build_methodology_nodes(context: ActuarialReceptorContext) -> list[ASTNode]`
     * `build_quantification_table_nodes(context: ActuarialReceptorContext) -> list[ASTNode]`
     * `build_prioritization_nodes(context: ActuarialReceptorContext) -> list[ASTNode]`
3. **Concrete Strategy Implementations**:
   * `AvailabilityOutageStrategy(IActuarialReceptorStrategy)`
   * `CapitalInefficiencyStrategy(IActuarialReceptorStrategy)`
   * `ProductivityToilStrategy(IActuarialReceptorStrategy)`
   * `RegulatoryBreachStrategy(IActuarialReceptorStrategy)`
4. **`ActuarialReceptorFactory` (Registry & Resolver)**:
   * Maintains an immutable mapping (sourced from configuration/schema) linking Domain IDs (`T1`..`T10`) or explicit payload receptor overrides to their respective Strategy Singleton.
   * `payload_to_ast.py` simply executes:
     ```python
     strategy = ActuarialReceptorFactory.get_strategy(domain_payload.receptor_type)
     ch4_nodes = strategy.build_chapter_4_ast(receptor_context)
     ```

---

### Dimension 3: Mathematical Identity Conservation (Zero-Rounding Drift)

In Tier-1 financial and actuarial reporting, if a summary table displays:
* Vector Alpha: `$450,000`
* Vector Beta: `$350,000`
* Vector Gamma: `$200,001`
* **Total ALE**: `$1,000,000`

The report immediately fails an audit due to a `$1` floating-point rounding discrepancy. 

#### The Largest Remainder / Residual Allocation Algorithm:
To guarantee the mathematical identity $V_\alpha + V_\beta + V_\gamma \equiv \text{ALE}_{\text{total}}$ across all currencies and scales:

1. **Weight Definition**: Each receptor defines canonical actuarial split weights $(\omega_\alpha, \omega_\beta, \omega_\gamma)$ stored in configuration (or dynamically derived from the upstream Monte Carlo engine) such that $\omega_\alpha + \omega_\beta + \omega_\gamma = 1.0$.
   * *Example (`REGULATORY_AND_BREACH`)*: $\omega_\alpha = 0.55$ (Fines/Legal), $\omega_\beta = 0.25$ (Forensics/IR), $\omega_\gamma = 0.20$ (Churn/Notification).
2. **Integer Cent/Unit Truncation**:
   * $V_\alpha = \lfloor \text{ALE}_{\text{total}} \times \omega_\alpha \rfloor$
   * $V_\beta = \lfloor \text{ALE}_{\text{total}} \times \omega_\beta \rfloor$
3. **Exact Residual Closure**:
   * $V_\gamma = \text{ALE}_{\text{total}} - (V_\alpha + V_\beta)$
4. **Invariance**: By computing the third vector as the exact arithmetic complement of the first two quantized vectors, the sum is **mathematically guaranteed** to equal `total_fair_ale` with zero cent/unit discrepancy, regardless of currency magnitude (USD, EUR, JPY, GBP).

---

## 4. PHASED EXECUTION ROADMAP (ZERO-DEFECT DELIVERY PLAN)

To guarantee zero regressions and 100% deterministic verification, the implementation is partitioned into four strict phases. No phase may begin until the preceding phase passes all automated gates.

### PHASE 1: Domain Taxonomy, Configuration & Mathematical Contracts
* **Objective**: Establish the domain-to-receptor mapping, mathematical weight allocations, and data structures without touching the AST compiler or locales yet.
* **Deliverables**:
  1. Define `EconomicReceptorType` Enum (`AVAILABILITY_OUTAGE`, `CAPITAL_INEFFICIENCY`, `PRODUCTIVITY_TOIL`, `REGULATORY_AND_BREACH`) in the core domain/schema layer.
  2. Define the canonical mapping of `T1..T10 -> EconomicReceptorType` and default vector weights $(\omega_\alpha, \omega_\beta, \omega_\gamma)$ in engine configuration.
  3. Implement the `ActuarialVectorAllocator` utility enforcing the Exact Residual Closure identity ($V_\alpha + V_\beta + V_\gamma \equiv \text{ALE}_{\text{total}}$).
* **Verification Gate**: Unit tests proving 100% exact additive identity across 10,000 randomized fuzzing inputs (from `$0` to `$10B`).

### PHASE 2: Complete 6-Language I18N Externalization (`locales.json`)
* **Objective**: Populate `engine_config/locales.json` with high-precision, C-Suite-grade actuarial terminology for all 4 receptors across all 6 languages (`en`, `es`, `pt`, `fr`, `de`, `it`).
* **Deliverables**:
  1. Inject `annex_ch4_receptors` dictionary trees into all 6 language blocks in `locales.json`.
  2. Ensure zero Spanish/English cross-contamination and 100% parity of format placeholders (`{domain_name}`, `{total_ale}`, `{vector_alpha_val}`, etc.) across every language.
* **Verification Gate**: A dedicated JSON schema & placeholder parity test verifying that every receptor key and `{variable}` placeholder exists identically across all 6 locales.

### PHASE 3: GoF Strategy Implementation & AST Compiler Refactoring
* **Objective**: Build the polymorphic receptor strategies and decouple `payload_to_ast.py`.
* **Deliverables**:
  1. Create `src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py` containing `IActuarialReceptorStrategy`, the 4 concrete strategies, and `ActuarialReceptorFactory`.
  2. Refactor `_build_chapter_4_actuarial_modeling` and `_build_chapter_4_2_prioritization` inside `payload_to_ast.py` to delegate AST node generation to `ActuarialReceptorFactory`.
  3. Purge all legacy hardcoded downtime narratives and monolithic assumptions from `payload_to_ast.py`.
* **Verification Gate**: Static analysis (ruff/flake8/mypy) confirming 100% English codebase, strict type safety, and zero cyclomatic complexity spikes.

### PHASE 4: Comprehensive Test Suite & End-to-End AST Verification
* **Objective**: Prove mathematically and structurally that every domain renders its exact receptor narrative in any language without regression.
* **Deliverables**:
  1. **Strategy Resolution Tests**: Verify `T1..T5, T10` resolve to `AvailabilityOutageStrategy`, `T6` to `RegulatoryBreachStrategy`, `T7, T9` to `ProductivityToilStrategy`, and `T8` to `CapitalInefficiencyStrategy`.
  2. **AST Structural & Narrative Assertion Tests**: Compile full AST payloads for all 10 domains across all 6 languages and assert that `T6` never mentions "server downtime", `T8` explicitly models "capital waste/FinOps", and `T9` models "human productivity toil".
  3. **Financial Conservation Tests**: Extract rendered currency values from the compiled AST tables and verify that the sum of the sub-vectors equals the headline ALE.
* **Verification Gate**: 100% green `pytest` execution across the entire test suite with zero warnings.

---

## 5. ARCHITECTURAL SIGN-OFF

This blueprint eliminates technical debt, eradicates hardcoded domain bias, enforces Open FAIR™ actuarial rigor, and guarantees multi-lingual, multi-vertical scalability for Tier-1 global enterprises.

**Awaiting your authorization to initiate Phase 1.**