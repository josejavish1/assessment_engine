#!/usr/bin/env python3
"""Consulting gemini-4-argon on the Mathematical & Architectural Coupling Between CMMI Maturity and Open FAIR Risk."""

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
Role: Chief Risk Officer (Open FAIR Fellow) & Senior Strategy Partner (McKinsey/Gartner CMMI & Risk Practice).

USER QUESTION & DILEMMA:
The user asks:
"Parece que suena bien, pero cada empresa tiene niveles de madurez diferentes y sus riesgos son distintos, ¿no?"
(It sounds good, but each company has different maturity levels, and their risks are different, right?)

THE DEEP ARCHITECTURAL QUESTION:
How does a Tier-1 enterprise platform couple CMMI Maturity (1.00 to 5.00) with Open FAIR Risk Modeling, and how does the engine ensure that:
1. Companies with different maturity levels (Level 1 Initial vs Level 3 Defined vs Level 4 Managed) generate completely different, mathematically defensible risk profiles.
2. The maturity score is NOT just a decorative label, but dynamically modulates the actuarial physics of risk:
   - Resistance Strength (RS) & Vulnerability Probability: Vuln = P(Threat Capability > Resistance Strength).
   - Mean Time to Detect (MTTD) and Mean Time to Recover (MTTR): Higher maturity = automated telemetry = lower MTTR.
   - Loss Event Frequency (LEF) and Financial Exposure (ALE).
3. The catalog of scenarios and risks naturally adapts to the company's specific vertical, maturity posture, and scope without hardcoding.

YOUR TASK:
Provide a rigorous, executive, and practical explanation:
1. The Actuarial Bridge: Exactly how CMMI Maturity (qualitative maturity) drives Open FAIR (quantitative financial risk).
2. The Comparative Enterprise Reality: Show a clear contrast table of how the exact same technological domain behaves for:
   - Enterprise A (Level 1.8 - Chaotic / Ad-hoc)
   - Enterprise B (Level 2.6 - Defined / Manual Redundancy / Molins baseline)
   - Enterprise C (Level 4.2 - Quantitatively Managed / Automated N+1 / Target posture)
3. Engine Implementation Architecture: How the Assessment Engine derives the active failure scenarios and their actuarial parameters dynamically from the evaluated maturity scores in the payload, ensuring zero hardcoding and total multi-tenant flexibility.
"""

print(f"Requesting maturity-risk coupling guidance from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: MATURITY-RISK COUPLING ARCHITECTURE (CMMI <-> OPEN FAIR)")
print("=" * 80)
print(response.text)
print("=" * 80)
