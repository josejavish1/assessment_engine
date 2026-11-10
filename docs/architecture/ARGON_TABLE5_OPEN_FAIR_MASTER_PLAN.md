### ARCHITECTURAL MANIFESTO: ZERO-DEFECT ACTUARIAL RECONCILIATION
**Authority:** `gemini-4-argon` (Principal Enterprise Architect, Supreme Actuarial Arbiter & Chief Forensic Auditor)  
**Target Standard:** Open FAIR™ (ISO/IEC 27005 / CosO ERM) & Basel III/Solvency II Capital Allocation  
**Architecture Paradigm:** Domain-Driven Design (DDD), Hexagonal Isolation, Zero Hardcoding, 100% Locale & Currency Agnostic, Mathematically Immutable.

---

### EXECUTIVE SUMMARY OF THE ARCHITECTURAL STRATEGY
To position this engine as the undisputed global #1 standard across all enterprise verticals (from Mid-Market to Fortune 500 / Global Tier-1), the implementation of **Table 5 (Actuarial Risk Exposure & Diversification Reconciliation)** cannot rely on superficial presentation-layer patches or ad-hoc arithmetic. It must be engineered from the ground up as a **Deterministic-Stochastic Hybrid Pipeline**.

Before writing a single line of production code, we observed a subtle mathematical discrepancy in the user-approved mockup illustration: in the mockup, the sum of the *Net Portfolio Contribution* rows equals `€829,698` (`122.1%`), whereas the consolidated total states `€819,398` (`100.0%`). In our production engine, **this mathematical gap will be impossible**. By enforcing **Tasche’s Conditional Expectation (Euler Allocation)** paired with the **Largest Remainder Method (Hare-Niemeyer)** for integer/cent rounding, the engine will guarantee that:
1. Every vector reconciles to the exact cent/unit of any currency (`USD`, `EUR`, `GBP`, `JPY`, `CHF`, etc.).
2. All relative risk contributions sum to **100.0%** without floating-point drift.
3. The codebase remains 100% in strict Technical English, with all natural language and formatting delegated to externalized configuration contracts.

We will execute this transformation in **Four Sequential, Gate-Checked Engineering Phases**.

---

### PHASE 1: MATHEMATICAL ENGINE & COPULA CO-EXPECTATION
**Target Directory:** `src/assessment_engine/domain/actuarial/`

#### 1.1 Architectural Separation of Concerns
We will decouple the stochastic simulation from the accounting reconciliation by introducing two pure domain services:
*   `StandaloneTowerSimulator`: Computes the bottom-up marginal distribution $L_i$ for each active technology domain $i \in \{1 \dots N\}$ using Open FAIR Monte Carlo trials ($M \ge 50,000$, seeded deterministically via SHA-256 of the assessment UUID for 100% audit reproducibility).
*   `EulerPortfolioAllocator`: Performs the joint dependency convolution via a Student-$t$ / Gaussian Copula over the active $N \times N$ correlation matrix $\Sigma$, and extracts the exact Euler risk decomposition.

#### 1.2 Mathematical Formulation (Zero Heuristics)
1. **Standalone Bottom-Up ALE ($ALE_{standalone, i}$):**
   For each active domain $i$, let $L_{i, m}$ be the simulated loss in Monte Carlo trial $m \in \{1 \dots M\}$ driven by its specific CMMI maturity score, Loss Event Frequency ($LEF$), and Loss Magnitude ($LM$).
   $$ALE_{standalone, i} = \frac{1}{M} \sum_{m=1}^{M} L_{i, m}$$

2. **Undiversified Gross Portfolio Subtotal ($ALE_{gross}$):**
   $$ALE_{gross} = \sum_{i=1}^{N} ALE_{standalone, i}$$

3. **Consolidated Net Portfolio ALE ($ALE_{net}$):**
   Through the Copula dependency structure and systemic absorption caps (modeling multi-domain cascading failures, shared cyber-insurance limits, and concurrent incident response saturation), the total portfolio loss in trial $m$ is $L_{portfolio, m} = \Phi(L_{1,m}, \dots, L_{N,m})$.
   $$ALE_{net} = \frac{1}{M} \sum_{m=1}^{M} L_{portfolio, m}$$

4. **Euler Marginal Portfolio Contribution ($ALE_{Euler, i}$):**
   Per Euler’s Homogeneous Function Theorem (Tasche, 1999), the exact risk contribution of domain $i$ to the diversified portfolio is its co-expectation with the tail/total portfolio performance. To guarantee exact additive coherence across non-linear absorption boundaries:
   $$ALE_{Euler, i} = E\left[ L_i \mid L_{portfolio} \right]_{\text{allocated}} \quad \text{such that} \quad \sum_{i=1}^{N} ALE_{Euler, i} \equiv ALE_{net}$$

