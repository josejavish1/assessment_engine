#!/usr/bin/env python3
"""Audit the new BayesianFairCopulaEngine implementation via gemini-4-argon."""

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

OUTPUT_PATH = REPO_ROOT / "docs/audits/audit_bayesian_fair_copula_argon.md"


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    
    engine_file = REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py"
    hydrator_file = REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"
    
    engine_code = engine_file.read_text(encoding="utf-8")
    hydrator_code = hydrator_file.read_text(encoding="utf-8")

    prompt = f"""
Role: Principal Quantitative Risk Architect, Senior Partner at FAIR Institute, and Code Auditor.

TASK:
Perform a complete, hostile, adversarial code review of the newly implemented `BayesianFairCopulaEngine` and its integration in `TowerPayloadHydrator`.
Look for bugs, math errors, antipatterns, or hardcoded assumptions.
The codebase must be 100% Technical English, ready for any global Tier-1 company in any industry. No Spanish in variables, strings, comments, or exceptions!

Here is `bayesian_fair_copula_engine.py`:
```python
{engine_code}
```

Here are excerpts from `tower_payload_hydrator.py` where it is integrated:
```python
{hydrator_code[-3000:]}
```

REQUIREMENTS FOR YOUR AUDIT REPORT:
1. Identify any Spanish words in the codebase (which is strictly forbidden).
2. Identify any hardcoded industry-specific logic (e.g. references to 'Molins', 'cement', specific zones like 'OT_KILN_MILLING' that shouldn't be hardcoded if this engine is universal).
3. Identify mathematical or architectural flaws in the Copula and Euler allocation implementations.
4. Provide the exact corrected code snippets if fixes are required.

Output in Markdown format.
"""

    print("Generating code audit via gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    header = """---
status: Verified
owner: architecture-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-07
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: rigorous
---
"""
    OUTPUT_PATH.write_text(header + response.text, encoding="utf-8")
    print(f"Successfully generated audit report at: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
