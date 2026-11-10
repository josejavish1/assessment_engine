#!/usr/bin/env python3
"""Consult gemini-4-argon on how a top tier-1 team would elegantly eradicate recurring flaws."""

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

AUDIT_PROMPT = """You are 'gemini-4-argon', Principal Enterprise Architect, Supreme Code Quality Arbiter, and Chief Forensic Auditor for the Assessment Engine.

USER'S PROFOUND QUESTION:
"Pero se han detectado fallos varias veces, ¿cómo hacemos para erradicar esos problemas de raíz como lo haría un equipo top tier 1, encontrando la causa exacta y resolviéndolo de la forma más elegante posible?"

THE RECURRING PATTERN OBSERVED:
Across the tower reviews, the user notes that while we fix bugs, certain classes of flaws recur:
1. Cloned / Formulaic Titles & Bullets: In Tower 8, all 5 risk cards had the identical deterministic template: `Unbudgeted licensing liability and cloud infrastructure cost drift in [Pillar]`, and executive bullets P12-P14 repeated the exact same paragraph 3 times with only the pillar name swapped.
2. Conceptual Mismatch of Economic Loss: In Tower 8 (FinOps & Strategy), the report stated that FinOps gaps halt transactional clearing at £140,000/hr, which makes the CTO and CFO laugh because unoptimized cloud spend does not stop clearing payments; it inflates the AWS bill.
3. Why does this happen? Because when running without `--enrich-risks`, the engine relies on hardcoded fallback string interpolations in `build_client_delivery_suite.py` and treats all 10 towers as "transactional availability downtime" systems.

YOUR MISSION:
Explain with uncompromising technical depth and elegance how a Top Tier-1 engineering team (OpenAI Applied, Palantir Foundry, Jane Street, Google DeepMind) would permanently eradicate these root causes:
1. The Mathematical & Domain Decoupling: How Open FAIR loss archetypes must be classified by domain (Transactional Availability, Cloud Capital Inefficiency, Workforce Productivity Toil, Cyber Incident Breach), so FinOps evaluates cloud drift and Core evaluates clearing outage.
2. The Eradication of Cloned Deterministic Strings: How to design the synthesis architecture so that even in offline/fallback mode, deterministic generation uses a diversified, ontology-driven semantic matrix with zero repeated strings, or makes semantic synthesis the mandatory first-class citizen with SHA-256 caching.
3. The Architectural Elegance Guarantee: A concrete, minimal, and mathematically pristine blueprint that solves this forever across any client, vertical, and language.

Constraints:
- Respond in 100% Technical English.
- Provide the exact diagnosis, architectural principles, and the concrete implementation strategy.

Deliver your architectural judgment now.
"""

def main() -> None:
    print(f"Submitting Tier-1 elegance and root-cause eradication request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/architecture/ARGON_TIER1_ROOT_CAUSE_ELEGANCE.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nReport written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3500])

if __name__ == "__main__":
    main()
