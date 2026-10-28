import json
import logging
from pathlib import Path
from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

blueprint_path = Path("working/redeia_v3/T2/blueprint_t2_payload.json")
data = json.loads(blueprint_path.read_text(encoding="utf-8-sig"))

graph = EpistemicGraph(client_id="redeia_v3")

engine = SovereignPolicyEngine(graph)
updated_data = engine.compile(data)

total_ale = 0.0
for pillar in updated_data.get("pillars_analysis", []):
    for finding in pillar.get("health_check_asis", []):
        total_ale += float(finding.get("fair_ale_score", 0.0))

# updated_data doesn't store total_ale natively, but generate_asis_markdown_modules calculates it or reads it from "total_fair_ale" which was added previously?
# Let's check `generate_asis_markdown_modules.py`
updated_data["total_fair_ale"] = total_ale

blueprint_path.write_text(json.dumps(updated_data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Updated risks successfully. Total ALE: {total_ale}")
