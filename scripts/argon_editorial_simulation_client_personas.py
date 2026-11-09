#!/usr/bin/env python3
"""Argon Editorial Simulation: Battle-Hardened Client Persona Evaluation of Pillar Generation Strategies."""

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

# Load sample evidence
samples = []
for t_code, p_id in [("T1", "T1.P2"), ("T2", "T2.P2"), ("T5", "T5.P3"), ("T6", "T6.P2"), ("T9", "T9.P1")]:
    payload_path = REPO_ROOT / f"working/molins/{t_code}/blueprint_{t_code.lower()}_payload.json"
    if payload_path.exists():
        with open(payload_path) as f:
            data = json.load(f)
        p_data = [p for p in data["pillars_analysis"] if p["pillar_id"] == p_id]
        if p_data:
            samples.append(p_data[0])

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

PROMPT_SIMULATION = f"""You are 'gemini-4-argon', the supreme arbiter of executive consulting quality.
You are now adopting the persona of a battle-hardened, cynical, Tier-1 Client (CIO/CFO of a €1B manufacturing company). You have read thousands of consulting reports from Big 4, Gartner, and McKinsey. You hate template-driven reports, you hate robotic structures where every section looks exactly the same, and you hate when consultants drop names (like "According to Gartner...") just to sound smart when it doesn't add value.

We are trying to design the ultimate prompt logic for our AI engine to write the 3.2 section (the 50 pillars).

Currently, we are debating how to inject 'SOTA Frameworks' (like ISO 22301, DORA, ASHRAE, CIS Controls) into the text.
Option A: Force an explicit citation in every pillar (Robotic, feels like an academic paper).
Option B: Weave the framework's wisdom *implicitly* without naming it (Elegant, but maybe lacks punch when we really need to prove the client wrong).
Option C: Dynamic, context-aware synthesis. The AI decides *when* to drop the hammer explicitly (e.g., when the client is delusional and there is a huge gap between declared and calibrated scores, or a massive catastrophic blind spot) and *when* to use implicit wisdom for standard/mature pillars.

YOUR TASK:
1. Analyze this debate from the perspective of the battle-hardened CIO. Tell us exactly what makes you throw a report in the trash, and what makes you say "These guys are brilliant."
2. Define the definitive "Dynamic Generative Ruleset" that the AI engine should follow for every pillar so that NO TWO PILLARS FEEL LIKE A TEMPLATE, but all of them are 100% senior and pericial.
3. Apply your ruleset to write the perfect 2-paragraph narrative for these three distinct cases, demonstrating the shifting tone and strategy:
   - CASE 1 (The Delusional Gap): T2.P2 (Containers). Client declared 4.25, reality is 1.00. 300 VMs, no containers. Needs the hammer.
   - CASE 2 (The Hidden Catastrophe): T5.P3 (Disaster Recovery). Client thinks 2 CPDs at 500m is a DR. They share the same power grid. Needs implicit architectural wisdom.
   - CASE 3 (The Mature/Stable Routine): T9.P1 (Endpoint Lifecycle). Client renews laptops every 4 years. Score 4.00. Needs empathy, business logic, zero name-dropping.

Output a highly critical, authoritative markdown report.
"""

def main() -> None:
    print("Running Argon Editorial Simulation with Client Personas...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT_SIMULATION,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_EDITORIAL_PERSONA_SIMULATION.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("=" * 80)
    print("SIMULATION COMPLETE. VERDICT:")
    print("=" * 80)
    print(response.text[:2000] + "...\n[Output truncated, see full file]")
    print(f"\nFull report written to {out_file}")

if __name__ == "__main__":
    main()
