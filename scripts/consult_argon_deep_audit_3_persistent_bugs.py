"""Consult gemini-4-argon: Deep Root-Cause Forensic Audit of the 3 Persistent Mathematical Bugs."""

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

payload_to_ast_py = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")
in_mem_compiler_py = (REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py").read_text(encoding="utf-8")
euler_allocator_py = (REPO_ROOT / "src/assessment_engine/domain/actuarial/euler_allocator.py").read_text(encoding="utf-8")
input_resolver_py = (REPO_ROOT / "src/assessment_engine/domain/actuarial/input_resolver.py").read_text(encoding="utf-8")

PROMPT = f"""You are 'gemini-4-argon', operating as the Chief Principal Software Architect, Chief Compilers Engineer, and Head of Model Risk Management (SR 11-7 / Basel III / Solvency II).

The user has reviewed the actual generated Word documents and uncovered three persistent, critical mathematical anomalies:

ANOMALY 1: Broken Additive Sums in the Presentation Layer
In 7 risk cards, the printed bullet point literally displays:
- T6 [RVS02]: Indisponibilidad primaria (0,0h a 0 €/h): 0 €
  + Costes directos de reemplazo: +0 €
  + Pérdida secundaria ponderada: +4.576 €
  + Ajuste estocástico: +0 €
  = Pérdida Media por Evento (Mean SLE): 43.433 €!  <-- Arithmetic violation: 0 + 0 + 4576 != 43433!
- T3 [RVS04]: 0 € + 35.000 € + 4.576 € + 0 € = 78.433 €!  <-- 35000 + 4576 != 78433!
- T3 [RVS03]: 0 € + 4.000 € + 3.890 € + 0 € = 25.653 €!   <-- 4000 + 3890 != 25653!
- T8 [RVS03]: 0 € + 0 € + 500 € + 0 € = 11.882 €!        <-- 500 != 11882!
- T10 [RVS02]: 0 € + 0 € + 3.890 € + 0 € = 15.790 €!     <-- 3890 != 15790!
- T2 [RVS07]: 0 € + 0 € + 5.491 € + 0 € = 62.691 €!      <-- 5491 != 62691!

ANOMALY 2: Idle VM Decommissioning (T2-RVS07) Still Assigned 143,266 € / year ALE
Despite our efforts to treat idle/orphaned VMs as FinOps waste:
Table 10 in Annex 2 still displays:
`PÉRDIDA ANUALIZADA (ALE): 143.266 € / año`!
A CFO will immediately reject the notion that forgetting to delete test VMs costs 143,000 € every single year.

ANOMALY 3: The 85% to 90% Euler Slashes (Standalone Hyper-Inflation vs. Euler Laundering)
Look at the numbers printed in the tables:
- T4 [RVS02]: Standalone = 317.272 €/year -> Euler Diversification Credit = -282.121 €/year (-88.9%) -> Net ALE = 35.151 €/year.
- T6 [RVS01]: Standalone = 192.932 €/year -> Euler Diversification Credit = -174.099 €/year (-90.2%) -> Net ALE = 18.833 €/year.
- T3 [RVS06]: Standalone = 101.598 €/year -> Euler Diversification Credit = -89.810 €/year (-88.4%) -> Net ALE = 11.788 €/year.
- T2 [RVS01]: Standalone = 418.840 €/year -> Euler Diversification Credit = -351.214 €/year (-83.9%) -> Net ALE = 67.626 €/year.
A CFO will argue: "Why are you calculating a standalone risk of €418,000 and then applying an 84% magic credit (-€351,000) to bring it down to €67,000? Either your standalone model is hyper-inflated, or your diversification credit is an accounting trick."

--- YOUR MANDATORY INSTRUCTION ---
We refuse all hardcoding, all client-specific branching, and all non-English code in `src/`.
Your solution MUST work universally for 100% of enterprises on Earth:
- A high-velocity UK digital bank (Starling Bank, GBP, CMMI 4.8).
- A heavy industrial manufacturer (Molins / Cemex, EUR, CMMI 1.9).
- A healthcare hospital network in Brazil (Rede D'Or, BRL, CMMI 2.2).
- A critical infrastructure utility in Germany (E.ON, EUR, SCADA).
- Any currency, any language, any maturity.
- 100% Technical English in `src/`.

--- ATTACHED CODE SNIPPETS ---

Excerpt 1: `payload_to_ast.py` lines 3850-3940 and 4130-4220:
```python
{payload_to_ast_py[135000:152000]}
```

Excerpt 2: `in_memory_asis_compiler.py` lines 580-730:
```python
{in_mem_compiler_py[18000:26000]}
```

Excerpt 3: `euler_allocator.py` lines 330-460:
```python
{euler_allocator_py[11000:17000]}
```

Excerpt 4: `input_resolver.py` lines 390-480:
```python
{input_resolver_py[13000:19000]}
```

--- QUESTIONS FOR YOUR MICROSCOPIC ROOT-CAUSE AUDIT:

1. TRACE ANOMALY 1 (BROKEN ADDITIVE SUMS):
- Why did `reconciled_sle` become 43.433 € while `primary_downtime_loss` = 0, `repl_cost_num` = 0, and `sec_weighted_loss` = 4.576 €?
- Trace where `reconciled_sle` was pulled from in `payload_to_ast.py`. Why did it ignore the additive components?
- What is the exact mathematical code fix to enforce:
    `reconciled_sle = primary_downtime_loss + repl_cost_num + sec_weighted_loss`
  so that broken sums ($0 + 0 + 4576 = 43433$) are IMPOSSIBLE?

2. TRACE ANOMALY 2 (143k € IDLE VM DECOMMISSIONING):
- Why did T2-RVS07 retain 143.266 € Net ALE?
- Trace where 143.266 € originated (was it read from `hc.get("ale")` or `fair_ale_score` in `in_memory_asis_compiler.py`? Was `allocate_findings_within_domain` bypassed or fed the legacy payload number?).
- How should FinOps waste be calculated from scratch purely from tenant telemetry so that it produces a defensible, realistic figure (e.g. 3k - 10k €)?

3. TRACE ANOMALY 3 (THE 85%-90% EULER DASHES):
- Why did Standalone ALE reach 317k € - 418k € in the first place?
- Is the formula `standalone_base_ale = round(displayed_mult_freq * reconciled_sle)` blowing up because `displayed_mult_freq` is 4.0 events/year and `reconciled_sle` was 79k € or 104k €?
- In Open FAIR, how should Standalone ALE be properly bounded at the single-finding level, and how should Euler portfolio allocation be constrained to realistic 10% - 25% overlap benefits?

4. THE DEFINITIVE PRODUCTION-READY UNIVERSAL CODE FIXES:
- Provide the exact code diffs for `payload_to_ast.py`, `in_memory_asis_compiler.py`, `euler_allocator.py`, and `input_resolver.py`.
- Ensure 100% Technical English and zero hardcoded magic numbers.

Respond with brutal, mathematical, unflinching rigor.
"""


def main() -> None:
    print(f"Submitting Deep Root-Cause Audit of 3 Persistent Bugs to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_DEEP_AUDIT_3_PERSISTENT_BUGS.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nDeep Root-Cause Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:4000] + ("\n... [TRUNCATED]" if len(report) > 4000 else ""))


if __name__ == "__main__":
    main()
