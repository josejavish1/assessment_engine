#!/usr/bin/env python3
"""Argon Strategic Consultation: Pure AS-IS Executive Summaries without AI Formulaic Patterns.

Addresses two critical user mandates:
1. Strict AS-IS Purity: Forbid TO-BE recommendations/CAPEX prescriptions in an AS-IS diagnostic.
   Frame the executive summary around architectural posture, technical debt, and business implications of the Status Quo.
2. Organic Narrative Mastery (Zero AI-Smell): Eliminate formulaic cookie-cutter paragraph templates
   (e.g. rigid 3-sentence rules). Ensure each of the 10 towers has an authentic, domain-bespoke
   executive voice (Facility physics vs Network routing vs Industrial plant dispatch) that reads
   like an elite Principal Architect, not a generative AI following a prompt formula.
"""

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
print(f"Connecting to Reasoning model '{model_name}' for AS-IS Executive Narrative Strategy...")

prompt = """You are 'gemini-4-argon', the Principal Staff Systems Architect, Lead Forensic Due Diligence Partner, and Master Technical Editor.

USER CRITIQUE (Sharp, high-signal, and 100% correct):
1. PURE AS-IS SCOPE INVARIANT:
   "Remember that we are ONLY in the AS-IS diagnostic phase. We MUST NOT prescribe TO-BE solutions, new hardware purchases, or CAPEX recommendations (e.g. 'buy 4 nodes', 'migrate to Nutanix'). That belongs to Tomo 2 (TO-BE & Roadmap). The AS-IS summary must strictly evaluate where the client stands today and the consequences of inaction/status quo inertia."
2. ANTI-AI FORMULAIC MONOTONY:
   "If you enforce a rigid 3-sentence template on every tower, it creates an unbearable 'AI smell' (every tower having the exact same syntactic rhythm, making it obvious an LLM generated it). We need the executive summary to extract the MAXIMUM bespoke value of THAT specific tower, with organic narrative variety and domain-authentic depth."

MISSION:
Design a comprehensive architectural and prompt-engineering blueprint for the Per-Tower Executive Summaries that guarantees:
1. 100% AS-IS Purity: How to articulate executive urgency, risk exposure, and operational debt WITHOUT crossing the line into TO-BE recommendations or roadmap solutions.
2. Anti-Robotic Organic Variety: How to prompt the synthesizer so that each tower adopts its natural architectural voice (Facilities = physical geography/power/cooling; Compute = hypervisor contention/RAM/licensing; Networks = topological centralization/firewall chokepoints; Security = privilege sprawl/MFA; Plant Floor = real-time dispatch/SCADA/básculas) without cookie-cutter paragraph templates.
3. Maximum Domain Value Extraction: How to ensure the summary captures the deep, bespoke technical reality discovered in the interviews (e.g., Molins twin CPDs at 500m, single DBA in Croatia, SimpliVity RAM saturation by OT/Test, Oracle Forms on 10g) while keeping each tower strictly orthogonal and free of repetitive echo-chamber filler.
4. Universal Multi-Tenant Generalization: How this applies seamlessly to ANY client (e.g., Starling Bank in the UK, Rede D'Or in Brazil) without client-specific hardcoding.

Structure your response with executive clarity, specific prompt directives, and concrete before/after examples for an AS-IS executive summary.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/architecture/ARGON_PURE_ASIS_EXECUTIVE_NARRATIVE_BLUEPRINT.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved strategic blueprint to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:2500] + "\n... [TRUNCATED] ...")
print("=" * 80)
