#!/usr/bin/env python3
"""Dual-Persona Adversarial Audit (Tough CTO & SOTA Specialist) for all 10 Towers.

Evaluates the synthesized risks from the newly generated blueprints.
"""

from __future__ import annotations

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

def load_tower_risks(tower_code: str) -> str:
    """Loads the risk payload for a specific tower."""
    payload_path = REPO_ROOT / f"working/molins/{tower_code}/blueprint_{tower_code.lower()}_payload.json"
    if not payload_path.exists():
        return f"No payload found for {tower_code}"
    
    with open(payload_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    findings_summary = []
    for pillar in data.get("pillars_analysis", []):
        pillar_id = pillar.get("pillar_id")
        for hc in pillar.get("health_check_asis", []):
            finding = hc.get("finding", "")
            risk = hc.get("business_risk", "")
            severity = hc.get("severity", "UNKNOWN")
            findings_summary.append(f"- [{pillar_id}] [{severity}] Finding: {finding} | Risk: {risk}")
            
    return "\n".join(findings_summary) if findings_summary else "No explicit risks logged."

def main():
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Connecting to Reasoning model '{model_name}' for Dual-Persona Audit...")
    
    audit_report = "# DUAL-PERSONA ADVERSARIAL RISK AUDIT (TOUGH CTO & SOTA SPECIALIST)\n\n"
    
    for i in range(1, 11):
        tower_code = f"T{i}"
        print(f"Auditing {tower_code}...")
        
        risks_text = load_tower_risks(tower_code)
        
        prompt = f"""You are 'gemini-4-argon', acting simultaneously as two distinct personas evaluating the risks identified for Technology Tower {tower_code}.

THE TARGET AUDIENCE:
We have generated technical risk findings for a client in the heavy manufacturing/cement industry ($1.14B revenue).

HERE ARE THE SYNTHESIZED RISKS FOR TOWER {tower_code}:
{risks_text}

YOUR MISSION:
Evaluate these risks rigorously from two separate perspectives.

PERSONA 1: THE TOUGH CLIENT CTO
- You are a highly defensive, deeply technical CTO who knows your own infrastructure perfectly.
- You hate generic consultant fluff ("buzzword bingo").
- You evaluate risks based on operational reality, budget constraints, and whether the finding accurately captures the pain of the business without exaggerating.
- Do these risks sound like a Tier-1 consultancy actually listened to the context session, or do they sound like generic boilerplate?
- Challenge the severity and the business impact. Are the impacts real?

PERSONA 2: THE TIER-1 GLOBAL DOMAIN SPECIALIST (SOTA VALIDATION)
- You are an uncompromising, world-class Principal Engineer / Fellow specializing exclusively in this tower's domain.
- You evaluate the risks against the absolute State of the Art (SOTA) in 2026.
- Cite specific, modern architectural patterns, academic papers, or industry standards (e.g., NIST, IEEE, ACM, DORA, NIS2, FAIR) that validate or invalidate the identified risks.
- Is the technical diagnosis accurate, deep, and structurally sound?

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS FOR THIS TOWER:

## TOWER {tower_code} AUDIT

### PERSONA 1: TOUGH CLIENT CTO EVALUATION
(Provide a brutal, honest, 2-3 paragraph critique from the CTO's perspective. Highlight what is good and what feels weak/generic.)

### PERSONA 2: TIER-1 DOMAIN SPECIALIST (SOTA VALIDATION)
(Provide a rigorous, deeply technical 2-3 paragraph validation. Cite specific concepts, standards, or SOTA architectural papers.)

### FINAL DIAGNOSIS & ACTIONABLE IMPROVEMENTS
(1 paragraph summarizing what is currently correct and strong, followed by 1-2 bullet points of severe gaps or things that must be improved).

Remember: 100% Technical English. Be unforgiving, precise, and highly analytical.
"""
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        
        audit_report += response.text + "\n\n---\n\n"
        print(f"✓ Completed audit for {tower_code}.")

    # Apply governance front matter
    front_matter = """---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
doc_type: operational
diataxis: reference
verification_mode: editorial
---

"""
    
    audit_file = REPO_ROOT / "docs/audits/ARGON_DUAL_PERSONA_RISK_AUDIT_ALL_TOWERS.md"
    audit_file.write_text(front_matter + audit_report, encoding="utf-8")
    print(f"\n✓ Saved formal audit report to {audit_file.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()
