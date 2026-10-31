#!/usr/bin/env python3
"""Adversarial Audit and Refinement of RFC-026 Plan via gemini-4-argon (100% Technical English)."""

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

PLAN_PATH = REPO_ROOT / "docs" / "architecture" / "RFC_026_AST_COMPILER_CONVERGENCE_PLAN.md"


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    current_plan = PLAN_PATH.read_text(encoding="utf-8")

    prompt = f"""
Role: Principal Systems Architect, Chief Compiler Engineer & Staff Quality Auditor (Google Tier-1 / Anthropic Infrastructure).

OBJECTIVE:
Perform a deep adversarial review and refinement of the architectural blueprint:
"RFC-026: AST Compiler Convergence & Zero-Entropy Document Synthesis".

USER'S NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTIPATTERNS, ZERO DEFECTS:
   - Ensure the architecture is mathematically and structurally flawless before writing a single line of implementation code.
2. ZERO HARDCODING (UNIVERSAL DYNAMIC CONFIGURATION):
   - The platform MUST serve ANY company in the world: from a mid-market manufacturing plant to a Global Fortune 10 bank.
   - Any industry vertical (Banking, Heavy Industry, Healthcare, Aerospace, Energy, SaaS).
   - Any jurisdiction and legal framework (EU, US, Brazil, Japan, Singapore, UK, Saudi Arabia).
   - Zero hardcoded company names ("Molins", "Consultora"), zero fixed currencies ("EUR"), zero fixed countries ("ES").
3. MULTI-LINGUAL DELIVERABLE OUTPUT (ANY HUMAN LANGUAGE):
   - The engine must support generating deliverables in ANY requested language (English, Spanish, German, Japanese, Portuguese, Arabic).
   - The codebase, docstrings, comments, exceptions, logs, and schemas MUST be 100% Technical English.
4. MAXIMUM HUMAN READABILITY & EXECUTIVE VALUE:
   - Eliminate robotic, repetitive, or fragmented text.
   - The compiled document MUST read like an elite McKinsey/Gartner strategic advisory publication: clear narrative arc, Minto Pyramid structure, granular explainability for every single currency unit of financial risk, and 100% verified visual contrast (WCAG 2.1 compliance).

CURRENT RFC-026 PLAN:
```markdown
{current_plan}
```

TASK:
1. Identify any latent flaws, ambiguities, or missing components in the plan.
2. Refine the plan to ensure it guarantees:
   - Complete elimination of Split-Brain #1 (deprecating the binary template mutator completely).
   - Dynamic narrative explainability (linking each FAIR risk row to its business impact, threat frequency, and loss magnitude).
   - Strict locale-independent AST compilation (supporting multi-lingual token dictionaries without hardcoded fallback strings).
   - Clean, elegant class and method signatures.
3. Output the COMPLETE, DEFINITIVE, REFINED RFC-026 ARCHITECTURAL SPECIFICATION in 100% Technical English. Include valid YAML front matter (status: Verified, owner: docs-governance, doc_type: canonical, diataxis: explanation, verification_mode: editorial).
"""

    print(f"Auditing and refining RFC-026 plan with {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    if not response.text:
        print("ERROR: Empty response from model.")
        sys.exit(1)

    PLAN_PATH.write_text(response.text, encoding="utf-8")
    print(f"Refined RFC-026 plan successfully updated at: {PLAN_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
