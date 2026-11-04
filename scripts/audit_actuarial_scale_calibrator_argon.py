#!/usr/bin/env python3
"""Argon-4 Master Consultation: Forensic Adversarial Audit of Actuarial Scale Calibrator.

Performs an exhaustive adversarial code review of:
- src/assessment_engine/domain/actuarial_scale_calibrator.py
- src/assessment_engine/adapters/compilers/asis_fair_chapter.py (dynamic LM integration)
- src/assessment_engine/adapters/compilers/ast_table_builders.py (dynamic LM integration)
- tests/unit/test_actuarial_scale_calibrator.py

Audits for:
1. Zero hardcoding of tenant names, magic numbers, or single-client assumptions.
2. Universal multi-tenant scalability across ANY enterprise scale ($10M to $100B),
   ANY industry vertical, ANY currency (USD, EUR, JPY, GBP, SEK), and ANY language.
3. Strict adherence to Clean Architecture (zero dependencies escaping the domain layer).
4. 100% Technical English codebase (zero Spanish in code, symbols, docstrings, comments).
5. Actuarial mathematical robustness (division by zero, negative inputs, float precision).
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
    test_code = read_file_safe(
        REPO_ROOT / "tests/unit/test_actuarial_scale_calibrator.py"
    )
    fair_chapter_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/asis_fair_chapter.py"
    )
    table_builders_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/ast_table_builders.py"
    )

    prompt = f"""
Role: Principal Distributed Systems & Actuarial Architect, Chief Quality Gatekeeper, and Distinguished Enterprise Code Auditor (Google Cloud / Gartner Fellow / McKinsey Senior Partner).

MISSION OBJECTIVE:
Execute an uncompromising, adversarial forensic code review of the newly implemented Dynamic Loss Magnitude (LM) Scale Calibrator and its integration across the Open FAIR 5x5 Risk Heatmap compilers.

The platform user has issued a zero-tolerance directive:
- ZERO hardcoding (no client names, no hidden single-tenant constants, no magic numbers).
- UNIVERSAL multi-tenant scalability (must serve ANY enterprise in the world, from a $10M mid-market to a $100B Global Fortune 500, across ANY vertical: Banking, Healthcare, Retail, Manufacturing, Gov, in ANY currency: USD, EUR, JPY, GBP, CHF, SEK, and ANY delivery language).
- 100% Technical English codebase (absolute prohibition of Spanish in code, variable names, functions, docstrings, comments, or log messages).
- ZERO bugs, antipatterns, or architectural split-brains.

CODE ARTIFACTS UNDER AUDIT:

--- COMPONENT 1: Dynamic Actuarial Scale Calibrator (`src/assessment_engine/domain/actuarial_scale_calibrator.py`) ---
{calibrator_code}

--- COMPONENT 2: Unit Test Suite (`tests/unit/test_actuarial_scale_calibrator.py`) ---
{test_code}

--- COMPONENT 3: FAIR Heatmap Document Integration (`src/assessment_engine/adapters/compilers/asis_fair_chapter.py` - Lines 50-160) ---
{fair_chapter_code[:4000]}

--- COMPONENT 4: AST Table Builders Integration (`src/assessment_engine/adapters/compilers/ast_table_builders.py` - Lines 110-210) ---
{table_builders_code[3000:7000]}

REQUIRED ADVERSARIAL REPORT STRUCTURE:
1. Executive Verdict & Quality Score:
   - Overall Code Quality Score (0 to 10).
   - Definitive Pass/Fail verdict against the Zero-Hardcoding and Universal Multi-Tenancy mandates.
2. Forensic Finding Log (Categorized by Critical, High, Medium, Low):
   - Scrutinize:
     * Are there any hidden single-client biases or unvalidated magic numbers?
     * Actuarial edge cases: what happens if `annual_revenue` is negative, zero, or `1e12`? What if `hourly_downtime_cost` is `0.0` or `None`?
     * Does the currency parity mapping properly handle all ISO codes?
     * Are Clean Architecture boundaries strictly preserved (zero outer layer dependencies in `domain/`)?
     * Is the codebase 100% Technical English without a single Spanish word?
     * Thread-safety and immutability.
3. Code Quality Certification & Specific Refinement Recommendations:
   - Detail any surgical improvements needed before proceeding to the next phase.
"""

    print(f"Submitting audit prompt to {model_name}...")
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

    out_file = REPO_ROOT / "docs/architecture/ARGON_AUDIT_ACTUARIAL_SCALE_CALIBRATOR.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("ARGON-4 ADVERSARIAL AUDIT OF ACTUARIAL SCALE CALIBRATOR COMPLETE")
    print("=" * 80)
    print(f"Output saved to: {out_file.relative_to(REPO_ROOT)} ({len(response.text):,} characters)")


if __name__ == "__main__":
    main()
