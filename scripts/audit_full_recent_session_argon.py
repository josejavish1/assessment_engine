#!/usr/bin/env python3
"""Argon-4 Master Consultation: Exhaustive Adversarial Code Review of Recent Implementations.

Audits all components developed/modified in the current session:
1. src/assessment_engine/domain/actuarial_scale_calibrator.py
2. tests/unit/test_actuarial_scale_calibrator.py
3. src/assessment_engine/adapters/compilers/ast_table_builders.py
4. src/assessment_engine/adapters/compilers/asis_fair_chapter.py
5. src/assessment_engine/adapters/compilers/payload_to_ast.py
6. src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py
7. src/assessment_engine/application/services/tower_payload_hydrator.py
8. tests/unit/test_payload_to_ast_multi_tenant.py
9. tests/unit/test_tomo_asis_ast_compiler_multi_tenant.py

Strict Audit Mandates:
- ZERO hardcoding (no client names, magic numbers, or single-tenant assumptions).
- UNIVERSAL multi-tenant scalability (mid-market $50k to Global Fortune 500 $100B, ANY vertical, ANY currency, ANY language).
- 100% Technical English codebase (ZERO Spanish in code, docstrings, comments, logs, or identifiers).
- Actuarial and numerical correctness (Open FAIR 5x5 matrices, IEEE-754 edge cases).
- Clean Architecture, thread-safety, and zero antipatterns.
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
    get_fallback_model,
    get_model,
)


def read_file_safe(path: Path) -> str:
    if not path.exists():
        return f"[File {path.name} not found]"
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    calibrator_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/domain/actuarial_scale_calibrator.py"
    )
    calibrator_tests = read_file_safe(
        REPO_ROOT / "tests/unit/test_actuarial_scale_calibrator.py"
    )
    table_builders_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/ast_table_builders.py"
    )
    fair_chapter_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/asis_fair_chapter.py"
    )
    payload_to_ast_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py"
    )
    tomo_compiler_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py"
    )
    hydrator_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"
    )
    payload_ast_tests = read_file_safe(
        REPO_ROOT / "tests/unit/test_payload_to_ast_multi_tenant.py"
    )
    tomo_compiler_tests = read_file_safe(
        REPO_ROOT / "tests/unit/test_tomo_asis_ast_compiler_multi_tenant.py"
    )

    prompt = f"""
ROLE & IDENTITY:
You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Chief Actuarial Auditor, and Enterprise Quality Gatekeeper (Google Cloud Fellow / McKinsey Senior Partner / Gartner Fellow).

MISSION:
Execute an uncompromising, exhaustive, adversarial forensic audit of the codebase components programmed and modified during this active engineering session.

AUDIT CRITERIA & NON-NEGOTIABLE MANDATES:
1. ZERO HARDCODING:
   - Absolutely no client names (e.g. "Molins", "Client"), physical plant references, or single-tenant assumptions hardcoded in code logic.
   - No magic numbers or undocumented scaling factors. All factors must be typed, named `Final` domain constants.
2. UNIVERSAL MULTI-TENANT SCALABILITY:
   - Must scale seamlessly from a $50K small enterprise to a $100B Global Fortune 500 conglomerate.
   - Must support ANY industry vertical: Banking/FinTech, Healthcare, Heavy Manufacturing, Retail, Utilities, Cloud/Tech, Public Sector.
   - Must support ANY global currency (USD, EUR, JPY, GBP, CHF, SEK, BRL, INR, CAD, AUD, etc.) and ANY locale/language.
   - Dynamic Loss Magnitude (LM) and Threat Event Frequency (TEF) scales must never clip or distort under extreme values.
3. 100% TECHNICAL ENGLISH CODEBASE (STRICT LANGUAGE DECOUPLING):
   - Zero tolerance for Spanish tokens, words, comments, docstrings, variable names, function names, class names, log messages, or exception strings.
   - Spanish is ONLY permitted as localized runtime data inside `engine_config/locales.json` or as simulated client input data in tests.
