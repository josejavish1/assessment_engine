import json

with open('working/redeia_v3/T5/blueprint_t5_payload.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

print("=== CANARY AUDIT: VERIFYING NEW T5 PAYLOAD PROJECTS ===")
for idx, p in enumerate(data.get('pillars_analysis', [])):
    p_id = p.get("pilar_id")
    p_name = p.get("pilar_name")
    projs = [proj.get("name") for proj in p.get("projects_todo", [])]
    print(f"Pilar {idx + 1}: {p_id} - {p_name}")
    print(f"         Custom Projects: {projs}")
