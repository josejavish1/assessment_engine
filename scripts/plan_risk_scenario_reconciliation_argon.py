#!/usr/bin/env python3
"""Consult gemini-4-argon on dynamic risk scenario count reconciliation (Table 4 vs Table 5)."""

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
Role: Principal Enterprise Systems Architect, Lead Actuary for Technology Risk, and Zero-Trust Systems Auditor.

OBJECTIVE:
Formulate the architectural and mathematical specification (RFC 069) to resolve an arithmetic split-brain in Table 4 of Chapter 3:
"En la tabla del 3.1 se indica 'Escenarios Evaluados' en una columna que tiene en todas las torres 4 escenarios evaluados pero luego dice total de consolidado 29 y ese número no cuadra."

AUDIT OF THE ARITHMETIC FLAW:
1. In Table 4 (Section 3.1 - Annualized Financial Exposure by Domain):
   - The column header is "Escenarios Evaluados" (Evaluated Scenarios).
   - Currently, the compiler populated this column using `len(subpillars)` (which is 4 for each of the 10 towers).
   - $10 \times 4 = 40$!
   - But the total row at the bottom hardcoded `"29"`!
   - This caused an embarrassing arithmetic contradiction: 10 rows showing `4` (sum = 40), and the total row showing `29`.
2. In Table 5 (3-Tier Portfolio Table):
   - Tier 1: 7 scenarios
   - Tier 2: 12 scenarios
   - Tier 3: 10 scenarios
   - Total: $7 + 12 + 10 = 29$ risk scenarios!
3. In Section 3.1 introductory narrative:
   - Mentions "29 escenarios evaluados a lo largo de los 10 dominios tecnológicos".

NON-NEGOTIABLE LAWS:
- Multi-Tenant Scale: Must work for any organization in the world (whether they have 20, 29, 35, or 50 risk scenarios).
- 100% Dynamic Reconciliation: The total row must compute `sum(scenario_counts)` dynamically—NEVER hardcode `"29"` or any fixed string in the total cell!
- Ontological Clarity: Clearly distinguish between:
  * "Risk Scenarios" ($N=29$ in Molins portfolio, partitioned across the 10 towers: T1:3, T2:4, T3:3, T4:2, T5:4, T6:3, T7:2, T8:3, T9:2, T10:3 $\sum = 29$).
  * "Subpillars / Diagnostic Dimensions" ($N=40$ across 10 towers, 4 per tower).
- 100% Technical English Codebase: Zero Spanish in Python code, docstrings, or variables.

DELIVERABLES REQUIRED IN RFC 069:
1. Exact mathematical distribution of risk scenarios per domain ensuring $\sum_{i=1}^{10} S_i = S_{\text{portfolio}} = 29$.
2. Dynamic telemetry data model: How `financial_telemetry` or `global_payload` can specify scenario counts per domain, with a fallback algorithm that allocates total scenarios proportional to domain risk weight or catalog baseline.
3. Code implementation blueprint for `tomo_asis_ast_compiler.py`:
   - Dynamic computation of `total_scenarios_sum = sum(domain_scenarios.values())`.
   - Dynamic interpolation of `total_scenarios_sum` in Table 4 total row, bridge narrative, and Table 5.
"""

    print(f"Requesting RFC 069 specification from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_069_RISK_SCENARIO_RECONCILIATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")
    print(f"Successfully generated RFC 069 specification: {out_file}")


if __name__ == "__main__":
    main()
