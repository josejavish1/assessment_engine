---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/ai/documentation-governance.md
- pyproject.toml
- src/assessment_engine
- .github/workflows/quality.yml
last_verified_against: 2026-11-12
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
notes: Project entry point and onboarding index.
---
# Assessment Engine

`assessment-engine` is an actuarial intelligence engine and technical assessment compilation platform. It transforms unstructured client transcripts, audit questionnaires, and documentary evidence into a structured Epistemic Knowledge Graph, executes dual TCO + Open FAIR Monte Carlo simulations (10,000 iterations), and compiles executive and technical deliverables in OpenXML (.docx) and HTML formats.

---

## 1. System Topology & Directory Routing

```
assessment_engine/
├── src/assessment_engine/             # Core Backend (Hexagonal Architecture)
│   ├── domain/                        # Pure business models, actuarial logic, Pydantic schemas (NO I/O)
│   ├── ports/                         # Abstract interface ports (document_compiler.py, graph_analyzer.py)
│   ├── adapters/                      # OpenXML/HTML AST compilers, JSON converters, HTTP clients
│   ├── application/                   # Pipeline runners, CLI entrypoints, PO orchestrator, linters
│   ├── infrastructure/                # Graph persistence, Vertex AI / Gemini clients, runtime env
│   └── mcp_server.py                  # Model Context Protocol (FastMCP) server with SQLite job store
├── business_command_center/           # Executive War Room & Client Portal (Next.js 15, React, TS, Refine)
├── engine_config/                     # Actuarial Single Source of Truth (SSOT): rate cards, taxonomies, scales
├── templates/                         # Word (.docx) templates, HTML assets, and golden path scaffolding
├── tests/                             # Hermetic automated test suite (unit, integration, architecture)
└── docs/                              # Canonical Diataxis documentation governed by documentation-map.yaml
```

---

## 2. Type-State Pipeline Architecture

Data flows strictly across validated type boundaries from raw input to immutable deliverable:

1. **Ingestion & Evidence Graph:**
   - Raw transcripts & questionnaire answers $\to$ `RawTranscriptParser` / `EmpiricalResponseParser`
   - Facts and citations $\to$ `EpistemicGraphService` $\to$ `EvidenceLedger` with SHA-256 byte-span provenance.
2. **Actuarial Simulation (Dual TCO + FAIR):**
   - Priors $\to$ Conjugate Bayesian Inference (Gamma-Poisson for TEF, Beta-Binomial for VULN).
   - `PolicyEngine` executes 10,000 thread-safe Monte Carlo iterations $\to$ `ActuarialTensor` (ALE, SLE, ROSI).
3. **Immutable Document AST:**
   - `PayloadToASTBridge` maps actuarial tensors and tower findings into a declarative `DocumentAST`.
   - The presentation layer is strictly decoupled: view compilers format AST nodes without recalculating metrics.
4. **Hermetic OpenXML & HTML Compilation:**
   - `Volume1AsisASTCompiler` and `DocxCompiler` render validated DOCX deliverables. Zero PDF output.

---

## 3. Canonical Entrypoints & Execution Commands

### Prerequisites & Dependency Sync
```bash
# Requires Python 3.11 and uv
uv sync --all-groups
source .venv/bin/activate
uv run pre-commit install
```

### Pipeline Execution (CLI)
```bash
# Execute end-to-end tower assessment pipeline
uv run python -m assessment_engine.application.cli --client-id <client_slug> --towers all

# Execute isolated consolidated Tomo 1 compiler
uv run python scripts/build_full_client_delivery_suite.py --tomo1-only
```

### Model Context Protocol (MCP) Server
```bash
# Start MCP server exposing autonomous assessment tools to AI agents
uv run python -m assessment_engine.mcp_server
```

### Business Command Center (Next.js 15 Web Portal)
```bash
cd business_command_center
npm install
npm run dev
```

### Verification & Automated Testing
```bash
# Run the hermetic test suite (100% network isolated)
uv run pytest tests/

# Validate documentation governance, frontmatter, and schema synchronization
uv run pytest tests/functional/test_validate_documentation_governance.py tests/functional/test_compile_llms_full.py
```

---

## 4. Sovereign Architectural Invariants (Negative Constraints)

All autonomous agents and software engineers must strictly adhere to these non-negotiable constraints:

- **Language Decoupling:** All source code, docstrings, variable names, logs, tests, and commit messages MUST be 100% Technical English. Multilingual content resides solely in declarative catalogs (`engine_config/locales.json`).
- **Presentation-Layer Immunity:** Never calculate, adjust, or patch business metrics in presentation compilers (`payload_to_ast.py`, `docx_compiler.py`). Deficiencies must be resolved upstream in domain calculation engines.
- **Zero External Network in Tests:** Standard `pytest` runs must execute completely hermetic. Network-dependent diagnostics reside under `tests/diagnostics/` prefixed with `diag_*.py`.
- **Zero-Entropy Architecture:** Output artifacts must be isolated in `working/out/[client_id]/`. Never leave loose files, compressed `.zip` archives, or logs in the repository root.
- **SSOT Monism:** Probabilistic models are the sole authoritative source of truth. Hardcoded heuristic fallbacks or defensive bypasses (`if payload.get(...) is None`) that discard simulation data are prohibited.

---

## 5. Navigation & Canonical Documentation

- **Agent Constitution & Laws:** [`AGENTS.md`](AGENTS.md)
- **Agent Operational Adapters:** [`GEMINI.md`](GEMINI.md) | [`.cursor/rules/`](.cursor/rules/)
- **Documentation Master Map:** [`docs/README.md`](docs/README.md) and [`docs/documentation-map.yaml`](docs/documentation-map.yaml)
- **System Architecture Deep Dive:** [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md)
- **Contract & Payload Boundaries:** [`docs/contracts/payload-render-boundaries.md`](docs/contracts/payload-render-boundaries.md)
- **Troubleshooting & Operations Runbook:** [`docs/operations/troubleshooting-working.md`](docs/operations/troubleshooting-working.md)
