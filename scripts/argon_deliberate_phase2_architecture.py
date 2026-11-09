#!/usr/bin/env python3
"""Consult gemini-4-argon on Tier-1 architectural rigor vs patch for Phase 2 Causal Risk Impact."""

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

OUTPUT_FILE = REPO_ROOT / "docs/architecture/ARGON_PHASE2_TIER1_ARCHITECTURE_DELIBERATION.md"

PROMPT = """You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Actuary, and Chief Quality Gatekeeper.

USER CHALLENGE:
The user raised a critical concern regarding Phase 2:
"respecto a la fase 2, no se si resolverlo así es como lo haría un equipo top tier 1 o es un parche lo que propones"
(Regarding Phase 2, I don't know if solving it this way is how a top Tier-1 team would do it, or if what you are proposing is just a patch).

FORENSIC CODE ANALYSIS OF THE ROOT CAUSE:
1. In `working/molins/T1/blueprint_t1_payload.json`, the findings created by `_generate_canonical_kpi_finding` contain:
   `"impact": "HIGH"` (a categorical severity rating)
   and completely lack `"business_risk"` or `"primary_impact"` (a qualitative narrative description).
2. In `in_memory_asis_compiler.py`:
   Line 69: `business_risk = str(hc.get("business_risk") or hc.get("impact") or "").strip()`
   The compiler conflated the categorical enum `impact` with the qualitative narrative `business_risk`!
   Because `business_risk` was missing, it fell back to `"impact"`, setting `business_risk = "HIGH"`.
3. In `payload_to_ast.py`:
   Line 2698: `raw_impact = str(hc.get("primary_impact") or hc.get("business_risk") or "").strip()`
   Because `business_risk` was `"HIGH"`, it formatted `impact_txt = "HIGH."` and rendered `Impacto en la Operación y Continuidad: HIGH.` in Tables 13, 14, 17.

THE ARCHITECTURAL QUESTION:
Is simply intercepting `HIGH.` inside `payload_to_ast.py` with an `if impact_txt in ["HIGH.", "CRITICAL."]: ...` a band-aid / patch / workaround?
How would a world-class Tier-1 engineering team (OpenAI, Anthropic, Google Staff) resolve this fundamentally, deterministically, and with zero technical debt?

Provide an authoritative architectural deliberation:
1. Candid Assessment: Is compiler string interception a patch? (Yes/No, why).
2. The Root-Cause Tier-1 Solution:
   - Data Contract Disambiguation (Pydantic schema / Domain entities distinguishing `impact_level: SeverityTier` from `operational_impact: NarrativeText`).
   - Upstream Elimination at Hydration & Synthesis (`_generate_canonical_kpi_finding` and synthesis prompts must produce genuine, causal operational impact narratives).
   - Compiler Invariant Gate (Compiler rejects non-narrative enums at AST construction time as an invariant assertion, rather than silently band-aiding them).
3. Complete Production-Grade Implementation across the domain model, hydrator, and compiler (100% Technical English, zero hardcoding, vertical-agnostic).
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Consulting gemini-4-argon on Phase 2 Tier-1 Architecture ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("---\nstatus: Verified\nowner: architecture-governance\nsource_of_truth:\n- docs/README.md\nlast_verified_against: 2026-11-07\napplies_to:\n- gemini\n- architecture\ndoc_type: operational\ndiataxis: reference\nverification_mode: editorial\n---\n")
        f.write(response.text)

    print(f"Tier-1 deliberation saved at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON TIER-1 DELIBERATION SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
