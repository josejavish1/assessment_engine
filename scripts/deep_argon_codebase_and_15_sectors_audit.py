#!/usr/bin/env python3
"""Adversarial Codebase Review by gemini-4-argon: Deep code-level audit and 15-sector simulation for universal zero-hardcoding."""

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

# Read the physical code of all relevant files
gatekeeper_code = (REPO_ROOT / "src/assessment_engine/domain/coherence_gatekeeper.py").read_text(encoding="utf-8")
financial_profile_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial/financial_profile.py").read_text(encoding="utf-8")
ledger_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial/actuarial_ledger.py").read_text(encoding="utf-8")
receptors_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py").read_text(encoding="utf-8")

payload_to_ast_path = REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py"
p_ast_text = payload_to_ast_path.read_text(encoding="utf-8")
p_ast_compile_snippet = p_ast_text[p_ast_text.find("def compile_asis_docx_via_ast("):]
p_ast_ch4_snippet = p_ast_text[p_ast_text.find("def _build_chapter_4_actuarial_modeling("):p_ast_text.find("def _build_chapter_5_conclusions(")]

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Global Platforms.

USER'S SACRED MANDATE & CHALLENGE:
"Antes de continuar, quiero que le digas a gemini-4-argon que haga una revisión completa de lo que acabas de programar y busque bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en inglés, nada de español ni una sola palabra... Simplemente haz una simulación de que en realidad no son solo estas 3 empresas; piensa en más empresas de sectores diferentes... creo que podría llegar a fallar..."

HERE IS THE EXACT CODE CURRENTLY DEPLOYED IN THE REPOSITORY:

=== FILE 1: src/assessment_engine/domain/coherence_gatekeeper.py ===
{gatekeeper_code}

=== FILE 2: src/assessment_engine/domain/actuarial/financial_profile.py ===
{financial_profile_code}

=== FILE 3: src/assessment_engine/domain/actuarial/actuarial_ledger.py ===
{ledger_code}

=== FILE 4: src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py ===
{receptors_code}

=== FILE 5: AST COMPILER SNIPPET (compile_asis_docx_via_ast & Chapter 4) ===
{p_ast_compile_snippet[:4000]}
...
{p_ast_ch4_snippet[:6000]}

YOUR DETAILED AUDIT INSTRUCTIONS:
1. **Zero Hardcoding & 100% Technical English Law:**
   - Scan every line of Python code, comments, docstrings, variable names, and error messages.
   - Are there ANY Spanish words anywhere in the Python files?
   - Are there ANY hardcoded client names, sector names, vendor names, or currencies in the engine logic?
2. **Multi-Tenant Simulation across 15 DIVERSE GLOBAL ENTERPRISES:**
   Simulate the code execution for 15 companies across different sizes, currencies, languages, and sectors:
   1. Commercial Airline (Singapore Airlines - SGD S$ / en)
   2. Supermarket / Retail Chain (Carrefour - EUR € / fr)
   3. Upstream Oil & Gas / Energy (Saudi Aramco - SAR / ar)
   4. High-Tech Semiconductor Foundry (ASML / TSMC - EUR € / nl)
   5. Multi-Tenant B2B SaaS Hyperscaler (Datadog - USD $ / en)
   6. Public Healthcare Network / ICU (NHS Trust - GBP £ / en)
   7. Nuclear & Electric Power Grid (TEPCO - JPY ¥ / ja)
   8. Fast-Fashion Global Supply Chain (Inditex Zara - EUR € / es)
   9. Global Corporate Investment Bank (Barclays - GBP £ / en)
   10. Automotive Just-in-Time Assembly (Toyota - JPY ¥ / ja)
   11. Mid-Market German CNC Precision Tooling (40M EUR turnover, 250 staff, de)
   12. Emerging Market Mobile Money Telecom (M-Pesa Safaricom Kenya - KES / sw)
   13. Global Mining & Mineral Extraction (BHP - AUD A$ / en)
   14. Cross-Border Corporate Law & Advisory Firm (Skadden - USD $ / en)
   15. Defense & Aerospace Systems Contractor (Airbus - EUR € / fr)
3. **Forensic Analysis of Failure Modes across the 15 Enterprises:**
   - For each enterprise, trace the code path: where could an unhandled exception, template KeyError, broken math, or sector mismatch occur?
   - Examine how the upstream split-brain affects them: what happens if interview facts contradict survey scores?
   - What happens to the financial calculations if a company is very small (5M EUR) vs very large (150B USD)?
4. **Definitive Checklist of Bugs, Problems, or Antipatterns in the Current Code:**
   - Identify every single remaining flaw, bug, or risk of failure in the codebase.
5. **Final Executive Verdict & Actionable Remediation.**

Respond in 100% Technical English with supreme executive authority and unflinching technical rigor.
"""

def main() -> None:
    print(f"Submitting 15-Sector Codebase Review to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_15_SECTOR_CURRENT_CODEBASE_DEEP_REVIEW.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nDeep Codebase Review written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
