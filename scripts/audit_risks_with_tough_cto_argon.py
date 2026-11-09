#!/usr/bin/env python3
"""Adversarial Audit: Simulation of a Tough, Senior Tier-1 Industrial CTO Reviewing Risks Across All 10 Towers."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.adapters.compilers.in_memory_asis_compiler import derive_in_memory_fair_risks
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

# Extract full risk registers across all 10 towers
towers_risk_data = {}
for t in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]:
    p = REPO_ROOT / f"working/molins/{t}/blueprint_{t.lower()}_payload.json"
    if not p.exists():
        continue
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)

    risks, _ = derive_in_memory_fair_risks(d, doc_lang="es", currency="€")
    towers_risk_data[t] = {
        "tower_code": t,
        "tower_name": d.get("tower_name") or d.get("document_meta", {}).get("tower_name"),
        "annual_revenue": d.get("annual_revenue") or d.get("document_meta", {}).get("annual_revenue"),
        "total_fair_ale": d.get("total_fair_ale"),
        "total_fair_p90": d.get("total_fair_p90"),
        "total_fair_max": d.get("total_fair_max"),
        "num_risks": len(risks),
        "risks": [
            {
                "id": r.get("id"),
                "pillar_id": r.get("pillar_id"),
                "capability": r.get("capability"),
                "finding": r.get("finding"),
                "business_risk": r.get("business_risk"),
                "tef": r.get("tef"),
                "lm": r.get("lm"),
                "lef": r.get("lef"),
                "sle": r.get("sle"),
                "ale": r.get("ale"),
                "p90": r.get("p90"),
                "ownership_type": r.get("ownership_type")
            }
            for r in risks
        ]
    }

prompt_evidence = json.dumps(towers_risk_data, indent=2, ensure_ascii=False)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

CTO_AUDIT_PROMPT = f"""You are 'gemini-4-argon' simulating the persona of an **Uncompromising, Battle-Hardened Group CTO & Chief Risk Officer** of a multinational heavy industrial enterprise (€1.14B annual revenue, 24/7 continuous clinker kilns, cement grinding, automated batch dispatch, quarry operations, and international subsidiaries).

You have spent 25 years running industrial infrastructure. You have zero tolerance for:
1. **Academic Fluff & Hand-Waving:** Risks that describe generic IT inconveniences without quantifying factory downtime, lost shipping loads, or legal liability.
2. **Financial Absurdity & Calibration Disconnect:** ALEs (Annual Loss Expectancy) or Single Loss Expectancies (SLE) that are absurdly tiny (€500 for a plant halt?) or wildly exaggerated (€50M for a laptop patch issue). Every euro must tie back to downtime cost per hour (€10k-€50k/hr on kilns/dispatch), regulatory fines (NIS2), or tangible hardware CapEx.
3. **Cross-Domain Duplication & Blurry Custody:** Towers claiming risks that belong to another domain (e.g., Compute claiming physical power failure; Workplace claiming weighbridge hardware).
4. **Unrealistic Threat Frequencies (TEF) or Vulnerabilities (VULN):** Giving a 5.0 frequency (multiple times a year) to events that would literally shut down the company, or rating severe unpatched vulnerabilities as "low impact".

HERE IS THE COMPLETE DERIVED RISK REGISTER ACROSS ALL 10 TOWERS:
{prompt_evidence}

YOUR MANDATE AS TOUGH SENIOR CTO:
Deliver an unsparing, exhaustive forensic audit of the Risk Dossiers across all 10 towers before they are presented to the Executive Board.

For EACH tower (T1 to T10):
1. **CTO Score (0.0 to 10.0):**
   - **Actuarial Realism & Financial Credibility (25%)**: Are ALE, SLE, and P90 mathematically grounded in Molins's revenue and plant downtime costs?
   - **Operational Depth & Grounding (25%)**: Do the findings and business risks reflect actual cement/industrial operations (kilns, mills, weighbridges, básculas, NetApp, Zabbix, NIS2)?
   - **Custody Purity & Non-Duplication (25%)**: Does this tower own its risks cleanly, or does it steal problems from other towers?
   - **Board-Level Actionability (25%)**: Does this risk give the CFO/Board a clear, defensible reason to allocate CapEx/OpEx, or will it be laughed out of the boardroom?
2. **The CTO's Verdict:**
   - What is dead-on and bulletproof?
   - What is soft, flawed, or dangerously miscalibrated?
   - What would the CTO challenge in a brutal interrogation?
3. **Exact Remediation Directives:**
   - Specific numbers, phrasing, or ownership adjustments needed to achieve a 10.0/10.0 benchmark.

Conclude with a consolidated Scorecard Table (T1 to T10) and an overall Executive Verdict.
Language of the report: Spanish (Technical & Direct Executive Prose).
"""


def main() -> None:
    print("Initiating Tough Senior CTO Adversarial Risk Audit across all 10 towers with gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=CTO_AUDIT_PROMPT,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_TOUGH_CTO_RISK_AUDIT_ALL_TOWERS.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    front_matter = """---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
- risks
doc_type: operational
diataxis: reference
verification_mode: editorial
---

"""
    out_file.write_text(front_matter + response.text, encoding="utf-8")

    print("=" * 80)
    print("ARGON TOUGH SENIOR CTO RISK AUDIT REPORT:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Full audit report written to {out_file}")


if __name__ == "__main__":
    main()
