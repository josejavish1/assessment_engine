---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/domain/schemas/annex_synthesis.py
- src/assessment_engine/application/run_executive_annex_synthesizer.py
- src/assessment_engine/adapters/compilers/payload_to_ast.py
- docs/contracts/payload-render-boundaries.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical technical specification of the executive Tower Annex document structure and AST layout.
---
# Tower Annex Technical Design Specification

Canonical specification defining the editorial structure, section hierarchy, deterministic calculations, and OpenXML AST layout for the **Tower Technical Annex** deliverable (`Anexo_<tower>_ASIS_<client>.docx`).

---

## 1. Architectural Role & Ingestion Flow

The Tower Technical Annex bridges deep engineering diagnostics and executive decision-making. It derives deterministically from the single-tower blueprint SSOT:

```
[ blueprint_<tower>_payload.json (SSOT) ]
                    |
                    v (run_executive_annex_synthesizer.py)
[ approved_annex_<tower>.template_payload.json (AnnexPayload) ]
                    |
                    v (payload_to_ast.py)
[ Document AST: Headings, Tables, KPI Boxes, Callouts ]
                    |
                    v (docx_compiler.py)
[ Anexo_<tower>_ASIS_<client>.docx (Word OpenXML Binary) ]
```

### Core Derivation Rules:
1. **Blueprint Immutability:** The annex synthesizer inherits quantitative scores, pillar bands, risks, and initiatives from the parent blueprint without mutation.
2. **Deterministic Layout:** AST compilers (`payload_to_ast.py`, `docx_compiler.py`) assemble visual elements deterministically; presentation modules are strictly prohibited from recalculating business metrics.
3. **Format Monism:** Compiled output is strictly Microsoft Word (`.docx`).

---

## 2. Standard 8-Section Document Structure

The OpenXML AST compiler serializes the Tower Annex across eight formal sections:

| Section Number & Title | Section Scope | Primary Visual Component | Data Source in `AnnexPayload` |
|---|---|---|---|
| **1. Executive Summary** | High-level synthesis, overall CMMI score, maturity band, target maturity, and 3 strategic takeaways. | Callout KPI Box & Metric Grid | `executive_summary`, `overall_score`, `maturity_band` |
| **2. Pillar Maturity Profile** | Cross-pillar maturity comparison, identifying strongest pillar, weakest pillar, and structural bottlenecks. | Vector Radar Chart (`.png`) & Compact Scorecard Table | `pillar_scores`, `radar_chart_path` |
| **3. AS-IS Diagnostic** | Factual baseline assessment, operational strengths, and discovered architectural liabilities. | Structured Narrative & Diagnostic Table | `asis_narrative`, `strengths`, `liabilities` |
| **4. Priority Risk Matrix** | Consolidated operational, financial, and regulatory risks ranked by severity. | Severity-Colorized Risk Matrix Table | `risks` (ranked by risk score) |
| **5. Target State & Gaps** | 3-year target architecture, guiding architectural principles, and pillar-by-pillar gap analysis. | Comparative Gap Matrix (`AS-IS` vs `Target` vs `Gap`) | `target_vision`, `gap_analysis` |
| **6. Strategic Initiatives** | Actionable remediation roadmap with initiative sizing ($S, M, L, XL$), delivery horizon ($H_1, H_2, H_3$), and dependencies. | Phased Roadmap Schedule & Initiative Cards | `initiatives` (grouped by wave) |
| **7. Executive Conclusion** | Final strategic verdict, priority investment areas, and board-level recommendations. | Executive Conclusion Box | `conclusion`, `strategic_priorities` |
| **8. Open Observations** | Unverified hypotheses and missing evidence items flagged for client validation. | Formal Itemized Checklist | `open_observations` |

---

## 3. Division of Responsibilities: Deterministic vs. Generative

The pipeline strictly delineates mathematical computation from bounded semantic synthesis:

### A. Deterministic Engine Responsibilities:
- Quantitative scoring aggregation: `overall_score`, individual pillar ratings.
- Qualitative maturity band mapping: translation of numeric scores to discrete bands (`Initial`, `Managed`, `Defined`, `Quantitatively Managed`, `Optimizing`) via `maturity_band.py`.
- Vector radar chart rendering: multi-axis matplotlib figure generation via `generate_tower_radar_chart.py`.
- Initiative dependency topological sorting and wave allocation ($H_1, H_2, H_3$).
- Table formatting, cell background tinting, and typography layout in OpenXML.

### B. Generative Language Model Responsibilities:
- Executive headline formulation and elevator pitch synthesis.
- Strategic business framing of technical gaps and operational risks.
- Contextualizing findings against the client's corporate agenda and active vendor programs.
- Drafting C-level conclusion narratives.

---

## 4. Typography & Layout Invariants

1. **Strict Hyphen Rule:** All generated Word XML files must enforce standard ASCII short hyphens (`-`, 0x2D); em-dashes (`—`) and en-dashes (`–`) are systematically stripped by `docx_compiler.py`.
2. **Page-Budget Integrity:** Sections must maintain compact spacing to ensure executive scannability; narrative paragraphs exceeding 5 lines without visual break are penalized by style linters.
3. **Data Grid Density:** Technical data (scores, gaps, initiatives) must format inside structured OpenXML table grids with shaded headers rather than bulleted lists.
