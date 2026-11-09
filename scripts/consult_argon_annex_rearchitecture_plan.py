#!/usr/bin/env python3
"""Consult gemini-4-argon to architect a multi-phase remediation plan for Annex AST compilation."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Chief Cybersecurity Auditor, and Supreme Code Quality Arbiter for the Assessment Engine.

CRITICAL USER MANDATE & ALERT:
We must stop, think, and meticulously architect a multi-phase master plan before writing any more code. The goal is Tier-1 global quality (matching top-tier consulting firms like McKinsey or BCG) for ANY company in the world (from a $20M SMB to a $500B global multinational), across ANY vertical, and in ANY language. 
The Python codebase must be 100% Technical English without a single word of Spanish. No hardcoding is permitted.

CONTEXT:
We just compiled the Annex 5 (Resilience & Continuity) for a synthetic benchmark client: Starling Bank (a UK Cloud-Native FinTech running 100% on AWS).
The resulting DOCX revealed catastrophic hardcoding leaks, semantic inversions, and legacy anti-patterns inside the AST compilation pipeline (`src/assessment_engine/adapters/compilers/ast_appendices_builder.py`, `payload_to_ast.py`, and `engine_config/locales.json`).

SPECIFIC FAILURES FOUND IN THE ANNEX 5 DOCX:
1. Cross-Vertical Hallucination: The Executive Summary explicitly stated the bank uses "industrial networks, plant control systems, and operational technology (OT)". This string is hardcoded in `locales.json` under `operational_mission`.
2. Hardcoded Scenario Leaks: The Dashboard text claimed: "a 500-meter proximity between datacenters sharing electrical feeds turns localized power cuts into total plant halts". This is a residual string from a legacy cement plant client, hardcoded in the AST builder.
3. Semantic Inversion in Risk Cards: The Risk Cards extracted `target_state` instead of `finding` or `business_risk`. As a result, strengths like "[RVS03] Standardized procedures and automated controls active" were printed as critical risks with associated financial losses.
4. Repetitive/Degenerated KPI Strings: The compiler concatenated the same string 4 times in a single paragraph: "...analyzing key factors such as disaster Recovery Architecture & Failover operational controls (T5.P3.K1), disaster Recovery Architecture & Failover operational controls (T5.P3.K2)...".
5. Unresolved Placeholders: `diag_summary_default` leaked into the Economic Risk Evaluation section.
6. Naive ALE Math: Every single risk card received the exact same flat financial loss (e.g., "£9,656 / year"), ignoring the Bayesian / FAIR distribution curves that should apply severity weights.

YOUR MISSION:
Deliver a comprehensive, zero-bug, zero-hardcoding architectural blueprint and multi-phase execution plan to remediate the Annex AST compilers (`payload_to_ast.py`, `ast_appendices_builder.py`, etc.).

The plan must address:
- PHASE 1: Baseline & Catalog Sanitization (Purging all static industry biases like "OT", "plant", "500-meter" from `locales.json` and AST files).
- PHASE 2: AST Compiler Decoupling & Semantic Fixes (Fixing the Risk Card semantic inversion, eliminating `diag_summary_default`, and ensuring fluent, dynamic KPI string generation).
- PHASE 3: Actuarial Math & Financial Integrity (Ensuring the ALE is properly distributed and formatted in the annex tables based on the actual payload, not flattened).
- PHASE 4: Final Certification (How we will test and verify the output for all 5 benchmark clients).

Constraints:
- Respond in 100% Technical English.
- Detail exactly which files and functions need to be modified.
- Provide clear architectural guidelines to prevent these anti-patterns from ever returning.

Be authoritative, exhaustive, and structure your response as a Master Architecture Document.
"""

def main() -> None:
    print(f"Submitting uncompromising audit request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_UNIVERSAL_ANNEX_REARCHITECTURE_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nArchitecture Plan generated successfully. Report written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3000])

if __name__ == "__main__":
    main()