4. ACTUARIAL, NUMERICAL & OPEN FAIR ROBUSTNESS:
   - Full IEEE-754 resilience: safe handling of NaN, +inf, -inf, zero, negative revenue, zero burn rate.
   - Clean half-up rounding avoiding Python banker's rounding bias where applicable.
   - Accurate 5x5 risk matrix coordinate calculation.
5. CLEAN ARCHITECTURE, THREAD-SAFETY & CODE PURITY:
   - Domain layer (`domain/`) must depend only on Python stdlib and domain schemas.
   - Shared data structures must be immutable (`MappingProxyType`, `frozenset`).
   - Zero mutable global state, figure leakage in chart generation, or split-brain coordinate mappings between AST and document compilers.
   - Identify any bugs, latent race conditions, antipatterns, or architectural flaws.

CODE UNDER AUDIT:

================================================================================
COMPONENT 1: Dynamic Actuarial Scale Calibrator
File: src/assessment_engine/domain/actuarial_scale_calibrator.py
================================================================================
{calibrator_code}

================================================================================
COMPONENT 2: Calibrator Test Suite
File: tests/unit/test_actuarial_scale_calibrator.py
================================================================================
{calibrator_tests}

================================================================================
COMPONENT 3: AST Table Builders (Dynamic LM & TEF Integration)
File: src/assessment_engine/adapters/compilers/ast_table_builders.py
================================================================================
{table_builders_code}

================================================================================
COMPONENT 4: FAIR Chapter Compiler (Open FAIR Heatmap Integration)
File: src/assessment_engine/adapters/compilers/asis_fair_chapter.py
================================================================================
{fair_chapter_code}

================================================================================
COMPONENT 5: Tower Payload Hydrator
File: src/assessment_engine/application/services/tower_payload_hydrator.py
================================================================================
{hydrator_code}

================================================================================
COMPONENT 6: Multi-Tenant Tests
Files:
- tests/unit/test_payload_to_ast_multi_tenant.py:
{payload_ast_tests}
- tests/unit/test_tomo_asis_ast_compiler_multi_tenant.py:
{tomo_compiler_tests}
================================================================================

================================================================================
COMPONENT 7: Excerpts from payload_to_ast.py and tomo_asis_ast_compiler.py
================================================================================
--- payload_to_ast.py (Lines 140-270) ---
{payload_to_ast_code[4500:9500]}

--- tomo_asis_ast_compiler.py (Lines 1-120 and Chapter 3/4 builders) ---
{tomo_compiler_code[:4500]}
{tomo_compiler_code[22000:27000]}

OUTPUT FORMAT:
Generate a structured, exhaustive report:
1. Executive Verdict & Quality Score (0.0 to 10.0) with Pass/Fail determination against the 5 non-negotiable mandates.
2. Forensic Finding Log categorized by:
   - CRITICAL (Architectural blockers, data corruption, hard crash)
   - HIGH (Language violations, hidden single-tenant hardcoding, split-brain logic)
   - MEDIUM (Edge-case boundary failures, thread-safety, cyclomatic complexity)
   - LOW (Style, documentation, minor optimizations)
3. Direct Code Remediation Blueprint:
   - Provide exact, production-ready code replacements for every single finding identified.
4. Final Certification Statement.
"""

    print(f"Submitting comprehensive audit prompt to {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
    except Exception as e:
        print(f"Error querying primary model {model_name}: {e}")
        fallback = get_fallback_model(model_name)
        if fallback:
            print(f"Falling back to {fallback}...")
            response = client.models.generate_content(
                model=fallback,
                contents=prompt,
            )
        else:
            raise

    out_file = REPO_ROOT / "docs/architecture/ARGON_AUDIT_FULL_SESSION_IMPLEMENTATION.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("ARGON-4 COMPREHENSIVE ADVERSARIAL AUDIT COMPLETE")
    print("=" * 80)
    print(
        f"Output saved to: {out_file.relative_to(REPO_ROOT)} ({len(response.text):,} characters)"
    )


if __name__ == "__main__":
    main()
