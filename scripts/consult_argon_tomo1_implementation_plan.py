"""Consult gemini-4-argon for the exact step-by-step code implementation plan for Tomo 1."""

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

PROMPT = """You are 'gemini-4-argon', Lead Adversarial Red Team Chief Architect at a top-tier consulting firm in November 2026.

We need an EXACT, STEP-BY-STEP IMPLEMENTATION PLAN to refactor `tomo_asis_ast_compiler.py` and `scripts/build_full_client_delivery_suite.py` so that `Molins_202610_Tomo_1_Diagnostico_ASIS.docx` is generated with 100% mathematical monism, zero stale cache, zero 0 EUR anomalies, and 100% referential integrity with the 10 specialist annexes.

Key Files:
1. `src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py`
2. `scripts/build_full_client_delivery_suite.py`
3. `engine_config/locales.json`

Specific Requirements for the Plan:
1. **Dynamic Bottom-Up Ingestion:** In `_resolve_financial_telemetry` and `compile`, strictly iterate over `tower_payloads` calling `derive_in_memory_fair_risks`. Collect all 61 active risks.
2. **Deterministic Mathematical Monism:**
   - `corporate_ale` = sum of all active risk ALEs from the 10 towers.
   - `worst_incident_cost` = max(r['sle'] for r in active_risks if r['sle'] > 0). Identify exact `worst_incident_code` and `worst_incident_domain`.
   - `corporate_p90` = corporate_ale * 1.35 (or portfolio copula calculation). Must be > corporate_ale.
3. **Top 5 / Top 10 Dynamic Sort:**
   - Sort all 61 active risks by `ale` descending. Top 5 cards and Top 10 table MUST use these exact sorted objects. Never read `corporate_top_risks` or `tomo_top_risks_catalog`.
4. **CMMI Score Unification:**
   - Set single authoritative score `2.01 / 5.00` everywhere (or arithmetic 2.10, but pick ONE and use it consistently across cover, cockpit, text, and tables).
5. **Lexical Gate for Table 8:**
   - Clean all pipe delimiters `|` and unparsed database dumps from systemic risk taxonomy descriptions.

Provide the exact file paths, function signatures, replacement logic, and validation checks. Be precise and exhaustive.
"""

print(f"Submitting Tomo 1 Implementation Plan query to {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=PROMPT,
)

out_file = REPO_ROOT / "docs" / "audits" / "TOMO1_DETAILED_IMPLEMENTATION_PLAN.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\nPlan complete. Wrote {len(response.text)} chars to {out_file.relative_to(REPO_ROOT)}")
