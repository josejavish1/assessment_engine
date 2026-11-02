#!/usr/bin/env python3
"""Argon-4 Comprehensive Adversarial Audit: Full Codebase & Recent Implementation Review.

Examines recent code changes against all non-negotiable architectural laws:
1. Zero Bugs, Zero Antipatterns
2. Zero Hardcoding (Universal Global Enterprise Readiness: any tier, vertical, currency, language)
3. 100% Technical English Codebase (Zero Spanish words in Python source code)
4. Split-Brain Eradication (100% 10-Tower Symmetry T1..T10)
5. ISO/IEC 29500 OpenXML & Editorial Perfection
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
    get_model,
)


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    # Gather git diff against origin/main or recent commits
    diff_cmd = ["git", "diff", "HEAD~4"]
    diff_res = subprocess.run(diff_cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    git_diff = diff_res.stdout

    if not git_diff:
        diff_cmd = ["git", "diff", "HEAD~1"]
        diff_res = subprocess.run(diff_cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        git_diff = diff_res.stdout

    # Also include the full content of toc_page_resolver.py
    toc_resolver_path = REPO_ROOT / "src/assessment_engine/adapters/compilers/toc_page_resolver.py"
    toc_resolver_content = (
        toc_resolver_path.read_text(encoding="utf-8")
        if toc_resolver_path.exists()
        else "NOT FOUND"
    )

    prompt = f"""
Role: Principal Actuarial Systems Architect & Chief Compiler Engineer (Google Tier-1 / Anthropic Core Infrastructure / MIT Actuarial Fellow).

TASK:
Perform a comprehensive, adversarial, forensic code review of all recently modified and created files in this repository.

THE 5 NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTIPATTERNS, ZERO DEFECTS:
   - Flawless mathematical, exception-handling, and architectural design.
   - Fail-fast enforcement: no silent error swallowing, no generic `except Exception: pass`.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The engine must scale to ANY company in the world: any tier (50M€ to 50B€ turnover), any vertical, any currency (EUR, USD, GBP, JPY, CHF, etc.), and any language (en, es, de, fr, pt, etc.).
   - Zero hardcoded client names, zero hardcoded monetary amounts, zero language-specific assumptions in Python code.
3. 100% TECHNICAL ENGLISH CODEBASE (LANGUAGE DECOUPLING LAW):
   - All Python code, class names, method names, variables, identifiers, comments, docstrings, logs, exceptions, and regexes must be 100% Technical English.
   - Zero Spanish words anywhere in Python source code files. (Spanish is ONLY permitted in `locales.json` data dictionary).
4. SPLIT-BRAIN ERADICATION (100% 10-TOWER SYMMETRY):
   - Towers T1 through T10 must execute the exact same unified pipeline and code paths. Zero special-casing for T1 or T2.
5. ISO/IEC 29500 OPENXML & EDITORIAL EXCELLENCE:
   - Valid OpenXML markup, native Word Table of Contents, table auto-fit to 100% window width, professional typography (#2E404D slate, 10.5pt body).

SOURCE CODE TO AUDIT:

--- FILE: src/assessment_engine/adapters/compilers/toc_page_resolver.py ---
{toc_resolver_content}

--- GIT DIFF (RECENT COMMITS) ---
{git_diff[:25000]}

OUTPUT FORMAT:
Return a valid JSON object matching this schema:
{{
  "verdict": "PASS" | "FAIL",
  "zero_bugs_or_antipatterns": true | false,
  "zero_hardcoding_verified": true | false,
  "universal_tier1_enterprise_ready": true | false,
  "strict_english_only_verified": true | false,
  "split_brain_eradicated": true | false,
  "openxml_editorial_excellence_verified": true | false,
  "findings": [
    {{
      "file_path": "path/to/file.py",
      "line_number": 123,
      "category": "BUG" | "HARDCODING" | "SPANISH_IN_CODE" | "SPLIT_BRAIN" | "EDITORIAL",
      "severity": "CRITICAL" | "MAJOR" | "MINOR",
      "technical_critique": "Detailed explanation of why this fails the law",
      "mandatory_fix": "Concrete instruction to resolve it cleanly"
    }}
  ],
  "forensic_executive_summary": "Thorough, objective executive synthesis of the codebase status."
}}
"""

    print(f"Requesting comprehensive adversarial audit from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/COMPREHENSIVE_RECENT_AUDIT_ARGON.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: COMPREHENSIVE ADVERSARIAL AUDIT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nAudit saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
