#!/usr/bin/env python3
"""Consult gemini-4-argon to evaluate scalability findings and formulate a remediation plan."""

import json
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

CENSUS_FILE = REPO_ROOT / "docs/audits/scalability_blockers_census.json"

def main():
    if not CENSUS_FILE.exists():
        print(f"Error: Census file not found at {CENSUS_FILE}")
        sys.exit(1)

    findings = json.loads(CENSUS_FILE.read_text(encoding="utf-8"))

    prompt = f"""You are 'gemini-4-argon', Principal Enterprise Architect, Chief Cybersecurity Auditor, and Supreme Code Quality Arbiter.

CRITICAL USER MANDATE & ALERT:
The user demands absolute universal scalability. The engine MUST work for ANY enterprise in the world, from an SMB ($20M) to a top Tier-1 global corporation ($500B), across ANY vertical (banking, manufacturing, healthcare, public sector, retail, aviation), in ANY target language (en, es, pt, fr, de, ja).
The code must be 100% Technical English without a single word of Spanish (Spanish is ONLY allowed as output data in locales).
There must be ZERO hardcoded values (no fixed EUR currencies, no fixed locales in core code, no hardcoded regulations masquerading as core logic).
We want 100% quality in deliverables with ZERO bugs, problems, or anti-patterns.

CONTEXT:
We have just executed a strict 4-Vector Global Scalability Audit. 
Here are the exact findings from the census:
{json.dumps(findings, indent=2)}

YOUR MISSION:
1. Evaluate each finding individually. Determine if it is a genuine architectural error/hardcoding leak, or if it is "by design" (e.g., URN registrations in framework_urn.py are valid data declarations, not logic coupling).
2. Formulate a rigorous, phased Remediation Master Plan. We will execute this plan step-by-step later. DO NOT write the final code implementations now.
3. The plan must guarantee the code achieves the Tier-1 Global Scalability invariant.
4. Provide the response entirely in English as requested by the user, maintaining a strict, objective, and highly professional architectural tone.

OUTPUT FORMAT:
- FINDINGS EVALUATION: (Briefly categorize what needs fixing vs what is valid).
- MASTER REMEDIATION PLAN: (Break down the exact phases, e.g., Phase 1: Linguistic Decoupling, Phase 2: Actuarial Scale Currency Resolution, etc., detailing exactly what architectural pattern will be used to resolve the issues without introducing bugs).
"""

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    
    print(f"Consulting {model_name} (gemini-4-argon) for the Master Remediation Plan...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={
            "temperature": 0.0,
        }
    )
    
    out_path = REPO_ROOT / "docs/strategy/argon_universal_scalability_plan.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(response.text, encoding="utf-8")
    
    print(f"Argon's plan successfully written to: {out_path.relative_to(REPO_ROOT)}")
    print("\n--- Argon's Plan Output ---")
    print(response.text)

if __name__ == "__main__":
    main()
