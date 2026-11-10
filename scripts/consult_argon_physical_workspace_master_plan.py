#!/usr/bin/env python3
"""Consult Gemini-4-Argon for a comprehensive Master Architecture Plan for physical workspace storage and deliverable compilation."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

ARGON_PROMPT = """You are 'gemini-4-argon', Supreme Cognitive Arbiter, Chief Enterprise Architect, and Master of Software Integrity.

# CONTEXT & STRATEGIC MISSION

Our project currently has a dual identity:
1. **The Core Engine (Battle-Tested CLI & Batch Pipeline):**
   - In our offline workflow, the entire platform operates from **exactly two input artefacts**:
     - **File 1 (Context Dossier / Transcript):** The interview session transcript or notes document (e.g. `source_docs/molins/260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx`).
     - **File 2 (Technical Assessment Responses):** The forensic questionnaire response matrix (e.g. `Preguntas Fast Assessment contestadas.xlsx` or `assessment_responses.txt`).
   - The engine runs `run_intelligence_harvesting.py`, builds the canonical `ClientDossierV3` at `working/[client_slug]/client_intelligence.json`, extracts evidence fragments into `working/[client_slug]/evidence_vault.json`, builds a recursive RAPTOR summary tree (`raptor_tree.json`), calculates the actuarial FAIR loss distribution (10,000 Monte Carlo runs), and compiles:
     - **Tome 1: Consolidated AS-IS Diagnostic & TO-BE Roadmap (.docx)**
     - **Up to 10 Specialized Technical Annexes (.docx)** in `working/out/[client_slug]/`.

2. **The New Self-Service Web Cockpit (Real-Time Interactive Platform):**
   - The strategic objective is to enable any enterprise client worldwide (from mid-market to top tier 1 global conglomerates in any vertical) to execute this entire journey through our modern web portal (`http://[host]:8000`), rather than requiring weeks of manual consultant meetings.
   - The portal must capture or ingest both artefacts in real time, persist them strictly in the canonical physical workspace structure (`working/[client_slug]/`), and orchestrate the authentic compilations asynchronously.

# THE RIGID ARCHITECTURAL CONSTRAINTS

1. **100% Technical English Codebase:**
   - Absolute zero Spanish in Python source code, TypeScript/TSX code, comments, docstrings, variable names, functions, exceptions, or schemas. Spanish is strictly an i18n data payload in `engine_config/locales_ui.json` and client deliverable documents (.docx).
2. **Zero Hardcoding & Universal Multi-Tenancy:**
   - No hardcoded customer names, no hardcoded if-statements (`if "molins"`), no inline ternary switches for countries or industries.
   - Must scale universally to any enterprise worldwide:
     - Heavy Manufacturing (e.g. Cementos Molins in Spain: EUR, NIS2, CER, IEC 62443, ISO 27001).
     - Digital FinTech / Challenger Banks (e.g. Starling Bank in UK: GBP, FCA/PRA Operational Resilience, DORA).
     - Healthcare & Hospital Networks (e.g. Rede D'Or in Brazil: BRL, LGPD, ANVISA, CFM).
     - Logistics & Global Supply Chains (e.g. Geodis in France: EUR, NIS2, ISO 27001).
     - Mid-market industrial operators to Fortune 50 mega-holdings.
3. **Physical Workspace Storage Supremacy:**
   - The web server must NOT maintain transient, volatile in-memory databases as single points of failure.
   - All state must be persisted in the canonical directory: `working/[client_slug]/` (`client_intelligence.json`, `evidence_vault.json`, `digital_twin_state.json`, `raptor_tree.json`, and `working/out/[client_slug]/`).
4. **Supreme Deliverable Quality (Actuarial & Forensic Rigor):**
   - Output documents must be 100% native Word (.docx) files, fully editable, mathematically verified, with zero placeholder leaks.

# YOUR ARCHITECTURAL BLUEPRINT MANDATE

Design a comprehensive, phased, zero-defect Master Implementation Plan:

### 1. Physical Workspace Integration Architecture
- How should `server.py` and the backend services manage `working/[client_slug]/`?
- Define the exact schema contracts for:
  - `client_intelligence.json` (ClientDossierV3 protocol).
  - `evidence_vault.json` (Evidence ledger & transcripts).
  - `digital_twin_state.json` (Real-time maturity ratings, notes, and answers per tower).
- How is atomic, safe file persistence guaranteed (preventing file corruption during concurrent operations)?

### 2. Dual-Mode Capture of the 2 Core Artefacts
- **Artefact 1 (Context Dossier):**
  - Path A (Interactive Real-Time): How the web session pre-harvests the profile, allows perimeter selection (Corporate Group vs. Subsidiary/Plant), and records executive context notes.
  - Path B (Document Ingestion): How a user can drag and drop an existing transcript or meeting notes document (`.docx`, `.txt`, `.pdf`), invoking the existing document extraction pipeline.
- **Artefact 2 (Domain Assessment Responses):**
  - Path A (Interactive Cockpit): Live calibration slider (1.0 to 5.0) and key forensic questions per domain.
  - Path B (Spreadsheet / Matrix Upload): Drag and drop of an existing completed questionnaire (`.xlsx` or `.txt`), automatically parsing scores into `digital_twin_state.json`.

### 3. Execution Pipeline & Real-Time Synthesis Trigger
- When the user clicks "Synthesize & Generate Deliverables" in Tab 3/4:
  - How does `server.py` trigger the real compilation pipeline (`build_client_delivery_suite.py` or `tomo_asis_ast_compiler.py`)?
  - How is progress communicated to the frontend (polling, SSE, or WebSocket)?
  - How does `GET /api/assessment/deliverables/{filename}` stream the real `.docx` files generated in `working/out/[client_slug]/`?

### 4. Phased Implementation Roadmap
- Break down the engineering work into sequential, test-driven phases.
- Detail the test oracles (including automated E2E Playwright verification across Spain, UK, and Brazil tenants).

Deliver the Master Plan in 100% Technical English with supreme architectural rigor and zero fluff.
"""

def main() -> None:
    print(f"Submitting Master Architecture Plan Consultation to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=ARGON_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_PHYSICAL_WORKSPACE_INTEGRATION_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")
    print(f"Master Architecture Plan successfully generated and saved to: {out_file}")
    print("\n--- FIRST 60 LINES OF ARGON MASTER PLAN ---")
    print("\n".join(report.splitlines()[:60]))

if __name__ == "__main__":
    main()
