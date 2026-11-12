import sys
import json
import re
from pathlib import Path
from typing import List, Dict

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

def extract_global_facts(towers_dir: Path) -> str:
    facts = []
    for fp in towers_dir.rglob("blueprint_*_payload.json"):
        with open(fp) as f:
            data = json.load(f)
            t_id = data.get("tower_id") or "UNKNOWN"
            for p in data.get("pillars_analysis", []):
                p_name = p.get("pillar_name") or p.get("pillar_id")
                desc = p.get("asis_architecture_description", "")
                if len(desc.split()) > 80:
                    facts.append(f"Fact in {t_id} / {p_name}: {desc[:200]}")
    return "\n".join(facts)

def rewrite_executive_snapshot(tower_id, tower_name, current_snapshot, global_facts):
    prompt = f"""You are a Principal Enterprise Architect conducting a forensic As-Is assessment for Cementos Molins.
Your objective is to rewrite the `executive_snapshot` for the entire domain: **{tower_name}** (Tower: **{tower_id}**).

### INPUT TELEMETRY:
1. Current Draft Snapshot (Contains Hallucinations/Cross-Domain Leaks): 
{json.dumps(current_snapshot, indent=2, ensure_ascii=False)}
2. Global Empirical Facts (Use as ground truth):
{global_facts}

### STRICT ARCHITECTURAL CONSTRAINTS:
1. ZERO HALLUCINATION. Do not invent vendors. 
2. STRICT DOMAIN ISOLATION. 
   - T1 is Physical DC / UPS / CRAC.
   - T2 is Compute / VMs / K8s.
   - T3 is Networking / Switches / WAN.
   - T4 is Storage / SAN / Backup.
   - T5 is DRP / BCP / Resilience.
   - T6 is Cybersecurity / Identity / NIS2.
   - T7 is ITSM / SRE / Observability / Helpdesk.
   - T8 is FinOps / Cloud Governance / M&A IT Contracts.
   - T9 is Workplace / EUC / Laptops / M365 / MDM.
   - T10 is OT / Factory Core Apps / Scales / Oracle / SAP.
   Do NOT put physical server issues (T1/T2) in T9 (Workplace). Do NOT put network issues (T3) in T4. 
3. SOBER, BOARD-READY TONE. Eradicate bombastic words ("erosión reputacional", "catástrofe inminente", "espectacular"). Use dry, factual engineering language.
4. MUST BE IN SPANISH (Technical).

### MANDATORY OUTPUT STRUCTURE:
Return ONLY a valid JSON object with the following exact keys:
{{
  "bottom_line": "A single cohesive paragraph (80-120 words) summarizing the architectural baseline, inventory, and systemic state for this specific domain. No bullet points.",
  "operational_benefits": [
    "One sentence describing a verified empirical strength or consolidated standard in this domain.",
    "Another sentence describing a verified empirical strength.",
    "A third sentence describing a verified empirical strength."
  ],
  "structural_risks": [
    "One sentence describing a severe structural debt or operational bottleneck strictly in this domain.",
    "Another sentence describing a specific capacity limit or obsolescence in this domain.",
    "A third sentence describing a friction point or risk in this domain."
  ]
}}
Do NOT wrap the JSON in markdown code blocks. Just output raw JSON.
"""
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        return json.loads(raw_text.strip())
    except Exception as e:
        print(f"Error generating for {tower_id}: {e}")
        return current_snapshot

def main():
    towers_dir = REPO_ROOT / "working" / "molins"
    print("Extracting global facts...")
    global_facts = extract_global_facts(towers_dir)
    global_facts = global_facts[:20000]

    for fp in sorted(towers_dir.rglob("blueprint_*_payload.json")):
        tower_id = fp.parent.name
        with open(fp) as f:
            data = json.load(f)
        
        tower_name = data.get("document_meta", {}).get("tower_name") or tower_id
        current_snapshot = data.get("executive_snapshot")
        if not current_snapshot:
            continue
            
        print(f"Rewriting Executive Snapshot for {tower_id} - {tower_name}...")
        new_snapshot = rewrite_executive_snapshot(tower_id, tower_name, current_snapshot, global_facts)
        
        if new_snapshot and "bottom_line" in new_snapshot:
            data["executive_snapshot"] = new_snapshot
            with open(fp, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  -> Saved {fp}")
        else:
            print(f"  -> Failed to parse JSON for {tower_id}")

if __name__ == "__main__":
    main()