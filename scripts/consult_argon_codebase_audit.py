"""Consult gemini-4-argon: Exhaustive Adversarial Code Review of Recent Workforce Segmentation & Actuarial Implementation."""

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

# Read the recently written code files
workforce_py = (REPO_ROOT / "src/assessment_engine/domain/actuarial/workforce_segmentation.py").read_text(encoding="utf-8")
ast_builders_py = (REPO_ROOT / "src/assessment_engine/adapters/compilers/ast_table_builders.py").read_text(encoding="utf-8")
payload_to_ast_py = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")
in_mem_compiler_py = (REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py").read_text(encoding="utf-8")
test_wf_py = (REPO_ROOT / "tests/unit/domain/actuarial/test_workforce_segmentation_resolver.py").read_text(encoding="utf-8")

PROMPT = f"""You are 'gemini-4-argon', operating as the Lead Principal Software Architect, Chief Compilers Engineer, and Head of Model Risk Management (SR 11-7).

You have been tasked with conducting an unflinching, adversarial code review of all code newly introduced in the repository.

--- MANDATES FROM THE USER ---
1. ZERO HARDCODING: The engine must work seamlessly for ANY company in the world—from a mid-market manufacturing plant in Brazil to a Fortune 10 global investment bank in London, Tokyo, or New York. No hardcoded company names, assumptions, magic ratios, or bespoke hacks.
2. 100% TECHNICAL ENGLISH CODEBASE: Every line of code, docstring, comment, variable name, exception message, logging statement, and domain logic in `src/` must be 100% Technical English. Spanish is ONLY permitted in localization data (`engine_config/locales.json`) and final client report rendering.
3. MATHEMATICAL & ACTUARIAL PURITY: No false equations, no unhandled divisions by zero, no impossible Euler bridges (e.g. 9,006 - 0 = 10,588), no quantile inversions.
4. ZERO REGRESSION & ZERO ENTROPY: Safe fallbacks, strict typing, and high-performance clean abstractions.

--- CODE FILE 1: src/assessment_engine/domain/actuarial/workforce_segmentation.py ---
```python
{workforce_py}
```

--- CODE FILE 2: tests/unit/domain/actuarial/test_workforce_segmentation_resolver.py ---
```python
{test_wf_py}
```

--- CODE FILE 3: Excerpts from src/assessment_engine/adapters/compilers/ast_table_builders.py (Lines 210-250) ---
```python
{ast_builders_py[6000:9000]}
```

--- CODE FILE 4: Excerpts from src/assessment_engine/adapters/compilers/payload_to_ast.py (Euler Bridge Lines 4100-4220) ---
```python
{payload_to_ast_py[140000:146000]}
```

--- CODE FILE 5: Excerpts from src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py (Line 1380-1440) ---
```python
{in_mem_compiler_py[48000:52000]}
```

YOUR MISSION:
Perform a relentless, microscopic adversarial code audit. Look for:
1. Language Decoupling Violations: Are there Spanish words, regexes matching only Spanish vocabulary, or non-English literals inside `src/assessment_engine/domain/actuarial/workforce_segmentation.py` (e.g., matching "flota", "renovacion", "portatiles", "quioscos" while failing completely for English "fleet", "refresh", "laptops", "kiosks" or Portuguese "computadores")?
2. Hardcoded Assumptions & Magic Numbers: Are there hardcoded constants (e.g. 3.5 years, 45.0 €/h, 0.285 refresh rate, 3.0h) embedded in Python logic rather than parameterized?
3. Mathematical & Algorithmic Bugs: Are there any edge cases (headcount = 0, negative values, division by zero, float precision bugs)?
4. Scalability across Verticals & Sizes: Does this logic break for an enterprise with 500,000 employees or a small firm with 40 employees?
5. Concrete, Actionable Fixes: For every issue found, provide the exact, production-ready Technical English refactoring.

Respond in 100% Technical English with supreme rigor and zero polite filler.
"""


def main() -> None:
    print(f"Submitting Comprehensive Code Audit to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_CODE_AUDIT_WORKFORCE_AND_EULER.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nAudit Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500] + ("\n... [TRUNCATED]" if len(report) > 3500 else ""))


if __name__ == "__main__":
    main()
