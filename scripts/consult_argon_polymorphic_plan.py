#!/usr/bin/env python3
"""Consult gemini-4-argon for a flawless, multi-phase plan to implement the Polymorphic Open FAIR Actuarial Engine."""

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

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Code Quality Arbiter, and Chief Forensic Auditor for the Assessment Engine.

THE USER'S MANDATE:
"Before we start coding, we need to think carefully about how we are going to approach this and in how many phases to guarantee that it is bug-free and that we will be #1 worldwide. It must work for any company in the world (mid-size to Tier 1), any vertical, any language, and with totally different maturity levels.
The code must be 100% in English, not a single Spanish word. Spanish is only the language we speak and one of the output languages of the deliverables.
Increase the quality of the deliverables to 100%. I want gemini-4-argon to think about it and do it without bugs, problems, or anti-patterns. NO HARDCODING."

YOUR MISSION:
Deliver a comprehensive, bug-free, zero-hardcoding architectural Master Plan to implement the Polymorphic Open FAIR Actuarial Engine across the entire Assessment Engine.

The plan must address:
1. PHASE 1: Domain-to-Archetype Mapping Registry. How to dynamically map each of the 10 Towers to its primary Open FAIR loss archetype (Availability Outage, Capital Inefficiency, Productivity Toil, Regulatory Breach) without hardcoding logic inside the actuarial engine.
2. PHASE 2: Polymorphic Telemetry Ingestion. How `case_input.json` and the client profile must be expanded to dynamically provide the required financial variables for ALL archetypes (e.g., FTE count and salary for Productivity Toil, Annual Cloud Spend for Capital Inefficiency), not just `hourly_revenue_loss`.
3. PHASE 3: Actuarial Engine Refactoring. How to use Pydantic discriminated unions (ADTs) and abstract base classes in `src/assessment_engine/domain/actuarial/` to calculate the mathematical ALE cleanly for any given archetype.
4. PHASE 4: AST Compiler and Narrative Agnosticism. How `payload_to_ast.py` and the LLM prompts will dynamically adapt the narrative based on the `EconomicLossVector` type, completely eliminating the hardcoded "clearing outage" strings for FinOps/Workplace.
5. QUALITY GATES: What strict Pydantic validations and `pytest` fixtures must be written to guarantee 0% regressions.

Constraints:
- Respond in 100% Technical English.
- The design must be maximally elegant, using SOLID principles, Dependency Injection, and strict typing.
- Provide the exact phases and the architectural contracts we need to build. No full implementations yet, just the exact blueprint.

Deliver your Master Plan now.
"""

def main() -> None:
    print(f"Submitting Polymorphic FAIR planning request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    plan_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_POLYMORPHIC_FAIR_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(plan_report, encoding="utf-8")
    print(f"\nArchitecture Plan written to: {out_file}\n")
    print("=" * 80)
    print(plan_report[:3500])
    if len(plan_report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")

if __name__ == "__main__":
    main()
