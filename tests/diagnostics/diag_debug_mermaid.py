import datetime
import json
from pathlib import Path

from dateutil.relativedelta import relativedelta


def debug_mermaid():
    payload_path = Path("working/redeia_v3/T2/blueprint_t2_payload.json")
    with open(payload_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    roadmap = data.get("roadmap", [])

    mermaid_code = "gantt\n    title Strategic Transformation Roadmap (Topological)\n    dateFormat  YYYY-MM-DD\n    axisFormat  %Y-%m\n\n"

    deps = data.get("external_dependencies", [])
    dep_map = {}
    for d in deps:
        project = d.get("project")
        depends_on = d.get("depends_on")
        if project not in dep_map:
            dep_map[project] = []
        if depends_on and depends_on not in ["Independiente", "Ninguna"]:
            dep_map[project].append(depends_on)

    proj_id_map = {}
    for w_idx, wave in enumerate(roadmap):
        for p_idx, proj in enumerate(wave.get("projects", [])):
            safe_name = proj.replace(":", "-").replace('"', "'")
            m_id = f"p{w_idx}_{p_idx}"
            proj_id_map[proj] = {
                "m_id": m_id,
                "safe_name": safe_name,
                "wave_idx": w_idx,
            }

    start_date = datetime.date.today()

    for w_idx, wave in enumerate(roadmap):
        wave_name = wave.get("wave", f"Wave {w_idx + 1}")
        # Clean section name too
        wave_name = wave_name.replace(":", "-").replace('"', "'")
        mermaid_code += f"    section {wave_name}\n"

        for proj in wave.get("projects", []):
            p_data = proj_id_map.get(proj)
            if not p_data:
                continue

            m_id = p_data["m_id"]
            safe_name = p_data["safe_name"]
            if len(safe_name) > 35:
                safe_name = safe_name[:32] + "..."

            project_deps = dep_map.get(proj, [])
            mermaid_deps = []
            for d in project_deps:
                if d in proj_id_map:
                    mermaid_deps.append(proj_id_map[d]["m_id"])

            duration_str = "180d" if w_idx == 0 else "180d" if w_idx == 1 else "360d"

            if mermaid_deps:
                deps_str = "after " + " ".join(mermaid_deps)
                mermaid_code += f"    {safe_name} :{m_id}, {deps_str}, {duration_str}\n"
            else:
                if w_idx == 0:
                    w_start = start_date
                elif w_idx == 1:
                    w_start = start_date + relativedelta(months=6)
                else:
                    w_start = start_date + relativedelta(months=12)
                mermaid_code += f"    {safe_name} :{m_id}, {w_start.strftime('%Y-%m-%d')}, {duration_str}\n"

    print("--- MERMAID CODE ---")
    print(mermaid_code)


if __name__ == "__main__":
    debug_mermaid()