5. **Overlap & Absorption Adjustment ($\Delta_{div, i}$):**
   $$\Delta_{div, i} = ALE_{Euler, i} - ALE_{standalone, i} \quad (\text{strictly } \le 0)$$
   $$\Delta_{total} = \sum_{i=1}^{N} \Delta_{div, i} \equiv ALE_{net} - ALE_{gross}$$

6. **Relative Risk Weight ($W_i$):**
   $$W_i = \frac{ALE_{Euler, i}}{ALE_{net}} \times 100\%$$

#### 1.3 The "Zero-Penny-Drift" Rounding Algorithm
Floating-point numbers (`float64`) inevitably cause 1-to-3 cent discrepancies when rounded for executive tables. The engine will implement a dedicated `LargestRemainderReconciler` class:
*   All standalone and Euler values are rounded to integer currency units (or minor units, configurable per ISO-4217 currency code) using the **Hare-Niemeyer Largest Remainder Method** constrained by $ALE_{gross}$ and $ALE_{net}$.
*   $\Delta_{div, i}$ is derived post-rounding as `euler_allocated_int[i] - standalone_int[i]`, guaranteeing that every single row in Table 5 satisfies `Column 3 + Column 4 == Column 5` horizontally, and every column satisfies `Sum(Row 1..N) == Summary Row` vertically.
*   Percentages ($W_i$) undergo the same Hare-Niemeyer reconciliation at 1 decimal place (`0.1%` granularity) so the column sum is mathematically locked to `100.0%`.

---

### PHASE 2: DATA CONTRACTS, CURRENCY & LOCALE AGNOSTICISM
**Target Files:** `src/assessment_engine/contracts/actuarial_schemas.py` & `engine_config/locales.json`

#### 2.1 Immutable Domain Data Contracts (Pydantic v2)
No dictionaries or untyped tuples will cross boundaries. We will define strict, self-validating Pydantic models in pure English:
*   `DomainRiskBreakdownRow`:
    *   `domain_id`: `str` (e.g., `"T1"`)
    *   `domain_label_key`: `str` (i18n lookup key)
    *   `cmmi_maturity`: `Decimal` (bounded `1.00` to `5.00`)
    *   `standalone_ale`: `int`
    *   `diversification_adjustment`: `int` (enforced $\le 0$)
    *   `euler_net_contribution`: `int` (enforced $\ge 0$)
    *   `portfolio_weight_pct`: `Decimal` (bounded `0.0` to `100.0`)
*   `ActuarialTable5ReconciliationContract`:
    *   `currency_code`: `ISO4217Currency` (`EUR`, `USD`, `GBP`, `JPY`, etc.)
    *   `active_domain_rows`: ` tuple[DomainRiskBreakdownRow, ...]` (1 to $N$ dynamic items)
    *   `subtotal_gross_cmmi_average`: `Decimal`
    *   `subtotal_gross_undiversified_ale`: `int`
    *   `actuarial_copula_adjustment_ale`: `int`
    *   `actuarial_copula_overlap_pct`: `Decimal`
    *   `total_net_consolidated_cmmi`: `Decimal`
    *   `total_net_consolidated_ale`: `int`
    *   `total_portfolio_weight_pct`: `Decimal` (locked to `Decimal("100.0")`)
    *   *Model Validator (`@model_validator(mode="after")`):* Executes horizontal and vertical accounting identity checks at instantiation time. If a 1-cent discrepancy exists, the contract raises an `ActuarialReconciliationIntegrityError` immediately.

#### 2.2 Zero-Hardcoding Localization Matrix (`engine_config/locales.json`)
All literal strings are purged from Python source files. We will introduce the `actuarial_table_5` namespace across all supported locales (`en`, `es`, `pt`, `fr`, `de`, `ja`):
*   `headers`:
    *   `col_1_domain`: `"Technology Domain"` (EN) / `"Dominio Tecnológico"` (ES) / `"Domaine Technologique"` (FR) / etc.
    *   `col_2_cmmi`: `"CMMI Maturity"`
    *   `col_3_standalone`: `"Standalone Bottom-Up ALE"`
    *   `col_4_adjustment`: `"Overlap & Absorption Adjustment"`
    *   `col_5_euler_net`: `"Net Portfolio Contribution (Euler ALE)"`
    *   `col_6_weight_pct`: `"% of Total Risk"`
