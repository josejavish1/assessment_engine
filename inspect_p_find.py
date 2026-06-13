import json

with open('working/redeia_v3/T2/findings.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

p_find = data['pillar_findings'][0]
print("=== PILLAR FINDING KEYS ===")
print(list(p_find.keys()))
print("candidate_initiatives:", p_find.get("candidate_initiatives"))
