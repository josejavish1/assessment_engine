#!/usr/bin/env python3
"""Actuarial & Architectural Audit by gemini-4-argon on Risk Accumulation, Independence Fallacy, and Deduplication."""

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

prompt = """
Role: Chief Risk Officer (Open FAIR Fellow), Lead Actuary (Enterprise Risk Modeling), and Senior Strategy Partner (McKinsey/Gartner).

CONTEXT & PROBLEM STATEMENT FROM THE CLIENT/USER:
The user inspected the generated document and noticed two severe, systemic issues:
1. "El coste que está en el índice / resumen vs en los riesgos no coincide y me preocupa muchísimo porque se supone que no hay split-brain."
   - The user noticed a discrepancy between the headline financial numbers (e.g. Total ALE, P90, or Chapter numbers) vs the sum of the individual risk items.
2. "Parece que tenemos como muchos riesgos pero parecen el mismo, en realidad tampoco tengo claro si el riesgo se acumula en estos casos. Se supone que el mismo riesgo no debería acumularse. Hay que pensar bien los riesgos cómo se cuentan porque es clave."
   - The user is pointing out a fundamental Actuarial & Risk Engineering flaw: **THE INDEPENDENCE FALLACY AND DOUBLE COUNTING IN RISK ACCUMULATION.**
   - In our current 14 risks, we have multiple items that all describe the EXACT SAME FAILURE EVENT:
     * Risk A: Thermal density and hotspots (air mixing).
     * Risk B: Lack of temperature/humidity sensors in racks.
     * Risk C: Lack of BMS/DCIM integration for cooling alerts.
     * Risk D: Mechanical thermostat wall controls.
   - If you treat these 4 items as independent risks and sum their ALEs:
     ALE(A) + ALE(B) + ALE(C) + ALE(D) = 4 separate plant stoppages!
     This implies the factory will stop 4 times as often because 4 related cooling weaknesses exist!
     In reality, they are NOT 4 independent loss events; they are multiple contributing vulnerabilities to the SAME SINGLE LOSS EVENT: "Thermal shutdown of core data center compute due to cooling failure".
   - Similarly for Electrical: single-path PDU, UPS battery age, manual transfer switch, lack of sub-metering. They all contribute to ONE event: "Loss of primary power to rack compute".
   - Summing individual risk ALEs naively creates gross risk double-counting and an absurdly inflated total ALE that any competent CFO or Risk Committee will immediately reject as fraudulent or naive.

YOUR TASK:
Provide an exhaustive, authoritative, actuarial and architectural diagnosis answering:

1. THE INDEPENDENCE FALLACY & NAIVE ADDITIVITY (OPEN FAIR AUDIT):
   - Explain mathematically and actuarially why summing individual vulnerability ALEs ($ALE_{total} = \sum ALE_i$) violates probability theory ($P(A \cup B) \neq P(A) + P(B)$) when failure modes share the same physical asset and common-cause triggers.
   - How does Open FAIR distinguish between a Loss Event Scenario vs Contributing Vulnerability Factors (Threat Event Frequency, Vulnerability %, Threat Capability, Resistance Strength)?

2. RISK CONSOLIDATION & DEDUPLICATION ARCHITECTURE:
   - How should the 14 granular audit findings be structured so they do NOT duplicate or falsely accumulate financial loss?
   - Evaluate the optimal architecture:
     * Architecture A: Consolidated Macro Loss Scenarios (e.g. 3 to 4 Macro Scenarios: 1. Thermal Collapse, 2. Power Continuity Failure, 3. Physical Security/Environment, 4. Operational Maintenance Blindness), where each Macro Scenario has a single actuarial ALE, and the granular items are listed as "Contributing Vulnerabilities / Audit Findings" within that scenario.
     * Architecture B: Systemic Loss Event Portfolio with Shared Loss Ceilings and Copula / Joint Distribution (Monte Carlo non-linear aggregation where asset capacity caps maximum annual loss).
     * Analyze which architecture delivers the highest clarity, defensibility, and executive impact for a Board / CFO.

3. SPLIT-BRAIN ERADICATION & MATHEMATICAL PARITY:
   - Exactly how must the Assessment Engine reconcile numbers across Chapter 1 (Executive Summary), Chapter 4 (Quantitative Risk Catalog), Chapter 5 (Roadmap ROI/Payback), and Appendix B (Actuarial Tables)?
   - Define the exact invariant rules that guarantee 100% mathematical parity across the document.

4. STEP-BY-STEP IMPLEMENTATION ROADMAP:
   - Provide a precise, technical plan for refactoring the schemas, engine, AST, and payload compiler to implement consolidated, non-duplicated risk modeling with zero bugs, zero anti-patterns, and zero hardcoding (100% Technical English).
"""

print(f"Requesting deep actuarial audit from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: ACTUARIAL DIAGNOSIS ON RISK ACCUMULATION & DEDUPLICATION")
print("=" * 80)
print(response.text)
print("=" * 80)
