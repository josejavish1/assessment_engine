#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 041 Domain-Specific Executive Prose, European Currency Formatting, and Operational P90 Realism."""

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

CONTEXT & USER CRITIQUE:
The user reviewed the Chapter 1 Executive Summary across Tower 1 and Tower 2 and provided four vital architectural and editorial critiques:

1. Cookie-Cutter Robotic Introductory Paragraphs Across 10 Towers:
   - The user noticed that Paragraph 1 in Tower 1 and Tower 2 are 100% identical word-for-word, except for the tower name and score:
     * T2: "La evaluación técnica de la torre de Hybrid Compute & Platforms en Molins sitúa su índice de madurez arquitectónica en 2,46 / 5,00 sobre 5.0 (Nivel 2 - Repetible), evidenciando una postura operativa expuesta a 3 vectores de vulnerabilidad estructural. Dado que este dominio sustenta directamente la continuidad de cargas de misión crítica de producción..."
     * T1: "La evaluación técnica de la torre de Physical Data Center & Facilities en Molins sitúa su índice de madurez arquitectónica en 2,61 / 5,00 sobre 5.0 (Nivel 3 - Definido), evidenciando una postura operativa expuesta a 3 vectores de vulnerabilidad estructural. Dado que este dominio sustenta directamente la continuidad de cargas de misión crítica de producción..."
   - User critique: "si los comparas chirria algo raro... parece demasiado encorsetado y suena a un robot en ambas torres. ¿Cómo lo mejoramos con el objetivo del primer párrafo? Piensa que son 10 torres y que cada una es diferente."
   - Architectural Need: Each of the 10 capability towers (T1 Data Center, T2 Compute, T3 Storage, T4 Network, T5 OT/Industrial, T6 Cybersecurity, T7 Applications/ERP, T8 Data/AI, T9 Workplace, T10 Governance/FinOps) has its OWN distinct operational mission, architectural role, and baseline challenge. Paragraph 1 must dynamically incorporate the specific domain role and mission from catalog telemetry (`engine_config/towers/T*/tower_definition_T*.json`) so that all 10 deliverables feel bespoke, natural, and distinct.

2. Repetitive Opening in Paragraph 2:
   - "El diagnóstico de ingeniería revela una convergencia de riesgos técnicos, contractuales y de ciclo de vida que comprometen la resiliencia a corto y medio plazo" feels like another rigid copy-paste opening. It needs dynamic variation based on the dominant risk theme (e.g., physical capacity vs contractual lifecycle vs security/governance).

3. European Currency Formatting & Rate Explanation:
   - In Spanish, German, French, and European typography, the currency symbol is placed AFTER the amount with a non-breaking space (e.g. `11.428,60 €/h`, `141.184 €`, `101.231 €`), NOT prefixed like American English (`€ 11.428,60/h`).
   - The rate `11.428,60 €/h` needs a brief, natural explanation: it incorporates base industrial output velocity plus contractual SLA breach penalties and emergency recovery labor burden.

4. The P90 Reality Dilemma (Crucial Operational Insight):
   - The user writes:
     "para acabar donde yo tengo dudas es el P90 tengo serias dudas de que sea real, porque en realidad el cliente en ese tiempo siempre encontrará soluciones antes para restablecer la productividad, no me creo que una fábrica se pare 59 horas o 102 horas según la torre que mires y el equipo IT no haya encontrado una solución en mucho menos tiempo para restablecer la fábrica, por lo que quizás el cómo se calcula el P90 debe ajustarse a una realidad operacional y no teórica."
   - The user is completely right: In heavy industrial manufacturing, no plant or dispatch weighbridge remains paralyzed for 102 continuous hours (over 4 full days). Plant engineers would implement manual paper dispatching, emergency generators, or disaster bypasses within 8 to 24 hours.
   - Root Cause of the Flaw: The previous code naively divided the total financial Value-at-Risk (P90) by the hourly downtime rate:
     $$\text{Hours} = \frac{1.168.111 \text{ €}}{11.428,60 \text{ €/h}} = 102,2 \text{ horas}$$
     This erroneously assumed that 100% of the P90 financial loss is *linear continuous plant stoppage*!
   - Real-World Actuarial Reality (Open FAIR / ISO 22301):
     In a catastrophic P90 event:
     a) Physical operational stoppage (RTO) is capped by business continuity procedures at a realistic operational recovery window (e.g., 12 to 24 hours max).
     b) The financial loss of 1,168,111 € consists of:
        - The direct physical downtime loss during that maximum recovery window.
        - PLUS: Emergency vendor SLA triage fees, expedited hardware replacement freight, contractual customer delivery delay penalties, and data reconstruction/reconciliation costs.
     - When explained this way, both the Plant Operations Director (who knows the plant will restart in <24h) and the CFO (who knows the true bill includes vendor fees, freight, penalties, and triage) will find the analysis 100% defensible and realistic!

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTIPATTERNS, ZERO DEFECTS:
   - Flawless mathematical, exception-handling, and architectural design.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - Works across all 10 capability towers (T1..T10), any tier (50M€ to 50B€), any vertical, any currency, and any locale.
   - Zero hardcoded client names or numbers in Python code.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, method names, variables, identifiers, docstrings, comments, logs, and exceptions must be 100% Technical English.
   - Zero Spanish words anywhere in Python source code.
4. SPLIT-BRAIN ERADICATION (100% 10-TOWER SYMMETRY).
5. ISO/IEC 29500 OPENXML & EDITORIAL EXCELLENCE.

YOUR TASK:
Synthesize a comprehensive Architectural Blueprint (RFC 041) in Markdown:
1. Dynamic Tower Mission Architecture: Show how to inject domain-specific operational missions into Paragraph 1 across all 10 towers from catalog definitions (`tower_definition_T*.json`), eliminating the robotic identical template.
2. Locale-Aware Currency Formatting Engine: Show how to format currency postfixes (`11.428,60 €/h`) vs prefixes (`$11,428.60/hr`) based on locale rules.
3. Operational P90 Modeling: Formulate the mathematical and narrative separation between the physical Recovery Time Window (capped at 12–24h) and the compound financial Value-at-Risk ($VaR_{90}$), explaining the exact composition of the tail loss.
4. Complete bilingual templates for `engine_config/locales.json` (Spanish and English).
5. Concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 041 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_041_OPERATIONAL_P90_REALISM_AND_TOWER_DIFFERENTIATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 041 OPERATIONAL P90 REALISM & TOWER DIFFERENTIATION")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
