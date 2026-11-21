---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/application/build_case_input.py
- src/assessment_engine/application/build_evidence_ledger.py
- src/assessment_engine/application/run_scoring.py
- src/assessment_engine/application/run_evidence_analyst.py
- src/assessment_engine/application/run_tower_pipeline.py
- src/assessment_engine/application/run_tower_blueprint_engine.py
- src/assessment_engine/application/run_executive_annex_synthesizer.py
- src/assessment_engine/application/run_global_pipeline.py
- src/assessment_engine/application/build_global_report_payload.py
- src/assessment_engine/application/run_commercial_pipeline.py
- src/assessment_engine/application/run_commercial_refiner.py
- src/assessment_engine/application/run_intelligence_harvesting.py
- src/assessment_engine/application/generate_tower_radar_chart.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: Canonical inventory, classification, and lineage of all workspace and working directory artifacts.
---
# Workspace & Execution Artifacts Map

Canonical specification defining the directory structure, artifact classifications, data lineages, and authority hierarchies within `workspaces/<client>/` and `working/<client>/`.

---

## 1. Directory Topology

Execution artifacts accumulate across client-specific workspace vaults:

```text
workspaces/<client_slug>/
├── client_intelligence.json                      [Shared Corporate Dossier (V3)]
├── global_report_payload.json                    [Global Consolidated SSOT]
├── commercial_report_payload.json                [Commercial Opportunity SSOT]
├── Tomo_1_Diagnostico_ASIS_<client>.docx        [Global Executive Deliverable]
├── Account_Action_Plan_<client>.docx             [Commercial Strategy Deliverable]
└── <TOWER_ID>/                                   [Single-Tower Execution Sandbox]
    ├── case_input.json                           [Normalized Case Telemetry]
    ├── evidence_ledger.json                      [Grounded Evidence Ledger]
    ├── scoring_output.json                       [Quantitative Maturity Scores]
    ├── findings.json                             [Grounded Gap Findings]
    ├── blueprint_<tower>_payload.json            [Tower Canonical SSOT]
    ├── approved_annex_<tower>.template_payload.json [Executive Presentation Payload]
    ├── pillar_radar_chart.generated.png          [Quantitative Maturity Vector Visual]
    ├── Anexo_<tower>_ASIS_<client>.docx         [Compiled Technical Annex]
    └── Blueprint_Transformacion_<tower>_<client>.docx [Compiled Blueprint Deliverable]
```

---

## 2. Artifact Classification Matrix

Artifacts are categorized into four epistemic tiers:

| Epistemic Tier | Concrete Artifacts | Invariant & Authority Rule |
|---|---|---|
| **Tier 1: Canonical SSOT Payloads** | `blueprint_<tower>_payload.json`, `global_report_payload.json`, `commercial_report_payload.json` | Authoritative single source of truth for each pipeline layer. Downstream stages must derive from these payloads without recalculation. |
| **Tier 2: Grounded Telemetry** | `client_intelligence.json`, `case_input.json`, `evidence_ledger.json`, `scoring_output.json`, `findings.json` | Deterministic baseline data feeding canonical synthesis engines. Immutable once generated. |
| **Tier 3: Presentation Intermediates**| `approved_annex_<tower>.template_payload.json`, `pillar_radar_chart.generated.png` | Formatted representations prepared specifically for OpenXML AST compilers. Must conform strictly to presentation schemas. |
| **Tier 4: Compiled Deliverables** | All `.docx` binary files | End-user documents serialized via `docx_compiler.py` and `tomo_asis_ast_compiler.py`. Strictly outputs; never parsed as inputs. |

---

## 3. End-to-End Artifact Lineage Graph

### A. Single-Tower Value Stream
$$\begin{matrix}
\text{Raw Input Texts} \\
\Downarrow \\
\texttt{case\_input.json} \quad \longrightarrow \quad \texttt{evidence\_ledger.json} \quad \longrightarrow \quad \texttt{scoring\_output.json} \quad \longrightarrow \quad \texttt{findings.json} \\
\Downarrow \\
\mathbf{blueprint\_<tower>\_payload.json} \quad \text{(SSOT)} \\
\Downarrow \\
\texttt{approved\_annex\_<tower>.template\_payload.json} \quad + \quad \texttt{pillar\_radar\_chart.generated.png} \\
\Downarrow \\
\mathbf{Anexo\_<tower>\_ASIS.docx} \quad + \quad \mathbf{Blueprint\_Transformacion\_<tower>.docx}
\end{matrix}$$

### B. Global Consolidation Value Stream
$$\begin{matrix}
\bigcup_{i=1}^N \mathbf{blueprint\_T_i\_payload.json} \quad + \quad \texttt{client\_intelligence.json} \\
\Downarrow \\
\mathbf{global\_report\_payload.json} \quad \text{(Refined in-place by run\_executive\_refiner.py)} \\
\Downarrow \\
\mathbf{Tomo\_1\_Diagnostico\_ASIS\_<client>.docx}
\end{matrix}$$

### C. Commercial Activation Value Stream
$$\begin{matrix}
\mathbf{global\_report\_payload.json} \quad + \quad \bigcup_{i=1}^N \mathbf{blueprint\_T_i\_payload.json} \quad + \quad \texttt{rate\_card.json} \\
\Downarrow \\
\mathbf{commercial\_report\_payload.json} \quad \text{(Multi-agent presales synthesis)} \\
\Downarrow \\
\mathbf{Account\_Action\_Plan\_<client>.docx}
\end{matrix}$$

---

## 4. Architectural Invariants for AI Agents

1. **Payload Primacy:** AI agents must query and mutate JSON payloads, never compiled `.docx` files. Word documents are write-only compiled artifacts.
2. **Blueprint-Only Handover:** Handover across pipeline boundaries operates exclusively via modern blueprint schemas. Direct reliance on legacy section files is strictly prohibited.
3. **Zero-Entropy Isolation:** All intermediate calculations and scratchpad files must isolate within `workspaces/<client_slug>/` and must never pollute root source folders or `docs/`.
