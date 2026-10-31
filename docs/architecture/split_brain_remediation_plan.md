# ARCHITECTURAL REMEDIATION PLAN: SPLIT-BRAIN CONVERGENCE

**Document ID:** `ARCH-REM-2026-001`  
**Status:** APPROVED FOR IMMEDIATE EXECUTION  
**Author:** Principal Systems Architect & Chief Software Auditor  
**Target System:** Enterprise Assessment & Actuarial Engine  
**Compliance Mandate:** Tier-1 Infrastructure Standards (Zero-Trust State, Deterministic Compilation, Pure Functional Core)

---

## Executive Summary

An exhaustive architectural audit of the Assessment Engine has surfaced five critical **Architectural Split-Brains**. A Split-Brain condition occurs when a system maintains multiple, mutually exclusive paradigms for a single bounded context, leading to state divergence, non-deterministic outputs, maintenance entropy, and silent data corruption. 

This document establishes the definitive State-of-the-Art (SOTA) remediation blueprints to converge these divergent subsystems into a unified, strictly typed, and mathematically sound architecture.

---

## 1. Compilation Paradigm Split-Brain

* **Current Pathology:** The document generation pipeline concurrently executes four incompatible paradigms: Abstract Syntax Tree (AST) traversal, imperative DOM/object mutation, binary template cloning, and monolithic procedural scripting.
* **Systemic Risk:** Non-deterministic document layouts, untraceable side effects during rendering, inability to statically analyze output structure before I/O commitment, and extreme fragility when upgrading underlying rendering libraries (e.g., `python-docx`).

### 1.1 SOTA Remediation Architecture: LLVM-Style Multi-Pass Compiler Pipeline

The rendering engine must be re-architected into a pure, multi-pass compiler utilizing a strictly typed **Intermediate Representation (IR)** and the **Visitor Pattern**. Imperative mutations, template cloning, and monolithic scripts are permanently deprecated.

```
[Pydantic Domain Model] 
       │
       ▼ (Pass 1: Frontend Lowering)
[High-Level Document AST (H-IR)] 
       │
       ▼ (Pass 2: Optimization & Layout Resolution)
[Normalized Layout IR (L-IR)] 
       │
       ▼ (Pass 3: Target-Specific CodeGen Backend)
[Binary Artifact (.docx / .pdf / HTML)]
```

1. **Frontend (AST Construction):** Pure functions ingest the validated Domain Model and emit an immutable High-Level IR (H-IR) representing semantic document structures (`SectionNode`, `ActuarialTableNode`, `RiskHeatmapNode`), completely agnostic of the target file format.
2. **Middle-End (IR Optimization Passes):** Stateless transformation passes traverse the H-IR to resolve cross-references, paginate tables, inject design tokens, and compute layout constraints, emitting a Normalized Layout IR (L-IR).
3. **Backend (Target CodeGen):** A strictly isolated `DocxBackendVisitor` traverses the L-IR. This is the *only* layer permitted to instantiate `python-docx` objects. It translates L-IR nodes into imperative library calls in a single, unidirectional pass without reading back from the mutated document object.

### 1.2 Scientific & Theoretical Justification

