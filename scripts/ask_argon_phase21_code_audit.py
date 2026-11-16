#!/usr/bin/env python3
"""
Invoke gemini-4-argon to execute an exhaustive forensic code audit of Phase 21 implementations.

Evaluates:
1. 100% Technical English compliance (Language Decoupling Law - zero Spanish in code, docstrings, comments, variables, tests).
2. Universal Enterprise Agnosticism ($50M to $100B+, any global vertical, zero client-specific hardcoding).
3. Code quality, edge cases, hidden bugs, and antipatterns.
4. Clean Architecture and mathematical integrity for Chapter 4 (FAIR vulnerability binding).

100% Technical English in prompt and generated audit report.
"""

import subprocess
import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def run_argon_phase21_audit() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: PHASE 21 COMPREHENSIVE FORENSIC CODE AUDIT")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    # Gather diff of recent commits (from b8ccde4^ to HEAD)
    git_diff = subprocess.check_output(
        ["git", "diff", "b8ccde4^..HEAD"],
        cwd=str(_REPO_ROOT),
        text=True,
    )

    # Read the full text of the newly modified/created modules
    files_to_read = [
        _REPO_ROOT / "src/assessment_engine/domain/ingestion/missing_data_circuit_breaker.py",
        _REPO_ROOT / "src/assessment_engine/domain/ingestion/context_router.py",
        _REPO_ROOT / "src/assessment_engine/domain/ingestion/epistemic_fact_registry.py",
        _REPO_ROOT / "tests/unit/test_upstream_ingestion_gating.py",
        _REPO_ROOT / "tests/unit/test_epistemic_fact_registry.py",
    ]

    source_code_context = ""
    for f in files_to_read:
        if f.exists():
            source_code_context += f"\n\n--- FILE: {f.relative_to(_REPO_ROOT)} ---\n"
            source_code_context += f.read_text(encoding="utf-8")

    prompt = f"""
You are Gemini-4-Argon, Global Chief Systems Architect, Principal Compiler Engineer, and Fellow of the Society of Actuaries.

MANDATE & OBJECTIVE:
Execute an uncompromising, deep-dive forensic code audit of our recent implementation across ingestion, registry, and compiler layers (commits b8ccde4^..HEAD).
Your goal is to detect any bugs, hidden antipatterns, hardcoding, or violations of engineering standards.

NON-NEGOTIABLE CORE INVARIANTS:
1. 100% TECHNICAL ENGLISH (LANGUAGE DECOUPLING LAW):
   - Every single line of code, variable name, function signature, class name, docstring, comment, log message, exception, and test must be in 100% Technical English.
   - Spanish is STRICTLY PROHIBITED in the codebase (it is only permitted in `engine_config/locales.json` as external localized client data).
   - Check every token in the diff and newly created files for Spanish words or diacritics.

2. ZERO HARDCODING & TOTAL SCALE AGNOSTICISM:
   - The engine must seamlessly evaluate ANY enterprise in the world, from a $50M mid-market firm to a $100B+ multinational conglomerate, across any vertical (Financial Services, Healthcare, Aerospace, Manufacturing, Retail).
   - No client names (e.g., 'Molins', 'SimpliVity', 'NetApp'), specific numbers (e.g., '613', '15', '3 hours'), or domain assumptions may be hardcoded into logic.

3. ARCHITECTURAL INTEGRITY & ROBUSTNESS:
   - Identify any edge cases, type errors, concurrency race conditions, null pointer risks, or performance bottlenecks.
   - Audit the OpenXML Word generation logic (anti-orphan page break guard, Heading pageBreakBefore) for layout regressions.
   - Audit the Chapter 4 actuarial derivation logic for mathematical correctness (specifically the binding of vulnerability_ratio from strategic_risk_cards).

RECENT GIT DIFF (b8ccde4^..HEAD):
```diff
{git_diff[:40000]}
```

FULL REVISED SOURCE MODULES:
{source_code_context}

YOUR DELIVERABLE:
Write an exhaustive, high-signal, publication-grade CODE AUDIT REPORT in Markdown format to be saved at `docs/architecture/ARGON_FORENSIC_CODE_AUDIT_PHASE21.md`.

Structure your audit report into:
1. EXECUTIVE AUDIT SUMMARY & VERDICT (Pass, Pass with Recommendations, or Critical Rejection).
2. COMPLIANCE AUDIT AGAINST CORE INVARIANTS:
   - Language Decoupling Law (100% Technical English check across code, comments, docstrings, variable names, and unit tests).
   - Zero Hardcoding & Scale Agnosticism check ($50M to $100B+, any vertical, any language).
3. IN-DEPTH DEFECT ANALYSIS (Bugs, edge cases, potential failure modes, or antipatterns).
4. VERIFICATION OF REMEDIATIONS (Confirm whether previous defects from Phase 20 were genuinely fixed):
   - Substring matching with word boundaries (\b...\b).
   - Fail-closed context router behavior.
   - Boolean-as-integer guard in MissingDataCircuitBreaker.
   - Thread-safety (RLock) and immutability (frozen=True) in EpistemicFactRegistry.
   - Elimination of the FAIR 60-85% vs 80-95% contradiction in payload_to_ast.py.
   - Elimination of hardcoded CMMI for Infrastructure in run_tower_blueprint_engine.py.
5. FINAL ARCHITECTURAL RATING & ACTIONABLE RECOMMENDATIONS.
"""

    print("Sending code diff and source files to Gemini-4-Argon for audit...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_FORENSIC_CODE_AUDIT_PHASE21.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Phase 21 Audit Report successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    run_argon_phase21_audit()
