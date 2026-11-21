---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/application/cli.py
- src/assessment_engine/infrastructure/auditor/scanner.py
- src/assessment_engine/infrastructure/auditor/models.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: explanation
verification_mode: editorial
notes: Canonical technical specification of the unified 21-probe audit framework and scoring algorithms.
---
# Unified Audit Framework & Multidimensional Quality Engine

Canonical specification defining the architecture, 21 automated diagnostic probes, scoring algorithms, and certification artifacts executed via the platform audit command:

```bash
python -m assessment_engine.application.cli audit
```

---

## 1. Unified Single-Pane-of-Glass Objective

The `cli audit` subsystem consolidates static analysis, security vulnerability scanning, dynamic DAST simulations, mutation testing, and AST topology reachability into a single deterministic command for Tier-1 enterprise due diligence:

```bash
python -m assessment_engine.application.cli audit [--target <project_root>] [--output-dir docs/audits]
```

- `--target`: Root directory to audit (default: repository root).
- `--output-dir`: Output destination for reports (default: `docs/audits`).

---

## 2. Deterministic Audit Lifecycle

```text
[ python -m assessment_engine.application.cli audit ]
                        |
                        v
[ Scanner: AST Directory Traversal (Excluding .git, .venv, .mypy_cache) ]
                        |
                        v
[ Execution of the 21 Automated Probes across 6 Dimensions ]
                        |
                        v
[ Mathematical Global Weighted Score Calculation (0.0% to 100.0%) ]
                        |
                        v
[ Formal Letter Grade Assignment: A+ (Platinum), A (Gold), B, C, F ]
                        |
                        +────────────────────────┬────────────────────────+
                        |                                                 |
                        v                                                 v
             [ AUDIT_REPORT.json ]                             [ AUDIT_CERTIFICATE.html ]
```

---

## 3. Catalog of the 21 Automated Probes

| Probe ID | Dimension & Focus | Weight | Standard / Threshold | Evaluation Method |
|:---|:---|:---:|:---|:---|
| `security_sast` | Static Security & Secrets | 8% | CWE-798, OWASP Top 10 | AST scan for injection sinks; Shannon entropy calculation to detect hardcoded credentials. |
| `security_dast` | Dynamic Red Team DAST | 8% | OWASP DAST | Simulates dynamic injection payloads; asserts zero exposure of unauthenticated endpoints. |
| `test_coverage` | Production Code Coverage | 8% | Tier-1 Core $\ge 65.0\%$ | Line and branch coverage across active production packages excluding offline tools. |
| `assertion_quality` | Test Assertion Density | 6% | Tier-1 Ratio $\ge 80.0\%$ | AST inspection of test suites requiring strict equality and schema bounds over loose assertions. |
| `mutation_gate` | Mutation Score (mutmut) | 8% | ISO/IEC/IEEE 29119 | Injects syntactic mutations (ROR, LCR, COR); asserts that tests fail upon code corruption. |
| `neurosymbolic_topology` | Graph Topology & Dead Code| 6% | Zero-Entropy Architecture | Builds NetworkX import graph; identifies orphan modules and circular dependencies. |
| `ast_complexity` | Cyclomatic Complexity | 8% | ISO 25010 & Sonar S3776 | Enforces $\text{CC} \le 10$ across $85\%+$ of functions; zero Grade F functions in active layers. |
| `code_hygiene` | Exception Hygiene | 2% | CWE-391 | Eradicates blind `except Exception: pass` blocks masking silent production failures. |
| `sre_observability` | Structured Logging | 5% | SRE OBS-001 | Blocks raw `print()` in production code; verifies structured logging with `logging.getLogger`. |
| `legal_compliance` | AI Liability & Disclaimer | 5% | EU AI Act & Liability | Verifies confidentiality notices, liability caps, and Monte Carlo actuarial disclaimers. |
| `supply_chain` | Supply Chain & SBOM | 8% | NIST SP 800-218 | Generates CycloneDX SBOM (`SBOM_CYCLONEDX.json`); asserts zero high-severity CVEs. |
| `performance_finops` | Latency & Token Budgets | 4% | FinOps Foundation | Validates asynchronous timeouts and rate limiter configurations in external LLM calls. |
| `browser_accessibility`| Web Portal Accessibility | 4% | WCAG 2.1 AA | Inspects HTML templates and React components for alt tags, color contrast, and ARIA attributes. |
| `contract_drift` | Pydantic Schema Alignment | 4% | Pydantic V2 Strict | Asserts exact structural correspondence between Markdown contract tables and Pydantic models. |
| `resilience_chaos` | Graceful Degradation | 4% | Chaos Engineering | Verifies deterministic failover circuits when cloud APIs experience outages. |
| `ai_safety_llm` | Prompt Injection Guardrails | 4% | OWASP LLM01/02 | Verifies XML encapsulation boundaries (`<untrusted_context>`) in all prompt YAML catalogs. |
| `concurrency_stress` | Deterministic PRNG | 4% | Concurrency Safety | Validates thread-safe local pseudo-random generators and SHA-256 stable seeds. |
| `hardcoded_artifacts` | Zero Hardcoded Paths | 2% | Zero-Entropy Policy | Enforces dynamic path resolution via `runtime_paths.py`; blocks absolute local paths. |
| `comment_quality` | Technical Docstrings | 2% | Clean Code Standards | Measures technical docstring coverage; prohibits informal emojis in production comments. |
| `documentation_quality`| Documentation Governance | 2% | Diataxis Framework | Validates front matter metadata parity, bidirectional links, and freshness deadlines. |
| `structural_smells` | Architectural Cleanliness | 2% | Clean Architecture | Detects God Objects, layering breaches, and cross-tier coupling. |

---

## 4. Weighted Scoring Formulation & Formal Certification Grades

The global quality score is the deterministic weighted sum of all 21 probe ratings ($0.0\%$ to $100.0\%$):

$$\text{Global Score} = \sum_{i=1}^{21} \left(\text{Probe Score}_i \times \text{Weight}_i\right)$$

### Certification Grade Scale:
- **Grade A+ (Platinum):** $\text{Global Score} \ge 90.0\%$ and **100% of probes passed** (`passed == True` on all 21 probes).
- **Grade A (Gold):** $\text{Global Score} \ge 80.0\%$ with zero open critical security vulnerabilities (`security_sast` and `security_dast` passed).
- **Grade B (Silver):** $\text{Global Score} \ge 70.0\%$ with zero open critical security vulnerabilities.
- **Grade C (Needs Improvement):** $\text{Global Score} \ge 50.0\%$.
- **Grade F (Failed):** $\text{Global Score} < 50.0\%$ or presence of unmitigated critical security vulnerabilities.

---

## 5. Generated Certification Deliverables

The audit command atomically outputs three formal artifacts in `docs/audits/`:
1. **`AUDIT_REPORT.json`:** Machine-readable report with all metrics, probe outcomes, and remediation recommendations.
2. **`AUDIT_CERTIFICATE.html`:** Responsive executive certificate for CTOs and due diligence auditors.
3. **`SBOM_CYCLONEDX.json`:** CycloneDX standard Software Bill of Materials.

### CI/CD Exit Code Invariants:
- **Exit Code `0`:** Grade A+, A, or B achieved.
- **Exit Code `1`:** Grade C or F (blocks pull request merge).
