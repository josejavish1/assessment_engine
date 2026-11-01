#!/usr/bin/env python3
"""Generates a step-by-step implementation plan for Cross-Tower Risk Deduplication using gemini-4-argon."""

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
Role: Chief Software Architect (Enterprise Systems) & Principal Risk Fellow (Open FAIR).

CONTEXT:
We have mathematically and ontologically validated the "Cross-Tower Deduplication Architecture" (Primary Custodian vs. Tangential Contributor).
Now, we must implement this safely in our Python codebase (`assessment_engine`).

MANDATES & CONSTRAINTS:
1. Zero Bugs, Zero Problems, Zero Anti-patterns.
2. Zero Hardcoding: The solution must scale to any enterprise worldwide, across any vertical, supporting any number of towers (T1..T6+), in any language, and any currency.
3. 100% Technical English Codebase: No Spanish words in the Python code, schemas, variables, or comments. Spanish is exclusively for output generation via `locales.json`.
4. Mathematical Parity (No Split-Brain): The cross-tower risk evaluation must yield exactly ZERO additional ALE for tangential contributor risks, resolving double counting.

YOUR TASK:
Provide a highly specific, step-by-step IMPLEMENTATION PLAN (in strict Technical English).
Detail exactly how to modify our codebase (e.g., `schemas/risk_ontology.py`, `actuarial_calculator.py`, `payload_to_ast.py`, `docx_compiler.py`, and `locales.json`) to implement this functionality.

The plan must address:
1. Schema Extension: Updating `ConditionalLossEvent` to support `ownership_type` (PRIMARY_CUSTODIAN vs TANGENTIAL_CONTRIBUTOR), `primary_risk_ref`, and `contributing_towers`.
2. Actuarial Logic: Ensuring the `ActuarialEngine` strictly zeros out the financial loss output (`effective_sle`, `annualized_loss_expectancy`) if `ownership_type` is TANGENTIAL_CONTRIBUTOR, while preserving frequencies or metadata if needed for presentation.
3. AST and UI Output: How `payload_to_ast.py` modifies the "Mini-Infographic Risk Card" layout to visually indicate a tangential risk (e.g. changing colors, omitting ALE fields, explicitly stating "ALE accounted for in [primary_risk_ref]").
4. Localization: New keys required in `locales.json` to explain cross-tower linkages in all supported languages.

Be extremely precise. This plan will dictate our next refactoring steps.
"""

print(f"Requesting implementation plan from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: IMPLEMENTATION PLAN FOR CROSS-TOWER DEDUPLICATION")
print("=" * 80)
print(response.text)
print("=" * 80)
