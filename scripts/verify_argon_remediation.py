#!/usr/bin/env python3
"""Run verification review with gemini-4-argon on the remediated code."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_POST_REMEDIATION_VERIFICATION.md"

COPULA_ENGINE_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py"
).read_text(encoding="utf-8")
HYDRATOR_CODE = (
    REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"
).read_text(encoding="utf-8")
TEST_CODE = (
    REPO_ROOT / "tests/unit/test_bayesian_fair_copula_engine.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect and Lead Actuarial Auditor.

Review the remediated codebase to verify whether ALL previous findings have been completely resolved:
1. Language Purity: Zero Spanish words in code, indicators, comments, docstrings, or tests (100% Technical English).
2. Zero Hardcoded Numbers & Vertical Agnosticism: No cement/manufacturing bias, no hardcoded tenant rates or unscaled monetary figures, dynamic operational tiers scaled to tenant baseline revenue/burn rate.
3. Currency Agnosticism: Strict requirement of ISO currency without default to EUR.
4. Mathematical & Algorithmic Rigor: Guard against division by zero (max_annual_outage_hours), no ID collision data loss, no falsy zero traps, exposure-weighted CMMI, and 11 parameterized unit tests passing across 5 global currencies.

UPDATED FILES:

--- FILE 1: src/assessment_engine/domain/bayesian_fair_copula_engine.py ---
{COPULA_ENGINE_CODE}

--- FILE 2: src/assessment_engine/application/services/tower_payload_hydrator.py (actuarial section) ---
{HYDRATOR_CODE[HYDRATOR_CODE.find("# RFC 084: Run Bayesian FAIR Copula Engine"):]}

--- FILE 3: tests/unit/test_bayesian_fair_copula_engine.py ---
{TEST_CODE}

Provide:
1. Final Executive Verdict (PASS / FAIL) and Numerical Score (0.0 to 10.0).
2. Verification Checklist of the 4 Mandates.
3. Architectural Certification.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing post-remediation audit with gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Certification saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON POST-REMEDIATION CERTIFICATION:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:60]:
        print(line)
    if len(lines) > 60:
        print(f"... ({len(lines) - 60} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
