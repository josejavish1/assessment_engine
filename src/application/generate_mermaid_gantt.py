import base64
import datetime
import json
from pathlib import Path

import requests
from dateutil.relativedelta import relativedelta


def generate_mermaid_gantt(payload_path: Path, output_png_path: Path) -> bool:
    """Generates a Mermaid Gantt chart PNG from a structured roadmap JSON file.

    This function reads a JSON file that defines a strategic roadmap, parsing
    project waves, inter-project dependencies, sizing estimates, and typologies.
    It translates this structured data into Mermaid.js Gantt chart syntax.

    Key logical operations include:
    - Mapping project sizing estimates (e.g., 'S', 'M', 'L', 'XL') to specific
      task durations in days.
    - Dynamically calculating the start date for each subsequent project wave based
      on the completion date of the longest-duration project in the preceding
      wave, enforcing a sequential execution model.
    - Grouping projects into distinct visual sections within the Gantt chart
      based on their assigned 'transformation_typology'.
    - Handling explicit project dependencies to correctly sequence tasks.

    The generated Mermaid code is then transmitted to an external rendering service
    to produce a PNG image. The primary service is kroki.io, which requires the
    payload to be zlib-compressed and then URL-safe Base64-encoded. If the
    primary service fails, a fallback request is made to mermaid.ink.

    Args:
        payload_path: The path to the input JSON file containing the roadmap
            data. The file is expected to contain keys such as 'roadmap',
            'pillars_analysis', and 'external_dependencies'.
        output_png_path: The destination file path for the output PNG image.

    Returns:
        True if the Gantt chart was successfully generated and saved to the
        specified path. False is returned upon any failure, including file
        I/O errors, JSON parsing issues, missing required data in the payload,
        or non-200 responses from both external rendering APIs.
    """
    try:
        with open(payload_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        roadmap = data.get("roadmap", [])
        if not roadmap:
            return False

        mermaid_code = "%%{init: {'gantt': {'useWidth': 1400, 'useMaxWidth': false, 'barHeight': 30, 'fontSize': 14}}}%%\ngantt\n    title Strategic Transformation Roadmap (Topological)\n    dateFormat  YYYY-MM-DD\n    axisFormat  %Y-%m\n\n"

        #
        deps = data.get("external_dependencies", [])
        dep_map = {}
        for d in deps:
            project = d.get("project")
            depends_on = d.get("depends_on")
            if project not in dep_map:
                dep_map[project] = []
            if depends_on and depends_on not in ["Independiente", "Ninguna"]:
                dep_map[project].append(depends_on)

        #
        proj_id_map = {}
        # The project's sizing estimate serves a dual purpose: it directly determines the task duration in the Gantt chart and is also used to map the project to a specific swimlane classification or typology.
        sizing_map = {}
        typology_map = {}
        for pilar in data.get("pillars_analysis", []):
            for p in pilar.get("projects_todo", []):
                name = p.get("name")
                sizing_map[name] = p.get("sizing", "M").upper()
                typology_map[name] = p.get(
                    "transformation_typology", "General Transformation"
                )

        roadmap_projects_by_typology = {}
        for w_idx, wave in enumerate(roadmap):
            for p_idx, proj in enumerate(wave.get("projects", [])):
                safe_name = proj.replace(":", "-").replace('"', "'")
                # Mermaid.js syntax imposes a strict constraint on task identifiers, which must be alphanumeric and contain no spaces. Consequently, project names undergo a sanitization process to generate compliant IDs before their inclusion in the diagram definition.
                m_id = f"p{w_idx}_{p_idx}"
                proj_id_map[proj] = {
                    "m_id": m_id,
                    "safe_name": safe_name,
                    "wave_idx": w_idx,
                }

                typology = typology_map.get(proj, "General Transformation")
                if typology not in roadmap_projects_by_typology:
                    roadmap_projects_by_typology[typology] = []
                roadmap_projects_by_typology[typology].append((w_idx, proj))

        start_date = datetime.date.today()

        # The start date for each successive wave is calculated dynamically. This date is set to the completion time of the project with the maximum duration in the immediately preceding wave, thereby enforcing a sequential, non-overlapping execution model for the waves.
        wave_start_dates = [start_date]
        for w_idx, wave in enumerate(roadmap):
            max_dur_days = 0
            for proj in wave.get("projects", []):
                sizing = sizing_map.get(proj, "M")
                durations = {"S": 45, "M": 90, "L": 150, "XL": 240}
                dur_days = durations.get(sizing, 90)
                if dur_days > max_dur_days:
                    max_dur_days = dur_days
            # The start time for a subsequent wave is calculated based on the completion time of the project with the maximum duration in the preceding wave. A fixed buffer is added to this completion time to ensure temporal separation between dependent waves.
            next_start = wave_start_dates[-1] + relativedelta(days=max_dur_days + 15)
            wave_start_dates.append(next_start)

        import re

        independent_count_total = 0

        for typology, projs in roadmap_projects_by_typology.items():
            safe_section = re.sub(r"[^a-zA-Z0-9\s]", "", typology)
            mermaid_code += f"    section {safe_section}\n"

            for w_idx, proj in projs:
                p_data = proj_id_map.get(proj)
                if not p_data:
                    continue

                m_id = p_data["m_id"]
                safe_name = p_data["safe_name"]
                if len(safe_name) > 60:
                    safe_name = safe_name[:57] + "..."

                project_deps = dep_map.get(proj, [])
                mermaid_deps = []
                for d in project_deps:
                    if d in proj_id_map:
                        mermaid_deps.append(proj_id_map[d]["m_id"])

                #
                sizing = sizing_map.get(proj, "M")
                durations = {"S": 45, "M": 90, "L": 150, "XL": 240}
                dur_days = durations.get(sizing, 90)
                duration_str = f"{dur_days}d"

                if mermaid_deps:
                    deps_str = "after " + " ".join(mermaid_deps)
                    mermaid_code += (
                        f"    {safe_name} :{m_id}, {deps_str}, {duration_str}\n"
                    )
                else:
                    # Root nodes, defined as projects with no intra-wave dependencies, are scheduled to commence at the calculated start date of their respective wave. A minor, incremental offset is applied to each root node's start time to prevent visual overlap and enhance readability in the rendered Gantt chart.
                    w_start = wave_start_dates[w_idx] + relativedelta(
                        days=10 * independent_count_total
                    )
                    mermaid_code += f"    {safe_name} :{m_id}, {w_start.strftime('%Y-%m-%d')}, {duration_str}\n"
                    independent_count_total += 1

        #
        import zlib

        # The kroki.io service is designated as the primary rendering engine. This selection is based on its extensive support for multiple diagrammatic formats and its superior output fidelity relative to other available rendering services.
        # The Kroki rendering service API mandates a specific payload encoding scheme. The Mermaid diagram definition must first be compressed using zlib, and the resulting byte stream must then be encoded into a URL-safe Base64 string.
        compressed = zlib.compress(mermaid_code.encode("utf-8"), 9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii")

        url = f"https://kroki.io/mermaid/png/{encoded}"

        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(output_png_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(
                f"Failed to generate Mermaid Gantt via Kroki: HTTP {response.status_code} - {response.text[:100]}"
            )
            # A fallback mechanism is implemented for diagram rendering. If the primary service endpoint (Kroki) fails, the system redirects rendering requests to a secondary, public endpoint (mermaid.ink) to maintain service availability.
            graphbytes = mermaid_code.encode("utf8")
            base64_bytes = base64.b64encode(graphbytes)
            base64_string = base64_bytes.decode("ascii")
            url = f"https://mermaid.ink/img/{base64_string}?type=png"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(output_png_path, "wb") as f:
                    f.write(response.content)
                return True
            return False

    except Exception as e:
        print(f"Error generating Mermaid Gantt: {e}")
        return False
