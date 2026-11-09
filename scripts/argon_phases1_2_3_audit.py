#!/usr/bin/env python3
"""Execute adversarial audit with gemini-4-argon across Phase 1, Phase 2, and Phase 3 implementations."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_PHASES1_2_3_ADVERSARIAL_AUDIT.md"

PAYLOAD_TO_AST_CODE = (
    REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py"
).read_text(encoding="utf-8")

IN_MEMORY_COMPILER_CODE = (
    REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"
).read_text(encoding="utf-8")

HYDRATOR_CODE = (
    REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"
).read_text(encoding="utf-8")

TEST_CH2 = (
    REPO_ROOT / "tests/unit/test_universal_chapter2_bridge.py"
).read_text(encoding="utf-8")

TEST_DISAMBIGUATION = (
    REPO_ROOT / "tests/unit/test_risk_impact_disambiguation.py"
).read_text(encoding="utf-8")

TEST_POLARITY = (
    REPO_ROOT / "tests/unit/test_table6_justification_polarity.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

Perform an UNCOMPROMISING, BRUTALLY ADVERSARIAL AUDIT of the newly engineered Phase 1 (Universal Chapter 2 Bridge), Phase 2 (Tier-1 Risk Impact Disambiguation & Invariant Gate), and Phase 3 (Table 6 Justification Polarity & Orthographic Sanitizer) implementations.

THE USER'S NON-NEGOTIABLE MANDATES FOR THIS AUDIT:
1. LANGUAGE DECOUPLING LAW:
   - All code, variable names, function signatures, docstrings, comments, exceptions, logs, and tests MUST be 100% Technical English.
   - ZERO SPANISH WORDS in the code! Spanish is strictly reserved for user chat conversation and client delivery templates (via locales.json). Check every identifier, comment, literal string, and log.
2. ZERO HARDCODED NUMBERS & VERTICAL/TENANT AGNOSTICISM:
   - The engine must work seamlessly for ANY company in the world (from a $20M mid-market firm to a $500B Fortune 10 global conglomerate).
   - The engine must work for ANY vertical (Banking, Healthcare, Retail, Technology, Heavy Manufacturing, Public Sector).
   - The topology must support any number of domains/towers (not hardcoded to T1..T10; support D1..D8, custom domain slugs, etc.) and any N-pillar topology with arbitrary valid weights.
3. ARCHITECTURAL PURITY & ZERO BUGS:
   - Verify Clean Architecture / Hexagonal layer boundaries.
   - Look for edge cases, subtle off-by-one errors, regex performance traps (ReDoS), unhandled None values, or remaining string patches.

CODE ARTIFACTS UNDER AUDIT:

--- ARTIFACT 1: Excerpt of resolve_domain_introduction in payload_to_ast.py (Phase 1 & Phase 2 Gate) ---
{PAYLOAD_TO_AST_CODE[300:2800]}

--- ARTIFACT 2: Excerpt of in_memory_asis_compiler.py (Phase 2 & Phase 3) ---
{IN_MEMORY_COMPILER_CODE[30:4500]}

--- ARTIFACT 3: Excerpt of tower_payload_hydrator.py (Phase 2 & 3 Hydrator Integration) ---
{HYDRATOR_CODE[150:2400]}

--- ARTIFACT 4: tests/unit/test_universal_chapter2_bridge.py ---
{TEST_CH2}

--- ARTIFACT 5: tests/unit/test_risk_impact_disambiguation.py ---
{TEST_DISAMBIGUATION}

--- ARTIFACT 6: tests/unit/test_table6_justification_polarity.py ---
{TEST_POLARITY}

YOUR TASK:
Provide an exhaustive, brutally honest audit report:
1. Executive Verdict (PASS / REVISE / FAIL) with numerical score (0.0 to 10.0).
2. Forensic Inventory of Defects:
   - Language Purity violations (List exact line numbers and Spanish words if any).
   - Hardcoding & Tenant/Topology Bias.
   - Architectural & Mathematical edge cases or bugs.
3. Complete Production-Grade Remediation Code for all affected artifacts (if any).
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing Phase 1, 2, 3 adversarial audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("---\nstatus: Verified\nowner: docs-governance\nsource_of_truth:\n- docs/README.md\nlast_verified_against: 2026-11-07\napplies_to:\n- gemini\n- architecture\ndoc_type: operational\ndiataxis: reference\nverification_mode: editorial\n---\n")
        f.write(response.text)

    print(f"Audit report saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON PHASES 1, 2, 3 AUDIT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
