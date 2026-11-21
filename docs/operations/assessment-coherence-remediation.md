---
status: Verified
owner: product-engineering
source_of_truth:
- src/assessment_engine/application/run_tower_blueprint_engine.py
- src/assessment_engine/domain/schemas/blueprint.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: how_to
verification_mode: workflow
notes: Operational runbook and diagnostic triage protocol for resolving cross-artifact assessment coherence defects.
---
# Assessment Coherence Remediation Runbook

Canonical operational specification establishing the protocol, root-cause attribution, and remediation lifecycle for cross-artifact semantic and metric discrepancies across `assessment-engine`.

---

## 1. Governance Policy: Zero Metric Divergence (P0 Invariant)

Cross-artifact metric consistency is an absolute architectural invariant. Any numerical contradiction or narrative split-brain between deliverable layers (e.g., radar chart displaying maturity $2.0$ while executive summary claims $4.0$) constitutes a **blocking Priority 0 (P0) defect**:

$$\text{Blueprint Overall Score} \equiv \text{Annex Global Score} \equiv \text{Global Portfolio Heatmap Rating}$$

The platform operates on a **Top-Down Monistic Lineage**. The payload `blueprint_<tower>_payload.json` is the sole canonical source of truth for an evaluated domain. All downstream deliverables (`Anexo_*.docx`, `Tomo_1_*.docx`, `Account_Action_Plan_*.docx`) are immutable projections of this baseline.

---

## 2. Root-Cause Attribution Protocol

When an audit detects semantic or quantitative dissonance, operators and autonomous agents MUST isolate the defect using this deterministic decision tree:

```
[ Dissonance Detected ]
          |
          v
[ Inspect blueprint_<tower>_payload.json ]
          |
          +-------------------------------------------------------+
          |                                                       |
          v (Blueprint Values are Valid)                          v (Blueprint Values are Corrupted)
+------------------------------------+                  +------------------------------------+
| PRESENTATION LAYER DEFECT          |                  | DOMAIN / COMPUTATION DEFECT        |
| - Root Cause: docx_compiler.py or  |                  | - Root Cause: run_scoring.py,      |
|   payload_to_ast.py layout logic.  |                  |   build_case_input.py, or          |
| - Remedy: Refactor AST compiler    |                  |   SovereignPolicyEngine passes.    |
|   without mutating domain schemas. |                  | - Remedy: Fix upstream calculator. |
+------------------------------------+                  +------------------------------------+
```

### Prohibited Action:
**Direct manual editing of compiled binary `.docx` deliverables is strictly prohibited.** Manual document patches are ephemeral and wiped out on subsequent pipeline runs. All fixes must be codified in Python logic.

---

## 3. Standard Remediation Lifecycle

Autonomous agents resolving coherence defects MUST execute the following sequence:

### Step 1: Empirical Regression Test Formulation
Construct a failing unit or integration test in `tests/` reproducing the exact numerical or structural divergence:
```python
def test_annex_score_strictly_mirrors_blueprint():
    # Assert red state before modifying production code
    assert annex_payload.executive_summary.global_score == str(blueprint_payload.overall_score)
```

### Step 2: Surgical Upstream Refactoring
- If the defect is computational, correct the upstream scoring algorithm (`run_scoring.py`), evidence analyst (`run_evidence_analyst.py`), or policy rule (`policy_engine.py`).
- If the defect is presentational, correct the AST mapper (`payload_to_ast.py`) or OpenXML cell formatting logic (`docx_compiler.py`).

### Step 3: End-to-End Re-compilation & Verification
1. Clean the workspace scratchpad to prevent stale artifact reuse:
   ```bash
   rm -rf workspaces/<client_id>/<tower_id>/scratchpad/
   ```
2. Re-run the single-tower evaluation pipeline:
   ```bash
   python -m assessment_engine.application.run_tower_pipeline --tower T1 --client acme_corp
   ```
3. Assert that the regression test transitions to green and all quality gates pass.

---

## 4. Architectural Invariants for AI Agents

1. **Top-Down Authority:** Compilers must never override domain scores; presentation adapters are strictly read-only transformers.
2. **Mandatory Test First:** No coherence bug may be marked resolved without an accompanying automated test case in `tests/`.
3. **Zero-Entropy Rule:** Temporary debug artifacts generated during triage must isolate in `.artifacts/` and must never pollute `docs/` or source packages.
