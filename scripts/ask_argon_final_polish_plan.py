#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 7: Final Polish & Linguistic Harmonization Master Plan.

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Multi-phase phased implementation plan with strict Quality Gates.
3. Universal scalability and zero hardcoding (multi-tenant agnostic).
4. Pure Clean Architecture.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def generate_final_polish_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: FINAL POLISH & LINGUISTIC HARMONIZATION MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & CONTEXT:
We have resolved all critical mathematical, scale, and topological invariants in the Assessment Engine.
However, a final forensic audit identified 5 remaining qualitative, epistemic, and linguistic flaws that must be resolved to achieve Tier-1 World Class Certification. We need a definitive architectural plan to resolve these systematically for ALL future clients.

THE 5 BLOCKING FLAWS:

1. LEGAL LIABILITY RISK (Audit vs. Assessment Lexicon):
   - Current Flaw: The generated text occasionally uses terms like "auditoría de campo", "peritaje", or "verificación empírica", which contradicts the legal disclaimer stating this is a "remote Fast Assessment without configuration inspection".
   - Goal: Systematically replace all audit/forensic lexicon with safe consultative terms ("evaluación diagnóstica", "sesión de contraste", "relevamiento arquitectónico") across prompts and UI locales.

2. CROSS-TOWER OWNERSHIP LEAKAGE:
   - Current Flaw: Tower 2 (Compute) sometimes diagnoses Network routing (Tower 3), ITSM SLAs (Tower 7), or FinOps (Tower 8), leading to double scoring.
   - Goal: Enforce strict boundary scopes in the Pillar Architect Prompt. Cross-tower topics must only be referenced as "operational dependencies" without diagnosing their maturity.

3. OPEN FAIR ACTUARIAL TRACEABILITY (Vulnerability Justification):
   - Current Flaw: The cards now correctly show TEF x Vuln = LEF, but an auditor cannot see why Vulnerability is set to 80% or 95%.
   - Goal: Inject a methodological footnote or explanation in the AST compiler (Section 4.2) that clarifies that Vulnerability ratios are mathematically derived from the CMMI Maturity Level (e.g., Level 1 implies absence of automated controls, hence 80-95% vulnerability to threat manifestation).

4. ELEGANT EVIDENCE TRACEABILITY:
   - Current Flaw: The auditor requested labeling each claim as [DECLARED], [CONTRASTED], or [EVIDENCED].
   - Goal: Hardcoded visual tags pollute the executive aesthetics. We must engineer a prompt directive that seamlessly weaves epistemic attribution into the narrative prose (e.g., "As declared by the engineering team..." vs "Observed in architectural diagrams...").

5. EXECUTIVE SUMMARY BUSINESS CONTEXT GROUNDING:
   - Current Flaw: The executive summary sometimes reads as a generic IT summary rather than hitting the client's actual pain points (e.g., VMware Broadcom licensing expiration, physical RAM saturation, lean 5-person team).
   - Goal: Update the Orchestrator Prompt to enforce that the top 3 contextual business drivers (extracted from `client_intelligence.json` CEO agenda or interview transcripts) MUST anchor the opening paragraph of the executive summary.

CORE INVARIANTS:
- 100% Technical English in code, variables, classes, docstrings, comments, logs, and prompt files.
- Zero Hardcoding: No client names or specific numbers in code. Must apply equally to a $50M retailer or a $100B bank.
- Zero Regressions: Must pass all 47 existing architecture and actuarial tests.

YOUR DELIVERABLE:
Write a comprehensive, exhaustive, publication-grade MASTER ARCHITECTURAL BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE7_FINAL_POLISH_MASTER_PLAN.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO: Addressing the 5 flaws.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 1: Lexical Sanitization & Legal Liability Shielding (Prompts & Locales).
   - Phase 2: Cross-Tower Ownership Enforcement (Prompt Engineering).
   - Phase 3: Open FAIR Vulnerability Traceability (AST Compiler).
   - Phase 4: Epistemic Attribution Flow (Prompt Engineering).
   - Phase 5: Business Context Anchoring in Executive Summary (Prompt Engineering).
3. QUALITY GATES & VERIFICATION ORACLES: Deterministic verification steps.
"""

    print("Sending prompt to Gemini-4-Argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE7_FINAL_POLISH_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    generate_final_polish_master_plan()
