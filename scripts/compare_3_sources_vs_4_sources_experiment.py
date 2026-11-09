#!/usr/bin/env python3
"""Empirical Experiment: Compare 3-Source Synthesis vs 4-Source Synthesis (with Live Academic/Industry Research)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

# Load real Molins evidence for T1.P2 and T2.P2
with open(REPO_ROOT / "working/molins/T1/blueprint_t1_payload.json") as f:
    t1 = json.load(f)
p_t1_p2 = [p for p in t1["pillars_analysis"] if p["pillar_id"] == "T1.P2"][0]

with open(REPO_ROOT / "working/molins/T2/blueprint_t2_payload.json") as f:
    t2 = json.load(f)
p_t2_p2 = [p for p in t2["pillars_analysis"] if p["pillar_id"] == "T2.P2"][0]

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

PROMPT_EXPERIMENT = f"""You are a Distinguished Principal Technology Auditor and Chief Enterprise Architect.

We are running an empirical benchmark comparing two approaches to generate an executive diagnostic subsection for an IT Assessment deliverable (AS-IS):
- APPROACH A (3 Sources):
  1. Client Questionnaire Response (Survey Score).
  2. Interview Context Transcript Evidence (Literal facts, quotes, operational pain).
  3. Static Curated Engineering Frameworks (ASHRAE TC 9.9 for cooling, CNCF/DORA for compute).
- APPROACH B (4 Sources):
  1. Client Questionnaire Response.
  2. Interview Context Transcript Evidence.
  3. Static Curated Engineering Frameworks.
  4. LIVE SOTA RESEARCH & ACADEMIC PAPERS: Retrieve and incorporate concrete, peer-reviewed empirical metrics, IEEE/ACM papers, Gartner/Forrester 2025-2026 benchmark statistics, or whitepapers regarding the exact technical dilemma.

TEST CASES:

CASE 1: Pillar T1.P2 - Precision Cooling & Environmental Control (Data Center Facilities)
- Survey: 1.67 / 5.00
- Transcript Evidence: CPDs and S/M server rooms located inside cement plants and active quarries with extreme dust and ambient heat; frequent plant power outages cut cooling; SimpliVity nodes (clusters 3 and 4) at CPU/thermal limits; no in-row cooling or cold/hot aisle containment.
- Framework: ASHRAE TC 9.9 (Thermal Guidelines for Data Processing Environments, Class A1-A4).

CASE 2: Pillar T2.P2 - Container Platforms & Application Packaging (Compute Infrastructure)
- Survey: Declared 4.25 / 5.00
- Transcript Evidence: Zero containers or Kubernetes in production; 100% of applications and developer requests deployed on >300 heavy virtual machines on VMware SimpliVity; extreme RAM saturation (nodes 3 and 4 at 95% capacity); development requests VMs that are never decommissioned.
- Framework: CNCF Cloud Native Maturity Model & DORA State of DevOps Metrics.

YOUR TASK:
For both Case 1 and Case 2:
1. Write the 3-paragraph executive diagnostic using APPROACH A (3 Sources).
2. Write the 3-paragraph executive diagnostic using APPROACH B (4 Sources, citing specific papers, benchmark percentages, or research findings like IEEE, ACM, Gartner, or academic studies).
3. Conduct a rigorous, critical comparison:
   - Does the 4th source add transformative value for the CIO/Board, or does it sound academic and detached?
   - What is the risk of hallucination or irrelevance?
   - What is the verdict on whether the 4th source is essential to reach 10.0/10.0?

Format the response in clean Markdown with clear headers.
"""


def main() -> None:
    print("Running 3-Source vs 4-Source Empirical Experiment with Gemini Reasoning Model...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT_EXPERIMENT,
    )

    out_file = REPO_ROOT / "docs/audits/EXPERIMENT_3_SOURCES_VS_4_SOURCES.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Results written to {out_file}")


if __name__ == "__main__":
    main()
