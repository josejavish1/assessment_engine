#!/usr/bin/env python3
"""Architectural Design & Strategy Formulation by gemini-4-argon for Table Auto-Fit & Risk Presentation."""

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
Role: Chief Risk Officer, Senior Strategy Partner (McKinsey/Gartner) & Principal Compiler Architect.

CONTEXT & PROBLEM STATEMENT:
The user has reviewed the generated deliverable and provided critical qualitative and visual feedback:
1. Table Width Auto-Fit:
   - "Matriz de Diagnóstico y Desempeño por Dominio Tecnológico" (3 columns) and "Perfil de Madurez por Dominio Tecnológico" (3 columns) look poorly proportioned when Word leaves column widths arbitrary. Columns must auto-fit to content with proportional width distribution (e.g. short scores getting compact widths, long gap analysis getting wide wrapping space).
2. Elimination of Cramped Risk Tables:
   - The user states: "Catálogo Priorizado de Riesgos should NOT be in a cramped table. It looks horrible and is poorly communicated. Someone reading a risk wants to see it clearly, understand the risk and impact, and understand perfectly how its financial cost was calculated (probability, downtime, hourly rate, secondary losses), narrated in clear prose or structured bullets, not squeezed into table cells."
3. Risk Organization & Hierarchy:
   - Should risks be grouped by Technology Pillars, or is there a vastly superior organizational structure?
   - Compare:
     * Architecture A: Grouped by the 3 Strategic Portfolios / Tiers (Tier 1: Critical Modernization, Tier 2: Operational Optimization, Tier 3: Maintenance Backlog), with risks sorted by ALE descending inside each tier.
     * Architecture B: Pure Global ALE Ranking (from #1 highest financial loss to lowest), with Tier and Pillar badges.
     * Architecture C: Grouped by Technology Pillar.
   - Analyze from both a Board/CFO capital allocation perspective and an engineering audit perspective.
4. Universal Zero-Hardcoding Mandate:
   - Must scale seamlessly from a 50-person mid-market firm to a Fortune 10 conglomerate across any industry vertical (Banking, Energy, Healthcare, Tech, Manufacturing, Retail) in any language and any ISO 4217 currency.
5. 100% Technical English Codebase:
   - Zero Spanish words anywhere in Python code identifiers, comments, docstrings, or schemas.

YOUR TASK:
Provide an exhaustive, definitive architectural blueprint addressing:
1. Table Layout & Auto-Fit Engine: Exact mathematical specifications for proportional column widths in `TableNode` and `DocxCompiler`.
2. Risk Narrative Card Architecture: Complete visual and structural anatomy of each risk block in prose/bullets (Header, Badges, Vulnerability Prose, Operational Impact, Actuarial Cost Derivation Breakdown, Audit Evidence).
3. Strategic Hierarchy Recommendation: The definitive verdict on how risks should be ordered and grouped to maximize Board decision-making authority.
4. Implementation Roadmap: Step-by-step technical plan to execute these changes with zero bugs, zero anti-patterns, and zero hardcoding.
"""

print(f"Requesting architectural design blueprint from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: STRATEGIC BLUEPRINT FOR TABLE AUTO-FIT & RISK NARRATIVE CARDS")
print("=" * 80)
print(response.text)
print("=" * 80)