*   `summary_rows`:
    *   `row_subtotal_gross`: `"SUBTOTAL GROSS UNDIVERSIFIED"`
    *   `row_copula_adjustment`: `"ACTUARIAL ADJUSTMENT (COPULA)"`
    *   `row_total_net`: `"TOTAL NET CONSOLIDATED RISK"`
    *   `badge_copula_overlap_template`: `"[{pct}% Copula Overlap]"`
    *   `symbol_not_applicable`: `"—"`
*   **CLDR Currency & Number Formatting Engine:** A dedicated `LocaleFormatter` utility will format monetary values and percentages according to the target locale and currency (e.g., `€962,015` vs `962.015 €` vs `¥145,200,000`), ensuring negative adjustments render cleanly as `-€8,540` (or `(€8,540)` if accounting format is toggled).

---

### PHASE 3: AST COMPILER INTEGRATION & DYNAMIC SCOPING
**Target File:** `src/assessment_engine/Compilers/tomo_asis_ast_compiler.py`

#### 3.1 Dynamic Scope Elasticity (1 to $N$ Active Towers)
Whether an enterprise engages in a full 10-tower industrial assessment (e.g., Cement/Logistics Tier-1) or a scoped 6-tower cloud-native assessment (e.g., Digital Banking/FinTech), the AST compiler will iterate strictly over `contract.active_domain_rows`:
*   **No static row indices:** The compiler dynamically builds $R = \text{len}(\text{active\_domain\_rows}) + 4$ rows (1 Header Row + $N$ Active Domain Rows + 3 Reconciliation Footer Rows).
*   **Correlation Matrix Sub-slicing:** In Phase 1, when a client scopes out towers (e.g., `T1 Physical Facilities` and `T10 Plant` excluded for a pure SaaS bank), the Copula engine automatically slices the master $10 \times 10$ correlation matrix $\Sigma$ into the active $k \times k$ sub-matrix and verifies Positive Semi-Definiteness (PSD) via Cholesky decomposition before running the simulation.
*   **Weighted CMMI Governance:** The CMMI average displayed in the `SUBTOTAL GROSS UNDIVERSIFIED` and `TOTAL NET CONSOLIDATED RISK` rows is computed dynamically across active domains only.

#### 3.2 OpenXML / AST Rendering Specification (`_build_chapter_3_actuarial_modeling`)
The AST node generator for Table 5 will construct an `ASTTableNode` with strict visual hierarchy and typographic precision:
1. **Column Alignment & Width Proportions:**
   *   Col 1 (`Domain`): Left-aligned (`26%` width)
   *   Col 2 (`CMMI`): Center-aligned (`10%` width)
   *   Col 3 (`Standalone ALE`): Right-aligned, tabular numerals (`16%` width)
   *   Col 4 (`Adjustment`): Right-aligned, tabular numerals (`18%` width)
   *   Col 5 (`Euler Net ALE`): Right-aligned, tabular numerals (`18%` width)
   *   Col 6 (`% of Total Risk`): Right-aligned, tabular numerals (`12%` width)
2. **Visual Styling Rules (Theme-Driven, Zero Hardcoded Hex Codes in Logic):**
   *   **Header Row:** Primary corporate navy background, bold white typography, bottom border accent.
   *   **Body Rows ($1 \dots N$):** Alternating subtle zebra striping; Col 4 (`Adjustment`) rendered in muted slate/crimson to visually denote risk reduction/absorption; Col 5 (`Euler Net`) rendered in semi-bold primary text.
   *   **Footer Row 1 (`SUBTOTAL GROSS`):** Top thin border, light neutral shading, bold text. Columns 4, 5, and 6 populated via `locales.symbol_not_applicable` (`"—"`), centered.
   *   **Footer Row 2 (`ACTUARIAL ADJUSTMENT`):** Accent tint shading. Col 2, 5, and 6 set to `"—"`. Col 3 displays `-€142,617`. Col 4 renders the localized template `[-14.8% Copula Overlap]`.
   *   **Footer Row 3 (`TOTAL NET CONSOLIDATED RISK`):** Double-line top border, heavy bottom border, dark executive shading with high-contrast bold typography. Displays both the Standalone reconciliation (`Col 3 - Col 4 = €819,398`) and the Euler portfolio summation (`Col 5 = €819,398`, `Col 6 = 100.0%`), visually proving the two-way actuarial bridge at a glance.

---

### PHASE 4: AUTOMATED VERIFICATION & CI/CD QUALITY GATES
**Target Directory:** `tests/unit/actuarial/` & `tests/integration/ast_compiler/`

