#!/usr/bin/env python3
"""Execute adversarial audit via gemini-4-argon across Phase 5 (Hydrator Sanitization & Persistence)

and Phase 6 (Ontological Prompt Scoper & Generative Boundary Directives).
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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_PHASE5_PHASE6_ADVERSARIAL_AUDIT.md"

HYDRATOR_EXCERPT = (
    REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"
).read_text(encoding="utf-8")[130:3000]

SCOPER_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/prompts/ontological_prompt_scoper.py"
).read_text(encoding="utf-8")

TEST_HYDRATOR = (
    REPO_ROOT / "tests/unit/test_tower_payload_hydrator_semantic_quarantine.py"
).read_text(encoding="utf-8")

TEST_SCOPER = (
    REPO_ROOT / "tests/unit/test_ontological_prompt_scoper.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

Perform an UNCOMPROMISING, BRUTALLY ADVERSARIAL AUDIT of the newly engineered Phase 5 (Payload Hydrator Ontological Sanitization & Disk Persistence) and Phase 6 (Ontological Prompt Scoper & Generative Boundary Directives) subsystems.

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
   - Identify bugs, edge cases, hardcoded mappings, or anti-patterns in Phase 5 and Phase 6.

CODE ARTIFACTS UNDER AUDIT:

--- ARTIFACT 1: Excerpt of tower_payload_hydrator.py (Phase 5) ---
{HYDRATOR_EXCERPT}

--- ARTIFACT 2: src/assessment_engine/domain/prompts/ontological_prompt_scoper.py (Phase 6) ---
{SCOPER_CODE}

--- ARTIFACT 3: tests/unit/test_tower_payload_hydrator_semantic_quarantine.py (Phase 5 Tests) ---
{TEST_HYDRATOR}

--- ARTIFACT 4: tests/unit/test_ontological_prompt_scoper.py (Phase 6 Tests) ---
{TEST_SCOPER}

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
    print(f"Executing Phase 5 & 6 adversarial audit via gemini-4-argon ({model})...")

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
    print("GEMINI-4-ARGON PHASE 5 & 6 AUDIT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
