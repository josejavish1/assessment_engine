#!/usr/bin/env python3
"""Executive Blueprint & Visual Cover Architecture Generator via gemini-4-argon.

Consults gemini-4-argon to formulate RFC 066:
1. Definitive FNMT CERES-style cover page visual design rules & AST implementation.
2. Complete architectural resolution of all 9 itemized user observations in Tomo 1 AS-IS.
3. Strict universal multi-tenant enterprise scalability (mid-market to global Tier 1, any vertical, any currency).
4. 100% Technical English codebase, zero hardcoded parameters, and zero antipatterns.
"""

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


def read_file_safe(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return f"[File {path.name} not found]"


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    observations_md = read_file_safe(
        REPO_ROOT / "docs/architecture/USER_OBSERVATIONS_ASIS_TOMO_1.md"
    )

    prompt = f"""
Role: Principal Enterprise Systems Architect, Advisory Partner at Gartner / McKinsey, and Global Design Director for Executive Deliverables.

OBJECTIVE:
Formulate the definitive, zero-bug, zero-antipattern architectural implementation plan (RFC 066) for the Consolidated Tomo 1 AS-IS Technical Diagnostic deliverable.

CONTEXT & MULTI-MODAL VISUAL EXTRACTION:
We have performed a side-by-side forensic visual audit comparing our current Tomo 1 cover against the official Tier-1 benchmark reference: `fnmt_ceres_as_is_consolidated_report_v1.1.pdf` (Fábrica Nacional de Moneda y Timbre / Real Casa de la Moneda).

CURRENT COVER DEFECTS IDENTIFIED:
1. Title is centered, crowded, and resembles an academic student paper rather than a Tier-1 executive advisory document.
2. Contains an artificial 3-tier heading ("MOLINS" in black, followed by "INFORME DE SITUACIÓN ACTUAL..." in blue, followed by "Tomo 1: Diagnóstico..." in italics).
3. Bottom metadata uses a clunky, heavy gray-boxed table with an aggressive 24pt left border ("Organización: Molins", "Fecha: ...", "Referencia: v6.0 - Gemelo Digital Soberano", "Clasificación: ...").
4. Visual breathing room (whitespace hierarchy) is poorly calibrated.

FNMT CERES VISUAL DESIGN RULES EXTRACTED:
1. Asymmetrical Left Alignment: The entire typography block is strictly LEFT-ALIGNED (NOT centered), creating a modern, high-end editorial feel.
2. Dual Header Space: The top header preserves ample whitespace for dual corporate branding (advisory firm logo on top-left, client entity badge/logo on top-right).
3. Vertical Position & Title Scale:
   - Starts at ~28-30% down the page (~130-150 pt vertical spacer).
   - Main title in Corporate Primary Blue (`#0072BC`), font size ~30-32 pt, clean sans-serif/Arial, line height 1.15.
   - Text layout across 3 elegant left-aligned lines:
     "Informe Consolidado de"
     "Situación Actual de la"
     "[Plataforma / Alcance Tecnológico]"
4. Entity Subtitle Hierarchy:
   - Sits immediately beneath the title (gap of ~16-20 pt), left-aligned.
   - Dark charcoal text (`#262626` / `#1A1A1A`), font size ~13-14 pt.
   - Line 1: Client Legal Entity Name (e.g., "Real Casa de la Moneda", "Molins S.A.").
   - Line 2: Division/Group Scope (e.g., "Fábrica Nacional de Moneda y Timbre", "Dirección de Infraestructura y Operaciones"), font size ~11-12 pt.
5. Large Whitespace Chasm:
   - Generous white breathing space (~240-280 pt spacer) between the subtitle and the bottom metadata.
6. Minimalist Single-Line Metadata:
   - Situated at ~78-80% down the page, left-aligned.
   - Font size ~11 pt, subtle charcoal (`#333333`).
   - Clean, borderless format: `{{formatted_date}} | Version {{version}}` (e.g., "02 diciembre 2025 | Version 1.1").
   - ZERO gray boxes, ZERO borders, ZERO clutter.

ADDITIONAL SYSTEMIC REQUIREMENTS FROM USER FORENSIC OBSERVATIONS:
Review the complete epistemic ledger below:
{observations_md}

NON-NEGOTIABLE CORE LAWS:
1. UNIVERSAL MULTI-TENANT ENTERPRISE SCALABILITY:
   - Code must work cleanly for ANY enterprise in the world: 50M$ mid-market to 50B$ global multinational, heavy industry, banking, healthcare, utilities, retail, tech.
   - Zero hardcoded client names ("Molins", "Secil"), site locations ("Sant Vicenç dels Horts"), specific vendors ("SimpliVity", "VMware", "SAP"), or fixed assumptions in Python code.
2. 100% TECHNICAL ENGLISH CODEBASE & LANGUAGE DECOUPLING:
   - All Python code, comments, docstrings, variable names, exceptions, and tests MUST be 100% Technical English.
   - Natural language deliverables are dynamically populated from `engine_config/locales.json` or localized payload metadata.
   - Language parameters must be mandatory (`doc_lang: str`), never optional with defaults.
   - Zero inline language ternaries (`if doc_lang == "es"`).
   - 100% mathematical symmetry in `locales.json` across all 6 supported locales (`es`, `en`, `pt`, `fr`, `de`, `ja`).

DELIVERABLE REQUIRED FROM YOU (GEMINI-4-ARGON):
Produce a comprehensive architectural blueprint and implementation specification (RFC 066):
1. Visual Cover Page Specification:
   - Exact AST node hierarchy, font sizes, margins, spacers, colors, and dynamic payload bindings to achieve identical aesthetics to FNMT CERES.
   - Comparison verification loop: How we will render the output to PNG (`pdftoppm`) and perform automated or visual parity comparison.
2. Complete Itemized Remediation Plan (Observations 2 through 9):
   - Detailed plan for each observation: root cause, exact localized wording in English and Spanish, and algorithmic/compiler updates.
   - Grounding and transparent decomposition of the 224.452 € emergency recovery figure.
   - Methodological justification paragraph for the CMMI 3.50 sector benchmark in Chapter 2.
   - Clear bridge reconciling the 29 Monte Carlo scenarios with the 10 domain rows in Table 4.
   - Positive capabilities ("Fortalezas Observadas") and richer narrative in Chapter 4 domain cards.
   - Dynamic sorting of Section 4.11 SPOF Matrix by descending criticality (`CRÍTICA` -> `ALTA` -> `MEDIA` -> `BAJA`).
   - Unification of the Legal Liability Disclaimer to match the canonical 4-paragraph disclaimer across all 20 tower annexes.
3. Step-by-Step Implementation & Verification Sequence:
   - Order of operations across configuration catalogs (`locales.json`), domain entities, and AST compilers.
   - Validation criteria ensuring 100% test pass rate across the full 706-test repository suite.
"""

    print(f"Requesting RFC 066 architecture blueprint from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_066_VISUAL_COVER_AND_EXECUTIVE_PERFECTION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated RFC 066 architecture blueprint: {out_file}")


if __name__ == "__main__":
    main()
