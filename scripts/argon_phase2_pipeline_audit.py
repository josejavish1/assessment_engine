#!/usr/bin/env python3
"""Execute adversarial audit with gemini-4-argon across Phase 2 Pipeline Integrity code."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_PHASE2_PIPELINE_AUDIT.md"

BLUEPRINT_ENGINE_EXCERPT = (
    REPO_ROOT / "src/assessment_engine/application/run_tower_blueprint_engine.py"
).read_text(encoding="utf-8")[1250:1320]

RESYNTH_CODE = (
    REPO_ROOT / "scripts/resynthesize_all_10_towers_from_raw_transcription.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect and Chief Quality Gatekeeper.

Perform an UNCOMPROMISING, ADVERSARIAL AUDIT of the Phase 2 Pipeline Integrity and Stochastic Boundary Enforcement implementation.

THE USER'S MANDATES FOR THIS AUDIT:
1. LANGUAGE DECOUPLING LAW:
   - All code, variable names, function signatures, docstrings, comments, exceptions, logs, and tests MUST be 100% Technical English.
   - ZERO SPANISH WORDS in the code! Spanish is strictly reserved for the human user conversation in chat and client delivery templates (via locales.json). Check every identifier, comment, and log string.
2. ZERO HARDCODED NUMBERS & VERTICAL/TENANT AGNOSTICISM:
   - The pipeline must work seamlessly for ANY company in the world (from a $20M mid-market firm to a $500B Fortune 10 global conglomerate).
   - The engine must work for ANY vertical (Banking, Healthcare, Retail, Technology, Heavy Manufacturing, Public Sector).
   - The topology must support any number of domains/towers (not hardcoded to T1..T10; support D1..D8, custom domain slugs, etc.) and any N-pillar topology with arbitrary valid weights.
   - Scripts must support dynamic tenant arguments (e.g. CLI parameter `--client-id`) rather than hardcoding client names.
3. MATHEMATICAL & ALGORITHMIC RIGOR:
   - Identify bugs, edge cases (missing scoring_output.json, corrupted files, unhandled exceptions, race conditions, atomic persistence), performance traps, or anti-patterns.

FILES UNDER AUDIT:

--- FILE 1: Phase 8.1 in src/assessment_engine/application/run_tower_blueprint_engine.py ---
{BLUEPRINT_ENGINE_EXCERPT}

--- FILE 2: scripts/resynthesize_all_10_towers_from_raw_transcription.py (Excerpt around synthesis and reconciliation) ---
{RESYNTH_CODE[RESYNTH_CODE.find("async def synthesize_tower"):RESYNTH_CODE.find("async def synthesize_tower") + 4500]}

YOUR TASK:
Provide an exhaustive, brutally honest audit report:
1. Executive Verdict (PASS / REVISE / FAIL) with numerical score (0.0 to 10.0).
2. Forensic Inventory of Defects:
   - Language Purity violations (List exact line numbers and Spanish words if any).
   - Hardcoding & Tenant/Topology Bias (e.g. assumption of T1..T10, hardcoded tenant names or file paths).
   - Mathematical & Algorithmic edge cases or bugs.
3. Complete Production-Grade Remediation Code for any file requiring patches.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing Phase 2 adversarial audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Audit report saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON PHASE 2 AUDIT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
