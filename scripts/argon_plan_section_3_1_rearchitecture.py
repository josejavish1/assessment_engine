#!/usr/bin/env python3
"""Argon Strategic Planner: Master Action Plan for Section 3.1 Architecture (10.0/10.0 Tier-1)."""

import json
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

PROMPT_PLANNING = """You are 'gemini-4-argon', the Principal Staff Enterprise Architect and AI Engineering Lead.

CONTEXT:
We have audited Section 3.1 of our IT Assessment generator across 10 towers and found it fails (4.70/10) due to generic boilerplate, copy-paste contamination (e.g., Compute text in Storage/FinOps), and lack of domain-specific business impact (e.g., truck queues, CapEx).
The goal is to elevate Section 3.1 to a certified 10.0/10.0, Tier-1 McKinsey/Gartner quality level.

NON-NEGOTIABLE LAWS:
1. LANGUAGE DECOUPLING LAW: 100% Technical English in ALL Python code (identifiers, comments, regex, literals). ZERO Spanish in `.py` files. All localized strings must reside in `engine_config/locales.json`.
2. ZERO HARDCODING & UNIVERSAL TENANT SCALABILITY: Must work for ANY enterprise worldwide ($20M to $500B), ANY vertical (banking, manufacturing, etc.), in ANY target locale. No magic strings or hardcoded client context (like 'Molins', 'NetApp', 'Zabbix') in the Python code or the catalog schema. The engine must extract reality dynamically from the tenant's payload or a localized catalog.
3. ALGORITHMIC INTEGRITY: No unhandled exceptions, zero-division, or list index errors.
4. MAXIMUM VALUE: Every tower must have a bespoke macroscopic synthesis and exactly 3 transversal structural patterns derived from that specific domain's realities, without cannibalizing the 5 granular pillars of Section 3.2.

YOUR MANDATE:
Generate a rigorous, multi-phase Execution Plan to implement this transformation safely and flawlessly.
The plan must detail:
- Phase 1: Data Architecture & Catalogs (How do we model the localized strings and dynamic domain properties in JSON without hardcoding the client?).
- Phase 2: Compiler Engine Refactoring (How do we modify `payload_to_ast.py` and `in_memory_asis_compiler.py` safely, maintaining 100% Technical English and zero hardcoding?).
- Phase 3: Dynamic Context Extraction (How do we extract the 3 transversal patterns from the tenant's payload dynamically, or how do we map them universally via ontology?).
- Phase 4: Quality Assurance & Invariants (What tests must be added or updated?).

Deliver the plan in professional, authoritative English Markdown. Focus on software engineering architecture, not just text replacement.
"""

def main() -> None:
    print("Initiating Section 3.1 Master Execution Plan with gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT_PLANNING,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_PLAN_SECTION_3_1_REARCHITECTURE.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("=" * 80)
    print("ARGON MASTER EXECUTION PLAN:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Full plan written to {out_file}")

if __name__ == "__main__":
    main()
