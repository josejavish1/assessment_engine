"""Consult gemini-4-argon: Adversarial Codebase Audit for Hardcoding, Anti-patterns, and Bugs."""

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

# Read the newly modified and added files
finding_resolver_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial/finding_archetype_resolver.py").read_text(encoding="utf-8")
input_resolver_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial/input_resolver.py").read_text(encoding="utf-8")
euler_allocator_code = (REPO_ROOT / "src/assessment_engine/domain/actuarial/euler_allocator.py").read_text(encoding="utf-8")
copula_engine_code = (REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py").read_text(encoding="utf-8")
payload_to_ast_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")
in_mem_compiler_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py").read_text(encoding="utf-8")
regenerate_script_code = (REPO_ROOT / "scripts/regenerate_molins_pure_from_raw_inputs.py").read_text(encoding="utf-8")

PROMPT = f"""You are 'gemini-4-argon', operating as the Chief Principal Auditor, Strict Static Analysis Fellow, and Head of Model Governance (SR 11-7 / Basel III / Solvency II).

The user has caught an unacceptable regression: in `scripts/regenerate_molins_pure_from_raw_inputs.py`, the AI inserted hardcoded numbers (`4800.0`, `12500.0`, `6500.0`) and a Spanish keyword (`"desmantelamiento"`) as a manual patch!

THE PRIME DIRECTIVE:
We refuse all patches, all hardcoded magic numbers, all client-specific branching, and all non-English tokens in `src/`.
The platform MUST function universally and dynamically for ANY enterprise on Earth:
- A high-velocity Tier-1 global investment bank (JPMorgan Chase / Starling Bank, USD / GBP, CMMI 4.8, 0% deskless).
- A heavy industrial manufacturer (Molins / Cemex, EUR, CMMI 1.9, 65% deskless).
- A private healthcare hospital system in Brazil (Rede D'Or, BRL, CMMI 2.2, clinical triage).
- A critical infrastructure utility in Germany (E.ON / EnBW, EUR, SCADA grid).
- A public cloud SaaS company in Japan (SoftBank / Mercari, JPY, cloud-native).
- In any language (en, es, pt, de, it, fr, ja), any currency, any maturity.
- 100% Technical English in `src/`. ZERO Spanish words in code/logic.

--- ATTACHED CODE TO AUDIT ---

File 1: `finding_archetype_resolver.py`
```python
{finding_resolver_code}
```

File 2: `input_resolver.py` (Selected excerpts around RTO and replacement costs):
```python
{input_resolver_code[10000:20000]}
```

File 3: `euler_allocator.py` (`allocate_findings_within_domain` lines 270-390):
```python
{euler_allocator_code[8000:15000]}
```

File 4: `payload_to_ast.py` (Lines 3840-4220):
```python
{payload_to_ast_code[135000:152000]}
```

File 5: `in_memory_asis_compiler.py` (Lines 580-750):
```python
{in_mem_compiler_code[18000:26000]}
```

File 6: `scripts/regenerate_molins_pure_from_raw_inputs.py` (Lines 150-250):
```python
{regenerate_script_code[5000:11000]}
```

--- YOUR MANDATORY ADVERSARIAL INSPECTION ---

1. CHEAT & HARDCODING EXPOSURE:
- Expose every single hardcoded number (e.g. 4800.0, 12500.0, 6500.0, 65.0, 50000.0, 30000.0, etc.) across ALL attached files.
- Expose every client-specific condition or non-English string found in Python code.
- Explain why these hardcoded values break for a bank in London or a hospital in Tokyo.

2. MATHEMATICAL & ALGORITHMIC BUGS:
- Identify any hidden mathematical bugs, division-by-zero risks, scale inconsistencies, or unit mismatches.
- Audit `allocate_findings_within_domain`: is the Hare-Niemeyer / Euler allocation mathematically sound, continuous, and monotone?
- Audit `FindingLossPhysics` and `PolymorphicFindingClassifier`: are there edge cases where classification fails or returns an inappropriate physics model?

3. ARCHITECTURAL PURITY & SEPARATION OF CONCERNS:
- Does `payload_to_ast.py` still perform any unauthorized arithmetic, or is it truly a pure serializer?
- Does `in_memory_asis_compiler.py` violate presentation isolation?
- How should parameters (like non-downtime OpEx waste or engineering toil) be derived dynamically from tenant financial telemetry (`annual_revenue`, `annual_it_opex`, `hourly_wage`, `headcount`) instead of arbitrary hardcoded numbers?

4. THE DEFINITIVE UNIVERSAL SPECIFICATION & CODE FIXES:
- Provide the exact mathematical formulas to compute OpEx waste and engineering toil dynamically from tenant telemetry.
- Provide production-ready, clean, 100% Technical English code replacements for all identified bugs and hardcoding.

Respond with brutal, unflinching technical rigor. Zero flattery, zero polite filler.
"""


def main() -> None:
    print(f"Submitting Adversarial Codebase Audit to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_ADVERSARIAL_CODE_AUDIT_ZERO_HARDCODING.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nAdversarial Codebase Audit written to: {out_file}\n")
    print("=" * 80)
    print(report[:4000] + ("\n... [TRUNCATED]" if len(report) > 4000 else ""))


if __name__ == "__main__":
    main()
