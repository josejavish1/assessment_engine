#!/usr/bin/env python3
"""Comprehensive Codebase Universality & Zero-Hardcoding Audit by gemini-4-argon across 15 Global Sectors."""

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

receptors_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py").read_text(encoding="utf-8")
ledger_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial/actuarial_ledger.py").read_text(encoding="utf-8")
financial_profile_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial/financial_profile.py").read_text(encoding="utf-8")

payload_to_ast_path = REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py"
p_ast_text = payload_to_ast_path.read_text(encoding="utf-8")

# Extract relevant AST methods: Chapter 1 synthesis, Chapter 4 modeling, and Section 4.3 risk scaling
ast_ch1_snippet = p_ast_text[p_ast_text.find("class ExecutiveNarrativeSynthesizer:"):p_ast_text.find("def resolve_domain_introduction(")]
ast_ch4_snippet = p_ast_text[p_ast_text.find("def _build_chapter_4_actuarial_modeling("):p_ast_text.find("def _build_chapter_5_conclusions(")]

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Global Platforms.

USER'S SACRED MANDATE & CHALLENGE:
"Antes de continuar, quiero que le digas a gemini-4-argon que haga una revisión completa de lo que acabas de programar y busque bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en inglés nada de español ni una sola palabra... Simplemente haz una simulación de que en realidad no son solo estas 3 empresas; piensa en más empresas de sectores diferentes... creo que podría llegar a fallar..."

HERE IS THE EXACT CODE CURRENTLY IN THE CODEBASE:

=== FILE 1: src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py ===
{receptors_code}

=== FILE 2: src/assessment_engine/domain/actuarial/actuarial_ledger.py ===
{ledger_code}

=== FILE 3: src/assessment_engine/domain/actuarial/financial_profile.py ===
{financial_profile_code}

=== FILE 4: AST COMPILER CHAPTER 1 SYNTHESIS (src/assessment_engine/adapters/compilers/payload_to_ast.py) ===
{ast_ch1_snippet}

=== FILE 5: AST COMPILER CHAPTER 4 MODELING & SECTION 4.3 (src/assessment_engine/adapters/compilers/payload_to_ast.py) ===
{ast_ch4_snippet}

YOUR AUDIT INSTRUCTIONS:
1. **Zero Hardcoding & 100% Technical English Law:**
   - Scan every line of Python code, comments, docstrings, log messages, and exception texts.
   - Are there ANY Spanish words anywhere in the Python files?
   - Are there ANY hardcoded client names, sector names, vendor names (e.g. Broadcom, VMware, Cisco), or currency symbols hardcoded in Python?
2. **Multi-Tenant Simulation across 15 DIVERSE GLOBAL ENTERPRISES:**
   Simulate the exact code execution for 15 companies across different sizes, currencies, languages, and sectors:
   1. Commercial Airline (Singapore Airlines - SGD S$ / en)
   2. Upstream Oil & Gas Supermajor (Saudi Aramco - SAR / ar)
   3. Lean Automotive Manufacturing (Toyota Motor Corp - JPY ¥ / ja)
   4. Hyperscale Multi-Tenant Cloud SaaS (Datadog / AWS - USD $ / en)
   5. Global Pharmaceutical R&D & Clinical GxP (Novartis - CHF / de)
   6. Fast Fashion Omnichannel Retail & Supply Chain (Inditex / Zara - EUR € / es)
   7. Nuclear & High-Voltage Electric Transmission Utility (TEPCO - JPY ¥ / ja)
   8. Global Reinsurance & Solvency II Capital Group (Allianz SE - EUR € / de)
   9. Intermodal Container Shipping & Automated Port Terminal (Maersk - DKK / da)
   10. Public Health Service & Acute Care ICU (Oxford University Hospitals - GBP £ / en)
   11. Mid-Market Precision CNC Tooling (German Mittelstand - EUR € / de - 40M EUR turnover, 250 staff)
   12. Emerging Market Mobile Money & Telecom Infrastructure (M-Pesa / Safaricom - KES / sw)
   13. Global Mining & Mineral Extraction (BHP / Rio Tinto - AUD A$ / en)
   14. Tier-1 Corporate Law & Cross-Border Advisory Firm (Skadden Arps - USD $ / en)
   15. Semiconductor Photolithography Equipment Manufacturer (ASML - EUR € / nl)
3. **Forensic Analysis of Execution Path for each Enterprise:**
   - For each enterprise, trace how `IndustryArchetype.from_str`, `delivery_model`, `operational_archetype`, `cloud_intensity_gamma`, `buffering_elasticity_beta`, and `ActuarialLedgerSSOT` behave.
   - Where could an unhandled exception occur?
   - Where could a template formatting `KeyError` occur?
   - Where could the math or text produce an incongruous result (e.g., clinker silos in a law firm, or server reboots in a licensing audit)?
4. **Identification of ANY Lingering Bugs, Problems, or Antipatterns:**
   - List every single flaw, bug, or risk of failure detected in the current codebase.
5. **Final Executive Verdict:**
   - Clear, unequivocal summary of the platform's readiness and exact recommendations.

Respond in 100% Technical English with supreme executive authority and mathematical precision.
"""

def main() -> None:
    print(f"Submitting 15-Sector Codebase Universality Audit to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_15_SECTOR_COMPREHENSIVE_CODEBASE_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\n15-Sector Comprehensive Audit Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
