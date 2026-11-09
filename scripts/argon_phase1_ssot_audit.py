#!/usr/bin/env python3
"""Execute adversarial audit with gemini-4-argon across Phase 1 SSOT scoring reconciler code."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_PHASE1_SSOT_AUDIT.md"

RECONCILER_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/services/score_reconciler.py"
).read_text(encoding="utf-8")
INTEGRITY_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/validation/mathematical_integrity.py"
).read_text(encoding="utf-8")
SYNC_CODE = (
    REPO_ROOT / "src/assessment_engine/application/sync_payload_scores.py"
).read_text(encoding="utf-8")
HYDRATOR_EXCERPT = (
    REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"
).read_text(encoding="utf-8")[130:2200]
TEST_UNIT = (
    REPO_ROOT / "tests/unit/test_score_reconciler.py"
).read_text(encoding="utf-8")
TEST_INT = (
    REPO_ROOT / "tests/integration/test_scoring_ssot_invariants.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect and Chief Quality Gatekeeper.

Perform an UNCOMPROMISING, ADVERSARIAL AUDIT of the Phase 1 SSOT Quantitative State Reconciler and Mathematical Integrity implementation.

THE USER'S MANDATES FOR THIS AUDIT:
1. LANGUAGE DECOUPLING LAW:
   - All code, variable names, function signatures, docstrings, comments, exceptions, logs, and tests MUST be 100% Technical English.
   - ZERO SPANISH WORDS in the code! Spanish is strictly reserved for the human user conversation in chat and client delivery templates (via locales.json). Check every identifier, comment, and log string.
2. ZERO HARDCODED NUMBERS & VERTICAL/TENANT AGNOSTICISM:
   - The engine must work seamlessly for ANY company in the world (from a $20M mid-market firm to a $500B Fortune 10 global conglomerate).
   - The engine must work for ANY vertical (Banking, Healthcare, Retail, Technology, Heavy Manufacturing, Public Sector).
   - The topology must support any number of domains/towers (not hardcoded to T1..T10; support D1..D8, custom domain slugs, etc.) and any N-pillar topology with arbitrary valid weights.
3. MATHEMATICAL & ALGORITHMIC RIGOR:
   - Identify bugs, edge cases (empty lists, division by zero, zero weights, floating point representation errors, missing IDs), performance traps, or anti-patterns.

FILES UNDER AUDIT:

--- FILE 1: src/assessment_engine/domain/services/score_reconciler.py ---
{RECONCILER_CODE}

--- FILE 2: src/assessment_engine/domain/validation/mathematical_integrity.py ---
{INTEGRITY_CODE}

--- FILE 3: src/assessment_engine/application/sync_payload_scores.py ---
{SYNC_CODE}

--- FILE 4: Excerpt of compute_canonical_score from tower_payload_hydrator.py ---
{HYDRATOR_EXCERPT}

--- FILE 5: tests/unit/test_score_reconciler.py ---
{TEST_UNIT}

--- FILE 6: tests/integration/test_scoring_ssot_invariants.py ---
{TEST_INT}

YOUR TASK:
Provide an exhaustive, brutally honest audit report:
1. Executive Verdict (PASS / REVISE / FAIL) with numerical score (0.0 to 10.0).
2. Forensic Inventory of Defects:
   - Language Purity violations (List exact line numbers and Spanish words if any).
   - Hardcoding & Tenant/Topology Bias (e.g. assumption of T1..T10, hardcoded thresholds).
   - Mathematical & Algorithmic edge cases or bugs.
3. Complete Production-Grade Remediation Code for any file requiring patches.
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
