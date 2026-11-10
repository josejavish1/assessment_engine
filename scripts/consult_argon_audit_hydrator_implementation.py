#!/usr/bin/env python3
"""Argon Strategic Audit: Comprehensive Adversarial Review of Tower Hydrator & Payload Changes.

Consults gemini-4-argon to scrutinize recent changes to tower_payload_hydrator.py,
actuarial_calculator.py, payload_to_ast.py, and domain exceptions for bugs,
hardcoded artifacts, vertical bias, linguistic coupling, and architectural antipatterns.
"""

from __future__ import annotations

import subprocess
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
print(f"Connecting to Reasoning model '{model_name}' for Adversarial Code Review...")

# Get git diff for production source files changed
diff_proc = subprocess.run(
    ["git", "diff", "HEAD", "--", "src/assessment_engine/"],
    cwd=REPO_ROOT,
    capture_output=True,
    text=True,
)
prod_diff = diff_proc.stdout

prompt = f"""You are 'gemini-4-argon', the Principal Staff Systems Architect, Lead Actuarial Engineer, and Compiler Verification Lead (ex-Anthropic/OpenAI core systems scale).

TASK:
Perform a relentless, uncompromising adversarial code audit on our recent production changes in `src/assessment_engine/`.

THE CODE DIFF UNDER AUDIT:
```diff
{prod_diff}
```

KEY MANDATES TO VERIFY:
1. UNIVERSAL MULTI-TENANT GENERALIZATION:
   - Must scale seamlessly from a €20M mid-market logistics operator to a $100B global systemic bank across all 11 GICS sectors.
   - Are there ANY remaining client-specific magic numbers, hardcoded assumptions, or cement-industry relics?
2. ZERO GHOST SCORING & EPISTEMIC SOUNDNESS:
   - Verify that the 2.50 silent fallback is completely eradicated and replaced by deterministic fail-fast validation (`PayloadIntegrityError`).
   - Are there any edge cases where an un-assessed payload could sneak through or cause an unhandled crash instead of a clean domain exception?
3. TOPOLOGICAL & ACTUARIAL ACCURACY:
   - Storage Tower (T4) reclassified to `TIER_1_MISSION_CRITICAL`. Is this consistent across all mapping dictionaries?
   - `calculate_severity_weighted_sle`: Is the math pure, stateless, and scale-invariant? Does it preserve degree-1 homogeneity?
4. CLEAN ARCHITECTURE & SRP:
   - Method decomposition in `TowerPayloadHydrator`: Are `_hydrate_epistemic_ledger_evidence` and `_enforce_ontological_gatekeeping` properly isolated?
   - Clean Architecture layer boundaries: Are there any forbidden upward imports or circular dependencies?
5. LINGUISTIC SOVEREIGNTY (100% TECHNICAL ENGLISH):
   - Zero non-English strings, comments, identifiers, or exceptions in Python code.
   - Are all deliverable client-facing localized texts strictly externalized to `engine_config/locales.json` via `t(...)`?
6. BUGS & NUMERICAL STABILITY:
   - Check for potential `ZeroDivisionError`, `KeyError`, `IndexError`, float rounding drifts, or type coercion pitfalls.

DELIVERABLE:
Provide a structured, ruthless forensic audit report evaluating each area:
- PASSED INVARIANTS: What was executed flawlessly.
- VULNERABILITIES & ANTIPATTERNS DETECTED: Specific line-level critique of any remaining bugs, smells, or biases.
- ACTIONABLE REMEDIATION DIRECTIVES: Exact code instructions for any finding requiring fixes.
- FINAL CERTIFICATION GRADE: A+ (Production Ready) through F (Reject).
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/audits/ARGON_HYDRATOR_IMPLEMENTATION_AUDIT.md"
out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved adversarial review to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:3500] + "\n... [TRUNCATED] ...")
print("=" * 80)
