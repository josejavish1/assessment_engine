#!/usr/bin/env python3
"""Consult gemini-4-argon to architect a 100% universal, zero-hardcoded actuarial calibration engine."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Actuarial Arbiter, and author of enterprise quantitative risk frameworks.

USER DIRECTIVE & ARCHITECTURAL CHALLENGE:
"Me preocupa que recalibremos para Molins pero para cualquier otra empresa de cualquier otro sector y otros niveles de madurez salga mal. Hay que encontrar una solución definitiva.
Antes de ponernos a programar hay que pensar bien cómo lo vamos a abordar y en cuántas fases para garantizar que queda sin errores y que vamos a ser #1 mundial, de cualquier vertical, en cualquier idioma.
El código debe estar 100% en inglés, nada de español ni una sola palabra. Aumentar la calidad de los entregables al 100% y que gemini-4-argon lo piense para que sea sin bugs, problemas o antipatrones, CERO HARDCODING. Que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial. Pídeselo a gemini-4-argon en inglés."

THE FUNDAMENTAL TENSION:
In our previous turn, we discovered that:
1. An uncalibrated top-down approach generated an inflated 2.42M EUR for Molins because it used global consolidated turnover for NIS2 and assumed heavy cloud spend on an on-premise cement manufacturer.
2. Conversely, the legacy monolithic downtime model produced an absurdly low 679k EUR (with only 90k for cybersecurity).
3. The true actuarial reality for Molins is ~1.49M EUR (~0.13% of turnover).

HOWEVER, the user rightly warns:
WE MUST NEVER INTRODUCE AD-HOC PATCHES OR CLIENT-SPECIFIC HARDCODING FOR MOLINS!
If we hardcode a "cement silo factor" or "Molins European perimeter haircut", we destroy the universality of the platform and break it for a Brazilian hospital network, a French logistics conglomerate, a Mexican retail chain, or a UK neobank.

YOUR MANDATE:
Design a 100% universal, mathematically grounded, declarative Actuarial Telemetry Calibration Engine that operates purely on macroeconomic principles, industry archetypes, and tenant operational parameters—ZERO client names, ZERO hardcoded hacks, 100% Technical English.

SPECIFIC DESIGN DIMENSIONS:
1. Macroeconomic Calibration Functions:
   - Operational Scope / Perimeter Ratio (omega_perimeter in (0, 1]): How to determine the revenue and asset perimeter exposed to the assessment without hardcoding.
   - Revenue Disruption Elasticity / Buffering Factor (beta_buffering in [0.10, 1.0]): How loss of operational availability scales by industry operational tempo (e.g., continuous digital fintech = 1.0, retail point-of-sale = 0.85, batch logistics = 0.50, heavy process manufacturing with inventory buffering = 0.35).
   - Infrastructure Topology & Cloud Intensity (gamma_cloud in [0.05, 0.95]): How capital inefficiency scales between CapEx-heavy on-premise infrastructure vs OpEx-heavy cloud-native estates.
   - Regulatory Jurisdiction & Supervisory Discretion Factor (theta_regulatory in [0.05, 0.40]): How statutory fines (NIS2, DORA, GDPR, HIPAA, LGPD) model empirical supervisory enforcement rather than theoretical turnover ceilings.
2. Multi-Tenant Parameterization via Industry Archetypes (`financial_profile.py` / `taxonomy_actuarial_archetypes.json`):
   - How these factors are derived organically from the 6 universal operational archetypes (CONTINUOUS_DIGITAL_FINTECH, PROCESS_MANUFACTURING_OT, LIFE_SAFETY_CRITICAL, HIGH_TEMPO_COMMERCIAL, DEFERRED_NETWORK_LOGISTICS, STANDARD_ENTERPRISE_B2B).
3. Exact Closed-Form Mathematical Proof:
   - Demonstrate mathematically how the exact same universal equations produce:
     * Cementos Molins (Process Manufacturing, 1.14B EUR) -> ~1.49M EUR Total ALE.
     * Starling Bank (Continuous Digital FinTech, 140M GBP) -> ~619k GBP Total ALE.
     * Rede D'Or (Life Safety Healthcare, 40B BRL) -> ~11.5M BRL Total ALE.
     * Chedraui (High Tempo Commercial Retail, 250B MXN) -> ~60M MXN Total ALE.
4. Execution Phasing & Implementation Roadmap:
   - Provide a step-by-step phased engineering roadmap to implement this into `src/assessment_engine/domain/actuarial/` without regressions.

Deliver the definitive, world-class Actuarial Calibration Architecture now.
"""

def main() -> None:
    print(f"Submitting Universal Actuarial Architecture request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "architecture" / "ARGON_UNIVERSAL_ACTUARIAL_CALIBRATION_SPEC.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nArchitecture Specification written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
