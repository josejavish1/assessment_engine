#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Definitive Upstream Ingestion & Context Routing Master Plan.

Addresses the root causes of cross-tower contamination and silent missing data imputation:
1. Monolithic transcript ingestion causing LLM hallucination/contamination.
2. Silent dropping of invalid/missing questionnaire data leading to false scoring.

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Multi-phase implementation plan with strict Quality Gates.
3. Universal scalability and zero hardcoding (multi-tenant agnostic).
4. Pure Clean Architecture.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def generate_upstream_refactor_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: UPSTREAM INGESTION & CONTEXT ROUTING MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & CONTEXT:
While we successfully overhauled the downstream mathematical scoring and output generation, the upstream data ingestion (`build_case_input.py`) remains structurally flawed. We applied tactical overrides to the generated JSON payloads to fix cross-tower contamination (e.g., 613 days of SimpliVity leaking into NetApp) and missing data (e.g., T4.P4.K3 ","). These tactical fixes do not scale to new clients.

We must implement a definitive architectural solution at the very source of data ingestion to guarantee Tier-1 World Class quality out-of-the-box for any global enterprise.

THE STRUCTURAL DEFECTS TO SOLVE UPSTREAM:

1. MONOLITHIC CONTEXT INGESTION (CROSS-TOWER CONTAMINATION):
   - Flaw: The entire interview transcript is ingested as a monolithic text block and fed to every tower prompt. This causes the LLM to hallucinate connections and duplicate facts across disparate towers (e.g., FinOps analyzing SCADA).
   - Architectural Fix: Design a `TowerContextBuilder` or `EpistemicGraphRouter` in the ingestion layer. The system must parse the raw transcript and route specific evidence fragments strictly to their relevant MECE domain towers based on semantic mapping. Tower 8 (FinOps) MUST ONLY receive FinOps-related transcript fragments.

2. SILENT MISSING DATA DISCARDING (FALSE IMPUTATION):
   - Flaw: The regex parser in `build_case_input.py` (`RESPONSE_RE`) silently ignores any response that is not a clean number (e.g., `,`, `N/A`, empty). This prevents the system from explicitly tracking missing KPIs, which later forces downstream calculators to average over a reduced set without warning the business user.
   - Architectural Fix: Design a `MissingDataCircuitBreaker` and strict typing schema. The parser must detect all expected KPIs. If a KPI response is missing or invalid, it must explicitly record an `EvidenceStatus.MISSING_OR_INVALID` object in the payload. The downstream systems must loudly flag this missing data, prohibiting silent imputation.

CORE INVARIANTS:
- 100% Technical English in code, variables, classes, docstrings, comments, logs, and prompt files.
- Zero Hardcoding: The context router and parser must be universal, driven by taxonomy, not hardcoded client rules.
- Pure Clean Architecture: Keep ingestion concerns separate from domain logic.

YOUR DELIVERABLE:
Write a comprehensive, publication-grade MASTER ARCHITECTURAL BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE16_UPSTREAM_INGESTION_REFACTOR.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY: The paradigm shift to strict upstream evidence gating.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 1: Missing Data Circuit Breaker (Strict parser and explicit MISSING state in `build_case_input.py`).
   - Phase 2: MECE Context Routing Engine (Extracting and mapping transcript fragments to specific Tower IDs before payload assembly).
   - Phase 3: Downstream integration of explicit MISSING states (e.g., generating "Data absent" markers in the AST instead of silently averaging).
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

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE16_UPSTREAM_INGESTION_REFACTOR.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    generate_upstream_refactor_master_plan()
