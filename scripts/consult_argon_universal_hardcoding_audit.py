#!/usr/bin/env python3
"""Adversarial audit by gemini-4-argon: Identify all hidden hardcoding, inline dictionaries, and sector fragility."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Design Patterns.

USER'S VITAL WARNING & ACCUSATION:
"Tengo la sensación de que has hardcodeado cosas que no deberías haber hardcodeado. Antes de continuar, quiero que le digas a gemini-4-argon que haga una revisión completa de lo que acabas de programar y busque bugs, problemas o antipatrones. No quiero nada hardcodeado, recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en inglés, nada de español ni una sola palabra. Simplemente haz una simulación de que en realidad no son solo estas 3 empresas; piensa en más empresas de sectores diferentes... Creo que podría llegar a fallar..."

THE ACCUSATION IS 100% JUSTIFIED.
Inspect the recent changes we made:
1. In `src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py`:
   - We embedded raw multilingual dictionaries (`text_map = {"es": "...", "pt": "...", "fr": "..."}`) directly into Python functions!
   - We literally hardcoded "(Broadcom/VMware)" into the Spanish text inside Python!
   - We hardcoded vendor/sector terminology into the strategy classes instead of delegating to `locales.json`!
2. In `src/assessment_engine/adapters/compilers/payload_to_ast.py`:
   - We implemented an ad-hoc keyword search:
     `is_cloud_tenant = any(k in combined_profile for k in ("FINTECH", "BANK", "CLEARING", "SAAS", "DIGITAL", "NEOBANK", "CLOUD"))`
     `is_health_tenant = any(k in combined_profile for k in ("HEALTH", "HOSPITAL", "CLINIC", "LIFE_SAFETY", "MEDICAL"))`
     `operational_archetype = "CONTINUOUS_DIGITAL_FINTECH" if is_cloud_tenant else ("LIFE_SAFETY_CRITICAL" if is_health_tenant else "PROCESS_MANUFACTURING_OT")`
   - WHAT HAPPENS TO EVERY OTHER SECTOR ON EARTH?
     A global airline (Lufthansa), an electric utility (Iberdrola), an omnichannel retailer (Walmart/Chedraui), a university, a telecom (Vodafone), a pharmaceutical company, a logistics carrier (Maersk/Geodis), a mining group (BHP)?
     Under our naive if/else, EVERY SINGLE ONE OF THEM defaults to "PROCESS_MANUFACTURING_OT" and starts receiving cement plant silo buffering narratives!

YOUR MANDATE:
Deliver an unsparing, exhaustive forensic audit:
1. SIMULATE 10 DIVERSE GLOBAL ENTERPRISES:
   - Commercial Airline (real-time flight dispatch & reservation)
   - Telecommunications Provider (5G packet core & OSS/BSS)
   - Global Omnichannel Retailer (POS & supply chain)
   - Public University & Research Hospital
   - National Electric Transmission Grid
   - Media Streaming & Entertainment Network
   - Aerospace & Defense Manufacturer
   - Tier-1 Corporate Law & Advisory Firm
   - Sovereign Wealth & Asset Management Fund
   - Global Container Shipping & Port Operations
2. SHOW EXACTLY HOW AND WHERE THE CURRENT CODE FAILS, HALLUCINATES, OR BREAKS FOR THESE 10 ENTERPRISES.
3. IDENTIFY EVERY SINGLE HARDCODED ARTIFACT IN OUR RECENT COMMITS:
   - Specific lines, specific embedded dictionaries, specific vendor names ("Broadcom/VMware").
4. PROVIDE THE DEFINITIVE, 100% DECLARATIVE ARCHITECTURAL REMEDIATION:
   - How `IndustryArchetype` in `financial_profile.py` maps to the 6 universal archetypes without keyword hacks.
   - How ALL text, headings, formulas, and context blocks are strictly externalized to `engine_config/locales.json` across all supported languages (Zero non-English text in Python).
   - How `delivery_model` is parameterized organically from tenant infrastructure telemetry (e.g. `cloud_ratio = cloud_spend / (cloud_spend + hardware_depreciation)`).

Respond in 100% Technical English with supreme precision and zero sycophancy.
"""

def main() -> None:
    print(f"Submitting Deep Hardcoding Audit to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_DEEP_HARDCODING_AND_UNIVERSALITY_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nHardcoding Audit Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
