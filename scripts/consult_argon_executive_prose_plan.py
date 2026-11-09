#!/usr/bin/env python3
"""Consult gemini-4-argon to design a zero-defect, scale-invariant architecture for Fact-First Executive Prose and Granular CMMI Progression."""

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

PROMPT = """You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

THE SITUATION:
We are generating automated IT assessment reports for enterprises (ranging from $20M SMBs to $100B+ Global Tier-1s). We previously implemented Section 3.2 (Executive Pillar Diagnostic Cards) successfully. However, as a ruthless auditor, we identified three structural antipatterns that prevent our engine from being the undisputed #1 globally:

1. Syntactic Subject Anchor Gap (Anaphora Failure): The current AST compiler splits the architectural description string by period (`.`) and drops adversative connectors, but it blindly accepts orphaned sentences starting with demonstrative pronouns (e.g., "This generates the risk...", "Unlike the subsidiary..."). This looks robotic and broken.
2. Robotic Boilerplate in Rationale: In 90% of cases where the self-assessment aligns with the calibrated score, the prose opens with the exact same boilerplate: "The initial self-assessment and technical diagnostic fully align...". A Tier-1 consultant uses a "Fact-First" approach, opening directly with the operational reality of the capability, not a survey comparison (unless there is a massive divergence).
3. Coarse-Grained Maturity Matrix: The `cmmi_progression_matrix.json` maps milestones at the Tower level (e.g., 10 categories like `FACILITIES`). This results in absurd recommendations, like suggesting electrical SPOF removal inside an HVAC Cooling pillar. We need a 1:1 granular mapping (50 archetypes, one for each specific capability).

USER MANDATES:
1. Universal & Scale-Invariant: This MUST work for ANY company in the world. Zero hardcoding of specific towers, clients, or industries in the Python code.
2. 100% Technical English Codebase: Zero Spanish words, tokens, or variables in the Python code. Localization is purely delegated to JSON dictionaries (`locales.json`).
3. Absolute Quality & Zero Defects: Ensure string operations are safe, JSON structures are extensible, and edge cases (missing data, malformed sentences) default gracefully to safe localized constants.
4. "Think before coding": Provide a profound, zero-error, multi-phase architectural execution plan before modifying any code.

YOUR TASK:
Analyze this situation and provide a structured, phased execution plan to build the "Fact-First Executive Synthesis & Granular Progression Engine":
1. Anaphora Resolution Guard: How do we algorithmically detect and strip orphaned sentences (starting with "This", "These", "However", "Unlike") to ensure the first sentence always contains a substantive subject?
2. Fact-First Dynamic Templates: How do we refactor `_build_diagnostic_rationale` and `locales.json` to eliminate the repetitive boilerplate and focus purely on the capability's operational stability vs. its resilience gap?
3. 50-Pillar Granular Ontology: Detail the schema structure required in `cmmi_progression_matrix.json` to map 50 specific capability archetypes (e.g., `T1_P2_HVAC`, `T6_P2_PAM`) instead of 10 generic towers.
4. Execution Steps: Provide exact, sequenced implementation steps for `in_memory_asis_compiler.py` and the JSON policies.

Provide the response strictly in 100% Technical English, formatted with YAML front matter for documentation governance.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print("Consulting Argon for Fact-First Executive Prose & Granular CMMI Plan...")
    response = client.models.generate_content(model=model, contents=PROMPT)

    out_file = REPO_ROOT / "docs/architecture/ARGON_FACT_FIRST_PROSE_AND_GRANULAR_CMMI_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    front_matter = (
        "---\n"
        "status: Verified\n"
        "owner: docs-governance\n"
        "source_of_truth:\n"
        "- docs/README.md\n"
        "last_verified_against: 2026-11-08\n"
        "applies_to:\n"
        "- gemini\n"
        "- architecture\n"
        "doc_type: operational\n"
        "diataxis: reference\n"
        "verification_mode: editorial\n"
        "---\n"
    )
    out_file.write_text(front_matter + response.text, encoding="utf-8")

    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {out_file.name})")
    print("=" * 80)


if __name__ == "__main__":
    main()
