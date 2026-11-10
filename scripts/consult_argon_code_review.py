"""Consult gemini-4-argon: Forensic adversarial code review of newly implemented actuarial lineage & reproducibility modules."""

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

# Read the newly implemented/modified code
file_paths = [
    REPO_ROOT / "src/assessment_engine/domain/taxonomy/archetype_registry.py",
    REPO_ROOT / "src/assessment_engine/domain/models/parameter_lineage.py",
    REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py",
    REPO_ROOT / "src/assessment_engine/application/tools/actuarial_ledger_generator.py",
    REPO_ROOT / "scripts/fit_actuarial_priors.py",
]

code_extracts = []
for p in file_paths:
    code_extracts.append(f"### FILE: {p.relative_to(REPO_ROOT)}\n```python\n{p.read_text(encoding='utf-8')}\n```\n")

FULL_CODE_PAYLOAD = "\n".join(code_extracts)

REVIEW_PROMPT = f"""You are 'gemini-4-argon', Supreme Enterprise Architect, Chief Actuarial Examiner, Fellow of the Open FAIR Institute, and Master of Zero-Defect Systems Engineering.

We have just completed the implementation of Phase 1, Phase 2, Phase 3, and Phase 4 of the Actuarial Lineage, Parameter Traceability, and Deterministic Portfolio Reproduction specification.

Here is the EXACT source code of all modified and newly created modules:

{FULL_CODE_PAYLOAD}

YOUR REVIEW MANDATE:
Perform an exhaustive, adversarial, line-by-line forensic code review.
Specifically search for and identify:
1. Hidden Bugs, Edge Cases, or Unhandled Failure Modes:
   - Zero divisions, array indexing out of bounds, floating point precision limits.
   - Null pointer / NoneType dereferences.
   - Pydantic schema validation failures under unexpected input variations.
2. Anti-patterns and Hardcoding:
   - Any remaining magic numbers or hardcoded assumptions that break for arbitrary companies.
   - Does this code work seamlessly for ANY enterprise in the world, from a 5-person SMB to a Fortune 10 global conglomerate, in ANY industry vertical, with ANY currency, and in ANY language?
3. Language Decoupling Mandate:
   - Verify that 100% of the code, comments, docstrings, variable names, exception messages, and log strings are in Technical English.
   - Flag ANY occurrence of Spanish or non-English text in production code.
4. Mathematical & Actuarial Rigor:
   - Verify the exactness of `_cvar` (Rockafellar-Uryasev sorted tail formula).
   - Verify the independence of Poisson event count sampling from copula uniform marginals.
   - Verify the deterministic replay parity assertion in `replay_portfolio_simulation()`.
5. Actionable Remediation Verdict:
   - For every finding, provide exact line references, explain why it is a risk, and provide the exact replacement code.

Respond in 100% Technical English with supreme precision, unflinching rigor, and zero sycophancy.
"""


def main() -> None:
    print(f"Submitting Code Review Request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=REVIEW_PROMPT,
    )
    ruling = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_ADVERSARIAL_CODE_REVIEW_RULING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(ruling, encoding="utf-8")

    print(f"\nReview written to: {out_file}\n")
    print("=" * 80)
    print(ruling[:2500] + ("\n... [TRUNCATED]" if len(ruling) > 2500 else ""))


if __name__ == "__main__":
    main()
