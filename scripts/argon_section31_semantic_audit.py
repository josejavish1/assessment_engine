#!/usr/bin/env python3
"""Execute adversarial audit with gemini-4-argon across newly programmed Section 3.1 semantic firewall code."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_SECTION31_ADVERSARIAL_AUDIT.md"

MODELS_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/ontology/models.py"
).read_text(encoding="utf-8")
GATEKEEPER_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/validation/semantic_gatekeeper.py"
).read_text(encoding="utf-8")
LOADER_CODE = (
    REPO_ROOT / "src/assessment_engine/infrastructure/ontology/taxonomy_loader.py"
).read_text(encoding="utf-8")
COMPILER_CODE = (
    REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"
).read_text(encoding="utf-8")[160:3200]
TEST_LOADER = (
    REPO_ROOT / "tests/unit/test_taxonomy_loader.py"
).read_text(encoding="utf-8")
TEST_GATEKEEPER = (
    REPO_ROOT / "tests/unit/test_semantic_gatekeeper.py"
).read_text(encoding="utf-8")
TEST_ISOLATION = (
    REPO_ROOT / "tests/integration/test_maturity_matrix_isolation.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

Perform an UNCOMPROMISING, BRUTALLY ADVERSARIAL AUDIT of the newly engineered Section 3.1 Ontological Semantic Gatekeeper and In-Memory Maturity Matrix Compiler subsystem.

THE USER'S MANDATES FOR THIS AUDIT:
1. LANGUAGE DECOUPLING LAW:
   - All code, variable names, function signatures, docstrings, comments, exceptions, logs, and tests MUST be 100% Technical English.
   - ZERO SPANISH WORDS in the code! Spanish is strictly reserved for the human user conversation in chat and client delivery templates (via locales.json). Check every identifier, comment, and log string.
2. ZERO HARDCODED NUMBERS & VERTICAL/TENANT AGNOSTICISM:
   - The engine must work seamlessly for ANY company in the world (from a $20M mid-market firm to a $500B Fortune 10 global conglomerate).
   - The engine must work for ANY vertical (Banking, Healthcare, Retail, Technology, Heavy Manufacturing, Public Sector).
   - The topology must support any number of domains/towers (not hardcoded to T1..T10; support D1..D8, custom domain slugs, etc.) and any N-pillar topology with arbitrary valid weights.
3. ARCHITECTURAL PURITY & ROBUSTNESS:
   - Verify Clean Architecture / Hexagonal layer boundaries (Domain layer has zero outward imports).
   - Identify bugs, edge cases, hardcoded mappings (e.g. domain_category_mapping with hardcoded T1..T10), or anti-patterns.

CODE ARTIFACTS UNDER AUDIT:

--- ARTIFACT 1: src/assessment_engine/domain/ontology/models.py ---
{MODELS_CODE}

--- ARTIFACT 2: src/assessment_engine/domain/validation/semantic_gatekeeper.py ---
{GATEKEEPER_CODE}

--- ARTIFACT 3: src/assessment_engine/infrastructure/ontology/taxonomy_loader.py ---
{LOADER_CODE}

--- ARTIFACT 4: Excerpt of derive_in_memory_maturity_matrix in in_memory_asis_compiler.py ---
{COMPILER_CODE}

--- ARTIFACT 5: tests/unit/test_taxonomy_loader.py ---
{TEST_LOADER}

--- ARTIFACT 6: tests/unit/test_semantic_gatekeeper.py ---
{TEST_GATEKEEPER}

--- ARTIFACT 7: tests/integration/test_maturity_matrix_isolation.py ---
{TEST_ISOLATION}

YOUR TASK:
Provide an exhaustive, brutally honest audit report:
1. Executive Verdict (PASS / REVISE / FAIL) with numerical score (0.0 to 10.0).
2. Forensic Inventory of Defects:
   - Language Purity violations (List exact line numbers and Spanish words if any, including fallback string templates in Python).
   - Hardcoding & Tenant/Topology Bias (e.g. domain_category_mapping hardcoded to T1..T10).
   - Architectural & Mathematical edge cases or bugs.
3. Complete Production-Grade Remediation Code for all affected artifacts.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing Section 3.1 adversarial audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Audit report saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON SECTION 3.1 AUDIT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
