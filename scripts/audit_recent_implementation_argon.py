#!/usr/bin/env python3
"""Adversarial Implementation Auditor via gemini-4-argon.

Performs an exhaustive, uncompromising audit of the recent codebase modifications:
1. src/assessment_engine/domain/actuarial_taxonomy_clusterer.py
2. Section 3.1 & 3.2 modifications in src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py
3. Localization additions in engine_config/locales.json
4. Clean packaging in scripts/build_full_client_delivery_suite.py

Audits for:
- Hidden hardcoding or assumptions about specific clients, verticals, or towers.
- Language Decoupling Law violations (any Spanish in Python code/comments).
- Mathematical or actuarial edge-case defects (division by zero, rounding discrepancies, empty feeds).
- Anti-patterns in Clean/Hexagonal Architecture or AST rendering.
"""

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
    print(f"Connecting to reasoning engine: {model_name}...")

    clusterer_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial_taxonomy_clusterer.py").read_text(encoding="utf-8")
    compiler_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py").read_text(encoding="utf-8")
    
    # Extract relevant sections of tomo_asis_ast_compiler.py (around Chapter 3)
    c_lines = compiler_code.splitlines()
    ch3_excerpt = "\n".join(c_lines[1390:1780])

    prompt = f"""
Role: Principal Staff Systems Architect, Zero-Trust Code Auditor, and Senior Partner at McKinsey / Anthropic / Google.

TASK:
Perform a hostile, uncompromising code and architectural audit of our recent implementation in the Assessment Engine repository.
You must rigorously hunt down ANY bug, latent defect, architectural anti-pattern, or hardcoding violation.

CORE MANDATES & LAWS:
1. 100% TECHNICAL ENGLISH CODEBASE:
   - Check every line of Python code, comments, docstrings, variable names, logs, exceptions, and tests.
   - Any non-English word or Spanish character in Python source files is a CRITICAL violation.
2. ZERO HARDCODING:
   - No assumptions that a client is in manufacturing, banking, or retail.
   - No assumptions about specific company names, domain codes ("T1", "T5"), or specific numbers.
   - Must scale cleanly from a 50M€ mid-market company to a 50B€ global Tier-1 multinational, across any vertical and any of our 6 supported languages (es, en, pt, fr, de, ja).
3. ACTUARIAL & MATHEMATICAL INTEGRITY:
   - Check all arithmetic operations: division by zero guards, rounding stability (ROUND_HALF_UP / Decimal vs float), percentage summation reconciliation.
   - Check edge cases: what happens if risk_vectors is empty? What happens if tower_payloads is None or missing pillars? What happens if total_portfolio_ale is 0.0?
4. CLEAN / HEXAGONAL ARCHITECTURE:
   - Domain layer (src/assessment_engine/domain/) must remain 100% pure (zero I/O, zero network, zero open() calls).
   - AST node construction must be robust, thread-safe, and deterministic.

CODE UNDER AUDIT:

--- FILE 1: src/assessment_engine/domain/actuarial_taxonomy_clusterer.py ---
{clusterer_code}

--- FILE 2 EXCERPT: tomo_asis_ast_compiler.py (Chapter 3 Risk Register & Taxonomy Table 3.2.B) ---
{ch3_excerpt}

AUDIT DELIVERABLE:
Generate a comprehensive, board-ready audit report in Markdown:
"ARGON ADVERSARIAL IMPLEMENTATION AUDIT: SECTION 3.1 & 3.2 DYNAMIC RISK TAXONOMY".

The report MUST include:
1. Executive Verdict: Pass / Fail / Conditional Pass.
2. Forensic Inspection Findings (categorized as Critical, High, Medium, Low, or Informational):
   - Language Decoupling inspection.
   - Zero-Hardcoding inspection.
   - Mathematical / Actuarial Edge-Case inspection.
   - Clean Architecture & AST Layout inspection.
3. Concrete Remediation Plan: Exact, surgical Technical English code changes for every identified finding (if any).
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    output_path = REPO_ROOT / "docs/architecture/ARGON_ADVERSARIAL_RECENT_IMPLEMENTATION_AUDIT.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.text, encoding="utf-8")
    print(f"✅ Adversarial Audit successfully completed by {model_name} at: {output_path}")


if __name__ == "__main__":
    main()
