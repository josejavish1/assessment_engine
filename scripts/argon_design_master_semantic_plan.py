#!/usr/bin/env python3
"""Execute consultation with gemini-4-argon to design the complete multi-phase semantic integrity plan."""

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

OUTPUT_FILE = REPO_ROOT / "docs/architecture/ARGON_MASTER_SEMANTIC_INTEGRITY_BLUEPRINT.md"

PROMPT = """You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

USER MANDATE:
The user has approved our architectural diagnosis of Section 3.1 (cross-pillar contamination and hallucinated breach text, such as reporting SimpliVity RAM saturation under Fire Protection & Environmental Safety).
Before writing any code, the user explicitly mandates:
1. Think through the entire architecture carefully and define an exact multi-phase execution roadmap.
2. 100% Technical English: All code, variable names, function signatures, docstrings, comments, exceptions, logs, and tests must be in English. Zero Spanish words in the codebase. (Spanish is only for chat conversation and localized client output templates).
3. Zero Hardcoding: The architecture must be globally multi-tenant and vertical-agnostic. It must serve any company in the world (from a $20M mid-market firm to a $500B Fortune 10 conglomerate), in any vertical (Banking, Healthcare, Retail, Technology, Heavy Manufacturing, Public Sector), in any language, and for any domain topology (T1..T10, D1..D8, custom slugs).
4. Deliver 10/10 Quality: Zero bugs, zero anti-patterns, zero semantic drift.

YOUR MISSION:
Deliver a comprehensive, battle-hardened architectural design answering:
1. EXACTLY HOW MANY PHASES are needed, what will be programmed in each phase, and why?
2. How to leverage the existing `engine_config/ontologies/global_tech_ontology.yaml` and `engine_config/towers/*/tower_definition_*.json` without hardcoding any tenant names, vertical rates, or static text?
3. How `derive_in_memory_maturity_matrix` in `in_memory_asis_compiler.py` must be refactored to eliminate the naive `findings[0]` positional fallacy, ensuring:
   - Strengths are derived strictly from high-scoring KPIs (score >= 4.0).
   - Breaches are derived strictly from low-scoring KPIs (score < 4.0) belonging to that specific pillar.
   - If findings exist, they pass through a semantic gatekeeper; if an out-of-domain finding is detected, it is quarantined and replaced with a deterministic KPI-anchored formulation.
4. What automated unit and integration tests must be written to mathematically and ontologically certify that zero cross-pillar contamination exists across all deliverables?

Structure your output as an authoritative Engineering Design Document (EDD).
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Consulting gemini-4-argon on Master Semantic Integrity Blueprint ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Master blueprint saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON MASTER BLUEPRINT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
