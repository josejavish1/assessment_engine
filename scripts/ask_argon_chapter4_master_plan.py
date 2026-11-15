#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Definitive, Multi-Phase, Zero-Defect
Universal Chapter 4 Master Implementation Blueprint.

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Multi-phase phased implementation plan (Phases 1 to 5) with strict Quality Gates.
3. Universal scalability: Any industry vertical, any enterprise size ($50M to $100B+), any maturity (CMMI 1 to 5), 6 output languages.
4. Zero hardcoding: All rates, thresholds, and profiles loaded dynamically from ConfigurationRegistry.
5. Absolute code purity: Pure Clean Architecture / Hexagonal Architecture without split-brain or heuristics.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def generate_chapter4_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: DEFINITIVE PHASED CHAPTER 4 MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, the Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & NON-NEGOTIABLE OPERATIONAL CONSTRAINTS:
We are re-architecting Chapter 4 ("Evaluación Económica de Riesgos de Infraestructura y Coste del Statu Quo" / "Infrastructure Risk Economic Evaluation & Cost of Inaction") across the Assessment Engine's 10 Specialist Domain Annexes.
The user demands the definitive, production-grade, multi-phase engineering plan that ensures this engine becomes the undisputed #1 Global Solution in technical due diligence (surpassing McKinsey, Gartner, Bain, and Big-4).

CORE ARCHITECTURAL INVARIANTS:
1. Multi-Phase Phased Architecture: The implementation MUST be organized into clearly bounded, sequential phases (e.g., Phase 1 to Phase 5), each featuring an explicit Quality Gate, Verification Oracle, and Pre-Flight Invariant.
2. Universal Scale & Vertical Agnosticism: The engine must adapt seamlessly to:
   - Any Enterprise Scale: Mid-market ($50M revenue, 200 employees) to Global Mega-Caps ($100B+ revenue, 250,000 employees).
   - Any Industry Vertical: Discrete & Process Manufacturing (OT/SCADA), Banking & Financial Markets, Healthcare & Clinical Systems, Retail & E-Commerce, Critical Energy & Utilities, Telecoms, and SaaS / Cloud-Native.
   - Any Maturity Level: CMMI Level 1 (Initial / Chaotic) to CMMI Level 5 (Optimizing / Resilient).
   - Any Deliverable Language: English, Spanish, Portuguese, German, French, Japanese.
3. 100% Technical English Codebase: Zero Spanish in code, variables, classes, docstrings, comments, logs, exceptions, prompts, or test cases. Spanish (and other languages) exist EXCLUSIVELY as externalized localized data (e.g. in `engine_config/locales.json`).
4. Zero Hardcoding: Absolutely no inlined corporate names, currency symbols, hardcoded labor rates, fixed disruption ratios, or static regulatory lists in Python code. Everything must be resolved dynamically through `ConfigurationRegistry`, `RateCardCatalog`, `EnterpriseRegistry`, and `RegulatoryFrameworkCatalog`.
5. Actuarial Legitimacy (Open FAIR Monism): Decouple Chronic Operational Drag (COD = Toil + Contractual Escalation) from Probabilistic Event Risk (ALE = LEF * LM). Eradicate the "actuarial fallacy" by enforcing order-of-magnitude significant rounding (e.g., intervals like [55.000 €, 80.000 €]) and eliminating false precision (cents/single euros).
6. Total Split-Brain Eradication: Section 4.1 (Cost of Inaction), Section 4.2 (Strategic Risk Concentration & 5x5 Heatmap), and Section 4.3 (Technical Risk Cards) must derive from ONE SINGLE immutable Pydantic V2 domain model (`Chapter4SynthesisPayload`). Zero divergent calculation paths.
7. Executive Editorial Elegance: Permanently eradicate the 4 didactic textbook tables (defining TEF/LM) and cryptic machine codes (RVS01, RVS02). The 5x5 Heatmap must be populated with human-readable physical risk titles.

YOUR DELIVERABLE:
Write the complete, exhaustive, publication-grade MASTER BLUEPRINT in clean Markdown format to be saved at `docs/architecture/ARGON_UNIVERSAL_CHAPTER_4_MASTER_PLAN.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY & ACTUARIAL MANIFESTO: Resolving the Open FAIR legitimacy question, explaining the separation between chronic operational toil and probabilistic failure events.
2. UNIVERSAL MATHEMATICAL FORMULATION:
   - Dynamic CMMI maturity loss equations (Level 1 to Level 5).
   - Enterprise scale normalization (revenue and downtime hourly cost derivation).
   - Portfolio sub-additivity factor for overlapping shared failure domains.
   - The Actuarial Significant Figures Rounding Policy.
3. THE 5-PHASE INDUSTRIAL EXECUTION ROADMAP:
   - Phase 1: Declarative Pydantic V2 Domain Schemas & Mathematical Engine (`Chapter4SynthesisPayload`, `Chapter4ActuarialEngine`).
   - Phase 2: Upstream Domain Synthesizer & Dynamic CMMI/Vertical Calibration (`Chapter4Synthesizer`).
   - Phase 3: Pure Presentation AST Projection & Radical Clutter Purge (Refactoring `PayloadToASTBridge`, eradicating legacy code, didactic tables, and RVS codes; building clean 5x5 Heatmap with physical finding titles).
   - Phase 4: Full Multi-Tenant & Multi-Vertical Calibration Suite (Testing across 6 archetypes: Molins OT, Global Tier-1 Bank, Mid-market SaaS, Acute Hospital, Multinational Retailer, Energy Grid).
   - Phase 5: Automated Continuous Quality Gate Tribunal & CI/CD Guards (Rigorous automated test suite verifying mathematical monism, vertical budget, and diacritics integrity).
4. ARCHITECTURAL INVARIANT CHECKLIST & DEFINITION OF DONE:
   - Exact mathematical invariants that must pass on 100% of compiled documents.

Be surgical, mathematically rigorous, and exhaustive. 100% Technical English.
"""

    cfg = types.GenerateContentConfig(
        temperature=0.2,
        thinking_config=types.ThinkingConfig(thinking_budget=8192),
        http_options=types.HttpOptions(timeout=300000),
    )

    print("Invoking Gemini-4-Argon for definitive phased Chapter 4 Master Blueprint...")
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=cfg,
    )

    content = resp.text or ""
    if not content:
        raise RuntimeError("Received empty response from cognitive engine.")

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_UNIVERSAL_CHAPTER_4_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(content, encoding="utf-8")

    print(f"Definitive Phased Chapter 4 Master Plan successfully saved to: {out_file} ({len(content)} characters)")
    return out_file

if __name__ == "__main__":
    try:
        generate_chapter4_master_plan()
    except Exception as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(1)
