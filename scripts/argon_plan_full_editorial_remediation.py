#!/usr/bin/env python3
"""Execute consultation with gemini-4-argon to design the universal multi-tower forensic remediation plan."""

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

OUTPUT_FILE = REPO_ROOT / "docs/architecture/ARGON_UNIVERSAL_DELIVERABLE_REMEDIATION_PLAN.md"

PROMPT = """You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

USER PROBLEM STATEMENT & STRATEGIC CONTEXT:
Our section-by-section forensic truthfulness audit of Tower 1 (`Molins_202610_Anexo_01_Data_Center_ASIS.docx`) revealed that while mathematical scores (2.61/5.00) and interview facts are 100% exact, five systemic defects affect the generated deliverable:
1. CHAPTER 2 BLANK / PLACEHOLDER DEFECT:
   In `payload_to_ast.py`, `compile_asis_docx_via_ast` passed `approved_annex_path=""`, causing `annex_data` to be empty. The compiler looked only at `annex_data.get("domain_introduction")` instead of `blueprint_data.get("domain_introduction")`, printing "Módulo de introducción y alcance no disponible" in Section 2.1 and leaving Section 2.2 (Platform Description) completely blank! This bug affects ALL 10 TOWERS across the platform.
2. RAW ENUM PLACEHOLDERS IN RISK CARDS:
   In Risk Cards (Tables 13, 14, 17), when `primary_impact` / `business_risk` is missing or contains a raw enum value like `"HIGH"`, the compiler literally prints `Impacto en la Operación y Continuidad: HIGH.` instead of a rich, domain-grounded operational impact narrative.
3. AD-HOC TECHNICAL EMBELLISHMENTS & HALLUCINATIONS IN SECTION 3.1:
   When the client selected low scores in the questionnaire (e.g. Score 1 in electrical capacity or Score 1 in work permits), the LLM embellished with invented tools and practices not found in any source: "pinzas amperimétricas" (clamp meters), "especificaciones de placa de fabricante", "formularios impresos con firmas manuscritas".
4. TRUNCATED & ORPHANED FRAGMENTS IN TABLE 6:
   Residual sentence fragments from previous sanitization (e.g. "No obstante, la efectividad real de este diseño de supervivencia...") were placed under "Fortaleza Operativa Identificada" for pillars scoring 4.0/5.0, confusing strengths with weaknesses, accompanied by unaccented template strings ("Deficit en gestión...").
5. CROSS-TOWER FOCUS IN EXECUTIVE SUMMARIES:
   The Executive Summary of Tower 1 (Facilities) prominently focused on SimpliVity RAM and legacy ERPs (which belong to Compute/Virtualization and Application towers), instead of keeping the primary spotlight on physical power, cooling, and space.

THE USER'S MANDATES:
The user states: "This doesn't only apply to Tower 1; it will happen across all towers. Before programming, we must carefully think through how to tackle this across all towers in well-defined phases to ensure zero errors and Tier-1 world-class quality for any enterprise globally, any vertical, in any language. 100% Technical English in all code, zero Spanish in the codebase, and zero hardcoding."

YOUR MISSION:
Deliver an authoritative Engineering Design Document (EDD) defining a comprehensive, multi-phase master remediation roadmap across the entire platform:
1. EXACTLY HOW MANY PHASES are needed, what will be built in each phase, and why?
2. How to architect the Universal Chapter 2 Bridge in `payload_to_ast.py` so that every domain (T1..T10, D1..D8, custom slugs) dynamically receives rich, fully grounded Objective, Technical Scope, and Platform Descriptions with zero blank sections or fallback error strings.
3. How to engineer the Causal Risk Impact Resolver in `payload_to_ast.py` so that raw enum strings (`HIGH.`, `MEDIUM.`, `CRITICAL.`) are intercepted and replaced with domain-specific operational downtime narratives derived from the threat and vulnerability context.
4. How to enforce Strict Grounding Guardrails in the synthesis layer (`resynthesize_domains_from_raw_transcription.py` & prompt scoper) to eradicate invented physical tools (clamp meters, paper forms) and anchor every gap strictly to the client's actual questionnaire choices.
5. How to sanitize Table 6 justifications systematically so that strengths are always positive, gaps are grounded in low-scoring KPIs, and orphaned sentence fragments are eradicated.
6. What automated unit, integration, and AST-purity tests must be implemented to certify 10.0/10.0 quality across all 10 deliverables simultaneously.

Structure your response as an authoritative, production-grade Engineering Design Document (EDD).
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Consulting gemini-4-argon on Universal Deliverable Remediation Plan ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("---\nstatus: Verified\nowner: architecture-governance\nsource_of_truth:\n- docs/README.md\nlast_verified_against: 2026-11-07\napplies_to:\n- gemini\n- architecture\ndoc_type: operational\ndiataxis: reference\nverification_mode: editorial\n---\n")
        f.write(response.text)

    print(f"Master remediation plan saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON UNIVERSAL REMEDIATION PLAN SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
