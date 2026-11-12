import sys
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'src'))

from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

targets = [
    ('T1', 'T1.P2', 'Climatización, Refrigeración y Control'),
    ('T7', 'T7.P2', 'Service Desk, Gestión de Incidentes'),
    ('T9', 'T9.P2', 'Workplace Identity & Access Experience'),
    ('T3', 'T3.P4', 'Hybrid Cloud Connectivity & Edge Services'),
    ('T9', 'T9.P4', 'Operación, Soporte y Autoservicio')
]

for tid, pid, pname_sub in targets:
    fp = REPO_ROOT / f'working/molins/{tid}/blueprint_{tid.lower()}_payload.json'
    with open(fp) as f:
        data = json.load(f)
    for p in data.get('pillars_analysis', []):
        curr_pname = p.get('pillar_name', '')
        curr_pid = p.get('pillar_id', '')
        if (curr_pid == pid) or (pname_sub in curr_pname):
            print(f'Expanding {curr_pid} {curr_pname}...')
            current_desc = p.get('asis_architecture_description', '')
            findings = ' | '.join([hc.get('finding', '') for hc in p.get('health_check_asis', [])])
            prompt = f"""You are a Principal Enterprise Architect conducting a forensic As-Is assessment for Cementos Molins.
Synthesize the `asis_architecture_description` for: **{curr_pname}** (Tower: **{tid}**).

Current text: {current_desc}
Findings: {findings}
Key Facts: Molins has 2 CPDs at Sant Vicenç separated by 500m, heavy manufacturing, 60 VMs, HPE SimpliVity, NetApp, PreNet for truck dispatch, 9 precast plants, SECIL Portugal with NOS.

Format: Return ONLY plain text in Spanish (4 cohesive analytical paragraphs, 220-280 words total).
1. Technical Footprint & Baseline in Molins.
2. Cross-Tower Interlock & Operational Reality.
3. Architectural Friction & Risk Debt.
4. Business Impact on Plant Operations and Costs.
No markdown headers, no bullet points, no mention of scores or self-assessment.
"""
            resp = client.models.generate_content(model=model_name, contents=prompt)
            clean = re.sub(r'#.*?\n', '', resp.text)
            clean = re.sub(r'\*\*', '', clean).strip()
            p['asis_architecture_description'] = clean
            print(f'  -> Done: {len(clean.split())} words')
    with open(fp, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
