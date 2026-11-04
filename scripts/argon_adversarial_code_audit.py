#!/usr/bin/env python3
"""Adversarial Implementation Auditor via gemini-4-argon.

Conducts an exhaustive, adversarial static analysis and architectural review of
recently implemented code across the Assessment Engine ecosystem.

Evaluates against:
1. Universal Enterprise Multi-Tenancy (50M€ to 50B€, any vertical, any currency).
2. Zero Hardcoding (client names, site locations, hardware vendors, or fixed assumptions).
3. 100% Technical English Codebase (zero Spanish words, accented characters, or comments).
4. Bug and Edge-Case Vulnerabilities (concurrency, numeric precision, exception handling).
5. Clean Architecture & Clean Code Anti-Patterns.
"""

from __future__ import annotations

import json
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


def read_file_safe(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return f"[File {path.name} not found]"


def get_git_diff_summary() -> str:
    res = subprocess.run(
        ["git", "diff", "--stat"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return res.stdout


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    # Collect source files
    actuarial_reconciler_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/domain/actuarial_reconciler.py"
    )
    test_actuarial_reconciler_code = read_file_safe(
        REPO_ROOT / "tests/unit/test_actuarial_reconciler.py"
    )
    tomo_compiler_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py"
    )
    toc_resolver_code = read_file_safe(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/toc_page_resolver.py"
    )
    taxonomy_resolver_diff = subprocess.run(
        ["git", "diff", "src/assessment_engine/domain/taxonomy_resolver.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    ).stdout
    payload_to_ast_diff = subprocess.run(
        ["git", "diff", "src/assessment_engine/adapters/compilers/payload_to_ast.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    ).stdout

    diff_stat = get_git_diff_summary()

    prompt = f"""
Role: Principal Enterprise Systems Architect, Adversarial Code Auditor, and Staff Security/Reliability Engineer.

OBJECTIVE:
Execute an uncompromising, adversarial code review of the newly implemented modules and modifications in the Assessment Engine codebase.

Your mission is to rigorously hunt for:
1. BUGS & RELIABILITY DEFECTS:
   - Logic flaws, rounding discrepancies, potential division by zero, out-of-bounds indexing.
   - Resource leaks, unhandled exceptions, subprocess failures, or concurrency race conditions.
2. ZERO HARDCODING VIOLATIONS:
   - Does any Python source file contain hardcoded assumptions about specific clients (e.g. "Molins", "Secil"), specific locations (e.g. "Sant Vicenç dels Horts"), specific vendors (e.g. "SimpliVity", "VMware", "SAP"), specific numbers of towers (e.g. fixed 10 without generic bounds), or specific currencies (e.g. "€" hardcoded instead of dynamic)?
   - Can this code execute cleanly for a 50M$ retail chain in North America, a 5B£ utility provider in the UK, or a 50B¥ electronics multinational in Japan?
3. 100% TECHNICAL ENGLISH CODEBASE & LANGUAGE DECOUPLING:
   - Check every line of Python code, comments, docstrings, variable names, and string literals.
   - Is there ANY Spanish word, Spanish accented character (á, é, í, ó, ú, ñ), or non-English docstring inside the Python production code?
   - Are language parameters mandatory (e.g. `doc_lang: str`), with zero default parameters like `doc_lang="es"`?
   - Are all natural language strings resolved exclusively through externalized configuration (`locales.json`) via `t(key, locale=doc_lang)`?
4. ARCHITECTURAL INTEGRITY & ANTI-PATTERNS:
   - Clean Architecture / Hexagonal Boundaries: Does the domain layer (`actuarial_reconciler.py`, `taxonomy_resolver.py`) have zero dependencies on infrastructure or adapters?
   - Are there any hidden side effects, mutable global states, or forbidden inline language conditionals (`if doc_lang == "es"`)?
5. MATHEMATICAL SOUNDNESS (OPEN FAIR & CMMI):
   - In `ActuarialReconciler`, does the Hamilton largest remainder allocation method handle all edge cases: target=0, all-zero inputs, negative numbers, extreme scale disparities, tie-breaking determinism?
   - Does `reconcile_scenario_card` guarantee that quantized SLE * LEF == ALE?

GIT STATUS & DIFF SUMMARY:
{diff_stat}

--- CODE UNDER REVIEW: src/assessment_engine/domain/actuarial_reconciler.py ---
{actuarial_reconciler_code}

--- CODE UNDER REVIEW: tests/unit/test_actuarial_reconciler.py ---
{test_actuarial_reconciler_code}

--- CODE UNDER REVIEW: src/assessment_engine/adapters/compilers/toc_page_resolver.py (Excerpts around soffice subprocess) ---
{toc_resolver_code[:4000]}

--- DIFF UNDER REVIEW: src/assessment_engine/domain/taxonomy_resolver.py ---
{taxonomy_resolver_diff}

--- DIFF UNDER REVIEW: src/assessment_engine/adapters/compilers/payload_to_ast.py ---
{payload_to_ast_diff}

--- CODE UNDER REVIEW: src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py (Structure and Key Logic) ---
{tomo_compiler_code[:12000]}
... [truncated for token efficiency, core AST builders and table composers] ...
{tomo_compiler_code[-12000:]}

INSTRUCTIONS FOR YOUR RESPONSE:
Provide a structured, forensic report:
1. Executive Verdict: PASS, PASS WITH RESERVATIONS, or FAIL.
2. Forensic Findings by Category:
   - Hardcoding & Multi-Tenant Scalability Audit.
   - Language Decoupling & 100% Technical English Audit.
   - Bugs, Mathematical Integrity & Reliability Audit.
   - Clean Architecture & Anti-Pattern Audit.
3. Concrete Recommendations & Remediations (if any are identified).
4. Final Certification Statement.
"""

    print(f"Requesting adversarial implementation audit from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/ARGON_ADVERSARIAL_IMPLEMENTATION_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Adversarial audit completed successfully: {out_file}")
    print("\n" + "=" * 80)
    print("AUDIT REPORT PREVIEW:")
    print("=" * 80)
    print(response.text[:2500])


if __name__ == "__main__":
    main()