* **Lattner, C., & Adve, V. (2004). *LLVM: A Compilation Framework for Lifelong Program Analysis & Transformation*. (CGO '04):** Demonstrates that decoupling source semantics from target machine/format specifics via a strongly-typed, Static Single Assignment (SSA) Intermediate Representation eliminates $O(M \times N)$ translation complexity and enables deterministic optimization passes.
* **Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*:** The **Visitor Pattern** allows separating an algorithm (DOCX binary serialization) from the object structure on which it operates (the Document AST), adhering strictly to the Open-Closed Principle (OCP).

### 1.3 Zero-Downtime Refactoring Strategy

1. **Phase 1: Define the IR Schema:** Implement immutable `frozen=True` Pydantic models or Python `dataclasses` representing all structural nodes (`DocumentNode`, `BlockNode`, `InlineNode`).
2. **Phase 2: Implement the Backend Visitor:** Build the `DocxCodeGenVisitor` capable of rendering the IR to a byte stream. Verify equivalence using **Golden Master Testing** (comparing XML trees of legacy vs. IR-generated `.docx` files).
3. **Phase 3: Strangler Fig Migration:** Wrap legacy imperative generators in `LegacyAdapterNode` wrappers within the AST. Incrementally replace each monolithic script/template section with pure AST-emitting functions.
4. **Phase 4: Decommission Legacy Pathways:** Once 100% of sections emit pure H-IR, delete all binary template files used for cloning and purge imperative mutation helpers. Enforce AST-only compilation via architectural linter rules (`import-linter`).

---

## 2. Actuarial Calculation Split-Brain

* **Current Pathology:** Financial and cyber risk metrics are simultaneously computed by a rigorous Monte Carlo Bayesian Engine in the analytics core and overwritten or bypassed by naive, static heuristic multipliers (`risk = severity * 0.25`) embedded directly inside the document compiler.
* **Systemic Risk:** Severe fiduciary and audit compliance failure. The generated report exhibits internal mathematical contradictions (e.g., probabilistic Value-at-Risk charts disagreeing with executive summary tables).

### 2.1 SOTA Remediation Architecture: Pure Functional Actuarial Core & Pre-Computed Tensor State

Enforce **Strict Separation of Concerns (SoC)** and **Command-Query Responsibility Segregation (CQRS)**. The Document Compiler must be demoted to a **Dumb View Layer** with zero mathematical capabilities.

```
[Raw Telemetry & Priors] 
       │
       ▼ (Bayesian / Monte Carlo Engine)
[Immutable ActuarialLedger (Value Object)] ──(Cryptographic Hash)──► [Audit Log]
       │
       ▼ (Read-Only Injection)
[Document Compiler Frontend]
```

1. **Single Authority Calculation:** All stochastic simulations (Loss Exceedance Curves, VaR, CVaR, Bayesian posterior updates) execute exclusively within the `ActuarialEngine` prior to compilation.
2. **The `ActuarialLedger` Value Object:** The engine outputs a deeply immutable, strictly validated `ActuarialLedger` object containing pre-computed percentiles ($P_{5}, P_{50}, P_{95}$), summary statistics, and serialized distribution vectors.
3. **Compiler Lobotomy:** The compiler receives the `ActuarialLedger` via Dependency Injection. It is architecturally forbidden from performing arithmetic operations (`+`, `-`, `*`, `/`) on risk primitives. It may only format pre-computed floats into localized currency/percentage strings.

### 2.2 Scientific & Theoretical Justification

* **Hubbard, D. W., & Seiersen, R. (2016). *How to Measure Anything in Cybersecurity Risk*:** Establishes that ordinal scales and static heuristic matrices introduce severe mathematical distortion and false precision; quantitative risk requires consistent probabilistic Monte Carlo models (e.g., FAIR framework) across all reporting tiers.
* **Bernhardt, G. (2012). *Boundaries (Functional Core, Imperative Shell)*:** Dictates that complex business logic (actuarial math) must reside in a pure, deterministic functional core (controlled via PRNG seeding) with zero I/O, while the imperative shell handles orchestration and rendering.

### 2.3 Zero-Downtime Refactoring Strategy

1. **Phase 1: Audit & Shadow Mode:** Instrument the compiler heuristics to log every static calculation alongside the corresponding Monte Carlo output in a shadow telemetry stream to quantify the divergence delta.
2. **Phase 2: Expand the `ActuarialLedger` Contract:** Extend the Bayesian engine's output schema to explicitly include every derivative metric currently synthesized on-the-fly by the compiler.
3. **Phase 3: Dependency Injection Cutover:** Wire the `ActuarialLedger` directly into the AST Frontend passes. Replace all inline heuristic math expressions in the compiler with direct attribute lookups on the ledger.
4. **Phase 4: Static Analysis Guardrails:** Implement a custom AST Flake8/Ruff plugin over the `compiler/` directory that raises a build-breaking error if any statistical modules (`numpy`, `scipy`) or arithmetic operators are applied to domain risk fields.

---

## 3. Styling & Design System Split-Brain

* **Current Pathology:** A declarative Design Token system exists in configuration, but the codebase contains over 100 hardcoded `RGBColor(x, y, z)`, font size (`Pt(11)`), and margin injections scattered across imperative rendering functions.
* **Systemic Risk:** Visual incoherence, inability to support white-labeling or dynamic theming (e.g., Dark Mode / High-Contrast accessibility compliance), and O(N) engineering effort required for trivial brand updates.

### 3.1 SOTA Remediation Architecture: W3C-Compliant Hierarchical Design Token Engine

Eradicate all literal visual primitives from the logic and code-generation layers. Implement a three-tiered **Design Token Resolution Engine** resolved during the Middle-End IR compilation pass.

```
[Tier 1: Primitive Tokens]      (e.g., palette.blue.900 = "#0A192F")
           │
           ▼
[Tier 2: Semantic Tokens]       (e.g., color.risk.critical = {palette.red.700})
           │
           ▼
[Tier 3: Component Tokens]      (e.g., table.header.bg = {color.brand.primary})
           │
           ▼ (Injected via Context into Backend Visitor)
[Target-Specific Primitive]     (e.g., docx.shared.RGBColor(10, 25, 47))
```

1. **Semantic AST Tagging:** AST nodes declare *intent*, never appearance. A node specifies `style_token="typography.heading.h2"` or `severity_token="status.critical"`, never `color=RGBColor(255, 0, 0)`.
2. **Contextual Theme Provider:** An immutable `ThemeRegistry` loads and validates a declarative JSON/YAML token graph at startup.
3. **Centralized Materialization:** Only the `ThemeMaterializer` inside the Target CodeGen Backend is permitted to import `docx.shared.RGBColor`, `Pt`, or `Inches`. It translates semantic token paths into target binary primitives at the final moment of serialization.

### 3.2 Scientific & Theoretical Justification

* **W3C Design Tokens Community Group (2023). *Design Tokens Format Module Specification*:** Standardizes the abstraction of visual style atoms away from platform-specific implementations using aliased, hierarchical token graphs.
* **Parnas, D. L. (1972). *On the Criteria To Be Used in Decomposing Systems into Modules*. (Communications of the ACM):** Proves that modules must encapsulate "design decisions which are likely to change" (Information Hiding). Visual representation and brand hex codes are high-volatility decisions that must be hidden behind a stable semantic interface.

### 3.3 Zero-Downtime Refactoring Strategy

1. **Phase 1: Static Scraping & Tokenization:** Run an AST codemod (`LibCST`) across the repository to extract all 100+ `RGBColor`, `Pt`, and `Inches` instantiations. Cluster them into a canonical `tokens.yaml` file mapped to semantic names.
2. **Phase 2: Build the `ThemeRegistry`:** Implement a Pydantic-validated loader that parses `tokens.yaml`, resolves aliases, and exposes a type-safe accessor API (e.g., `theme.color.risk.high`).
3. **Phase 3: Automated Codemod Replacement:** Execute a `LibCST` transformation pass that replaces every hardcoded `RGBColor(r, g, b)` call in the codebase with the corresponding semantic token lookup via the `ThemeMaterializer`.
4. **Phase 4: CI Enforcement:** Add a pre-commit hook and CI regex/AST gate that strictly bans the string `RGBColor(` or `Pt(` outside of the single `compiler/backend/theme_materializer.py` module.

---

## 4. Linguistic & Localization Split-Brain

* **Current Pathology:** The system features a dynamic internationalization (i18n) engine, yet LLM orchestration layers and prompt templates contain hardcoded `target_language="Spanish"` default arguments and inline Spanish string literals.
* **Systemic Risk:** Silent linguistic contamination (Spanglish artifacts in English/Portuguese reports), thread-safety violations in multi-tenant concurrent executions, and complete failure of the i18n abstraction layer.

### 4.1 SOTA Remediation Architecture: Inversion of Control (IoC) via Ambient Locale Context & ICU MessageFormat

Eliminate all default language arguments across the entire call graph. Enforce explicit **Inversion of Control (IoC)** where linguistic state is an ambient, immutable property of the execution context.

```
[API Request / CLI Invocation (Locale: "pt-BR")]
       │
       ▼ (Instantiates)
[Immutable ExecutionContext (contextvars.ContextVar)]
       │
       ├──► [ICU MessageFormat Catalogs (Static UI/Report Strings)]
       │
       └──► [Prompt Compiler (Injects ISO-639/BCP-47 Constraints into LLM System Prompts)]
```

1. **Zero-Default Mandate:** No function signature in the codebase may contain `target_language: str = "Spanish"` (or any default). The locale (`BCP47Locale` type) must be a required parameter at the system boundary and propagated via Python's `contextvars` or explicit Dependency Injection.
2. **Declarative Prompt Templates:** LLM prompts are extracted from Python code into versioned, parameterized Jinja2/Prompt-IR templates. Target language directives are injected dynamically by the `PromptCompiler` reading from the `ExecutionContext`.
3. **ICU MessageFormat Standard:** All deterministic strings (table headers, axis labels, boilerplate legal text) are resolved through strict ICU MessageFormat catalogs (`.ftl` Fluent or `.json` ICU files), handling pluralization, gender agreement, and number/currency formatting natively per locale.

### 4.2 Scientific & Theoretical Justification

* **Fowler, M. (2004). *Inversion of Control Containers and the Dependency Injection Pattern*:** Demonstrates that low-level execution components (prompt formatters, table builders) must never instantiate or assume configuration defaults; dependencies (such as `LocaleContext`) must be injected by a higher-level orchestrator.
* **Unicode Consortium (UTS #35). *Unicode Locale Data Markup Language (LDML) & ICU MessageFormat*:** Establishes the mathematical and linguistic state machines required to separate grammatical structure from code execution without string-concatenation vulnerabilities.

### 4.3 Zero-Downtime Refactoring Strategy

1. **Phase 1: Introduce `LocaleContext`:** Define a strict `BCP47Locale` Enum (`ES_ES`, `EN_US`, `PT_BR`) and bind it to an immutable `ExecutionContext` object initialized at the application entrypoint.
2. **Phase 2: Signature Sanitization (Deprecation):** Remove default values from `target_language` parameters. Where backward compatibility is transiently required during migration, set the default to a sentinel `UNSET` object that logs a high-severity deprecation warning and resolves the value from `LocaleContext`.
3. **Phase 3: Prompt Externalization:** Extract all inline prompt strings containing Spanish instructions into external template files. Parameterize linguistic instructions using `{{ context.locale.language_name }}` and `{{ context.locale.bcp47_code }}`.
4. **Phase 4: Linter Lockdown:** Configure static analysis (`mypy --strict` and custom Ruff rules) to fail the build if any function defines a default string literal for `language` or `locale` parameters, or if non-ASCII characters appear in `.py` files outside of test fixtures.

---

## 5. State & Data Provenance Split-Brain

* **Current Pathology:** The engine establishes an in-memory Pydantic Single Source of Truth (SSOT), but downstream compilation stages bypass this state to perform ad-hoc, unvalidated disk reads of residual Markdown files (`asis_modules/*.md`).
* **Systemic Risk:** Severe TOCTOU (Time-of-Check to Time-of-Use) race conditions, stale data injection from previous runs, broken reproducibility, and total violation of data provenance guarantees in cloud/containerized environments.

### 5.1 SOTA Remediation Architecture: Parse, Don't Validate at Ingress & Pure In-Memory DAG Execution

Enforce a **Zero-I/O Core Architecture**. The file system is treated as an untrusted external boundary accessible *only* during the initial Hydration Ingress phase and the final Egress Serialization phase.

```
[Ingress Boundary: Disk / DB / API] 
       │
       ▼ (Hydration & Parsing Layer - ONLY place allowed to read disk)
[Immutable Pydantic SSOT (Deeply Frozen State Graph + SHA-256 Provenance Hash)]
       │
       ▼ (Pure In-Memory DAG Execution - Network/Disk I/O Strictly Blocked)
[Egress Boundary: Artifact Writer]
```

1. **Ingress Hydration Layer:** If `asis_modules/*.md` files are legitimate inputs, an explicit `IngressHydrator` reads them *once* at pipeline initialization, parses their Markdown/Frontmatter into structured AST or validated string fields, computes their SHA-256 content hashes, and seals them inside the root `AssessmentState` Pydantic model (`ConfigDict(frozen=True)`).
2. **Provenance Sealing:** The `AssessmentState` computes a deterministic Merkle-tree style hash of all its constituent inputs. Any mutation attempt raises an immediate `ValidationError` / `FrozenInstanceError`.
3. **Air-Gapped Core Pipeline:** The Analytics Engine and Document Compiler operate exclusively on the in-memory `AssessmentState` reference. They possess no file path references, `pathlib.Path` objects, or I/O handles.

### 5.2 Scientific & Theoretical Justification

* **King, A. (2019). *Parse, Don't Validate*:** Proves that input data (such as raw `.md` files on disk) must be parsed at the very boundary of the system into a strict, total data type (the Pydantic SSOT) that makes illegal or unvalidated states unrepresentable downstream.
* **Kleppmann, M. (2017). *Designing Data-Intensive Applications*:** Establishes the principle of **Derived Data vs. System of Record (SSOT)**. Reading from uncoordinated side-channels (residual disk files) during a transaction violates linearizability and creates permanent state divergence.

### 5.3 Zero-Downtime Refactoring Strategy

1. **Phase 1: Extend the Pydantic SSOT Schema:** Add explicit, typed fields to the root Pydantic state model (`AssessmentState.asis_modules: Mapping[ModuleID, ValidatedMarkdownModule]`) to house the content previously read from disk.
2. **Phase 2: Implement the Ingress Hydrator:** At the earliest stage of pipeline bootstrap, ingest `asis_modules/*.md` (or generate them in-memory from the LLM orchestrator without ever touching the disk) and populate the Pydantic SSOT.
3. **Phase 3: Reroute Downstream Consumers:** Refactor all downstream compiler and assessment functions to read from `state.asis_modules[module_id]` instead of calling `open()` or `Path.read_text()`. Stop writing intermediate `.md` files to disk entirely (or relegate them to an optional `--debug-dump-state` Egress observer).
4. **Phase 4: Kernel/Test Sandbox Enforcement:** In the test suite (`pytest`), wrap all core engine and compiler tests in a fixture that monkeypatches `builtins.open`, `os.open`, and `pathlib.Path.read_text` to raise a `RuntimeError("Illegal I/O in Pure Core")`, guaranteeing 100% in-memory provenance forever.

---

## 6. Master Convergence Verification Matrix

To certify the complete eradication of all five Split-Brains, the CI/CD pipeline must enforce the following invariant gates prior to merging to `main`:

| Split-Brain Domain | Architectural Target | Automated CI/CD Invariant Gate |
| :--- | :--- | :--- |
| **1. Compilation** | Multi-Pass AST $\rightarrow$ IR $\rightarrow$ Visitor | `import-linter`: `docx` imports restricted solely to `compiler/backend/docx_visitor.py`. |
| **2. Actuarial** | Pure Functional Core $\rightarrow$ `ActuarialLedger` | Custom AST Linter: Zero arithmetic operators (`+`, `-`, `*`, `/`) allowed on risk nodes in `compiler/`. |
| **3. Styling** | W3C 3-Tier Design Token Engine | Regex/AST Gate: Zero occurrences of `RGBColor` or `Pt` outside `theme_materializer.py`. |
| **4. Localization** | IoC `LocaleContext` + ICU Catalogs | `mypy --strict` + AST Gate: Zero default string arguments for `locale`/`language` parameters. |
| **5. Provenance** | Parse at Ingress $\rightarrow$ Frozen Pydantic SSOT | `pytest` I/O Sandbox: `builtins.open` blocked across all middle-end and compilation test suites. |