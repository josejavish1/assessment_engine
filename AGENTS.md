---
status: Verified
owner: docs-governance
source_of_truth:
- docs/ai/documentation-governance.md
- docs/README.md
- docs/documentation-map.yaml
- docs/operations/agentic-development-workflow.md
- docs/operations/engineering-quality-gates.md
last_verified_against: 2026-11-12
applies_to:
- ai-agents
doc_type: operational
diataxis: how_to
verification_mode: editorial
---
# AGENTS

This document serves as the **short operational entry gate for any AI agent** operating on `assessment-engine`.

## Reading Order

1. [`README.md`](README.md)
2. [`docs/README.md`](docs/README.md)
3. [`docs/ai/documentation-governance.md`](docs/ai/documentation-governance.md)
4. [`docs/operations/agentic-development-workflow.md`](docs/operations/agentic-development-workflow.md) when executing AI-assisted modifications
5. [`docs/operations/engineering-quality-gates.md`](docs/operations/engineering-quality-gates.md) when writing or modifying code or tests
6. The canonical document closest to the target component

## Core Invariants

- Do not treat this file as a standalone source of truth for repository architecture.
- Do not introduce detailed architecture, contracts, or operations here; store them in `docs/`.
- Rely on verified code, test suites, schemas, and CI workflows as primary truth.
- Never act upon ambiguous instructions: make the problem, scope, source of truth, and invariants explicit first.
- Materialize critical rules into executable code, automated tests, schemas, or CI gates—never solely in prompts.
- Keep `docs/documentation-map.yaml` synchronized whenever a document's status or path changes.
- If a technical statement cannot be verified empirically, mark it as `Needs Review` rather than hallucinating details.
- **GOLDEN PATHS (Strict):** Never create files from scratch for a new service, worker, or endpoint. You MUST use base templates located in `templates/golden_paths/` and implement solely the business logic. Preserve baseline logging structure and validation layers. For stateless Pydantic models, DTOs, or pure helpers, you may start from a blank file provided `# golden-path: ignore` is present in the header.

## Sovereign Non-Negotiable Engineering Laws (Zero-Tolerance Rules)

Every agent (Gemini, ChatGPT, Claude, Cursor, Copilot) must submit unconditionally to these sovereign laws:

1. **Protocol Tyranny (Anti-Complacency):** Technical and architectural integrity supersedes delivery speed. Never force CI/CD pipelines to pass, suppress warnings, disable automated tests, or execute administrative merges to bypass branch protections.
2. **Zero Workarounds:** For any runtime, typing, or linting failure, investigate and resolve the exact root cause. Never silence warnings with generic exception handlers or bypasses.
3. **Zero-Entropy Architecture:** Compressed archives (`.zip`), temporary backup folders (`_archive`, `old`), and loose test scripts in the root directory are strictly prohibited. Git is the sole time machine. Keep the entire codebase clean and symmetric.
4. **Language Decoupling (100% Technical English):** Regardless of the language used by the human operator in conversational chat (even when discussing in Spanish), **ALL** source code, comments, signatures, docstrings, log messages, exception messages, agent prompts, variable names, automated tests, and git commit messages MUST be written strictly in **Technical English**. Hardcoded Spanish literals or `locale="es"` defaults in Python or TypeScript source code are strictly prohibited. Multilingual text resides exclusively in declarative catalogs (`engine_config/locales.json`). The test suite (`test_no_spanish_characters_in_python_code` and `test_no_hardcoded_locale_es_in_src`) deterministically enforces this rule.
5. **Mandatory Empirical Verification:** Never assume changes succeed based solely on the absence of compiler errors. You MUST run the full automated test suite (`pytest`) and verify execution artifacts before concluding any task.
6. **Presentation-Layer Immunity (Zero Presentation-Layer Patching):** Never calculate, recalculate, adjust, or patch business metrics or mathematical bounds in presentation compilers (`payload_to_ast.py` / `docx_compiler.py`). The presentation layer is a passive visual consumer. If a metric is inaccurate in a deliverable, the defect resides upstream in calculation engines (`calculators.py`, `fair_risk.py`, `continuous_risk_allocator.py`).
7. **Mandatory Data Lineage Audit:** When identifying anomalies in values or text, trace complete variable lineage from input ingestion through each transformation step before proposing a code modification.
8. **Zero Stochastic Theater:** The probabilistic actuarial model (Bayesian Copula / Monte Carlo) is the sole Single Source of Truth (SSOT) authorized to compute risks and loss bounds. Hardcoded heuristic fallbacks or conditional bypasses (`if payload.get(...) is None`) that discard simulation data are prohibited.
9. **Behavioral Drift Sentinel (Canary Protocol):** To detect attention dilution and context rot in extended sessions, autonomous agents MUST prepend every response with the deterministic sentinel: `[CANARY: V4 | MONISM: SSOT | LOCALE: EN]`. Omission of this tag signals context degradation, requiring immediate session re-initialization.

