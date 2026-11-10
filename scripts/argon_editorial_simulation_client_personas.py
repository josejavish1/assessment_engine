#!/usr/bin/env python3
"""Simulation of Molins CTO, CIO, and Super-Specialist Forensic Auditor.

Audits the actual Executive Snapshot of all 10 Molins towers currently generated on disk:
1. CTO of Molins (Pragmatic plant engineer, knows every switch, SimpliVity node, kiln, and truck scale)
2. CIO of Molins (Strategic IT executive, board defensibility, budget, Broadcom, team structure)
3. Super-Specialist Forensic Auditor (Hyper-critical nitpicker searching for contradictions, bugs, hallucinations)

Rates each of the 10 towers out of 10 and delivers their exact, unvarnished dialogue and verdict.
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

towers_data = {}
for i in range(1, 11):
    p = REPO_ROOT / f"working/molins/T{i}/blueprint_t{i}_payload.json"
    if p.exists():
        d = json.load(open(p, encoding="utf-8"))
        towers_data[f"T{i}"] = {
            "name": d.get("tower_name"),
            "score": d.get("score") or d.get("maturity_score"),
            "ale": d.get("total_fair_ale"),
            "executive_snapshot": d.get("executive_snapshot", {}),
        }

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)
print(f"Connecting to Reasoning model '{model_name}' for 3-Persona Client Simulation...")

prompt = f"""You are simulating an intensive, adversarial review meeting with 3 key figures at Molins evaluating the 10 Specialist Annex Executive Snapshots:

THE 3 REVIEWERS:
1. The CTO of Molins: Pragmatic industrial engineering veteran. Knows the Sant Vicenç plant inside out, knows the SimpliVity nodes, knows the quarry, knows the truck scales (básculas), hates consultant fluff, respects brutal physical accuracy.
2. The CIO of Molins: Corporate IT leader. Reports to the Executive Committee / Board. Cares about budgets, Broadcom renewal cliff, SECIL Portugal debt, team bandwidth (5 internal staff), and board defensibility.
3. The Super-Specialist Forensic Auditor (Tier-1 Nitpicker): World-class auditor hunting for logical contradictions, cross-tower repetition, hallucinations, and ungrounded claims.

THE ACTUAL DATA OF THE 10 TOWERS UNDER REVIEW:
{json.dumps(towers_data, indent=2, ensure_ascii=False)}

TASK:
For EACH of the 10 Towers (T1 to T10):
1. CTO's Reaction: What does the CTO say? Does he believe it?
2. CIO's Reaction: What does the CIO say? Does he find it actionable for the Board?
3. Forensic Auditor's Critique: What flaw, contradiction, or strength does the auditor detect?
4. Numerical Score (0 to 10) awarded to that tower's executive snapshot.

FINALLY:
- Overall Scorecard across all 10 towers.
- Final Verdict: Would the CTO and CIO sign off on these executive summaries to be delivered to the Board of Directors tomorrow morning?

Format the response in authoritative, realistic, high-impact Markdown.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/audits/MOLINS_CTO_CIO_AUDITOR_SIMULATION.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved 3-Persona Client Simulation report to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:2500] + "\n... [TRUNCATED] ...")
print("=" * 80)
