import json
from pathlib import Path

def test():
    findings_path = Path("working/redeia_v3/T2/findings.json")
    refined_findings = json.loads(findings_path.read_text(encoding="utf-8-sig"))
    
    payload_path = Path("working/redeia_v3/T2/blueprint_t2_payload.json")
    payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))
    
    for p_analysis in payload.get("pillars_analysis", []):
        p_id = p_analysis.get("pilar_id")
        print(f"Checking {p_id}")
        match_found = False
        for p_find in refined_findings.get("pillar_findings", []):
            if p_find.get("pillar_id") == p_id:
                print(f"  Found match in findings.json for {p_id}")
                initiatives = p_find.get("candidate_initiatives", [])
                print(f"  Initiatives: {[i.get('title') for i in initiatives]}")
                match_found = True
        if not match_found:
            print(f"  NO MATCH in findings.json for {p_id}")

if __name__ == "__main__":
    test()
