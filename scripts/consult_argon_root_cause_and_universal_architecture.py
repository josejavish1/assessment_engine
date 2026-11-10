#!/usr/bin/env python3
"""Consult gemini-4-argon to architect a permanent, universal root-cause solution for deliverable purity."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Code Quality Arbiter, and Chief Forensic Auditor for the Assessment Engine.

CRITICAL USER MANDATE:
"Hay que encontrar la causa raíz de cada uno de esos problemas no para solucionarlo aquí, que es una empresa de control para calibrar, sino que lo solucionemos para siempre con una solución robusta top tier 1:
- Antes de ponernos a programar hay que pensar bien cómo lo vamos a abordar y en cuántas fases para garantizar que queda sin errores y que vamos a ser número 1 mundial, de cualquier vertical, en cualquier idioma.
- El código debe estar 100% en inglés, nada de español ni una sola palabra.
- CERO hardcoding: debe servir para cualquier empresa del mundo, desde mediana a top tier 1."

THE 4 ROOT-CAUSE VULNERABILITIES DISCOVERED IN TOWER 1 AUDIT:

1. ROOT CAUSE 1: Foreign Language Leakage in English Deliverables (Spanish KPI & Pillar Names):
   - In Starling Bank (English UK neobank), Annex 1 generated:
     * Table 13 Risk Title: `[RVS04] Protección Contra Incendios y Seguridad Ambiental`
     * Table 14 Risk Title: `[RVS05] Operación de Facilities, Monitorización y Mantenimiento`
     * Executive Bullets P11-P13: `Absence of empirical verification in Utilización de capacidad eléctrica (potencia instalada vs potencia usada)`
   - Discovered Mechanism: 
     a) `engine_config/towers/T*/tower_definition_T*.json` files were historically authored with Spanish pillar/KPI names.
     b) `engine_config/taxonomy_multilingual.json` contains translations for towers and pillars, but LACKS a canonical multilingual schema for individual KPIs (K1..Kn).
     c) In `in_memory_asis_compiler.py` and `payload_to_ast.py`, when a capability name or finding title is resolved, if the taxonomy resolver does not find an exact match, it falls back to `default=raw_cap` (which is the raw Spanish string from the definition file).

2. ROOT CAUSE 2: Actuarial P90 Exposure Discrepancy (£3.5M vs £14k):
   - In Executive Summary (P15), the template formats `{p90_var_exposure_fmt}`, which receives the CONSOLIDATED corporate portfolio P90 exposure (£3,569,781).
   - In Section 4.3 (P108), the tower callout box calculates the LOCAL tower-specific P90 loss (£14,098).
   - An executive CTO reading the document sees £3.5M on page 3 and £14k on page 16, destroying actuarial credibility.

3. ROOT CAUSE 3: Blanket Downtime Rate Without Domain Attenuation Scope:
   - The global revenue hourly burn rate (£140,000/hr) is stated in Tower 1 as if losing one facility circuit immediately halts 100% of the bank's clearing operations, rather than contextualizing the Open FAIR single-loss impact factor (e.g. 20% or 40% partial operational degradation).

4. ROOT CAUSE 4: Codebase English Purity & Non-English Localized Delivery:
   - The user requires 100% Technical English engineering artifacts (code, schemas, comments, logs, variable names). Spanish or other languages exist strictly as localized customer output data.

YOUR MISSION:
Deliver an uncompromising, multi-phase master architectural blueprint to solve these 4 root causes permanently and universally:
- How to structure the multilingual taxonomy so that ANY tower, pillar, or KPI automatically resolves to the requested document language (EN, PT, ES, FR, DE, JA) with ZERO fallback to Spanish or English leaks.
- How to reconcile the actuarial P90 narrative contracts so that executive summaries and callout boxes present mathematically coherent, non-contradictory local vs. consolidated exposures.
- How to structure the Open FAIR hourly downtime narrative so the impact factor and scope attenuation are transparently explained.
- How to implement automated CI/CD linguistic purity gates to prevent any foreign string leaks.

Constraints:
- Respond in 100% Technical English.
- Do not provide code implementation yet; provide the rigorous, step-by-step Architectural Plan.
- Must be globally universal for ANY company, ANY vertical, and ANY language.

Deliver your architectural judgment now.
"""

def main() -> None:
    print(f"Submitting root cause and universal architecture request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_UNIVERSAL_ROOT_CAUSE_BLUEPRINT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nUniversal Architecture Blueprint written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3500])
    if len(audit_report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")

if __name__ == "__main__":
    main()
