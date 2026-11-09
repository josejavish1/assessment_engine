#!/usr/bin/env python3
"""Execute adversarial audit of Phase 4 Closed-World Grounding Firewall via gemini-4-argon."""

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

OUTPUT_FILE = REPO_ROOT / "docs/audits/ARGON_PHASE4_GROUNDING_FIREWALL_AUDIT.md"

FIREWALL_CODE = (
    REPO_ROOT / "src/assessment_engine/domain/services/closed_world_grounding_firewall.py"
).read_text(encoding="utf-8")

SCOPER_ADDITIONS = (
    REPO_ROOT / "src/assessment_engine/domain/prompts/ontological_prompt_scoper.py"
).read_text(encoding="utf-8")[-2500:]

PROMPT_YAML_1 = (
    REPO_ROOT / "src/assessment_engine/domain/prompts/registry/annex_executive_synthesizer.yaml"
).read_text(encoding="utf-8")[:1800]

PROMPT_YAML_2 = (
    REPO_ROOT / "src/assessment_engine/domain/prompts/registry/blueprint_pilar_architect_prompt.yaml"
).read_text(encoding="utf-8")[:2500]

TEST_FIREWALL = (
    REPO_ROOT / "tests/unit/test_closed_world_grounding_firewall.py"
).read_text(encoding="utf-8")

TEST_SCOPER = (
    REPO_ROOT / "tests/unit/test_closed_world_grounding_scoper.py"
).read_text(encoding="utf-8")

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

Perform an UNCOMPROMISING, BRUTALLY ADVERSARIAL MASTER AUDIT of the PHASE 4 implementation:
1. `closed_world_grounding_firewall.py` (Domain service enforcing empirical closed-world grounding, zero ungrounded tools/artifacts, and domain-isolated executive summaries).
2. `ontological_prompt_scoper.py` additions (`build_closed_world_grounding_directive`, `build_executive_summary_scoping_directive`, and literal questionnaire statement injection).
3. Prompt blueprints (`annex_executive_synthesizer.yaml`, `blueprint_pilar_architect_prompt.yaml`).
4. Accompanying test suites (`test_closed_world_grounding_firewall.py`, `test_closed_world_grounding_scoper.py`).

THE USER'S MANDATES FOR THIS AUDIT:
1. LANGUAGE DECOUPLING LAW:
   - All code, variable names, function signatures, docstrings, comments, exceptions, logs, and tests MUST be 100% Technical English.
   - ZERO SPANISH WORDS in Python source files! Multilingual patterns are decoupled into locales.json or injected via LocalizationPort.
2. ZERO HARDCODED NUMBERS & VERTICAL/TENANT AGNOSTICISM:
   - Must work for any enterprise ($20M to $500B+), any vertical, any language.
   - Closed-world verification dynamically checks against the client's empirical evidence corpus.
3. ARCHITECTURAL PURITY & CLEAN ARCHITECTURE:
   - Domain layer must be pure with ZERO outward imports from infrastructure or adapters.
   - Clean handling of edge cases, regex boundaries, punctuation preservation, and sentence parsing.

ARTIFACTS UNDER AUDIT:

--- ARTIFACT 1: closed_world_grounding_firewall.py ---
{FIREWALL_CODE}

--- ARTIFACT 2: ontological_prompt_scoper.py (Grounding & Scoping Directives) ---
{SCOPER_ADDITIONS}

--- ARTIFACT 3: Prompt YAMLs ---
{PROMPT_YAML_1}
...
{PROMPT_YAML_2}

--- ARTIFACT 4: tests/unit/test_closed_world_grounding_firewall.py ---
{TEST_FIREWALL}

--- ARTIFACT 5: tests/unit/test_closed_world_grounding_scoper.py ---
{TEST_SCOPER}

YOUR TASK:
Provide an exhaustive, brutally honest audit report:
1. Executive Verdict (PASS / REVISE / FAIL) with numerical score (0.0 to 10.0).
2. Forensic Verification of:
   - Language Purity.
   - Clean Architecture adherence (no outward layer imports).
   - Epistemic Grounding effectiveness against hallucinated instruments (clamp meters, paper forms).
   - Domain headline isolation in Executive Summaries.
3. Final Gatekeeper Sign-Off.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Executing Phase 4 Audit via gemini-4-argon ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("---\nstatus: Verified\nowner: docs-governance\nsource_of_truth:\n- docs/README.md\nlast_verified_against: 2026-11-07\napplies_to:\n- gemini\n- architecture\ndoc_type: operational\ndiataxis: reference\nverification_mode: editorial\n---\n")
        f.write(response.text)

    print(f"Phase 4 audit report saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON PHASE 4 AUDIT SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
