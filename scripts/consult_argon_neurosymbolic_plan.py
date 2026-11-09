#!/usr/bin/env python3
"""Consult gemini-4-argon to architect a flawless, multi-phase plan for neurosymbolic synthesis."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect and Supreme Code Quality Arbiter for the Assessment Engine.

CRITICAL USER MANDATE & ALERT:
We have successfully prototyped a "Reverse-FAIR" actuarial synthesis where the LLM writes hyper-specific, stack-aware risk cards based on deterministic math pre-computed by Python. 

However, the user has halted implementation with the following strict directive:
"I want us to think carefully about how to approach it and in how many phases to guarantee zero errors, so we can be global Tier-1 for any vertical and any language. The code must be 100% in English. I want gemini-4-argon to think about it and do it without bugs or anti-patterns, nothing hardcoded. We need to ensure this doesn't generate problems for other companies (like small businesses)."

THE CHALLENGE:
Integrating live LLM calls directly into the document generation loop (AST compiler) is an anti-pattern. It introduces API latency, breaks offline CI/CD deterministic tests, causes "hallucinated sophistication" for low-maturity clients, and creates data drift.

YOUR MISSION:
Deliver a definitive, multi-phase master architectural blueprint to safely integrate this Neurosymbolic Synthesis into the production pipeline. 
The plan must ensure 100% decoupling, zero regressions, and absolute stability for CI/CD, while elevating the deliverable quality to global Tier-1.

The plan must address:
- PHASE 1: Persistent Caching Strategy (Single-Write, Infinite-Read). How to structure the `blueprint_tX_payload.json` so the LLM synthesis is only executed ONCE during the intelligence harvesting phase, allowing the AST compiler to remain 100% offline and instantaneous.
- PHASE 2: Offline Circuit Breakers & CI/CD Stability. How to implement an `--enrich-risks` flag or deterministic fallback so our 29 automated tests continue to run instantly without hitting API rate limits or failing due to network issues.
- PHASE 3: Adaptive Complexity Ceiling. How to design the LLM prompt and pipeline to adapt to the client's maturity (e.g., preventing the LLM from inventing "Kubernetes" or "Zero Trust" for a traditional SME that only uses local servers).
- PHASE 4: Phased Rollout & Validation. How to implement and verify these changes safely across the codebase.

Constraints:
- Respond in 100% Technical English.
- Do not provide code implementations yet, just the rigorous, step-by-step Architectural Plan.
- The plan must apply to ANY vertical and ANY language.
- Emphasize zero hardcoding and robust engineering practices.

Deliver your verdict with absolute technical authority.
"""

def main() -> None:
    print(f"Submitting uncompromising architecture request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_NEUROSYMBOLIC_IMPLEMENTATION_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nArchitecture Plan generated successfully. Report written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3000])
    if len(audit_report) > 3000:
        print("\n... [Report Truncated for CLI Display] ...\n")

if __name__ == "__main__":
    main()
