#!/usr/bin/env python3
"""Consult gemini-4-argon: Design the Universal, Transversal Sobresaliente Architecture across global tenants."""

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

USER_DELIBERATION_PROMPT = """You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Global Platforms.

THE USER'S BRILLIANT, GROUNDED REAL-WORLD REFLECTION & CHALLENGE:
1. **On Point 1 (Catastrophic Recovery vs Emergency Bypass):**
   "Respecto al punto 1 decirte que bueno, 14 a 28 días era para una recuperación total, pero es verdad que para los procesos críticos si hubiera una catástrofe, un usuario de IT va a ir a la fábrica o donde fuera y va a reinstalar desde cero todo limpio y va a instalar el software básico para arrancar y van a empezar a funcionar. Eso ocurre en cualquier empresa: como mínimo lo más crítico, aunque estuviera muy muy mal y no tuvieran una política de 3-2-1-1-0 con todo probado, arranca en modo de contingencia."
   -> The user identifies the crucial operational distinction:
      - **MVR (Minimum Viable Operational Recovery / Emergency Factory Bypass):** Restoring the critical controllers, basic billing, and minimum dispatch so production restarts in 24–72 hours via degraded manual/contingency workarounds.
      - **FFR (Full Forensic & Fleet Restoration):** Total sanitation, Active Directory forensic rebuild, re-imaging of all secondary endpoints, and formal audit closure, which takes 14–28 days.
      The deliverable must articulate BOTH so auditors and C-levels see that we understand real-world factory continuity without trivializing the total forensic recovery tail!

2. **On Point 2 (Actuarial Materiality vs Client Believability):**
   "Respecto al punto dos, llevas razón pero tienen que ser números que la empresa se crea, a ver si vamos a poner un número que no se va a creer y además el ALE es una cosa y el riesgo total es otra. ¿Tú crees que de verdad está tan infravalorado? Vamos a pensarlo bien."
   -> The user is 100% right:
      We CANNOT inflate the ALE into unbelievable fantasy numbers (e.g., tens of millions of euros) that a CFO will instantly dismiss as consultant fear-mongering!
      ALE is the *expected average annualized friction/loss* (a fraction of turnover), while P90 / SLE is the *single extreme catastrophic tail event*.
      How do we calibrate the mathematical relationship between ALE, P90, and corporate turnover so that numbers are 100% credible, mathematically defensible, and sufficiently material to justify modernization CAPEX?

3. **On Point 3 (Workforce Taxonomy in T9):**
   The user agrees that T9 metrics must adapt to the workforce profile (blue-collar frontline operators vs white-collar digital workers).

4. **On Point 4 (CMMI vs Text Inconsistency - The Universal Anti-Pattern Warning):**
   "Respecto al punto 4, ya se supone que teníamos esto superado, se supone que si había una puntuación porque el usuario daba una cosa pero luego la realidad hemos mostrado otra, todo esto se supone que ya lo teníamos trabajado... no sé por qué volvemos a tener ahora estas discrepancias si se supone que todo eso ya estaba solucionado... Y me da mucho miedo que los cambios que apliques solo los apliques para un caso de una empresa como Molins, cuando realmente tiene que ser transversal a todos. Tienes que hacer simulaciones de si ese cambio que propones lo aplicáramos de forma general, si realmente aumentaría la nota de todos o sólo de alguna empresa y cuál sería el plan correcto porque el objetivo es que consigamos un sobresaliente en todos los clientes."

YOUR MANDATE:
Perform an exhaustive architectural and actuarial deliberation:
1. **Root Cause Analysis of CMMI vs Finding Discrepancy:**
   Why did T6 display CMMI 4.50 for PAM while describing shared root passwords? Where does the survey score get injected vs the finding severity?
   How do we build a **Deterministic Universal Coherence Gatekeeper** that automatically caps CMMI sub-scores whenever critical hygiene findings are present, across ANY client in the world?
2. **The Dual-Horizon Recovery Model (MVR vs FFR):**
   How to formulate the P90 scenario universally so it captures both MVR (24-72h operational restart) and FFR (multi-week forensic cleanup) across all industries.
3. **Actuarial Materiality Calibration Matrix:**
   Provide the exact mathematical formula balancing ALE credibility (no fear-mongering) with executive decision-making materiality (CFO defensibility).
4. **Universal Workforce Taxonomy for T9:**
   How `financial_profile.py` automatically routes T9 metrics based on sector workforce composition.
5. **Cross-Tenant Simulation Across 6 Diverse Global Enterprises:**
   Simulate and prove whether this universal architecture elevates the tribunal grades to **Sobresaliente (>8.5/10)** across:
   - Enterprise A: Heavy Process Industry (Cementos Molins - EUR / Spain)
   - Enterprise B: Digital Challenger Bank (Starling Bank - GBP / UK)
   - Enterprise C: Life-Safety Healthcare (Rede D'Or - BRL / Brazil)
   - Enterprise D: Commercial Airline (Global Airline - SGD / Singapore)
   - Enterprise E: Hyperscale Cloud SaaS (Datadog - USD / USA)
   - Enterprise F: Mid-Market Precision Manufacturing (German CNC Mittelstand - EUR / Germany)

Deliver your definitive, 100% Technical English architectural report.
"""

def main() -> None:
    print(f"Submitting Universal Sobresaliente Architecture deliberation to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=USER_DELIBERATION_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "architecture" / "ARGON_UNIVERSAL_SOBRESALIENTE_ARCHITECTURE.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nUniversal Architecture written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
