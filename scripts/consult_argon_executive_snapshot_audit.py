#!/usr/bin/env python3
"""Adversarial Peer Review by gemini-4-argon: Per-Tower Executive Snapshots.

Evaluates the 'executive_snapshot' (Bottom Line, Strengths, Risks) across all 10 towers
for Molins, Starling Bank, and Rede D'Or. Determines if they are 10/10 C-Level quality,
free of consultant boilerplate, and packed with concrete physical/technical realities.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

def extract_snapshots(client_id: str, towers: list[str]) -> dict:
    data = {}
    for t in towers:
        p = REPO_ROOT / f"working/{client_id}/{t}/blueprint_{t.lower()}_payload.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
                data[t] = d.get("executive_snapshot", {})
    return data

clients = {
    "molins": extract_snapshots("molins", [f"T{i}" for i in range(1, 11)]),
    "starling_bank": extract_snapshots("starling_bank", ["T1", "T3", "T5", "T6", "T8", "T10"]),
    "rede_d_or_sao_luiz": extract_snapshots("rede_d_or_sao_luiz", [f"T{i}" for i in range(1, 10)])
}

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)
print(f"Connecting to Reasoning model '{model_name}' for Executive Snapshot Audit...")

prompt = f"""You are 'gemini-4-argon', the Principal Staff Systems Architect and Fortune 500 CTO/CRO.

THE CHALLENGE:
We need a 10/10 evaluation of the "Executive Snapshots" (the 1-page summary at the start of each technical Tower Annex) for 3 global companies:
1. Molins (Spain - Heavy Manufacturing)
2. Starling Bank (UK - FinTech)
3. Rede D'Or (Brazil - Healthcare)

The target audience for these Executive Snapshots are busy C-Level executives (CTO, CIO, CFO, CEO) who often only read this page. It must be a 10/10.

EVALUATION CRITERIA:
1. Concreteness & Anti-Boilerplate: Do they mention specific vendors, physical realities, and architectural bottlenecks (e.g., "SimpliVity RAM exhaustion", "Sant Vicenç twin data centers at 500m", "Oracle 10g Forms", "Active Directory single point of failure")? Or do they use empty consultant jargon ("Opportunities for optimization exist")?
2. Severity vs Reality: Do the operational benefits and structural risks align with the numerical score and the reality of the industry?
3. C-Level Impact: Does the "bottom_line" immediately convey the existential threat and the required investment strategy?
4. Multi-Tenant Purity: Did the LLM cross-contaminate languages or clients? (e.g. speaking Spanish in the UK report, or mentioning cement in the hospital report).

PAYLOAD DATA (Extract of the Executive Snapshots for each Tower):
{json.dumps(clients, indent=2)}

TASK:
Write a ruthless, comprehensive forensic audit of these executive snapshots. 
- Highlight what is a 10/10.
- Highlight where the text falls into empty "boilerplate" or fails to capture the true existential risks (like the single-person dependency in Croatia for Molins, or the 500m CPD distance).
- Provide a concrete architectural verdict on whether the `UniversalTowerSynthesizer` prompt needs to be radically sharpened to force the LLM to put the most critical technical facts into the `bottom_line` and `structural_risks` arrays.

Format your response in Markdown with clear sections, actionable critiques, and a final verdict. Be unsparing.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/audits/ARGON_EXECUTIVE_SNAPSHOT_AUDIT.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved Executive Snapshot audit report to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:2500] + "\n... [TRUNCATED] ...")
print("=" * 80)
