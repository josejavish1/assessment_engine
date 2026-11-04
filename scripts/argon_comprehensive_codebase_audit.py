#!/usr/bin/env python3
"""Argon-4 Master Consultation: Exhaustive Adversarial Code Review of Recent Implementations.

Audits all components developed/modified in the current session against strict enterprise mandates:
1. ZERO HARDCODING: Must scale seamlessly from mid-market ($50k) to Global Fortune 500 ($100B),
   any vertical (FinTech, Healthcare, Heavy Manufacturing, Retail, Utilities, Cloud, Public Sector),
   any global currency and locale.
2. 100% TECHNICAL ENGLISH CODEBASE: Not a single Spanish word in variables, docstrings,
   comments, exceptions, logs, or prompts.
3. BUGS, PROBLEMS & ANTIPATTERNS: Thread safety, IEEE-754 numerical stability, AST consistency,
   proper error handling, and zero code rot.
"""

from __future__ import annotations

import subprocess
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


def get_git_diff() -> str:
    res = subprocess.run(
        ["git", "diff", "HEAD", "src/"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return res.stdout


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    git_diff = get_git_diff()
    asis_fair_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/asis_fair_chapter.py"
    )
    tomo_compiler_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py"
    )
    ast_table_builders_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/ast_table_builders.py"
    )
    hydrator_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"
    )
    build_payload_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/application/build_global_report_payload.py"
    )
    radar_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/application/generate_global_radar_chart.py"
    )
    calibrator_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/domain/actuarial_scale_calibrator.py"
    )

    prompt = f"""
ROLE & IDENTITY:
You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Chief Actuarial Auditor, and Enterprise Quality Gatekeeper (Google Cloud Fellow / McKinsey Senior Partner / Gartner Fellow).

MISSION:
Execute an uncompromising, exhaustive, adversarial forensic audit of the codebase components programmed and modified during this active engineering session.

AUDIT CRITERIA & NON-NEGOTIABLE MANDATES:
1. ZERO HARDCODING (UNIVERSAL MULTI-TENANT SCALABILITY):
   - Absolutely no client names (e.g. "Molins", "Client"), physical plant references, or single-tenant assumptions hardcoded in code logic.
   - Must scale seamlessly from a $50K small enterprise to a $100B Global Fortune 500 conglomerate.
   - Must support ANY industry vertical: Banking/FinTech, Healthcare, Heavy Manufacturing, Retail, Utilities, Cloud/Tech, Public Sector.
   - Must support ANY global currency (USD, EUR, JPY, GBP, CHF, SEK, BRL, INR, CAD, AUD, etc.) and ANY locale/language.
   - Dynamic Loss Magnitude (LM) and Threat Event Frequency (TEF) scales must never clip or distort under extreme values.
   - No magic numbers or undocumented scaling factors. All factors must be typed, named `Final` domain constants.

2. 100% TECHNICAL ENGLISH CODEBASE (STRICT LANGUAGE DECOUPLING):
   - Zero tolerance for Spanish tokens, words, comments, docstrings, variable names, function names, class names, log messages, or exception strings.
   - Spanish is ONLY permitted as localized runtime data inside `engine_config/locales.json` or as simulated client input data in tests.
   - Verify every identifier, comment, and log in the modified files.

3. ACTUARIAL, NUMERICAL & OPEN FAIR ROBUSTNESS:
   - Full IEEE-754 resilience: safe handling of NaN, +inf, -inf, zero, negative revenue, zero burn rate.
   - Clean half-up rounding avoiding Python banker's rounding bias where applicable.
   - Accurate 5x5 risk matrix coordinate calculation.

4. CLEAN ARCHITECTURE, THREAD-SAFETY & CODE PURITY:
   - Domain layer (`domain/`) must depend only on Python stdlib and domain schemas.
   - Shared data structures must be immutable (`MappingProxyType`, `frozenset`).
   - Zero mutable global state, figure leakage in chart generation, or split-brain coordinate mappings between AST and document compilers.
   - Identify any bugs, latent race conditions, antipatterns, or architectural flaws.

CODE UNDER AUDIT:

================================================================================
GIT DIFF (ALL MODIFICATIONS TO src/ IN ACTIVE SESSION):
================================================================================
{git_diff}

================================================================================
FULL FILE 1: asis_fair_chapter.py
================================================================================
{asis_fair_code}

================================================================================
FULL FILE 2: tomo_asis_ast_compiler.py
================================================================================
{tomo_compiler_code}

================================================================================
FULL FILE 3: ast_table_builders.py
================================================================================
{ast_table_builders_code}

================================================================================
FULL FILE 4: tower_payload_hydrator.py
================================================================================
{hydrator_code}

================================================================================
FULL FILE 5: build_global_report_payload.py
================================================================================
{build_payload_code}

================================================================================
FULL FILE 6: generate_global_radar_chart.py
================================================================================
{radar_code}

================================================================================
FULL FILE 7: actuarial_scale_calibrator.py
================================================================================
{calibrator_code}

OUTPUT FORMAT:
Generate a structured, exhaustive report:
1. Executive Verdict & Quality Score (0.0 to 10.0) with Pass/Fail determination against the 4 non-negotiable mandates.
2. Forensic Finding Log categorized by:
   - CRITICAL (Architectural blockers, data corruption, hard crash)
   - HIGH (Language violations, hidden single-tenant hardcoding, split-brain logic)
   - MEDIUM (Edge-case boundary failures, thread-safety, cyclomatic complexity)
   - LOW (Style, documentation, minor optimizations)
3. Direct Code Remediation Blueprint:
   - Provide exact, production-ready code replacements for every single finding identified (if any).
4. Final Certification Statement.
"""

    print(f"Submitting comprehensive adversarial audit prompt to {model_name}...")
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

    out_file = REPO_ROOT / "docs/architecture/ARGON_AUDIT_FINAL_PERFECTION.md"
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
