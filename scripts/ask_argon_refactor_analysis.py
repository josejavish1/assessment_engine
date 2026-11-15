#!/usr/bin/env python3
"""
Invoke gemini-4-argon to perform a Root Cause Analysis and propose the New Flow
for the Universal Generator Refactor, addressing the 20-point structural feedback.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def generate_root_cause_analysis() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: UNIVERSAL REFACTOR ROOT CAUSE ANALYSIS")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    
    prompt = """
You are Gemini-4-Argon, Chief Systems Architect and Global Managing Partner for Enterprise Due Diligence.

MANDATE:
The latest portfolio review rated our 10-tower delivery at 6.0/10. The AI auditor explicitly stated:
"The system must transition from: [data -> summary -> LLM expands -> document] TO [original sources -> structured evidence model -> deterministic calculations -> traceable claims -> LLM writes ONLY what is accredited -> automatic validators -> document]."

The LLM CANNOT be the source of truth for weights, scoring, maturity bands, FAIR calculations, installed technologies, architectural facts, contradiction resolution, or missing data imputation.

BEFORE WE MODIFY CODE, YOU MUST PRODUCE THE ROOT CAUSE ANALYSIS AND NEW FLOW PROPOSAL.

STRUCTURE YOUR RESPONSE EXACTLY AS FOLLOWS (in Markdown format, 100% Technical English):

1. ROOT CAUSE IDENTIFICATION IN CURRENT ARCHITECTURE:
   For each of the major categories (Scoring/Weights, Fact vs. Inference/Hallucination, Evidence Retrieval, Contradictions, Missing Data, Cross-Tower Contamination, FAIR quantification, Language/Validation State, Widespread 'Expand' Prompting), explain exactly *why* the current architecture fails.

2. MODULES CAUSING THE BEHAVIOR:
   List the specific Python modules, prompts, or configuration files responsible for these defects (e.g., `payload_to_ast.py`, `build_case_input.py`, `blueprint_pilar_architect_prompt.yaml`, `chapter4_synthesizer.py`, etc.). Be highly specific about their current flawed logic.

3. PROPOSED NEW ARCHITECTURAL FLOW:
   Outline the new deterministic pipeline. Detail the creation of:
   - Single Source of Truth for the Framework (Master Matrix).
   - 100% Deterministic `ScoringEngine`.
   - `EvidenceItem` and `Claim` Ledgers (Claim-level evidence gating).
   - `ContradictionEngine` and Missing Data rules (Fail-closed technical facts).
   - `TowerContextBuilder` and `SharedFactRegistry` (MECE isolation).
   - `LanguagePolicyEngine` and Pre-Document Validators (`validate_framework()`, etc.).
   - Explicit separation of Fact, Evidence, Gap, Implication, Recommendation.

CORE INVARIANTS:
- 100% Technical English.
- No hardcoded solutions for specific clients or towers (must be universal).
- Emphasize "Fail-Closed for Technical Facts" and "Factual Parsimony".

Save this output to `docs/architecture/ARGON_UNIVERSAL_REFACTOR_ROOT_CAUSE_ANALYSIS.md`.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_UNIVERSAL_REFACTOR_ROOT_CAUSE_ANALYSIS.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Analysis successfully generated and saved to: {out_file}")
    return out_file

if __name__ == "__main__":
    generate_root_cause_analysis()
