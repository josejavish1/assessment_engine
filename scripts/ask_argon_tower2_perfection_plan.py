#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Definitive, Multi-Phase, Zero-Defect
Tower 2 Final Perfection & Universal Defensibility Master Plan.

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Multi-phase phased implementation plan (Phases 1 to 5) with strict Quality Gates.
3. Universal scalability: Any industry vertical, any enterprise size ($50M to $100B+), any maturity (Level 1 to 5), 6 output languages.
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

def generate_perfection_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: TOWER 2 FINAL PERFECTION MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & CONTEXT:
We have completed Phase 1 & 2 of the Defensibility Plan (fixing the compiler override bug, exposing the full Open FAIR derivation chain, synchronizing Tower 2 weights to yield the exact 1.85 score, and introducing the calibration traceability callout).
A rigorous forensic audit (`Revision_Profunda_Torre_2_Iteracion_3.txt`) evaluated our latest generation. The reviewer validated that the 1.85 score and the 13.75k - 27k EUR risk sum are mathematically impeccable.
However, the auditor identified 6 remaining blocking flaws before the deliverable can be certified as Tier-1 World Class:

1. SCALE CONVERGENCE: The official project framework defines:
   - Initial: [1.00, 1.79]
   - Basic: [1.80, 2.59]
   - Standardized: [2.60, 3.39]
   - Optimized: [3.40, 4.19]
   - Advanced: [4.20, 5.00]
   Currently, `governance_scales.json` still uses legacy CMMI bands (cutting at 1.50, 2.50, etc.). We need a universal, multi-tenant solution to align this across `scale_engine.py`, `locales.json`, and visual templates without breaking existing clients.

2. WEIGHT CONSERVATION & DISPLAY (The 98% Visual Defect):
   On page 5, the pillar table formats weights as integers (22%, 19%, 20%, 18%, 20%), which visually sum to 98% or 99% instead of 100%. We must enforce 2-decimal formatting (22.38%, 19.05%, 20.48%, 17.62%, 20.47%) so they sum to exactly 100.00%.

3. EPISTEMIC HARMONIZATION (Resolving the Kubernetes Contradiction):
   The calibration note correctly states: "No containers in production; all workloads run on 300+ legacy VMs".
   However, the LLM qualitative findings narrative in Pillar 2 (inherited from older runs) describes an operational Kubernetes platform with Ingress, NetApp Trident CSI, RBAC, and cluster lifecycle management!
   When a pillar is calibrated to Level 1 (Initial / Incipient), the qualitative narrative generation must strictly reflect that embryonic reality (testing/lab environment, lack of formal governance) rather than hallucinating enterprise tooling.

4. DYNAMIC 5x5 HEATMAP MATRIX PLACEMENT (SLE -> LM Alignment):
   In the 5x5 heatmap, all 4 risks currently land in LM 3, even though their newly calculated Single Loss Expectancy (SLE) spans:
   - RSK-01 / RSK-02: SLE ~2,250 - 4,400 EUR (LM 2: 1,000 - 4,000 EUR or boundary to LM 3)
   - RSK-03 / RSK-04: SLE ~1,100 - 2,200 EUR (LM 2: 1,000 - 4,000 EUR)
   The heatmap coordinates must be derived dynamically from each risk's individual SLE midpoint relative to the dynamic LM scale brackets, rather than hardcoding all cards into a single column.

5. LAYOUT & PAGINATION FLOW (Eliminating Blank Page 9):
   A redundant `PageBreakNode()` combined with table spacing is causing an orphan blank page 9 before Chapter 4. We must engineer a fluid, compact layout rule that prevents blank orphan pages.

6. LEXICON & EVIDENCE TRANSPARENCY:
   - Eliminate residual mentions of unpresent cloud providers (e.g. AWS).
   - Align consultative language ("Technical Diagnostic Assessment" based on qualitative interviews and declared architecture) to harmonize with the legal disclaimer.

CORE INVARIANTS:
- 100% Technical English in code, variables, classes, docstrings, comments, logs, and prompt files.
- Zero Hardcoding: Everything must be dynamic, schema-driven, and multi-tenant.
- Zero Regressions: Must pass all 47 existing architecture, accent, and actuarial tests.

YOUR DELIVERABLE:
Write a comprehensive, exhaustive, publication-grade MASTER ARCHITECTURAL BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_TOWER2_FINAL_PERFECTION_MASTER_PLAN.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY & ARCHITECTURAL MANIFESTO: Addressing the 6 blocking issues.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 1: Maturity Scale Harmonization & Universal Bound Alignment.
   - Phase 2: Pillar Weight Precision & 100.00% Conservation Rule.
   - Phase 3: Epistemic Grounding & Narrative De-Hallucination Engine.
   - Phase 4: Dynamic Actuarial Heatmap Coordinate Derivation (SLE -> LM).
   - Phase 5: AST Layout Fluidity & Document Pagination Compactness.
3. QUALITY GATES & VERIFICATION ORACLES: Deterministic pytest assertions for each phase.
4. SYSTEMIC ROLLOUT & RISK MITIGATION: How this permanently guarantees world-class quality for any enterprise vertical.
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

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_TOWER2_FINAL_PERFECTION_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    generate_perfection_master_plan()
