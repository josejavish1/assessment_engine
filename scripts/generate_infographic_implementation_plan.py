#!/usr/bin/env python3
"""Generates an implementation plan for the Risk Ontology and Infographic update using gemini-4-argon."""

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
Role: Chief Risk Officer (Open FAIR Fellow), Senior Partner (Industrial Infrastructure & Board Advisory), and Principal Software Architect.

CONTEXT:
We need to implement the previously designed "Mini-Infographic Risk Card" and the new "Risk Ontology (Conditional Loss Events)" into the Assessment Engine.
The goal is to elevate the quality of the deliverables to 100%.

MANDATES & CONSTRAINTS:
1. Zero Bugs, Zero Problems, Zero Anti-patterns.
2. Zero Hardcoding: The solution must scale to any enterprise worldwide (mid-market to top tier 1), any vertical (Banking, Energy, Manufacturing, etc.), any language, and any currency.
3. 100% Technical English Codebase: No Spanish words in the Python code, schemas, variables, or comments. Spanish is only for localized output via `locales.json`.

YOUR TASK:
Provide a step-by-step, bulletproof IMPLEMENTATION PLAN (in English) that details EXACTLY how to refactor the Python codebase (`payload_to_ast.py`, `docx_compiler.py`, `ast.py`, etc.) and the data structures to achieve this.

The plan must cover:
1. Data Model / Schema Updates (e.g., updating `RiskItem` or AST nodes to support the 3-step bow-tie causal chain, SLE vs ALE, operational coupling factor).
2. Actuarial Engine Adjustments (where and how to safely calculate LEF, SLE, ALE, and the return period without hardcoding specific industry metrics).
3. AST Construction (how `payload_to_ast.py` should assemble the new `TableNode` structure with merged cells, specific DXA widths, and background colors to form the infographic).
4. DOCX Compiler updates (if any new layout features are needed in `docx_compiler.py` to support complex merged tables).
5. Localization (what new keys need to be added to `locales.json`).

Be highly specific regarding the architecture and the sequence of steps to ensure a flawless execution.
"""

print(f"Requesting implementation plan from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: IMPLEMENTATION PLAN FOR RISK INFOGRAPHICS & ONTOLOGY")
print("=" * 80)
print(response.text)
print("=" * 80)
