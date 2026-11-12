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

def word_count(text):
    if not text: return 0
    return len(text.split())

def is_boilerplate(text):
    return "autoevaluación" in text.lower() or "proyectaba" in text.lower() or "sin embargo" in text.lower()

def extract_global_facts(towers_dir: Path) -> str:
    facts = []
    for fp in towers_dir.rglob("blueprint_*_payload.json"):
        with open(fp) as f:
            data = json.load(f)
            t_id = data.get("tower_id") or "UNKNOWN"
            for p in data.get("pillars_analysis", []):
                p_name = p.get("pillar_name") or p.get("pillar_id")
                desc = p.get("asis_architecture_description", "")
                if word_count(desc) > 80:
                    facts.append(f"Fact in {t_id} / {p_name}: {desc[:300]}")
                for hc in p.get("health_check_asis", []):
                    f_text = hc.get("finding", "")
                    facts.append(f"Finding in {t_id} / {p_name}: {f_text}")
    return "\n".join(facts)

def rewrite_pillar_narrative(pillar_name, tower_id, current_desc, findings, global_facts):
    prompt = f"""You are a Principal Enterprise Architect conducting a forensic As-Is assessment for Cementos Molins (global industrial/manufacturing enterprise).
Your objective is to synthesize the `asis_architecture_description` for the pillar: **{pillar_name}** (Tower: **{tower_id}**).

### INPUT TELEMETRY:
1. Current Draft (Poor/Incomplete): {current_desc}
2. Specific Findings for this Pillar: {findings}
3. Global Adjacent Facts across the Enterprise:
{global_facts}

### STRICT ARCHITECTURAL CONSTRAINTS:
1. ZERO HALLUCINATION. Do not invent vendors. 
2. NO SCORE PARROTING. NEVER mention "autoevaluación", "puntuación", "score".
3. DEDUCTIVE SYNTHESIS OF NEGATIVE SPACE. If direct facts are sparse, deduce operational reality based on adjacent facts (e.g. if they have 60 VMs but no Kubernetes, deduce legacy provisioning).
4. MUST BE IN SPANISH (Technical).

### MANDATORY OUTPUT STRUCTURE:
Return ONLY the generated Spanish text. NO markdown formatting, NO headers, NO bold text. Just plain text paragraphs.
You must generate a cohesive, executive-grade narrative (160–250 words total) by seamlessly combining four analytical points:
1. Empirical Baseline & Footprint (The current technical state or lack thereof).
2. Cross-Tower Interlock & Operational Reality (How this pillar interacts with Network, Storage, Security, etc).
3. Architectural Friction & Debt Analysis (Specific bottlenecks, manual overheads, scalability limits).
4. Business & Firmographic Impact for Molins (What this means for plant uptime, TCO, or agility).
"""
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        # Strip all markdown
        clean_text = re.sub(r'#.*?\n', '', response.text)
        clean_text = re.sub(r'\*\*', '', clean_text)
        clean_text = re.sub(r'__', '', clean_text)
        return clean_text.strip()
    except Exception as e:
        print(f"Error generating for {pillar_name}: {e}")
        return current_desc

def main():
    towers_dir = REPO_ROOT / "working" / "molins"
    print("Extracting global facts...")
    global_facts = extract_global_facts(towers_dir)
    global_facts = global_facts[:20000]

    for fp in sorted(towers_dir.rglob("blueprint_*_payload.json")):
        tower_id = fp.parent.name
        with open(fp) as f:
            data = json.load(f)
        
        modified = False
        for i, p in enumerate(data.get("pillars_analysis", [])):
            p_name = p.get("pillar_name") or p.get("pillar_id")
            desc = p.get("asis_architecture_description", "")
            
            if word_count(desc) < 80 or is_boilerplate(desc):
                print(f"Rewriting {tower_id} - {p_name} (Current words: {word_count(desc)})")
                findings = " | ".join([hc.get("finding", "") for hc in p.get("health_check_asis", [])])
                new_desc = rewrite_pillar_narrative(p_name, tower_id, desc, findings, global_facts)
                
                if word_count(new_desc) > 80:
                    p["asis_architecture_description"] = new_desc.strip()
                    modified = True
                    print(f"  -> Success. New words: {word_count(new_desc)}")
                else:
                    print(f"  -> Failed density check. Words: {word_count(new_desc)}")

        if modified:
            with open(fp, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved {fp}")

if __name__ == "__main__":
    main()