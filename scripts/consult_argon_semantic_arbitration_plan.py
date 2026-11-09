#!/usr/bin/env python3
"""Consult gemini-4-argon to design a Universal Semantic Arbitration mechanism."""

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
We are generating automated IT assessment reports for enterprises (ranging from $20M SMBs to $100B+ Global Tier-1s).
We have detected a critical editorial and epistemological anomaly in the AST-based DOCX compiler (`in_memory_asis_compiler.py`) and the payload hydrator:
1. Low Maturity False Context (CMMI < 2.2): The compiler extracts the first sentence of the `asis_architecture_description` to use as the "Observed Operational State". However, this first sentence is often generic architectural context (e.g., "The architecture combines on-premise and cloud...") rather than the actual factual reason for the low score (e.g., "SPOFs are not identified and failover is manual").
2. High Maturity False Positives (CMMI >= 4.0): In some cases, the client survey claimed a 4.5 score (e.g., for PAM or Kubernetes), but the qualitative transcription reveals the reality is a 1.0 (e.g., "we share root passwords", "we don't use Kubernetes"). The JSON payload retains the 4.5 score but contains negative text. The compiler blindly labels negative text as "Operational Strength" because the numerical score is high.
3. Robotic Template Leakage: Sometimes the LLM or template outputs boilerplate like "deficit in sre (where applicable)..." which leaks into the final DOCX.

USER MANDATES:
1. Universal & Scale-Invariant: This MUST work for ANY company in the world. Zero hardcoding of "Molins" or any specific tower/pillar data.
2. 100% Technical English Codebase: Zero Spanish words, tokens, or variables in the Python code. Localization is purely delegated to JSON dictionaries.
3. Absolute Quality: We want to be #1 globally. The delivered text must be ruthlessly coherent: if a score is 1.0, the text must explain why it's broken. If a score is 4.5, it cannot contain negative findings labeled as strengths.
4. "Think before coding": Provide a profound, zero-error, multi-phase architectural execution plan before modifying any code.

YOUR TASK:
Analyze this situation and provide a structured, phased execution plan to build a "Universal Epistemological Arbitrator":
1. Epistemic Reconciliation: How do we algorithmically force the JSON numerical score and the text payload to be coherent BEFORE they reach the DOCX compiler? (e.g., lowering a 4.5 to 1.5 if the text detects severe vulnerabilities).
2. Semantic Extraction: How do we extract the TRUE operational state for low maturity pillars instead of just `.split('.')[0]`?
3. Robotic Text Suppression: How do we implement a deterministic regex/AST filter to strip template placeholders like "(where applicable)" or "[insert here]"?
4. Execution Steps: Detail exact module changes in `TowerPayloadHydrator`, `in_memory_asis_compiler.py`, or a new `SemanticArbitrator` class in 100% Technical English.

Provide the response strictly in 100% Technical English, formatted with YAML front matter for documentation governance.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print("Consulting Argon for Universal Semantic Arbitration Plan...")
    response = client.models.generate_content(model=model, contents=PROMPT)

    out_file = REPO_ROOT / "docs/architecture/ARGON_UNIVERSAL_SEMANTIC_ARBITRATION_PLAN.md"
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
