#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 042 Dynamic Tenant Workload Adaptation & Transparent Actuarial Rate Lineage.

Formulates the architectural blueprint before any code is modified, guaranteeing:
1. Zero hardcoding of tenant-specific application names (e.g. no hardcoded SAP/MES in catalogs).
2. Transparent, CFO-verifiable mathematical derivation of the composite hourly downtime rate.
3. 100% Technical English codebase and universal multi-tier enterprise scalability.
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


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    prompt = """
Role: Chief Actuarial Systems Architect & Principal Enterprise Compiler Engineer (Google Tier-1 Core Infrastructure / Anthropic Engineering / MIT Actuarial Fellow).

CONTEXT & USER CRITIQUE (DEEP ARCHITECTURAL FEEDBACK):
The user reviewed the proposed RFC 041 architecture and delivered two critical, staff-level engineering insights:

1. Dynamic Tenant Workload Adaptation (Anti-Hardcoding Law):
   - The user observed:
     "Respecto al punto 1 diferenciación narrativa dinámica entre las 10 Torres estoy de acuerdo en parte porque cada cliente es totalmente distinto entonces hardcodear exactamente el texto puede no ser la mejor opción por ejemplo tú dices en la torre dos su impacto en la disponibilidad transaccional del SAP ERP sistemas MES de fabricación y elasticidad ante picos pero la realidad es que cada cliente puede ser de un idioma distinto en un país distinto con una vertical distinta y con una casuística concreta distinta... hardcodearlo puede ser sí pero hay que tener mucho cuidado o quizá no para adaptarlo a cada empresa hay que pensar qué hacemos."
   - The user is 100% correct: Hardcoding specific enterprise applications like "SAP ERP" or "MES" into tower catalog definitions (`tower_catalog.json`) is a brittle anti-pattern. If the client is a Japanese logistics giant using Oracle/Go microservices, a German hospital chain running Cerner/Epic, or a US SaaS provider on AWS, hardcoding "SAP and MES" destroys credibility and violates Law #2 (Zero Hardcoding).
   - Architectural Requirement: How do we dynamically resolve the tenant's real mission-critical systems and workloads from their payload telemetry (`included_components`, `primary_workloads`, `business_critical_services`, `domain_introduction`), while keeping tower catalogs purely abstract and capability-oriented across all 10 towers?

2. Transparent Mathematical Lineage for the Hourly Rate (CFO Credibility):
   - The user observed:
     "y luego otro punto tú hablas de la explicación natural de la tasa en el párrafo 3 y yo lo que digo es que si salen 11428,60 € quiero saber la fórmula de cómo sale: 'oye pues para calcular esto se ha hecho teniendo en cuenta esto y este número así lo hemos tenido en cuenta teniendo esto entre esto'... es decir, contar la fórmula y de dónde han salido los números porque ese número es la clave de absolutamente todo, de todo lo que hacemos, de cómo escalamos. Ese número tiene que estar hiper bien explicado, quizá en el resumen ejecutivo no tanto pero sí un poco porque si no no se va a entender y van a tirar todo el informe a la basura."
   - The user is completely right: The hourly outage rate ($R_{\text{hourly}} = 11.428,60\text{ €/h}$) is the single foundational multiplier for the entire report. If a CFO asks *"How was this calculated?"* and the report gives only hand-wavy prose, the CFO will dismiss the entire deliverable.
   - Architectural Requirement:
     a) How should the exact mathematical formula be stated concisely in Chapter 1 (Executive Summary) so the CFO sees the mathematical lineage (Base Operational Velocity + Contractual SLA Penalties + Emergency Recovery Labor Burden) without overwhelming the narrative with unverified macro numbers?
     b) Where and how should the full step-by-step mathematical derivation table be rendered in the document (e.g. Chapter 2 Methodology / Chapter 4 Actuarial Analysis) so the finance department can audit every single variable down to the cent?
     c) How does this formula scale universally across enterprise tiers (e.g. 50M€ mid-market -> ~570 €/h, heavy industry -> ~11,400 €/h, tier-1 global bank -> ~150,000 €/h)?

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTIPATTERNS, ZERO DEFECTS.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - Scalable across any enterprise tier (50M€ to 50B€), any vertical, any currency (EUR, USD, GBP, JPY, CHF, etc.), and any locale.
   - Zero hardcoded client names, zero hardcoded application names (no hardcoded SAP/MES in catalogs), zero hardcoded rates.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, method names, variables, identifiers, docstrings, comments, logs, and exceptions must be 100% Technical English.
   - Zero Spanish words anywhere in Python source files.
4. SPLIT-BRAIN ERADICATION (100% 10-TOWER SYMMETRY).
5. ISO/IEC 29500 OPENXML & EDITORIAL EXCELLENCE.

YOUR TASK:
Synthesize a comprehensive Architectural Blueprint (RFC 042) in Markdown:
1. Dynamic Tenant Telemetry Resolution Engine: Design the algorithm that extracts and normalizes the client's actual systems, applications, and operational scope from payload telemetry across all 10 towers without hardcoding.
2. Transparent Mathematical Lineage for the Hourly Burn Rate:
   - Provide the exact algebraic formula and parameter definitions.
   - Design the concise 2-sentence executive explanation for Chapter 1.
   - Design the formal Actuarial Derivation Callout Box / Table for Chapter 2 or Chapter 4.
3. Executive Summary Narrative Templates for `engine_config/locales.json` in Spanish and English.
4. Concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 042 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_042_DYNAMIC_WORKLOADS_AND_TRANSPARENT_ACTUARIAL_LINEAGE_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 042 DYNAMIC WORKLOADS & TRANSPARENT ACTUARIAL LINEAGE")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
