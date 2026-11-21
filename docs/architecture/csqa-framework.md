---
status: Verified
owner: docs-governance
source_of_truth:
- .github/workflows/quality.yml
- pyproject.toml
- tests/architecture/
- src/assessment_engine/application/tools/
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
notes: Continuous Software Quality Assurance (CSQA) architectural fitness functions and mutation gates.
---
# Continuous Software Quality Assurance (CSQA) Framework

Canonical architectural specification defining the continuous quality assurance model, automated fitness functions, mutation testing gates, and metamorphic verification invariants across `assessment-engine`.

---

## 1. System Mission: Verification by Mathematical Invariance

The Continuous Software Quality Assurance (CSQA) framework rejects superficial "all tests green" complacency. Its objective is to **mathematically certify that the software evolutions preserve architectural boundaries, business invariants, and test oracle sensitivity**:

$$\text{System Health} = f(\text{Mutation Score}, \text{Graph Acyclicity}, \text{Metamorphic Coverage})$$

Passing unit tests is a necessary but insufficient condition; test suites must actively demonstrate detection sensitivity against deliberate semantic corruption.

---

## 2. Quality Fitness Functions

The framework continuously monitors three structural fitness vectors:

### A. Stratified Mutation Testing (Oracle Sensitivity)
- **Fast Gate (Pull Requests):** `mutation_gate.py` injects sampled mutations into boolean and relational operators across changed modules with a strict timeout ($<30\text{s}$). *Enforced Threshold: $>85\%$ Mutation Score.*
- **Deep Gate (Nightly / Scheduled CI):** Deep mutation testing engines (`mutmut`) subject Python code to arithmetic, return-value, and loop mutations to eliminate equivalent mutants and assert deep state validation.

### B. Dependency Graph Purity & Architectural Decoupling
- **Static Enforcement:** Driven by `import-linter` configured in `pyproject.toml`.
- **Enforced Metrics:**
  - **Forbidden Layers:** Zero dependencies from inner layers to outer layers (e.g., `domain \to infrastructure` or `domain \to application` is strictly blocked).
  - **Acyclic Siblings:** Zero circular dependency cycles across domain packages.
  - **I/O Encapsulation:** Domain modules are strictly prohibited from importing network, disk I/O, or external SDK packages (`include_external_packages = true`).

### C. Metamorphic Property-Based Oracles (Hypothesis)
- **Actuarial Invariant Validation:** Mathematical components (Bayesian copula, FAIR loss distributions, Euler capital allocators) are validated using property-based metamorphic relations:
  - **Monotonicity:** $\text{RiskExposure}(L_1) \le \text{RiskExposure}(L_2)$ for $L_1 \le L_2$.
  - **Asymptotic Convergence:** Boundary convergence under infinite sample limits.
  - **Robustness:** Zero tolerance for unhandled `NaN`, `Infinity`, or numeric overflow across all inputs.

---

## 3. Automated Degradation & Flakiness Prevention

1. **Strict Fixture Isolation (Anti State-Bleeding):** Pipelines abort on `pytest -W error::hypothesis.errors.HypothesisWarning` if a stochastic generator interacts with mutable fixture state, eliminating concurrency blindness.
2. **Deterministic PRNG Seeding:** All stochastic simulations (Monte Carlo runs) must use deterministic SHA-256 derived seeds to prevent flaky test regressions.
3. **AST-Based Structural Assertions:** Tests must assert against typed OpenXML AST nodes (tables, cells, headings) rather than brittle raw string matching, ensuring visual decoupling.

---

## 4. Autonomous AI Improvement & Governance Guardrails

When AI agents execute autonomous remediation or evolutionary optimization:

1. **Survivor Mutants Audit:** Agents receive diffs of surviving mutants from mutation gates to infer missing test preconditions or flag equivalent mutants.
2. **Quality Gate Immutability:** AI agents are strictly forbidden from modifying `[tool.importlinter]`, `.coveragerc`, or threshold values in `.github/workflows/quality.yml`. Automated code changes must always submit to pre-existing gates.
3. **Zero-Entropy Rule:** Mutation test caches and temporary coverage artifacts must remain confined to `.artifacts/` or git-ignored temporary directories.
