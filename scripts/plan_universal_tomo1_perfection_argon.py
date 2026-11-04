#!/usr/bin/env python3
"""Universal Tomo 1 AS-IS Architectural Plan Generator via gemini-4-argon.

Consults gemini-4-argon (reasoning tier) to produce a flawless, zero-bug, zero-antipattern
architectural plan and engineering specification for the consolidated Tomo 1 AS-IS report.

Guarantees:
1. Universal Enterprise Scalability (50M€ mid-market to 50B€ Tier-1 global, any vertical, any currency).
2. Pure AS-IS Diagnostic Boundary (zero premature TO-BE leakage or roadmap prescriptions).
3. Sober, Constructive Executive Tone (McKinsey/Gartner Board-ready, zero alarmism/FUD).
4. Transparent Actuarial & Closed-Form Mathematical Reconciliation (zero split-brain).
5. 100% Technical English Codebase & Zero Hardcoded Tenant Data.
6. Mathematical i18n Symmetry across all 6 supported locales (en, es, pt, fr, de, ja).
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
Role: Principal Enterprise Systems Architect & Senior Partner at Gartner / McKinsey, advising Executive Boards of Global Fortune 500 enterprises.

OBJECTIVE:
Formulate the definitive, zero-bug, zero-antipattern architectural implementation plan for the Consolidated Tomo 1 AS-IS Diagnostic Deliverable within the Assessment Engine compiler ecosystem.

The system compiles Abstract Syntax Tree (AST) representations into high-density, board-ready Word (.docx) and PDF documents. We need to elevate Tomo 1 AS-IS to an undisputed 10/10 masterwork of engineering, editorial elegance, and financial realism.

CRITICAL REQUIREMENTS & NON-NEGOTIABLE LAWS:

1. UNIVERSAL MULTI-TENANT ENTERPRISE SCALABILITY:
   - Must scale cleanly for ANY enterprise in the world: from a 50M€ mid-market industrial firm to a 50B€ multinational conglomerate.
   - Must support ANY industry vertical: Heavy Manufacturing, Utilities, Energy, Banking & Financial Services, Telecommunications, Healthcare, Retail & Logistics, etc.
   - Must support ANY currency (EUR, USD, GBP, JPY, CHF, etc.) and locale.
   - ZERO hardcoding of client names (e.g., Molins, Secil), physical locations (e.g., Sant Vicenç dels Horts), specific hardware models, or fixed numbers of findings in Python code.
   - The compiler must dynamically ingest data from SSOT payloads (global_payload, tower_payloads, financial_telemetry) and externalized configuration catalogs (`locales.json`).

2. 100% TECHNICAL ENGLISH CODEBASE & LANGUAGE DECOUPLING:
   - Python production code, comments, docstrings, variable names, exceptions, and tests MUST be 100% Technical English. Zero Spanish characters or words in Python source files.
   - Spanish (and any other natural language) exists exclusively as declarative content in `engine_config/locales.json` or localized payload data.
   - Language parameters must be mandatory (e.g. `doc_lang: str`), never optional with defaults like `doc_lang = "es"`.
   - Zero inline language ternaries or conditionals in adapters (e.g., no `if doc_lang == "es"`).
   - Zero hardcoded fallback string literals in translation calls (e.g., no `t("key", doc_lang, default="...")`).
   - 100% mathematical symmetry in `locales.json` across all 6 supported locales: `es`, `en`, `pt`, `fr`, `de`, `ja`. Every key present in `es` must exist in all other locales.

3. THE 4 STRATEGIC USER CRITIQUES (FROM RECENT FORENSIC AUDIT):
   A. Tone De-Catastrophization & Executive Elegance:
      - Eradicate sensationalist, apocalyptic, or alarmist FUD language (e.g., "severa deuda técnica", "riesgo inminente", "colapso térmico", "parálisis", "diagnóstico forense").
      - Shift to a sober, factual, objective McKinsey/Gartner tone: frame risks through operational capacity thresholds, design limits, life-cycle milestones, and statistical exposure.
   B. Title & Subtitle Simplification:
      - Replace baroque, jargon-heavy headings with simple, clear, executive Spanish (e.g., "1. Resumen Ejecutivo", "2. Nivel de Madurez Tecnológica", "3. Impacto Económico y Análisis de Riesgos", "4. Situación Actual por Áreas Tecnológicas", "5. Relaciones y Dependencias entre Áreas").
   C. Strict AS-IS Diagnostic Boundary:
      - Purge premature TO-BE prescriptions, target scores (e.g., "Objetivo H1"), roadmap waves, or vendor migration strategies that belong strictly in Tomo 2 (Target Architecture & Roadmap).
      - In Chapter 2 (Table 3), compare current maturity against Industry Benchmark (e.g., 3.50) and Deviation, NOT future targets.
      - In Chapter 4 domain headers, display operational status and exposure level, NOT future project priorities.
      - In Chapter 5, focus on Current Operational Coupling / Domino Effects (how an outage in Domain A propagates to Domain B under the existing architecture), NOT migration prerequisites.
   D. Closed-Form Actuarial & Financial Reconciliation (Zero Split-Brain):
      - Perfect accounting reconciliation: sum of 10 domain exposures must equal corporate ALE P50 to the exact integer.
      - Transparent distinction between:
        * Annualized Loss Expectancy (ALE P50): Latent unhedged actuarial risk exposure across all 29 stochastic scenarios.
        * Recurring Cash Leakage (e.g., FinOps contract duplication): Realized annual OPEX inefficiency with 100% certainty.
        * Local Major Outage (P90): Discrete worst-case single incident at a primary facility.
        * Annual Portfolio Tail Risk (ALE P90): Group-wide multi-event statistical tail risk.
      - Mathematical reconciliation in CMMI score: weighted average (2.55) vs simple arithmetic mean (2.62) with clear explanatory footnote.
      - Clean SLE * LEF = ALE arithmetic in top risk cards.

4. VISUAL DENSITY & EXECUTIVE ERGONOMICS:
   - High visual aesthetic without clutter.
   - Chapter 2: Integration of CMMI Polar Radar Chart (`global_radar_chart.png`).
   - Chapter 3: 5x5 Open FAIR Heatmap Mosaic Table & Top Corporate Systemic Risk Cards (3-column layout).
   - Chapter 4: Full 10-domain coverage with 4-column KPI strip (Score, Operational Status, ALE, Exposure Level) + narrative + 2-column deep-dive table (Sub-pillars vs Forensic Evidence) + 10-SPOF Matrix.
   - Chapter 5: Cross-Tower Operational Nexus table.
   - Appendix: Standard Glossary and Disclaimer.

DELIVERABLE REQUIRED FROM YOU (GEMINI-4-ARGON):
Produce a comprehensive, rigorous architectural blueprint and step-by-step implementation guide:
1. Architectural Design & Component Breakdown:
   - How `TomoAsisASTCompiler` will be structured to satisfy all clean architecture, performance, and anti-pattern rules.
   - Exact helper methods, data flows, and fallback telemetry resolvers.
2. Complete Internationalization (i18n) Strategy & Key Catalog:
   - List of all canonical keys needed in `locales.json`.
   - Exact Spanish and English translations for all headings, table headers, descriptions, and catalog items.
   - How symmetry across `es`, `en`, `pt`, `fr`, `de`, `ja` will be enforced deterministically.
3. Actuarial & Financial Precision Engine:
   - Closed-form formulas for ALE derivation, P90 scaling, tier distribution, and tower allocation.
   - Exact mathematical reconciliation rules to eliminate any apparent split-brain.
4. Step-by-Step Execution Plan:
   - Order of operations for code and configuration updates.
   - Regression prevention and test strategy to ensure all unit and integration tests pass with 0 failures.
   - PDF compilation and visual artifact validation steps.
"""

    print(f"Requesting universal architecture plan from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_065_UNIVERSAL_TOMO_1_PERFECTION_PLAN_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated universal architecture plan: {out_file}")


if __name__ == "__main__":
    main()
