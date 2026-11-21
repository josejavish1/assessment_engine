---
status: Verified
owner: docs-governance
source_of_truth:
- docs/contracts/payload-render-boundaries.md
- src/assessment_engine/adapters/compilers/docx_compiler.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: editorial
notes: ADR 0001 accepting exclusive Word DOCX monism and permanently disabling PDF and HTML presentations.
---
# ADR 0001: Exclusive Microsoft Word DOCX Deliverable Monism

- **Status:** Accepted
- **Date:** 2026-10-15
- **Deciders:** Principal Architect / Sovereign Engineering Board

---

## 1. Context & Problem Statement

Historically, enterprise advisory engagements produced multiple disjoint formats: PDF executive summaries, static HTML presentations, and Microsoft Word annexes. Maintaining three separate rendering pipelines (`weasyprint` for PDF, bespoke Jinja templates for HTML, and OpenXML for DOCX) caused severe maintenance overhead, visual regressions, and cross-format metric divergence.

Furthermore, enterprise clients require editable artifacts to integrate assessment findings into internal corporate decks, board papers, and procurement RFPs. PDF deliverables proved rigid, while static HTML presentations lacked corporate distribution channels.

---

## 2. Decision Drivers

- **Zero Format Divergence:** Eliminate bugs where numbers in a PDF or HTML dashboard differed from the formal Word report.
- **Client Editability:** Enterprise stakeholders mandate editable Microsoft Office formats (`.docx`).
- **Pipeline Simplicity & FinOps:** Stripping headless browser engines (Chromium/Puppeteer) and PDF binary libraries drastically reduces Docker image sizes, build times, and runtime vulnerabilities.

---

## 3. Considered Options

| Option | Pipeline Complexity | Client Editability | Metric Divergence Risk | Verdict |
|---|:---:|:---:|:---:|:---:|
| **Option 1: Multi-Format (HTML + PDF + DOCX)** | Critical (3 renderers) | Medium | High (Triple split-brain) | Rejected |
| **Option 2: PDF Primacy** | High (Headless Chrome) | Zero | Low | Rejected |
| **Option 3: Exclusive Word DOCX Monism** | Low (Single AST compiler) | High (Native MS Word) | Zero (SSOT AST) | **Accepted** |

---

## 4. Decision Outcome

**Chosen Option: Option 3 (Exclusive OpenXML DOCX Monism).**

All customer-facing deliverables compile strictly to Microsoft Word (`.docx`). PDF generation and ephemeral HTML web presentations are permanently disabled.

### Positive Consequences:
- **Single Source of Presentation Truth:** All layout rules, table styles, and typography invariants reside in one compiler suite (`docx_compiler.py`).
- **Zero Headless Browser Overhead:** No Puppeteer, Chromium, or WeasyPrint system dependencies in the container runtime.
- **Deterministic CI:** Automated tests assert document validity via `python-docx` without rendering visual DOMs.

### Negative Consequences & Trade-offs:
- Operators must use Microsoft Word or LibreOffice to visually inspect output binaries.
- Next.js portal (`business_command_center`) streams DOCX binaries directly for local opening rather than rendering rich inline document previews.
