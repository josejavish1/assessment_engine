#!/usr/bin/env python3
"""Run post-remediation audit with gemini-4-argon on Phase 2 pipeline integrity."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_PHASE2_PIPELINE_VERIFICATION.md"

BLUEPRINT_ENGINE_EXCERPT = (
    REPO_ROOT / "src/assessment_engine/application/run_tower_blueprint_engine.py"
).read_text(encoding="utf-8")[1250:1350]

RESYNTH_CODE = (
    REPO_ROOT / "scripts/resynthesize_domains_from_raw_transcription.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect and Chief Quality Gatekeeper.

Review the remediated Phase 2 Pipeline Integrity implementation:
1. Language Purity: 100% Technical English, zero Spanish words in code, variables, signatures, docstrings, comments, exceptions, or logs.
2. Tenant & Topology Agnosticism: Clean domain discovery (`discover_tenant_domains`) supporting arbitrary domain counts and names (D1..D8, T1..T10, custom slugs), CLI parameters (`--client-id`, `--domains`), no hardcoded client paths or 10-tower nomenclature.
3. Mathematical & Algorithmic Rigor: Phase 8.1 SSOT reconciliation gatekeeper in `run_tower_blueprint_engine.py` and `resynthesize_domains_from_raw_transcription.py`, strict assertion of `assert_tower_mathematical_integrity`, atomic persistence with `os.fsync`.

FILES:

--- FILE 1: Phase 8.1 in src/assessment_engine/application/run_tower_blueprint_engine.py ---
{BLUEPRINT_ENGINE_EXCERPT}

--- FILE 2: scripts/resynthesize_domains_from_raw_transcription.py ---
{RESYNTH_CODE}

Provide:
1. Final Executive Verdict (PASS / FAIL) and Numerical Score (0.0 to 10.0).
2. Verification Checklist of the 3 Mandates.
3. Architectural Certification.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing Phase 2 post-remediation audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Certification saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON PHASE 2 VERIFICATION:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:60]:
        print(line)
    if len(lines) > 60:
        print(f"... ({len(lines) - 60} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
