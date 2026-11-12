"""Consult gemini-4-argon: Adversarial Red Team Attack on Universal Solution for T7, T8, T9 and Global Enterprises."""

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

PROMPT = """You are 'gemini-4-argon', operating as the Chief Adversarial Red Team Leader, Head of Model Risk Management (SR 11-7), and Senior Fellow of the Open FAIR Institute.

A quantitative engineering team has proposed a 3-part definitive architectural solution to fix complaints across IT Service Management (T7), Strategy & FinOps (T8), and Digital Workplace (T9), aiming to make the engine universally robust for ANY enterprise in the world:

--- BEGIN PROPOSAL UNDER RED TEAM ATTACK ---
PROPOSAL 1: Euler Allocation & Presentation Arithmetic Closure
In `payload_to_ast.py`:
- Remove integer truncation in `PRODUCTIVITY_TOIL` so frequency is not artificially rounded to 1.0.
- Guarantee that `standalone_base_ale = max(round(freq * sle), canonical_ale)` and `euler_credit = standalone_base_ale - canonical_ale`.
- This ensures that on every risk card:
    Standalone ALE - Euler Credit = Net Assigned ALE
  and Euler Credit is never negative (so the printed table never exhibits 9,006 € - 0 € = 10,588 €).

PROPOSAL 2: Heatmap Strict Alignment to Per-Event Loss Magnitude (SLE)
In `ast_table_builders.py`:
- Strip the annual P90 variable from the Heatmap X-axis.
- Base the X-axis strictly on `sle_candidate` (the Single Loss Expectancy per event), as defined by standard Open FAIR matrices (LM 1: <13k, LM 2: 13k-52k, LM 3: 52k-208k, LM 4: 208k-832k, LM 5: >832k).
- If a risk has an SLE of 4,300 €, it is plotted strictly in LM 1, matching the card.

PROPOSAL 3: Universal Two-Tier Valuation: Deterministic OPEX Friction vs Stochastic Contingency Risk
In the core engine and parameter packs:
- Recognize that FinOps (T8) and Workplace (T9) are not "datacenter downtime" towers.
- Instead of forcing them through a downtime stoppage calculator (e.g. 6 hours of downtime), model them by separating:
  Tier A: Deterministic Baseline Operational Waste (Contractual duplication, unoptimized cloud sprawl, recurring manual provisioning hours).
  Tier B: Stochastic Tail Risk (Vendor audit penalties, uncontained patching crisis, catastrophic contract dispute).
- Synthesize this dynamically from the enterprise's annual revenue, IT budget, and workforce size (e.g. FTE hours * internal labor rate).
--- END PROPOSAL UNDER ATTACK ---

YOUR MISSION (RUTHLESS ADVERSARIAL DISSECTION):
Stress-test, attack, and expose every mathematical, actuarial, regulatory, and scalability flaw in this proposal.

Specifically scrutinize:
1. Euler Allocation & Superadditivity (Proposal 1):
   - Under Euler allocation in a copula with non-linear dependencies (e.g. systemic contagion, right-tail clustering), can a sub-portfolio's marginal risk contribution EVER exceed its standalone risk (Euler superadditivity / penalty)?
   - If that happens, does clamping `standalone_base_ale = max(..., canonical_ale)` commit fraud by hiding contagion penalty? How should an SR 11-7 compliant platform display systemic penalty vs diversification credit?
2. Heatmap X-Axis: Per-Event SLE vs Value-at-Risk (Proposal 2):
   - In Open FAIR, the matrix is TEF vs LM. But if a ransomware or outage scenario has a median SLE of 10,000 € (contained quickly 90% of the time) but a 5,000,000 € catastrophic tail (10% of the time when containment fails), does putting it in LM 1 create Board-level liability for concealing catastrophic risk?
   - What is the definitive, regulator-approved standard for matrix plotting of fat-tailed distributions?
3. Blending Deterministic OPEX with Stochastic ALE (Proposal 3):
   - In corporate finance and actuarial science, can you sum guaranteed annual cash outflows (OPEX bleed) and probabilistic loss expectations (ALE) into a single "Total Risk" headline figure?
   - What will a CFO or external Big-4 auditor say if a report claims a "Total Annual Risk of 1,200,000 €" when 450,000 € is actually already an OPEX line item in the P&L?
   - How should an infallible enterprise engine structure its financial reporting so that the CFO and Chief Risk Officer are both 100% satisfied?
4. The Definitive Global Standard:
   - Provide the exact mathematical, architectural, and presentation blueprint that works for ANY company on Earth (Fortune 500 bank, mid-market industrial, public sector hospital).

Respond in 100% Technical English with relentless rigor and zero polite fluff.
"""


def main() -> None:
    print(f"Submitting Universal Red Team Review to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "RED_TEAM_UNIVERSAL_OPEX_AND_EULER_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nUniversal Red Team Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:3500] + ("\n... [TRUNCATED]" if len(report) > 3500 else ""))


if __name__ == "__main__":
    main()
