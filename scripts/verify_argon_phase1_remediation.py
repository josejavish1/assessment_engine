#!/usr/bin/env python3
"""Execute post-remediation verification audit with gemini-4-argon on Phase 1 SSOT reconciler."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_PHASE1_SSOT_VERIFICATION.md"

RECONCILER_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/services/score_reconciler.py"
).read_text(encoding="utf-8")
INTEGRITY_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/validation/mathematical_integrity.py"
).read_text(encoding="utf-8")
SYNC_CODE = (
    REPO_ROOT / "src/assessment_engine/application/sync_payload_scores.py"
).read_text(encoding="utf-8")
TEST_INT = (
    REPO_ROOT / "tests/integration/test_scoring_ssot_invariants.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect and Chief Quality Gatekeeper.

Review the remediated Phase 1 SSOT codebase to verify whether ALL previous findings have been completely resolved:
1. Language Purity: Zero Spanish words in code, identifiers, comments, docstrings, or tests (100% Technical English).
2. Topology & Tenant Agnosticism: Dynamic domain discovery in `sync_payload_scores.py` without hardcoding T1..T10, supporting any domain identifiers (D1..D8, custom slugs), CLI `--towers` parameter, safe non-substring path exclusion in integration tests.
3. Mathematical & Algorithmic Rigor: Vector-level scale determination in `_resolve_ssot_pillar_weights` (no fragile `weight > 1.0` heuristics), rejection of non-finite numbers (NaN/Inf) and negative weights in `_to_finite_decimal` and `_parse_finite_decimal`, duplicate pillar ID tracking with `consumed_ssot_indices`, atomic file writes with `os.fsync` and temp cleanup.

UPDATED FILES:

--- FILE 1: src/assessment_engine/domain/services/score_reconciler.py ---
{RECONCILER_CODE}

--- FILE 2: src/assessment_engine/domain/validation/mathematical_integrity.py ---
{INTEGRITY_CODE}

--- FILE 3: src/assessment_engine/application/sync_payload_scores.py ---
{SYNC_CODE}

--- FILE 4: tests/integration/test_scoring_ssot_invariants.py ---
{TEST_INT}

Provide:
1. Final Executive Verdict (PASS / FAIL) and Numerical Score (0.0 to 10.0).
2. Verification Checklist of the 3 Mandates.
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
