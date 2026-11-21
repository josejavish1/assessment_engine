---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/agentic_benchmarker.py
- src/assessment_engine/domain/schemas/rubric.py
- engine_config/frameworks
- tests/functional/test_agentic_benchmarker.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: code
notes: Technical specification of the Runtime Agentic Grounding and Evaluation (RAGE) benchmarking subsystem.
---
# Runtime Agentic Grounding & Evaluation (RAGE) Architecture

Canonical specification defining the architecture, execution lifecycle, evidence caching, and deterministic evaluation of the **Runtime Agentic Grounding & Evaluation (RAGE)** benchmarking engine (`agentic_benchmarker.py`).

---

## 1. Architectural Objective: Eradicating Stochastic Vibe-Scoring

RAGE replaces subjective or non-deterministic LLM scoring with an **empirical, evidence-grounded, multi-agent evaluation pipeline**. The system decouples factual research from numerical scoring: language models perform bounded extraction and cross-examination, while pure-Python rule evaluators compute quantitative maturity scores:

```
[ Framework Rubrics: engine_config/frameworks/*.json ]
                         |
                         v
+---------------------------------------------------------------------------------------+
| 1. OSINT RESEARCH AGENT (Vertex AI / Google Search)                                   |
| - Formulates queries from rubric query_template parameterized by client industry/geo  |
+---------------------------------------------------------------------------------------+
                         |
                         v (Download Binary Assets)
+---------------------------------------------------------------------------------------+
| 2. LOCAL EVIDENCE SNAPSHOTTER (EvidenceSnapshotter)                                   |
| - Downloads source PDFs/HTMLs to workspaces/<client>/evidence_cache/ (Anti Link-Rot)   |
+---------------------------------------------------------------------------------------+
                         |
                         v (Isolated Text Extract)
+---------------------------------------------------------------------------------------+
| 3. FORENSIC CROSS-EXAMINATION AGENT (Adversarial Verifier)                            |
| - Cross-checks extracted metric against local cached text to assert 100% fidelity    |
+---------------------------------------------------------------------------------------+
                         |
                         v (Extracted Metric: e.g., adoption = 68.5%)
+---------------------------------------------------------------------------------------+
| 4. DETERMINISTIC PYTHON EVALUATOR (No-LLM Math Engine)                                 |
| - Evaluates mathematical conditions (ThresholdMapping: condition="adoption >= 60.0")  |
| - Computes exact score and serializes benchmarks_snapshot.json                        |
+---------------------------------------------------------------------------------------+
```

---

## 2. Hexagonal Subsystem Mapping

The RAGE engine separates domain schemas, execution harnesses, and declarative rules:

### A. Domain Contracts (`src/assessment_engine/domain/schemas/rubric.py`)
- `FrameworkRubric`: Root container declaring standard regulatory specifications (e.g., ENS Alta, DORA, DAMA-DMBOK).
- `RubricRule`: Binds a technology tower to an OSINT query template, target evaluation variable, and threshold mapping rules.
- `ThresholdMapping`: Mathematical condition mapping an extracted variable to an exact maturity score (e.g., condition: `"adoption >= 50.0"`, score: `4.0`).

### B. Infrastructure Engine (`src/assessment_engine/infrastructure/agentic_benchmarker.py`)
- `AgenticRageBenchmarker`: Asynchronous orchestrator coordinating Vertex AI search grounding, physical asset download, and cross-examination.
- `EvidenceSnapshotter`: Downloads and content-hashes official PDF/HTML reference documents, isolating them in `workspaces/<client_id>/evidence_cache/` to eliminate network link-rot.

### C. Declarative Regulatory Frameworks (`engine_config/frameworks/`)
Isolated JSON profiles declaring analytical rules:
- `ens_alta.json`: Spanish National Security Scheme (Esquema Nacional de Seguridad - High Category).
- `google_dora.json`: EU Digital Operational Resilience Act.
- `dama_dmbok.json`: Data Management Body of Knowledge.

---

## 3. Resilience & Failsafe Controls

1. **Local Evidence Snapshotting:** Physical persistence of source documents ensures reproducibility during offline execution and prevents external web outages from interrupting compilation.
2. **Deterministic Python Scoring:** LLMs are strictly forbidden from emitting final numerical scores. Numerical scores derive solely from Python AST evaluation over extracted metrics.
3. **Graceful Fallback Handlers:** If external OSINT fails or rate limits trigger, the engine logs a warning, falls back to `default_score`, and flags the resulting blueprint for human review (`Needs Review`).

---

## 4. Architectural Invariants for AI Agents

1. **Decoupled Scoring:** All scoring transitions must evaluate via `ThresholdMapping` condition parsing in Python; LLM prompts must never contain scoring assignment instructions.
2. **Local Asset Retention:** Every external citation in `benchmarks_snapshot.json` must be backed by a physically cached binary in `evidence_cache/`.
3. **Zero-Hallucination Isolation:** The research agent formulating queries and the forensic agent cross-examining evidence must execute in decoupled, non-overlapping prompt contexts.
