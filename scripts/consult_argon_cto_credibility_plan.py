#!/usr/bin/env python3
"""Consult gemini-4-argon to architect a master plan for CTO-credible risk and financial synthesis."""

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
We have successfully eliminated hardcoded factory/cement industry terms and semantic inversions from our reporting engine. The AST compiler now outputs clean, well-formatted DOCX reports in multiple languages with mathematically correct FAIR (Factor Analysis of Information Risk) variance. 

HOWEVER, the user (acting as a skeptical, battle-tested CTO) has identified a critical "Uncanny Valley" problem in the generated content:
1. The Risk Cards are generated with generic, formulaic titles (e.g., "[RVS08] Operational Risk Scenario: Disaster Recovery Architecture & Failover - Operational Execution & Controls").
2. The risk descriptions do not cite the actual technology stack mentioned in the raw interview transcripts (e.g., Kafka, AWS Route 53, YubiKeys).
3. The financial numbers (ALE, Downtime Cost), while mathematically correct in their variance, feel abstract because the narrative does not tie the £44,000 loss directly to the specific technical failure mechanism (e.g., "Split-brain post-failover desynchronizing the Aurora Global database").

The user explicitly demands:
"I want a deep analysis... as a tough client CTO who knows everything and a top Tier-1 expert who knows the state-of-the-art and current papers. The most important thing is that the numbers must be 100% credible to a CTO and seem 100% real. Before we start programming, we must think carefully about how to approach it and in how many phases to guarantee zero errors, so we can be global Tier-1 for any vertical and any language. The code must be 100% in English. I want gemini-4-argon to think about it and do it without bugs or anti-patterns, nothing hardcoded."

YOUR MISSION:
Deliver a definitive, multi-phase master architectural blueprint to solve the "CTO Credibility Gap". 
You must design a mechanism that ensures the LLM synthesizes hyper-specific, stack-aware, and mathematically credible risk titles, findings, and financial justifications tailored to the exact client vertical, without ANY hardcoded Python string templates.

The plan must address:
- PHASE 1: Epistemic Evidence Mapping (How to ensure the LLM maps the generic KPI scores strictly to the specific technology components mentioned in the raw transcript).
- PHASE 2: Actuarial-Narrative Cohesion (How to force the LLM to justify the specific FAIR financial numbers—like a £44k ALE—using state-of-the-art SRE/Cybersecurity failure scenarios relevant to that client's stack).
- PHASE 3: Universal Dynamic Payload Injection (How to structure the pipeline so this deep synthesis is done once during ingestion, saved in the payload, and flawlessly rendered by the "dumb" AST compiler).
- PHASE 4: Validation (How to verify that the generated risks are CTO-credible and not generic boilerplate).

Constraints:
- Respond in 100% Technical English.
- Do not provide code implementations yet, just the rigorous, step-by-step Architectural Plan.
- The plan must apply to ANY vertical (FinTech, Healthcare, Logistics, etc.) and ANY language (the synthesis output language will be dynamic).

Deliver your verdict with absolute technical authority.
"""

def main() -> None:
    print(f"Submitting uncompromising architecture request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_CTO_CREDIBILITY_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nArchitecture Plan generated successfully. Report written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3000])

if __name__ == "__main__":
    main()
