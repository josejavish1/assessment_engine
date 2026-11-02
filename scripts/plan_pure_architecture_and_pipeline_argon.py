#!/usr/bin/env python3
"""Argon-4 Master Architectural Consultation: RFC 040 Enterprise Executive Realism & Actuarial Credibility.

Instructs gemini-4-argon to think through and formulate the complete architectural blueprint
before any code is written, ensuring zero bugs, zero antipatterns, zero hardcoding,
and 100% Technical English codebase standards.
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

MISSION CONTEXT:
The user reviewed the generated assessment deliverables and delivered critical feedback regarding the executive narrative and actuarial framing of Chapter 1 (Executive Summary) in technical capability tower annexes:

"no se si es una tomadura de pelo, otra vez habla de 1.000.000 sigue todo bastante mal explicado la verdad ---> Para traducir esta fragilidad al lenguaje del comité de dirección, hemos huido de estimaciones teóricas. Aplicando un modelo actuarial calibrado sobre la facturación consolidada expuesta (1.000.000.000 €), determinamos un coste compuesto de inactividad de € 11.428,60/h (integrando lucro cesante directo del 0,0010%, penalizaciones de SLA y sobrecoste de recuperación). Esta valoración matemática vincula cada riesgo de la plataforma directamente con su impacto sobre el EBITDA de Molins.
Además, para evitar la inflación artificial del riesgo, hemos deduplicado los radios de impacto solapados: la exposición neta se sitúa en 8,9 horas críticas anuales, representando una Pérdida Anualizada (ALE) de € 101.231. En un escenario de estrés extremo (percentil 90), la parálisis se dispararía hasta las 59,1 horas de interrupción incontrolable (un impacto contingente de € 675.231).
hazme un diagnostico no cambies nada... lo único es antes de ponernos a programar hay que pensar bien como lo vamos a abordar para garantizar que queda sin errores y que vamos a aumentar la calidad de los entregables al 100% y quiero lo piense gemini-4-argon que lo haga sin bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra."

DEEP ROOT CAUSE ANALYSIS OF THE FAILURES:
1. Unverified Macro Revenue Leakage:
   Parading "(1.000.000.000 €)" in parentheses in a domain technical annex looks like an invented, unverified figure pulled from thin air. A technical specialist annex should NOT flaunt macro-corporate turnover unless explicitly certified by client financial filings.
2. Cognitive Dissonance in Executive Impact (Macro vs Micro Mismatch):
   Juxtaposing a 1,000,000,000 € turnover with an Annual Loss Expectancy (ALE) of 101,231 € creates a credibility collapse for the CFO. 101k € is 0.01% of revenue (less than 2 junior headcount). If leadership reads that the risk is only 8.9 hours and 100k €, they will conclude the tower is completely healthy and requires ZERO capital investment.
3. Defensive Consultant Meta-Narrative:
   Sentences like "hemos huido de estimaciones teóricas" or "para evitar la inflación artificial del riesgo hemos deduplicado los radios de impacto solapados" represent defensive analyst kitchen-talk. A Board of Directors / CIO wants business reality, operational urgency, and strategic investment trade-offs, not a consultant justifying how their algorithms work.
4. Total Erasure of Physical & Contractual Gravitas:
   The narrative was trapped in an abstract loop of theoretical rates and hours, while completely silencing the real, existential risks that keep engineers and plant managers awake:
   - Imminent contractual cliff: Broadcom/VMware renewal in May 2027 with massive core-based licensing price shocks.
   - Hardware End of Support (EoSL): HPE SimpliVity hyperconverged nodes facing lack of replacement parts between 2028-2030.
   - Severe RAM & CPU overcommitment: 300+ VMs preventing automated N+1 failover without manually shutting down dev/test environments.
   - Regulatory exposure: Unsupported legacy CentOS 5/6 operating systems violating European NIS2 cybersecurity mandates.

THE 5 NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTIPATTERNS, ZERO DEFECTS:
   - Flawless mathematical, exception-handling, and architectural design.
   - Fail-fast enforcement: no silent error swallowing.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The engine must scale to ANY company in the world: any tier (50M€ mid-market to 50B€ F10), any vertical (Heavy Manufacturing, Banking, Logistics, Healthcare, SaaS, Energy), any currency (EUR, USD, GBP, JPY, CHF, etc.), and any locale.
   - Zero hardcoded client names, zero hardcoded numbers, zero language-specific assumptions in Python code.
3. 100% TECHNICAL ENGLISH CODEBASE (LANGUAGE DECOUPLING LAW):
   - All Python code, class names, method names, variables, identifiers, comments, docstrings, logs, exceptions, and regexes must be 100% Technical English.
   - Zero Spanish words anywhere in Python source code files. (Spanish is ONLY permitted in `locales.json` data dictionaries).
4. SPLIT-BRAIN ERADICATION (100% 10-TOWER SYMMETRY):
   - All 10 towers (T1 through T10) must execute the exact same unified pipeline and code paths. Zero special-casing for T1 or T2.
5. ISO/IEC 29500 OPENXML & EDITORIAL EXCELLENCE:
   - Native Word TOC with deterministic layout synchronization, auto-fitted tables, professional executive typography (#2E404D slate, 10.5pt body).

YOUR TASK:
Synthesize a comprehensive, definitive Architectural Blueprint (RFC 040) in Markdown:

1. Architectural Separation of Concerns:
   - Define where macro-corporate financials (group revenue, enterprise-wide ALE) belong vs where domain technical annexes focus.
   - Show how technical annexes should frame financial exposure: focusing on domain operational continuity, asset replacement value, vendor renewal price shocks, and unhedged cost of inaction.

2. Actuarial Realism & Credibility Engine:
   - Redesign how hourly outage cost and loss expectancies are modeled so they never look like invented round numbers, nor trivial micro-percentages.
   - Show how domain criticality and asset tiering scale universally from mid-market to Fortune 10 without hardcoding.

3. Executive Narrative Framework (Minto Pyramid Principle):
   - Design the 4-part executive narrative structure in McKinsey/Gartner register:
     * Paragraph 1: Operational Posture & Critical Dependencies (grounded in the physical reality of the tower).
     * Paragraph 2: Core Architectural Dilemma & Contractual Horizons (hardware obsolescence, vendor licensing cliffs, regulatory compliance).
     * Paragraph 3: Financial Exposure & Downtime Horizon (probabilistic operational loss and business interruption velocity).
     * Paragraph 4: Modernization Mandate & Strategic ROI (the business case for transformation and operational stabilization).
   - Provide the complete, pristine bilingual templates for `engine_config/locales.json` (Spanish and English).

4. Production Implementation Plan:
   - Detail the exact files to be updated (`payload_to_ast.py`, `downtime_calibrator.py`, `locales.json`, etc.).
   - Provide concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 040 Master Architectural Blueprint from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_040_EXECUTIVE_REALISM_AND_ACTUARIAL_CREDIBILITY_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 040 MASTER ARCHITECTURAL BLUEPRINT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nBlueprint saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
