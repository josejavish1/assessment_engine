#!/usr/bin/env python3
"""Execute an exhaustive adversarial audit with gemini-4-argon across recent actuarial code."""

from __future__ import annotations

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_ADVERSARIAL_DEEP_REVIEW_ACTUARIAL.md"

COPULA_ENGINE_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py"
).read_text(encoding="utf-8")
HYDRATOR_CODE = (
    REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"
).read_text(encoding="utf-8")
COMPILER_DIFF = (
    REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py"
).read_text(encoding="utf-8")[440:1000]
TEST_CODE = (
    REPO_ROOT / "tests/unit/test_bayesian_fair_copula_engine.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Lead Actuarial Auditor, and Chief Quality Gatekeeper (Google Cloud Fellow / McKinsey Senior Partner / FAIR Institute Fellow).

You are performing an UNCOMPROMISING, ADVERSARIAL AUDIT of the recent codebase modifications implementing Open FAIR™ quantitative risk modeling and sub-additive Copula convolution.

THE USER'S MANDATES FOR THIS AUDIT:
1. LANGUAGE DECOUPLING LAW:
   - All code, variable names, function signatures, docstrings, comments, exceptions, logs, tests, string heuristics, and regexes MUST be 100% Technical English.
   - ZERO SPANISH WORDS in the code! Spanish is strictly reserved for the human user conversation in chat and user delivery templates (via locales.json). Check every keyword heuristic, fallback string, and comment.
2. ZERO HARDCODED NUMBERS & VERTICAL DECOUPLING:
   - The engine must work seamlessly for ANY company in the world (from a $20M mid-market firm to a $500B Fortune 10 global conglomerate).
   - The engine must work for ANY vertical (Banking, Healthcare, Retail, Technology, Heavy Manufacturing, Public Sector).
   - NO manufacturing-specific concepts ("KILN_MILL", cement, plant dispatch) or tenant-specific rates (13061, 8400, 5000, "Molins") must be hardcoded in application logic.
   - Any fallback zones must be generic (e.g. Tier-1 Mission Critical Core, Tier-2 High Availability Operational, Tier-3 Edge Operations, Tier-4 General Office/Support) and rates must scale parameterized from tenant Annual Revenue and Operating Hours if not explicitly provided in telemetry.
3. CURRENCY & MULTI-TENANT AGNOSTICISM:
   - Must support any ISO currency (USD, EUR, GBP, JPY, CHF, etc.) without assumption of "€" or "EUR".
4. MATHEMATICAL & ARCHITECTURAL RIGOR:
   - Identify bugs, numerical instabilities, division by zero, edge cases (empty findings list, zero revenue, single finding, identical loadings, extreme CMMI scores 0 or 6), memory leaks, or anti-patterns.

FILES UNDER AUDIT:

--- FILE 1: src/assessment_engine/domain/bayesian_fair_copula_engine.py ---
{COPULA_ENGINE_CODE}

--- FILE 2: src/assessment_engine/application/services/tower_payload_hydrator.py (Excerpt around actuarial hydration lines 500-750) ---
{HYDRATOR_CODE[HYDRATOR_CODE.find("# RFC 084: Run Bayesian FAIR Copula Engine"):]}

--- FILE 3: tests/unit/test_bayesian_fair_copula_engine.py ---
{TEST_CODE}

YOUR TASK:
Provide an exhaustive, brutally honest audit report:
1. Executive Verdict (PASS / REVISE / FAIL) with numerical score (0.0 to 10.0).
2. Forensic Inventory of Defects:
   - Language Purity violations (List exact line numbers and Spanish words found).
   - Hardcoding & Vertical Bias violations (List exact lines with hardcoded numbers, Molins rates, or industry-specific zone names).
   - Architectural & Mathematical edge cases or bugs.
3. Complete, Production-Grade Remediation Code (100% Technical English, fully parameterized, zero hardcoding).
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing adversarial audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Audit report saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON ADVERSARIAL AUDIT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
