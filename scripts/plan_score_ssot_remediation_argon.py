#!/usr/bin/env python3
"""Consult gemini-4-argon for the exact architectural remediation plan for Score SSOT."""

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

OUTPUT_FILE = REPO_ROOT / "docs/architecture/ARGON_SSOT_SCORE_REMEDIATION_PLAN.md"

PROMPT = """You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect and Chief Quality Gatekeeper (Google Cloud Fellow / FAIR Institute Fellow).

CONTEXT OF THE PROBLEM:
We have discovered a "Split-Brain" anti-pattern in the generated AS-IS reports (e.g. Molins Tower 1).
The issue:
1. The official quantitative maturity scores are calculated correctly by `src/assessment_engine/application/run_scoring.py` based on the user's questionnaire responses and official pillar/KPI weights defined in `engine_config/towers/*/tower_definition_*.json`. (e.g., Tower 1 overall score is exactly 2.61).
2. However, a subsequent step (`resynthesize_all_10_towers_from_raw_transcription.py`) asked an LLM to generate the `pillars_analysis` array based on forensic transcript evidence. The LLM hallucinated arbitrary flat scores (2.00, 2.20, 2.30) for the pillars, completely ignoring the deterministic scores calculated by `run_scoring.py`.
3. The AST compiler reads the 2.61 for the header, but iterates over the hallucinated `pillars_analysis` for the table, resulting in a mathematical absurdity where the total is higher than any of its parts.

ARCHITECTURAL ALIGNMENT:
- We do NOT want the LLM to invent scores.
- The Single Source of Truth (SSOT) for numerical maturity scores is the deterministic output of `run_scoring.py` (`build_scoring()`).
- The Epistemic Dissonance (the gap between what the client answered vs. the forensic reality found in the transcripts) is captured by the `EpistemicSynthesizer` (triggering `VERIFIED_DISSONANT` flag) and punished financially by the Open FAIR Actuarial Engine via increased ALE and VaR. The maturity score itself remains the faithful representation of the client's formal assessment.

YOUR MISSION:
Design a precise, multi-phase implementation roadmap to eradicate this split-brain bug and restore Mathematical SSOT across all pipelines.

MANDATES FOR THE PLAN:
1. 100% Technical English. No Spanish anywhere in the proposed code or architecture.
2. Zero Hardcoding. The solution must work for any tenant, any industry, any language, and any N-pillar tower topology.
3. Explicit Code Paths. Tell us exactly which Python scripts to modify, what functions to create, and how to sequence the execution.

Required Phases in your output:
- Phase 1: Payload Synchronization (How to inject the exact output of `build_scoring()` back into the JSON payloads of the towers, safely overwriting the LLM's hallucinated pillar scores without losing the LLM's generated narratives).
- Phase 2: Pipeline Integrity (How to ensure `resynthesize_all_10_towers_from_raw_transcription.py` or `run_tower_pipeline.py` enforces this SSOT after the LLM returns its generation).
- Phase 3: Validation (How to write automated tests to guarantee that `sum_product(pillars.score, pillars.weight) == tower.score` across all towers).

Output the complete, step-by-step technical plan.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Consulting gemini-4-argon via model: {model}...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Roadmap generated successfully at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON SSOT REMEDIATION PLAN SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
