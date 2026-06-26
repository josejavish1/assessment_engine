import json
from pathlib import Path

findings_path = Path("working/redeia_v3/T2/findings.json")
with open(findings_path, "r", encoding="utf-8-sig") as f:
    refined_findings = json.load(f)

p_id = "T2.P1"
for p_find in refined_findings.get("pillar_findings", []):
    if p_find["pillar_id"] == p_id:
        print(f"=== FOUND PILLAR FINDING FOR {p_id} ===")
        initiatives = p_find.get("candidate_initiatives", [])
        print("initiatives length:", len(initiatives))
        for idx, init in enumerate(initiatives):
            print(
                f"Init {idx}: title={init.get('title')}, name={init.get('name')}, rationale={init.get('rationale')[:50]}"
            )

            # This is the exact logic in run_tower_blueprint_engine.py:
            project_name = init.get("title", f"Iniciativa Estratégica {idx + 1}")
            print(f"   Generated project name: {project_name}")
