#!/usr/bin/env python3
"""Argon-4 Deep Forensic Audit: Financial Telemetry Incoherence, Hourly Downtime Rates, and Plain-Language Executive Risk Modeling (RFC 034)."""

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
Role: Principal Actuarial Systems Architect & Executive Editorial Director (Gartner / McKinsey Senior Partner / MIT Actuarial Fellow).

CRITICAL USER AUDIT & CORE INCOHERENCE REPORTED:
The user performed an in-depth review of Chapter 1 across Tower 1 (Data Center Facilities) and Tower 2 (Hybrid Compute) and raised 3 profound architectural questions:

1. INCOHERENCE IN HOURLY DOWNTIME COST BETWEEN TOWERS:
   - "no entiendo porque en la torre 2 habla de '10.000 €/hora.' y en la torre 1 dice '(€ 2.091/h)', sigo pensando que hay muchas incoherencias que no entiendo. ¿por qué tenemos un problema profundo de fondo que hay que solucionar?"
   - Forensic Analysis: For the same corporate client (Molins, a multinational cement and materials manufacturer), how can an hour of operational downtime cost 10,000 €/h in Tower 2 and 2,091 €/h in Tower 1?
   - In `payload_to_ast.py`, line 528 calculated `hourly_rate = total_fair_ale / 67.5 = 141,184 / 67.5 = 2,091 €/h` as an ad-hoc fallback because `hourly_downtime_rate` was not explicitly persisted in the blueprint payload, whereas in Tower 2, the narrative cited 10,000 €/h!
   - This creates an obvious credibility collapse: a CIO or CTO reading both towers immediately spots that the financial baseline rate is completely incoherent between reports!

2. ACCESSIBLE, SIMPLE FINANCIAL EXPLANATION FOR NON-FINANCIAL TECHNICAL READERS:
   - "toda la parte donde se habla de números creo que hay que pensarlo muy bien, no creo que esté bien explicada, vamos a pensar, imagina que eres el lector del documento y tienes perfil técnico pero no financiero, y te empiezo a hablar de números, tu quieres saber que son esos números explicados sencillo y de donde salen y como se han calculado, aunque sea en 2 3 párrafos porque todo absolutamente todo viene de ahí"
   - The current text throws dense actuarial terms (ALE, P90, Monte Carlo, Open FAIR) at the reader without plain, intuitive explanations.
   - A technical reader (VP Infrastructure, CTO, Lead Architect) needs to understand:
     a) What is ALE (Expected Annual Loss)? It is NOT an invoice or budget line item; it is the statistical average annual cost of recurring operational friction, micro-interruptions, and engineering fire-fighting toil.
     b) Where does the figure come from (e.g. 141,000 € or 101,000 €)? It comes from taking the empirical probability of failure across the evaluated technical risk scenarios and multiplying by the downtime hours and the client's validated cost of operational stoppage (e.g. 10,000 €/h).
     c) What is the P90 Stress Scenario (e.g. 1.17 M€ or 675 K€)? It is the "perfect storm" or severe tail-risk scenario (90th percentile): what happens when multiple concurrent failures strike during peak manufacturing or logistics dispatch windows, requiring extended recovery (MTTR).

3. GIANT WALLS OF TEXT / POOR EDITORIAL PACING:
   - "primero que los párrafos son como muy grandes y dificulta su lectura"
   - Currently, Paragraph 2 is an overwhelming 180-word block of dense text that mixes score, maturity band, ALE, P90, hourly cost, and failure scenarios into one suffocating paragraph.
   - We need clean, elegant, human executive pacing: 3 or 4 well-structured, readable paragraphs (each 50 to 80 words) with clear topic sentences and breathing room.

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless mathematical and architectural design.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The solution must scale to ANY company in the world: any vertical, any currency, any size.
   - Client-wide financial parameters (e.g. `hourly_downtime_cost`) must be authoritative at the tenant level and shared consistently across all towers.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, method names, variables, and docstrings must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 034) in Markdown:
1. Root cause analysis of the financial rate incoherence (10,000 €/h vs 2,091 €/h) and the pipeline fix to ensure a single, authoritative, tenant-level `hourly_downtime_cost` is propagated symmetrically across all 10 towers.
2. The "Plain-Language Financial Risk Model" pedagogical framework: how to explain ALE, P90, and downtime rate to a non-financial technical leader in crystal-clear, persuasive, credible prose.
3. Redesign of Chapter 1 executive narrative into well-paced, readable paragraphs (avoiding giant walls of text).
4. Concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 034 deep financial audit from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_034_FINANCIAL_TELEMETRY_AND_PEDAGOGICAL_NARRATIVE_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 034 FINANCIAL AUDIT & REMEDIATION PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
