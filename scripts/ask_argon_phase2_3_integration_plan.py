#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the detailed implementation plan for Phase 2 (ScoringEngine Integration)
and Phase 3 (Evidence Ledger Retrieval).

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Universal scalability and zero hardcoding (multi-tenant agnostic).
3. Pure Clean Architecture and 100% deterministic logic.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def generate_integration_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: SCORING & EVIDENCE INTEGRATION DETAILED PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & CONTEXT:
We have just completed Phase 1 of the Universal Generator Refactor by creating the 100% deterministic `ScoringEngine` (`src/assessment_engine/domain/scoring_engine.py`).
We must now plan the exact architectural implementation for Phase 2 and Phase 3 to guarantee world-class, Tier-1 quality, free of bugs, antipatterns, and hardcoding, suitable for any global enterprise.

Phase 2: Integrate `ScoringEngine` into the orchestration flow (`run_tower_blueprint_engine.py`, `run_executive_annex_synthesizer.py`).
Phase 3: Implement Raw Evidence Ingestion and the Evidence Ledger (retrieval by KPI in `build_case_input.py` and `build_evidence_ledger.py`).

THE CHALLENGE:
1. The LLM must be completely stripped of its ability to manipulate, decide, or interpolate scores and maturity bands. It must receive the deterministic `audit_trail` from `ScoringEngine` as immutable truth.
2. Evidence must be indexed and retrieved strictly by KPI. We must eliminate the practice of feeding lossy, generalized summaries to the LLM. The LLM must receive the exact raw transcription excerpts associated with the specific KPI to enforce the "Fail-Closed for Technical Facts" rule.

CORE INVARIANTS:
- 100% Technical English in code, variables, classes, docstrings, comments, logs, and prompt files.
- Zero Hardcoding: Algorithms must be universal, scaling to any vertical or company size.
- Pure Clean Architecture: Strict separation of concerns (Mathematical Domain vs. Language Rendering).

YOUR DELIVERABLE:
Write a comprehensive, exhaustive, publication-grade DETAILED ARCHITECTURAL BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE13_SCORING_EVIDENCE_INTEGRATION.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO: The paradigm shift from LLM-as-Calculator to LLM-as-Renderer.
2. DETAILED IMPLEMENTATION STRATEGY:
   - Phase 2 Implementation:
     - Exact modifications required in `run_tower_blueprint_engine.py` to intercept the raw JSON matrix inputs, pass them to `ScoringEngine`, and inject the immutable `audit_trail` into the `context_str` for the LLM.
     - Stripping score calculation logic from prompt files.
   - Phase 3 Implementation:
     - Re-architecting `build_case_input.py` and `build_evidence_ledger.py` to index `EvidenceItem` objects by `tower_id -> pillar_id -> kpi_id`.
     - Defining the `EvidenceItem` and `Claim` schemas to support Validation States (Exploratory, Contrasted, Evidenced).
     - Designing the retrieval mechanism to feed only KPI-specific raw excerpts into the LLM prompt.
3. QUALITY GATES & VERIFICATION ORACLES: Deterministic pytest validation suites to guarantee zero regressions.
"""

    print("Sending prompt to Gemini-4-Argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE13_SCORING_EVIDENCE_INTEGRATION.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    generate_integration_plan()
