#!/usr/bin/env python3
"""Stress-test the 4-Flaw Remediation Plan against global client fixtures (UK, Brazil, France, Mexico) with gemini-4-argon."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, and Master of Multi-Tenant Cloud Architecture.

USER'S VITAL INQUIRY & SKEPTICISM:
"¿Pero seguro que con ese plan para otras empresas como la UK o Brasil que tenemos también servirá? Piénsalo y dime si hay que hacer ajustes."

CONTEXT:
Our platform evaluates radically different enterprises across the globe using the exact same code engine:
1. **UK Neobank (Starling Bank):** Digital-Native FinTech, GBP (£), 6 active scoped towers, zero on-premise hardware, 100% AWS cloud-native, continuous real-time transaction tempo.
2. **Brazilian Healthcare Network (Rede D'Or São Luiz):** Life-Safety Critical, BRL (R$), Portuguese language, 9 active towers, clinical ICU telemetry, legacy hospital PACS systems, strict ANPD/LGPD privacy requirements.
3. **French Logistics Conglomerate (Geodis):** Deferred Network Logistics, EUR (€), French language, 10 active towers, distributed warehouses, customs EDI gateways, freight routing.
4. **Mexican Retail Chain (Chedraui):** High-Tempo Commercial Retail, MXN ($), Spanish language, 5 active towers, omnichannel supermarkets, point-of-sale terminal resilience.

YOUR MISSION:
Perform a deep, adversarial cross-tenant stress-test on the proposed 4-Phase Remediation Plan:
1. **Stress-Test on UK FinTech:**
   - Does Flaw 1 (P90 triggers) work when the company has NO physical plant? (e.g., T10 is core banking clearing, T1 is AWS co-location).
   - Does Flaw 3 (Gamma switch) properly select 100% Cloud FinOps for Starling without mentioning hardware depreciation?
   - Does Flaw 4 (Beta decay) correctly apply near-zero buffering (instant transaction loss)?
2. **Stress-Test on Brazilian Healthcare (Rede D'Or):**
   - Does the plan work in Portuguese (`pt_BR`)?
   - How does Flaw 1 handle life-safety medical systems (e.g., ICU clinical monitor disruption instead of cement clinker silos)?
   - How does Flaw 3 handle hybrid medical PACS architectures?
3. **Identify any Hidden Gaps or Flaws in the Plan:**
   - Are there any edge cases where the proposed plan would break or require manual tweaks?
   - What architectural adjustments MUST be incorporated into the Master Plan right now to guarantee 100% universal compatibility?
4. **Final Verdict & Necessary Refinements:**
   - State whether the plan is universally sound as-is, or detail the exact refinements required.

Respond in 100% Technical English with supreme precision.
"""

def main() -> None:
    print(f"Submitting Cross-Tenant Stress Test to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_CROSS_CLIENT_STRESS_TEST_REPORT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nStress Test Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500])
    if len(report) > 3500:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
