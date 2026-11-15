#!/usr/bin/env python3
"""
Invoke gemini-4-argon to perform an exhaustive, adversarial code review
of the implemented Chapter 4 Universal Architecture.

Audits:
1. Zero Spanish in code (100% Technical English mandate).
2. Zero hardcoding (scales dynamically from $50M to $100B, CMMI 1-5, all verticals).
3. Bugs, edge cases, null-pointer traps, floating point inaccuracies.
4. Multilingual fidelity across all 6 deliverable languages.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def run_chapter4_code_audit() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: EXHAUSTIVE CODE IMPLEMENTATION AUDIT")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    # Collect source code files implemented for Chapter 4
    files_to_audit = [
        "src/assessment_engine/domain/actuarial/schemas.py",
        "src/assessment_engine/domain/actuarial/rounding.py",
        "src/assessment_engine/domain/services/chapter4_synthesizer.py",
        "tests/architecture/test_universal_chapter4_actuarial_integrity.py",
        "tests/calibration/test_multi_vertical_archetypes.py",
        "tests/unit/test_chapter4_actuarial_schemas.py",
        "tests/unit/test_chapter4_synthesizer_monism.py",
    ]

    code_payload = []
    for rel_path in files_to_audit:
        full_path = _REPO_ROOT / rel_path
        if full_path.exists():
            code_payload.append(f"### FILE: {rel_path}\n```python\n{full_path.read_text(encoding='utf-8')}\n```\n")

    combined_code = "\n".join(code_payload)

    prompt = f"""
You are Gemini-4-Argon, Principal Systems Architect, Staff Compiler Engineer, and Chief Actuary.

MISSION:
Perform a ruthless, forensic, line-by-line code review of the newly implemented Chapter 4 Universal Architecture.
The user demands to know:
1. Are there ANY bugs, subtle edge cases, unhandled nulls, or floating point rounding traps?
2. Are there ANY lingering hardcoded numbers, client-specific assumptions, fixed ratios, or magic constants?
3. Is the code 100% in Technical English (ZERO Spanish words in variable names, functions, docstrings, comments, exceptions, or logs)?
4. Can this code genuinely scale to ANY enterprise in the world (from a $50M mid-market startup to a $100B+ Fortune 10 global conglomerate, across all 8 industry verticals and CMMI maturity levels 1.0 to 5.0)?
5. Does it uphold clean hexagonal architecture and strict separation of concerns?

SOURCE CODE TO AUDIT:
{combined_code}

INSPECTION CRITERIA:
1. LINGUISTIC PURITY (100% Technical English Mandate):
   - Scan every single identifier, string literal, docstring, and comment.
   - Flag ANY word in Spanish or any non-English language in the Python source code.
2. ZERO-HARDCODING & UNIVERSAL DYNAMICS:
   - Identify any hardcoded numbers (e.g. 750, 45, 3000, 0.8, 1.15) and evaluate if they properly scale dynamically or need dynamic catalog injection.
   - Verify that currency handling is 100% ISO-standard without hardcoded EUR/USD assumptions.
   - Check that enterprise scale normalization (headcount, revenue, operating hours) works correctly at extreme boundaries ($10M vs $100B, 10 employees vs 500,000 employees).
3. ACTUARIAL RIGOR & EDGE-CASE RESILIENCE:
   - Audit `allocate_subadditive_ale_to_cards` (Hare-Niemeyer discrete integer allocation). Can it ever raise RuntimeError or fail on zero sums, negative numbers, or ties?
   - Audit `compute_step_quantum` and `round_to_actuarial_significance`. Does it correctly handle zero, single-euro amounts, hyper-low risks, or multi-billion amounts?
   - Audit `Chapter4SynthesisPayload` validators. Can any valid edge case cause an unexpected ValidationError?
4. ARCHITECTURAL DECOUPLING & CLEANLINESS:
   - Are the Pydantic V2 models strictly frozen and decoupled from presentation?
   - Is there any memory leakage, mutation of input parameters, or circular import risk?
5. FINAL AUDIT SCORE & ACTIONABLE ENHANCEMENTS:
   - Provide an objective score (0 to 100) across Linguistic Purity, Zero-Hardcoding, Mathematical Rigor, and Production Readiness.
   - If ANY flaws or areas for improvement are found, provide the exact code replacements.

Write your complete forensic audit report in clean Markdown format to be stored at `docs/architecture/ARGON_CHAPTER_4_CODE_IMPLEMENTATION_AUDIT.md`.
100% Technical English. Be uncompromising, precise, and authoritative.
"""

    cfg = types.GenerateContentConfig(
        temperature=0.2,
        thinking_config=types.ThinkingConfig(thinking_budget=8192),
        http_options=types.HttpOptions(timeout=300000),
    )

    print("Running line-by-line code review with Gemini-4-Argon...")
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=cfg,
    )

    audit_content = resp.text or ""
    if not audit_content:
        raise RuntimeError("Received empty response from audit engine.")

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_CHAPTER_4_CODE_IMPLEMENTATION_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_content, encoding="utf-8")

    print(f"Code Implementation Audit Report successfully saved to: {out_file} ({len(audit_content)} characters)")
    return out_file

if __name__ == "__main__":
    try:
        run_chapter4_code_audit()
    except Exception as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(1)
