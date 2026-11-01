#!/usr/bin/env python3
"""Adversarial Reality-Check on the Exponential MTTR Transfer Function by gemini-4-argon."""

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
Role: Lead Reliability Engineer (IEEE 493 / Uptime Institute Tier Specialist), Chief Actuary (Open FAIR Fellow), and SRE Director (DORA Metrics).

USER'S SKEPTICAL QUESTION:
The user asks with total justification:
"¿Cómo de real es esto? --> MTTR_{ajustado} = MTTR_{base} × e^{-k · (CMMI_{dominio} - 3.0)}
* Si la nota CMMI del cliente en Climatización es 1.70 (muy baja), el tiempo de recuperación se dispara y la frecuencia sube.
* Si otro cliente en la Torre Cloud tiene un CMMI de 4.10, la duración se comprime hacia minutos y la frecuencia cae a una vez cada 5 o 10 años."

YOUR TASK:
Provide a brutally honest, scientifically rigorous, and unvarnished reality check:
1. THE RAW TRUTH:
   - Is `MTTR = MTTR_base * e^(-k * (CMMI - 3.0))` an official ISO, IEEE, or Open FAIR standard formula, or is it an actuarial proxy / transfer heuristic synthesized by modelers?
   - Be completely honest about what Open FAIR and CMMI actually dictate vs what is an engineering approximation.
2. EMPIRICAL VALIDITY (WHERE IT IS REAL VS WHERE IT BREAKS DOWN):
   - In Cloud / Software / DevOps (Tower 3 / Tower 5): Compare with real empirical DORA (DevOps Research and Assessment) benchmark data (e.g. Low vs Elite performers: MTTR from days down to under 1 hour).
   - In Physical Data Center Infrastructure (Tower 1: Power, Cooling, Cabling): Explain the physical boundaries of thermodynamics and mechanical components (IEEE 493 Gold Book, Uptime Institute).
     * Why a blown transformer, seized chiller compressor, or severed fiber cable CANNOT be repaired in "minutes" regardless of whether a company is CMMI 5.0.
     * What high maturity ACTUALLY does in physical facilities (Redundancy N+1/2N, predictive vibration/thermal telemetry, automated ATS/STS transfer, spare parts stocking, 4-hour vendor SLAs), and how that affects *business service downtime* vs *physical component repair time*.
3. HOW A TIER-1 ENGINE MUST ACTUALLY IMPLEMENT THIS (PRACTICAL & DEFENDABLE):
   - How should the Assessment Engine realistically bound and model recovery time and failure probability without relying on magic formulas that a skeptical Chief Engineer or CFO will tear apart?
   - Propose the bounded, auditable, and defensible methodology.
"""

print(f"Requesting unvarnished reality check from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: THE UNVARNISHED REALITY CHECK ON CMMI <-> MTTR TRANSFER FUNCTIONS")
print("=" * 80)
print(response.text)
print("=" * 80)
