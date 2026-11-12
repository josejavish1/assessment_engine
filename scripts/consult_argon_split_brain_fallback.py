"""Consult gemini-4-argon for the ultimate Tier-1 architecture to solve the Split-Brain Narrative & Operational Fallback crisis."""

from __future__ import annotations

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

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

PROMPT = """You are 'gemini-4-argon', Lead Adversarial Red Team Chief Architect (SR 11-7 / Open FAIR / Basel III / Solvency II) at a top-tier global consulting firm in November 2026.

We have encountered a SEVERE architectural flaw in our Assessment Engine's actuarial output that destroys credibility in front of a CFO/CTO:
1. **Split-Brain Inconsistency:** In the generated Word document, the top table says SLE = 38,530 EUR (8 hours downtime). But the new Plain Language Narrative cell right below it claims an impact of 180,900 EUR and 15.1 hours of downtime. The text generator is recalculating numbers independently from the actuarial engine, bypassing the established matrix.
2. **The "Total Paralysis" Fallacy (Ignoring Operational Resilience):** The model assumes that an IT failure (e.g., UPS failure in the data center causing a server cold crash) stops 100% of a heavy manufacturing plant's revenue (13,061 EUR/hour) for 15-18 hours. This is an operational absurdity. Industrial plants have PLCs, manual fallbacks, paper-based weighbridge tickets, and buffer silos. If IT goes down, they don't stop grinding clinker or loading trucks completely; they degrade to manual mode with 60-70% efficacy. IT downtime only impacts the marginal inefficiency and logistics backlog, not the gross corporate revenue. A server reboot takes 3-4 hours, not 18.

The user explicitly rejected any "tactical patch" (like just passing variables around) and demands a ROOT CAUSE, TIER-1 ARCHITECTURAL SOLUTION aligned with the state-of-the-art in November 2026.

YOUR MANDATE:
Design the ultimate Master Architecture to permanently solve this.
1. **Mathematical Monism (The Single Source of Truth Principle):** How do we architect the codebase so that it is mathematically impossible for the narrative text generator to invent or recalculate numbers? The narrative MUST act purely as a "dumb formatter" of the exact `sle`, `ale`, and `rto_hours` finalized by the ActuarialInferenceEngine.
2. **The Operational Resilience Attenuation Model (Mode Fallback / BCP Efficacy):** How do we mathematically model and inject the "Manual Fallback Efficacy" (e.g., 65% for cement plants, 40% for clinical triages) into the FAIR loss magnitude calculation, so that hourly burn rates reflect true marginal inefficiency, not gross revenue? Where does this live? (e.g., `engine_config/industry_profiles/`)
3. **Execution Plan:** Provide the exact file paths to modify (e.g., `payload_to_ast.py`, `industry_profiles/*.json`, `input_resolver.py`, `plain_language_narrative.py`) and the strict invariant rules to enforce.

Provide a definitive, aggressive, and highly technical design document (Markdown format). No pleasantries. Only Tier-1 architectural solutions.
"""

print(f"Submitting Deep Architecture Audit to {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=PROMPT,
)

out_file = REPO_ROOT / "docs" / "audits" / "RED_TEAM_SPLIT_BRAIN_AND_FALLBACK_ARCHITECTURE.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\nAudit complete. Wrote {len(response.text)} chars to {out_file.relative_to(REPO_ROOT)}")
