#!/usr/bin/env python3
"""Deep Universality and Hardcoding Audit by gemini-4-argon across 12 diverse global enterprises."""

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

# Read the physical code of the modified files
receptors_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py").read_text(encoding="utf-8")
ledger_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial/actuarial_ledger.py").read_text(encoding="utf-8")
payload_to_ast_snippet = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")[75000:95000]

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Global Platforms.

USER'S EXPLICIT DIRECTIVE & CONCERN:
"Antes de continuar, quiero que le digas a gemini-4-argon que haga una revisión completa de lo que acabas de programar y busque bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en inglés, nada de español ni una sola palabra... Simplemente haz una simulación de que en realidad no son solo las 3 empresas estas; piensa en más empresas de sectores diferentes... creo que podría llegar a fallar..."

HERE IS THE PHYSICAL CODE CURRENTLY RUNNING IN THE WORKSPACE:

--- FILE 1: src/assessment_engine/adapters/compilers/strategies/actuarial_receptors.py ---
{receptors_code}

--- FILE 2: src/assessment_engine/domain/actuarial/actuarial_ledger.py ---
{ledger_code}

--- FILE 3: SNIPPET FROM src/assessment_engine/adapters/compilers/payload_to_ast.py (Section 4 and Archetype Resolution) ---
{payload_to_ast_snippet}

YOUR AUDIT MANDATE:
Perform a relentless, forensic, adversarial audit of this physical implementation against the following non-negotiable criteria:
1. **Zero Hardcoding & 100% Technical English Law:**
   - Are there ANY Spanish words, Spanish comments, docstrings, variable names, or logs anywhere in the Python code?
   - Are there ANY hardcoded client names, vendor brands, currencies, or sector-specific constants inside the engine logic?
2. **Simulation Across 12 Diverse Global Enterprises (from Mid-Market to Global Tier-1):**
   Evaluate how this code behaves when executed for:
   1. Singapore Airlines (Commercial Aviation, SGD S$, Real-Time GDS)
   2. Saudi Aramco (Upstream Oil & Gas / Energy, SAR)
   3. Toyota Motor Corp (Automotive Lean Manufacturing, JPY ¥)
   4. Amazon Web Services / Datadog (Hyper-scale SaaS / Cloud Infra, USD $)
   5. Novartis (Pharmaceutical R&D & Clinical Trials, CHF)
   6. Inditex / Zara (Fast-Fashion Retail & Rapid Supply Chain, EUR €)
   7. Tokyo Electric Power / TEPCO (Nuclear & Power Grid Utilities, JPY ¥)
   8. Allianz SE (Global Reinsurance & Solvency II Capital, EUR €)
   9. Maersk Line (Intermodal Container Shipping & Automated Port Cranes, DKK)
   10. Oxford University Hospitals NHS Trust (Public Healthcare / ICU, GBP £)
   11. German Precision CNC Mittelstand (Tooling manufacturer, 40M EUR turnover, 250 employees)
   12. M-Pesa / Safaricom Kenya (Emerging Market Telecom & Mobile FinTech, KES)
3. **Flaw & Antipattern Scrutiny:**
   - What happens to the individual risk findings in Section 4.3? Why did the Tribunal notice that the sum of risks in Section 4.3 differed from the Executive Summary ALE?
   - How does the column title `ch4_lineage_col_hourly` in Table 4.1 behave?
   - Are there any edge cases where `IndustryArchetype.from_str` or `delivery_model` resolution will fail or produce an unexpected default?
4. **Definitive Checklist of Required Remediations:**
   Provide a prioritized, crystal-clear list of what must be tuned or refactored to achieve 100% flawless universality.

Respond in 100% Technical English with supreme executive authority and precision.
"""

def main() -> None:
    print(f"Submitting Deep Universality & Hardcoding Audit to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_DEEP_UNIVERSALITY_AND_HARDCODING_AUDIT_REPORT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nDeep Audit Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
