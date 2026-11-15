#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 10: Iteration 7 Factual & Epistemic Polish Master Plan.

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Multi-phase implementation plan with strict Quality Gates.
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

def generate_iteration7_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: ITERATION 7 FACTUAL POLISH MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & CONTEXT:
The latest forensic audit (`Revision_Profunda_Torre_2_Iteracion_7.txt`) rated our current deliverable at 8.0/10. It formally validated our mathematical engine (weights summing to 100%, 1.85 score alignment, FAIR chain integration, 13.75k - 27k EUR risk sum, dynamic heatmap mapping, and clean 15-page layout).
To reach a certified 9.5+/10 Tier-1 World Class level for any enterprise globally, we must solve the remaining factual and epistemic friction points before touching the codebase:

1. MASTER CATALOG LOCALE INTEGRITY:
   - Flaws: The Automation pillar description inherited a cyber-security template text ("protection and response measures"). There is a typo ("taxonomóa FinOps"). The CMMI reference is outdated ("CMMI v2.0").
   - Goal: Universally patch `engine_config/locales.json` and related catalogs to ensure accurate domain descriptions, correct typos, and formally adopt the `CMMI® V3.0 (adaptación a Infraestructura)` nomenclature.

2. METHODOLOGICAL VALIDATION STATE & REGULATORY POSTURE:
   - Flaws: The diagnostic lacks an explicit epistemic validation state. Furthermore, it categorically claims "High Breach (NIS2 Directive)" in the executive summary, which contradicts the legal disclaimer stating regulatory mentions are illustrative.
   - Goal: Introduce an explicit "Validation State: Exploratory (Fast Assessment)" declaration in the methodology block. Soften regulatory posture claims to "Priority Attention (NIS2 Resilience Principles - subject to Legal/T6 validation)".

3. STRICT NARRATIVE GROUNDING (POSITIVE EVIDENCE & SCALE ABSTRACTION):
   - Flaws: The engine inflated a single edge host to "departmental database clusters" and omitted positive evidence (e.g. 15-minute proven HA failover). It also suffers from the "Expand 50%" prompt hallucination catalyst, introducing unverified tech (BFD, flat accounts).
   - Goal: Architect a structural prompt upgrade that replaces "Expand 50%" with "Parsimonious Factual Precision". Ensure the prompt commands the LLM to balance severe capacity risks with proven tactical resilience successes (e.g. successful failovers) and prohibits scaling single nodes into enterprise clusters without evidence.

4. KPI-BY-KPI CALIBRATION TRACEABILITY:
   - Flaws: Calibrating Kubernetes from 4.25 down to 1.00 is justified broadly, but a rigorous auditor expects a KPI-by-KPI rebuttal.
   - Goal: Architect a universal mechanism in the AST presentation layer or intelligence payload to document (or structure the prompt to generate) the exact contrast between the high self-assessment scores (e.g. 4/4/5/4) and the observed empirical reality (incipient lab testing).

CORE INVARIANTS:
- 100% Technical English in code, variables, classes, docstrings, comments, logs, and prompt files.
- Zero Hardcoding: Algorithms and prompt directives must be universal, scaling from a $50M mid-market firm to a $100B global conglomerate.
- Zero Regressions: Must pass all 47 existing architecture and actuarial tests.

YOUR DELIVERABLE:
Write a comprehensive, exhaustive, publication-grade MASTER ARCHITECTURAL BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE10_ITERATION7_MASTER_PLAN.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO: Addressing the final push to 9.5+/10.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 1: Locale Baseline Rectification (Descriptions, CMMI V3.0, Orthography).
   - Phase 2: Epistemic Validation State & Regulatory Shielding.
   - Phase 3: Hallucination Catalyst Removal & Parsimonious Grounding Engine (Prompt Tuning).
   - Phase 4: Positive Resilience Recognition (Balanced Assessment Framework).
   - Phase 5: KPI-by-KPI Micro-Calibration Traceability.
3. QUALITY GATES & VERIFICATION ORACLES: Deterministic pytest validation suites.
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

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE10_ITERATION7_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    generate_iteration7_master_plan()
