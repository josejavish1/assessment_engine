#!/usr/bin/env python3
"""Consult gemini-4-argon on the exact next steps for Open FAIR actuarial calibration and deliverable regeneration."""

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

OUTPUT_FILE = REPO_ROOT / "docs/architecture/ARGON_NEXT_STEPS_OPEN_FAIR_ROADMAP.md"

PROMPT = """You are gemini-4-argon, acting as the Distinguished Principal Distributed Systems Architect, Chief Actuarial Auditor, and Enterprise Quality Gatekeeper (Google Cloud Fellow / McKinsey Senior Partner / FAIR Institute Fellow).

CONTEXT:
We are developing the enterprise Assessment Engine. In our recent session, we resolved a fundamental actuarial dilemma:
1. In the legacy implementation, `TowerPayloadHydrator` enforced a top-down fixed allocation (`domain_weights` in `financial_telemetry` hardcoding T1=141k, T2=100k, T5=206k, total = 916k €), so changes in technical evidence (e.g. RAM saturation in SimpliVity) did not move the needle of Tower 2's ALE.
2. We introduced `BayesianFairCopulaEngine` to compute bottom-up Open FAIR risk with dynamic CMMI->VULN mapping and sub-additive copula convolution across operational zones.
3. However, in initial runs, uncalibrated parameters (e.g. TEF default=2.0 events/year, arbitrary secondary losses, uncalibrated zone capacity caps) inflated total portfolio ALE to €3,129,772 / year.
4. The user and architectural consensus established the correct Open FAIR decomposition for industrial manufacturing (Molins: ~1,144 M€ turnover, benchmark ~0.08% turnover = ~850k - 920k €/year):
   - Primary Loss (60% -> ~470k €/year): Direct plant stoppage (weighbridge @ 5k €/h, kiln/mills @ 8.4k €/h, SAP ERP @ 13.061 €/h).
   - Secondary Loss (40% -> ~380k €/year): Post-incident emergency support (HPE/NetApp/Fortinet out-of-scope logic recovery), internal engineering overtime, and logistics/public works penalties.
   - Total Defensible Expected ALE: ~850,000 € to ~920,000 € / year (~880k € expected).
   - Catastrophic Outage Risk (VaR 90/99): ~3.1 M€ (worst-case severe multi-day cascade).
   - Cost of Inaction: 3-year loss = 2.64 M€ vs Transformation Plan (Tomo 2) = 1.4 M€ with 19-month payback.

CODEBASE CURRENT STATE:
- `src/assessment_engine/domain/bayesian_fair_copula_engine.py`: Remediated to be currency & industry agnostic, 2-factor loading Student-t copula with spectral floor, exact Aumann-Shapley pathwise allocation.
- `src/assessment_engine/application/services/tower_payload_hydrator.py`: Partially refactored to call `BayesianFairCopulaEngine`, but still contains naive heuristic parameter mapping (TEF=2.0 default, RTO=4.0/2.0, hardcoded secondary loss=5000, fixed zone conditionals `if code == 'T1'`).
- `docs/audits/audit_bayesian_fair_copula_argon.md`: Your prior audit rejecting the initial copula implementation and specifying clean architecture fixes.
- Generated documents: `Molins_202610_Tomo_1_Diagnostico_ASIS.docx` / `.pdf` and tower payloads in `working/molins/`.

THE USER'S QUESTION:
"y no se que cambios tenemos que hacer, puedes pedirle a gemini-4-argon que nos diga cuales son los siguientes pasos que tenemos que hacer?"

YOUR TASK:
Provide an authoritative, unambiguous, step-by-step master roadmap answering:
1. What exact code changes must be applied to `tower_payload_hydrator.py` and configuration files?
2. How to properly calibrate finding-level parameters (TEF, RTO, Secondary Loss, and Zone Burn Rates) so the bottom-up dynamic calculation organically converges to ~880k €/year expected ALE across 10 towers while reflecting individual tower evidence?
3. How to decouple the zone mappings from hardcoded tower codes (`if code == 'T1'`) into multi-tenant metadata/telemetry?
4. How to integrate the portfolio summary back into the global and tower payloads, ensuring mathematical conservation and C-level reporting integrity?
5. The exact sequence of commands and scripts to execute to validate, run tests, and regenerate the deliverables (`Molins_202610_Tomo_1_Diagnostico_ASIS.docx` and tower payloads).

Structure your response with:
- Strict technical English for all engineering artifacts/code blocks.
- Actionable, numbered step-by-step plan (Max clarity, zero fluff, zero sycophancy).
- Concrete code snippets / patch specifications.
- Clear validation criteria.
"""


def main() -> None:
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print(f"Consulting gemini-4-argon via model: {model}...")

    response = client.models.generate_content(
        model=model,
        contents=PROMPT,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Roadmap generated successfully at: {OUTPUT_FILE}")
    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON MASTER ROADMAP SUMMARY:")
    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:60]:
        print(line)
    if len(lines) > 60:
        print(f"... ({len(lines) - 60} more lines in {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
