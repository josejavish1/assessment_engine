#!/usr/bin/env python3
"""Adversarial and Comprehensive Codebase Review by gemini-4-argon of the recent Risk Ontology & Mini-Infographic implementation."""

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

# Load relevant source files
files_to_audit = [
    REPO_ROOT / "src/assessment_engine/domain/schemas/risk_ontology.py",
    REPO_ROOT / "src/assessment_engine/domain/actuarial_calculator.py",
    REPO_ROOT / "src/assessment_engine/domain/schemas/ast.py",
    REPO_ROOT / "src/assessment_engine/adapters/compilers/docx_compiler.py",
    REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py",
    REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py",
]

context_code = ""
for f_path in files_to_audit:
    if f_path.exists():
        context_code += f"\n\n{'=' * 40}\nFILE: {f_path.relative_to(REPO_ROOT)}\n{'=' * 40}\n"
        context_code += f_path.read_text(encoding="utf-8")

prompt = f"""
Role: Principal Security Architect, Lead Quality Assurance Auditor & Chief Risk Officer.

TASK:
Perform a relentless, exhaustive, and adversarial code review on the newly implemented Open FAIR Risk Ontology and Mini-Infographic Card compiler pipeline.

INSPECT THE FOLLOWING CODEBASE CONTEXT:
{context_code}

CRITICAL MANDATES TO AUDIT:
1. ZERO HARDCODING & UNIVERSAL SCALING:
   - Check every single line for hardcoded company names, facility locations, hardcoded currency symbols, fixed monetary amounts, or magic ratios.
   - Verify that this logic works seamlessly for a 50-person credit union, a regional hospital, a global investment bank, or a Fortune 10 manufacturer anywhere in the world.
   - Verify that all currencies (USD, EUR, GBP, JPY, etc.) and locales (en, es, fr, de, ja, pt, etc.) are handled dynamically.
2. 100% TECHNICAL ENGLISH CODEBASE:
   - Scan all identifiers, variable names, function names, class names, docstrings, inline comments, exception messages, logger statements, and regex literals.
   - Zero tolerance for any Spanish words or non-English identifiers in Python code (Spanish is permitted ONLY inside `locales.json` data dictionaries or dynamic translation output).
3. ZERO BUGS & ZERO ANTI-PATTERNS:
   - Identify any potential `KeyError`, `IndexError`, `AttributeError`, `ZeroDivisionError`, `TypeError`, or `NoneType` exceptions.
   - Verify table grid span calculations, column width sums, and boundary conditions in `TableLayoutCalculator` and `_compile_table`.
   - Inspect fallbacks: ensure no silent error masking (`except: pass`), CWE-391 fail-open defects, or unhandled null references.
4. ACTUARIAL RIGOR (OPEN FAIR):
   - Confirm proper distinction between SLE (Single Loss Expectancy), LEF (Loss Event Frequency), and ALE (Annualized Loss Expectancy).
   - Verify precision handling (`Decimal` vs floating point).

OUTPUT FORMAT:
Provide a structured, unvarnished audit report:
- FINAL VERDICT: PASS or FAIL
- FINDINGS COUNT: (Critical, Major, Minor)
- DETAILED FINDINGS: Line number, severity, exact issue, and required code change (if any).
- FINAL SYNTHESIS: Objective technical assessment of the implementation.
"""

print(f"Requesting deep adversarial review from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: ADVERSARIAL AUDIT OF RISK ONTOLOGY & INFOGRAPHICS")
print("=" * 80)
print(response.text)
print("=" * 80)