No code merges to `main` without passing a 4-tier automated forensic test suite using `pytest` and `hypothesis` (property-based testing):

#### 4.1 Mathematical Identity & Conservation Laws (`test_euler_allocation_identities.py`)
Using `hypothesis`, we will generate 500+ randomized enterprise profiles (varying revenue from $10M to $100B, random CMMI vectors $\in [1.0, 5.0]^N$, active towers $N \in [2, 10]$, and currencies `EUR`, `USD`, `JPY`):
*   **Assertion 1 (Horizontal Row Identity):** $\forall i \in \{1 \dots N\}, \text{Standalone}_i + \text{Adjustment}_i == \text{EulerNet}_i$.
*   **Assertion 2 (Vertical Standalone Identity):** $\sum_{i=1}^N \text{Standalone}_i == \text{SubtotalGross}$.
*   **Assertion 3 (Vertical Adjustment Identity):** $\sum_{i=1}^N \text{Adjustment}_i == \text{CopulaAdjustment}$.
*   **Assertion 4 (Vertical Euler Identity):** $\sum_{i=1}^N \text{EulerNet}_i == \text{TotalNetConsolidated}$.
*   **Assertion 5 (Bridge Cross-Check):** $\text{SubtotalGross} + \text{CopulaAdjustment} == \text{TotalNetConsolidated}$.
*   **Assertion 6 (Simplex Weight Conservation):** $\sum_{i=1}^N \text{WeightPct}_i == \text{Decimal}("100.0")$.

#### 4.2 Actuarial Boundary & Monotonicity Tests (`test_actuarial_monotonicity.py`)
*   **Sub-Additivity of Coherent Risk Measures:** Prove that for any positive correlation matrix, $\text{TotalNetConsolidated} \le \text{SubtotalGross}$ (i.e., `CopulaAdjustment <= 0`).
*   **CMMI Sensitivity Monotonicity:** Prove that holding all other domains constant, improving domain $i$'s CMMI maturity from $2.0 \to 3.5$ strictly decreases both $\text{Standalone}_i$ and $\text{EulerNet}_i$.
*   **Single-Tower Degenerate Case ($N=1$):** If an assessment is scoped to exactly 1 tower, `CopulaAdjustment` must equal `0`, `Overlap %` must equal `0.0%`, and `EulerNet_1 == Standalone_1`.

#### 4.3 Multi-Locale & AST Structural Integrity Tests (`test_table5_ast_compilation.py`)
*   Compile Table 5 across all 6 languages (`en`, `es`, `pt`, `fr`, `de`, `ja`) and verify that zero untranslated keys, `None` strings, or Spanish/English bleed-throughs occur.
*   Inspect the generated `.docx` XML tree (`w:tbl`) for benchmark profiles (e.g., 6-tower Digital Bank vs. 10-tower Heavy Manufacturing) to assert exact row counts ($6+4=10$ vs. $10+4=14$), cell alignments, and absence of XML schema corruption.

#### 4.4 Static Analysis & Zero-Hardcoding Gate (`test_codebase_hygiene.py`)
*   Automated AST linter scanning `src/` to enforce:
    *   100% English identifiers, docstrings, and comments (regex check rejecting Spanish diacritics or vocabulary in `.py` files).
    *   Zero hardcoded currency symbols (`€`, `$`, `£`, `¥`) inside domain or compiler logic.
    *   100% `mypy --strict` type coverage.

---

### EXECUTION ROADMAP & SIGN-OFF PROTOCOL

| Phase | Deliverable | Key Engineering Artifact | Verification Gate |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Core Actuarial & Copula Engine | `src/assessment_engine/domain/actuarial/euler_allocator.py` | `pytest tests/unit/actuarial/` (100% pass on 500 property-based scenarios) |
| **Phase 2** | Schemas & i18n Localization | `contracts/actuarial_schemas.py` & `engine_config/locales.json` | Schema validation & 6-language completeness check |
| **Phase 3** | AST Compiler & OpenXML Renderer | `Compilers/tomo_asis_ast_compiler.py` | End-to-end `.docx` generation for 6-tower and 10-tower benchmarks |
| **Phase 4** | Forensic Audit & Regression Suite | `tests/integration/test_table5_forensic_audit.py` | Zero-defect CI gate, `mypy --strict`, zero-hardcoding linter |

**Architect's Readiness Declaration:**  
The mathematical model is closed-form, the software architecture is cleanly decoupled, and the reconciliation invariants are airtight. Upon your authorization, we will commence **Phase 1** implementation immediately.