## Where to Write

- Architecture: `docs/SYSTEM_ARCHITECTURE.md` or scoped `docs/architecture/`
- Contracts & Schemas: `docs/contracts/`
- Agent Workflows: `docs/operations/agentic-development-workflow.md`
- Product Owner Orchestrator: `docs/operations/product-owner-orchestrator.md`
- Quality & CI: `docs/operations/engineering-quality-gates.md`
- Documentation Governance: `docs/ai/documentation-governance.md`
- Master Map & Status: `docs/README.md` and `docs/documentation-map.yaml`

Agent-specific adapters (`GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/`) only provide operational adaptations of this baseline.

---

## Agentic Change Discipline Checklist

Every AI agent or software engineer modifying the Assessment Engine pipeline MUST verify this checklist before completing work:

### 1. Contract-First
- [ ] Pydantic schemas define rigorous validation hierarchies.
- [ ] Strict schemas guard technical stacks and field metrics against silent structural regressions.

### 2. Regression Prevention
- [ ] Epistemic intelligence engines are validated from clean baselines.
- [ ] Technical entities and brand identities are protected against dilution (FidelitySentinel).

### 3. Payload Modifications
- [ ] Resulting payloads validate against canonical schemas.
- [ ] Sovereign security tests (`zero-lockin-guard`) execute green.

### 4. Observability & FinOps
- [ ] Token consumption and cost telemetry are captured for remote AI API calls.
- [ ] Structured logs preserve agent telemetry.

### 5. Documentation
- [ ] Architecture documents are updated to reflect workflow and schema changes.
- [ ] The documentation governance validator certifies link and frontmatter integrity.

---

## Explicit Prohibitions (Anti-patterns)

Autonomous agents and engineers are strictly forbidden from the following anti-patterns:

1. **No External Network Dependencies in Automated Tests:** Tests requiring external network calls (DuckDuckGo, Kroki, Google Search) must reside exclusively under `tests/diagnostics/` prefixed with `diag_*.py`, never in standard `pytest` test suites.
2. **No Suppression of Static Analysis or Typing:** Never use `# type: ignore` or type casts (`Any`, `cast`) to bypass typing errors without an explicit, documented architectural rationale.
3. **No Dynamic sys.path Modification:** All module imports must resolve via the absolute namespace (`from assessment_engine.application...`). Never manipulate `sys.path` dynamically.
4. **No Commented-Out Dead Code:** Stale, commented-out code must be removed immediately. Git is the sole time machine.

## Common Failure Modes & Auto-Healing (Troubleshooting)

If the test suite or runtime execution fails, follow these auto-healing heuristics:

- **Error: `TemplateNotFound` (Jinja2):** Verify that the template file exists under `/templates/` at repository root and that runtime path constants in `runtime_paths.py` resolve correctly.
- **Error: `TypeError: string indices must be integers`:** Occurs when passing translated strings rather than structured objects to domain resolvers. Reconcile schema mapping.
- **Error: `Incompatible types in assignment` / Type Errors (MyPy):** Never bypass with `# type: ignore` or `cast()`. The engine enforces strict schema-driven typing. Reconcile by returning validated Pydantic models or applying explicit runtime type guards (`isinstance(...)`).
- **Error: `ModuleNotFoundError` or `ImportError`:** Caused by obsolete relative imports following directory restructuring. Use fully qualified namespace imports (`assessment_engine.application...`, `assessment_engine.infrastructure...`).
