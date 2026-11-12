"""Consult gemini-4-argon: Deep Root-Cause Forensic Audit of the 4 Broken Layers across the Platform."""

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

# Read key code snippets to provide exact grounded context
input_resolver_py = (REPO_ROOT / "src/assessment_engine/domain/actuarial/input_resolver.py").read_text(encoding="utf-8")
copula_engine_py = (REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py").read_text(encoding="utf-8")
euler_allocator_py = (REPO_ROOT / "src/assessment_engine/domain/actuarial/euler_allocator.py").read_text(encoding="utf-8")
payload_to_ast_py = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")
in_mem_compiler_py = (REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py").read_text(encoding="utf-8")

PROMPT = f"""You are 'gemini-4-argon', operating as the Chief Principal Software Architect, Chief Compilers Engineer, and Head of Model Risk Management (SR 11-7 / Basel III / Solvency II).

The user and leadership have discovered that the risk quantification deliverables in our platform are structurally, mathematically, and epistemologically compromised. 
A deep forensic audit of 61 generated risk cards across 10 official deliverable documents revealed:
- 19 of 61 risks (31%) contain massive artificial "plug numbers" (-30,000 € to -102,000 €) masked as "Ajuste estocástico de dispersión".
- 17 of 61 risks (28%) contain robotic questionnaire boilerplate text ("Carencia de controles operativos formalizados y falta de supervisión continua...") instead of authentic client evidence.
- 12 of 61 risks (20%) have excessive, unconstrained Euler diversification discounts of 60% to 79%, artificially erasing 3/4 of severe risks (e.g., slashing a 293k € CentOS-5 obsolescence risk down to 67k €).
- 6 risks model software development practices (lack of Terraform / Kubernetes CSI) or idle VM decommissioning as catastrophic physical factory blackouts (14-hour plant stoppages costing 143k €).

CRITICAL DIRECTIVE:
Do NOT design a fix for Molins. Molins is only one client test case.
Your solution MUST work universally for 100% of enterprises on Earth:
- A high-velocity UK digital bank (Starling Bank, GBP £, CMMI 4.5, 0% deskless).
- A heavy process manufacturing multinational (Molins, EUR €, CMMI 1.9, 65% deskless).
- A healthcare/hospital network in Brazil (Rede D'Or, BRL R$, CMMI 2.2, clinical triage).
- A critical infrastructure power utility in the US (USD $, SCADA grid, NERC-CIP).
- Any currency, any language (en, es, pt, de, it, fr, ja), any maturity level.
- 100% Technical English in `src/`.

--- ATTACHED CODE SNIPPETS ---
Excerpt 1: `input_resolver.py` (Finding Input Resolution & Archetypes):
```python
{input_resolver_py[12000:18000]}
```

Excerpt 2: `payload_to_ast.py` (The Plug Number & Card Calculation Lines 4070-4200):
```python
{payload_to_ast_py[140000:147000]}
```

Excerpt 3: `euler_allocator.py` (Euler Portfolio Allocation & Scaling):
```python
{euler_allocator_py[4000:10000]}
```

Excerpt 4: `in_memory_asis_compiler.py` (Maturity & Risks Compilation):
```python
{in_mem_compiler_py[18000:26000]}
```

--- YOUR MANDATORY ANALYSIS (FOUR ROTTON LAYERS):

LAYER 1: Semantic Archetype Blindness (Tower-level vs Finding-level Polymorphism)
- Identify the exact code in `input_resolver.py`, `regenerate_molins_pure_from_raw_inputs.py`, and `payload_to_ast.py` where loss archetype is forced at the Tower level rather than dynamically dispatched per finding.
- Why did VM decommissioning in Compute (T2) get treated as an Availability Outage?
- How must a finding's archetype be polymorphically determined (e.g. from causal verbs, asset tag, or ontology) for ANY company on Earth?

LAYER 2: Upstream-Downstream Actuarial Split-Brain (The Plug Number Fraud)
- Trace the exact line of code where `stochastic_tail_adj = round(reconciled_sle - (primary_downtime_loss + repl_cost_num + sec_weighted_loss))` was born.
- Why is the presentation layer (`payload_to_ast.py`) computing downtime math on its own instead of reading an immutable additive vector from the domain layer?
- How must `BayesianFairCopulaEngine` or `ActuarialInputVector` emit an exact, closed-form additive breakdown:
    `SLE_mean = E[Downtime] + E[Direct_Replacement] + E[Secondary_Loss]`
  so that the presentation layer is strictly a read-only serializer with 0 arithmetic fabrication?

LAYER 3: Unconstrained Euler Diversification (The 78% Risk Eraser)
- Trace why the Euler allocator in `euler_allocator.py` slashes standalone risks by 60% to 79%.
- In actuarial science (Basel III, Solvency II, Open FAIR), what are the legal and statistical limits on diversification benefits?
- How should sub-additive diversification be bounded (e.g. max credit 15% - 25% under normal conditions, or 0% for deterministic OpEx) so that severe risks are never artificially anesthetized?

LAYER 4: Epistemic Hallucination & Robotic Boilerplate
- Trace why 17 risks fell back to `"Carencia de controles operativos formalizados..."`.
- How should the evidence ingestor and epistemic router handle silent or unassessed pillars?
- What is the institutional way to represent "Low Evidence" without fabricating a risk card with fake numbers?

LAYER 5: THE UNIFIED INSTITUTIONAL RE-ARCHITECTURE
- Provide the exact, production-ready Technical English architecture, data contracts, and code diffs to permanently resolve all 4 layers.

Respond in 100% Technical English with supreme rigor and zero polite fluff.
"""


def main() -> None:
    print(f"Submitting Deep Root-Cause Audit to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_DEEP_ROOT_CAUSE_4_LAYERS_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nDeep Root-Cause Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500] + ("\n... [TRUNCATED]" if len(report) > 3500 else ""))


if __name__ == "__main__":
    main()
