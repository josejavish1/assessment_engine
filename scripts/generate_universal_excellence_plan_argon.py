#!/usr/bin/env python3
"""Adversarial Strategy Review by gemini-4-argon for 100% Universal Deliverable Excellence."""

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
Role: Chief Technology Officer, Principal Compiler Architect & Senior McKinsey Strategy Partner.

OBJECTIVE:
Review the Proposed Architectural Strategy to achieve 100% Zero-Defect Universal Excellence across all assessment deliverables (applicable to any enterprise from mid-market to Global Fortune 10, in any vertical and language):

PROPOSED ARCHITECTURAL SYNTHESIS:
1. Chapter 2 (Objective, Scope & Methodological Framework):
   - Page 4: Executive Objective & Perimeter, Factory/Asset Topology, 3-Framework Alignment Table (CMMI, Domain Standard e.g. ASHRAE/ISO, Open FAIR), and 3 Executive Outcomes.
   - Page 5: 3-Phase Ground-Truth Calibration Methodology, 5-Level CMMI Maturity Scale, and Evaluated Capabilities & Pillar Weight Allocation Table (Climatización 24%, Energía 20%, etc.).
   - Rationale: Fully populates Page 5, resolves the visual white space, and consolidates all qualitative CMMI methodology into Chapter 2 where it belongs.

2. Chapter 3 (Technological Diagnosis & Maturity Dashboard):
   - Page 6: Radar Chart and Global Maturity Scorecard (Nivel 3 - Definido, Gobernanza Estándar, zero English leaks).
   - Pages 7-8: Pillar Diagnostic Table with explicit operational gap analysis and embedded O-FAIR Defensibility formulas.
   - Page 9: Dedicated Cross-Cutting Structural Debt Analysis (Telemetry Blindness, IT/OT Observability Silos, Manual Procedural Toil).

3. Chapter 4 (Quantitative Risk Matrix & Actuarial Exposure - O-FAIR):
   - Page 10: 5x5 Heatmap Matrix (TEF vs LM).
   - Page 11: Return on Resilience & Efficiency Hexagon (RoRE / TBM & FinOps: Lean IT, Cost of Delay, PUE Efficiency, EoL Support Avoidance, Tail Risk CVaR, NIS2 Compliance) and 3 Strategic Risk Portfolios (Tier 1 Critical Modernization, Tier 2 Operational Optimization, Tier 3 Maintenance Backlog).
   - Pages 12-16: Detailed Risk Vulnerability Cards (RVS01 to RVS14) with exact FAIR parameter breakdowns.

4. Chapter 5 (Conclusions, Investment Business Case & Roadmaps):
   - Pages 17-19: Target Transformation Paradigm (Platform as a Product), Immediate Remediations, and the Multi-Horizon Stochastic Inaction Table (1-Year, 3-Year, 5-Year ALE vs. CVaR P90 with 185k € CAPEX, Payback < 3 months, and 455% ROI).

5. Appendices (Institutional Trust & Rigor):
   - Page 20: Appendix C: Chain of Custody & Document Provenance Registry (10-row table mapping questionnaire, context dossier, ITIC downtime, CISA KEV, NIS2, ISO 27001).
   - Pages 21-22: Appendix A: Quantitative Risk Modeling Methodology (Open FAIR™ Standard, Monte Carlo 10,000-run simulation mechanics, TEF and LM scale tables).
   - Page 23: Appendix B: Abbreviations Glossary (clean 2-column table) & Legal Liability Disclaimer (with dynamically interpolated {client_name}).

MANDATORY INVARIANTS:
- Zero Hardcoding: Universal for any company, vertical, and language.
- 100% Technical English Codebase: Zero Spanish in code/docstrings/schemas; Spanish and other target languages exist exclusively as localized output data in engine_config/locales.json.
- Zero Layout Defects: No ghost pages, no orphan headings, strict WCAG 2.1 contrast.

CRITIQUE REQUIREMENTS:
1. Does this architecture achieve 100% consulting perfection and eliminate all residual defects?
2. Are there any hidden risks, layout traps, or anti-patterns in this proposed structure?
3. Provide your formal authorization to proceed with implementation.
"""

print(f"Requesting architectural validation from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: ADVERSARIAL STRATEGY REVIEW FOR 100% UNIVERSAL EXCELLENCE")
print("=" * 80)
print(response.text)
print("=" * 80)
