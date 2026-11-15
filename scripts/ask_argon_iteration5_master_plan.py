#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Phase 8: Iteration 5 Universal Perfection Master Plan.

Adheres strictly to the user's operational standards:
1. 100% Technical English prompt and generated documentation.
2. Multi-phase phased implementation plan with strict Quality Gates.
3. Universal scalability and zero hardcoding (multi-tenant agnostic).
4. Pure Clean Architecture.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def generate_iteration5_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: ITERATION 5 PERFECTION MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, Chief Systems Architect, Actuarial Fellow, and Global Managing Partner for Enterprise Due Diligence.

MANDATE & CONTEXT:
The latest forensic audit (`Revision_Profunda_Torre_2_Iteracion_5.txt`) rated our current deliverable at 7.5/10, acknowledging significant mathematical, typographical, and structural advances (weights summing to 100%, 1.85 score alignment, FAIR chain integration, and clean layout without table breaks).
To reach a certified 9.5+/10 Tier-1 World Class level for any enterprise globally, we must solve 5 specific technical and mathematical challenges before touching the codebase:

1. INTEGER WEIGHT DOT-PRODUCT PARITY (The 1.84 vs 1.85 Paradox):
   - Current Flaw: Visible weights are displayed as clean integers without decimals (e.g., 22%, 19%, 21%, 18%, 20% = 100%). However, if a reader manually computes the dot product with pillar scores (2.75, 1.00, 1.50, 1.00, 2.75), it yields 1.840, whereas the engine published 1.85 (derived from unrounded weights 22.38%, 19.05%, etc.).
   - Goal: Implement a deterministic Integer-Weight Harmonization Algorithm (such as an integer Linear Programming / Hare-Niemeyer dual-constraint solver) that finds integer weights summing to exactly 100% whose dot product with pillar scores rounds to the EXACT same published score (e.g. 23%, 19%, 20%, 18%, 20% -> 1.8525 -> 1.85). Both visual manual math and internal engine math must yield the identical score.

2. STRICT MATRIX-ROW TEF SYNCHRONIZATION:
   - Current Flaw: RSK-01 and RSK-02 were mapped into row TEF 3 (0.5 - 2.0 events/year) on the 5x5 heatmap, but their risk cards still printed `TEF = 2.4/year` and `Estimated Frequency: 2.0 - 10.0 events/year` (TEF 4).
   - Goal: Ensure that when a risk scenario's likelihood coordinate is set to TEF k, its numerical `threat_event_frequency_annual`, its text `estimated_frequency_label`, and its `LEF` are deterministically anchored to the exact midpoint of that TEF bracket (e.g. TEF 3 -> 1.25 events/yr, "0.5 - 2.0 events/year").

3. TO-BE SCOPE LEAKAGE ERADICATION:
   - Current Flaw: The AS-IS summary still had a residual sentence prescribing a future architecture: "towards a Sovereign Hybrid Edge model (70% on-prem / 30% cloud)".
   - Goal: Implement an AST & Prompt boundary firewall that strictly purges prescriptive allocation targets from AS-IS diagnostic deliverables, ensuring the AS-IS document is 100% diagnostic.

4. TOPOLOGICAL PRECISION (Clusters vs Nodes/Hosts):
   - Current Flaw: The text referred to "clusters 3 and 4", when the client operates 3 clusters consisting of 2 hosts each (6 nodes total).
   - Goal: Enforce a strict physical hierarchy parser in topology synthesis ensuring physical hosts/nodes are never conflated with logical high-availability clusters.

5. OPEN FAIR VULNERABILITY MODEL FRAMING:
   - Current Flaw: Presenting an 80%-95% vulnerability ratio as an "objective derivation" creates friction with auditors.
   - Goal: Frame the vulnerability ratio as an explicit "calibrated actuarial model assumption conditioned on CMMI Level 1 operational posture (absence of automated preventative safeguards)".

CORE INVARIANTS:
- 100% Technical English in code, variables, classes, docstrings, comments, logs, and prompt files.
- Zero Hardcoding: Algorithms must be universal, scaling from a $50M mid-market firm to a $100B global conglomerate.
- Zero Regressions: Must pass all 47 existing architecture and actuarial tests.

YOUR DELIVERABLE:
Write a comprehensive, exhaustive, publication-grade MASTER ARCHITECTURAL BLUEPRINT in Markdown format to be saved at `docs/architecture/ARGON_PHASE8_ITERATION5_MASTER_PLAN.md`.

Structure the plan into:
1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO: Addressing the 5 challenges.
2. DETAILED PHASED IMPLEMENTATION STRATEGY:
   - Phase 1: Dual-Constraint Integer Weight Parity Solver.
   - Phase 2: Actuarial Heatmap Coordinate and Frequency Tuple Synchronization.
   - Phase 3: Pure AS-IS Boundary Firewall (Zero Target Architecture Leakage).
   - Phase 4: Topology Parser & Hierarchy Normalization (Hosts vs Clusters).
   - Phase 5: Calibrated Actuarial Assumption Framing in Section 4.2.
3. QUALITY GATES & VERIFICATION ORACLES: Deterministic pytest validation suites.
"""

    print("Sending prompt to Gemini-4-Argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_PHASE8_ITERATION5_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Master Plan successfully generated and saved to: {out_file}")
    print(f"File size: {out_file.stat().st_size:,} bytes")
    return out_file

if __name__ == "__main__":
    generate_iteration5_master_plan()
