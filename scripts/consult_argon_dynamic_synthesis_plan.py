#!/usr/bin/env python3
"""Consult gemini-4-argon to architect the elimination of static analytical templates."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Chief Cybersecurity Auditor, and Supreme Code Quality Arbiter for the Assessment Engine.

CRITICAL USER MANDATE & ALERT:
The user correctly identified a profound architectural anti-pattern. We were about to "fix" the contradiction in Tower 6 (where a client with a 4.70/5.00 score was falsely accused of having "unvaulted shared administrative credentials") by adding logic to select different static string templates from `locales.json` based on the score (e.g., if score > 4.0 use optimistic text, else pessimistic).

The user explicitly halted this:
"I am not sure if that is an anti-pattern, program it like that... we must eradicate errors but knowing that the only thing is before we start programming we must think carefully about how we are going to approach it and in how many phases to guarantee that it is bug-free and that we will be a global Tier-1, for any vertical, in any language, and the code must be 100% in English... I want gemini-4-argon to think about it and do it without bugs, problems or anti-patterns, I don't want anything hardcoded, remember the goal is that it serves any company in the world... It cannot be that we fix it only for one client, we must identify the root cause and make a proposal so that for all clients the risks come out perfectly. But besides, I ask myself, are there superfluous risks or missing risks?"

THE ROOT CAUSE:
The AST compilation layer (`ast_appendices_builder.py`, `payload_to_ast.py`) relies on massive static text blocks in `engine_config/locales.json` (like `ch3_scorecard_by_tower`, `exec_narrative_p3`, etc.) to generate the analytical prose of the report. 
This is fundamentally flawed. A static catalog, even if branching by score, can NEVER accurately capture the true, nuanced risks of an arbitrary company in an arbitrary vertical. It forces the engine to "hallucinate" risks that aren't there (superfluous risks) and miss the ones that are (missing risks). 

The true risks and executive summaries should be dynamically synthesized by the LLM during the Intelligence Harvesting / Blueprint generation phase, leveraging the actual raw transcript and quantitative responses, and then passed as pure data to the AST compiler.

YOUR MISSION:
Deliver a definitive, multi-phase master architectural blueprint to completely eradicate static analytical templates from the presentation layer and transition to 100% dynamic, LLM-driven generative synthesis.

The plan must address:
- PHASE 1: Data Contract Re-Architecture (Defining what the JSON payload MUST contain so the AST compiler never has to guess or use a fallback catalog for narratives, risks, or executive summaries).
- PHASE 2: Dynamic Synthesis Engine (How and where in the pipeline the LLM should generate these highly specific, vertical-aware, client-tailored texts in the target language).
- PHASE 3: Purging the Static Baseline (Stripping `locales.json` of all analytical text, reducing it to only structural UI labels like "Executive Summary", "Table of Contents", etc.).
- PHASE 4: Validation (How to ensure no superfluous or missing risks exist in the final output).

Constraints:
- Respond in 100% Technical English.
- Do not provide code implementations yet, just the rigorous, step-by-step Architectural Plan.
- Ensure the architecture guarantees Tier-1 consulting quality for any global enterprise.

Deliver your verdict with absolute technical authority.
"""

def main() -> None:
    print(f"Submitting uncompromising architecture request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_DYNAMIC_SYNTHESIS_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nArchitecture Plan generated successfully. Report written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3000])
    print("\n... [Report Truncated for CLI Display] ...\n")

if __name__ == "__main__":
    main()
