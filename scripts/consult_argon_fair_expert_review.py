#!/usr/bin/env python3
"""Adversarial Peer Review by Open FAIR™ Fellow (gemini-4-argon).

Evaluates what an elite team of certified Open FAIR™ actuaries and risk quantitative analysts
would say if they inspected our codebase, methodology, and actual output figures across:
1. Starling Bank (UK FinTech - £665M GBP)
2. Rede D'Or São Luiz (Brazil Healthcare - R$ 47B BRL)
3. Molins (Spain Heavy Manufacturing - €1.144B EUR)
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

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
print(f"Connecting to Reasoning model '{model_name}' for Open FAIR™ Fellow Peer Review...")

prompt = """You are the President of the Open FAIR™ Certification Board, Senior Risk Actuary Fellow, and Creator of the Factor Analysis of Information Risk (O-FAIR) Standard (ISO/IEC 27005 / The Open Group).

THE QUESTION FROM THE USER:
"If an expert actuarial team specialized in the Open FAIR™ methodology saw what we do, how we do it in our code, and analyzed the results coming out for our different companies (Starling Bank in UK, Rede D'Or in Brazil, and Molins in Spain), what would they tell us?"

CODE CONTEXT (What we actually do in our codebase):
1. In `bayesian_fair_copula_engine.py`: We implement a two-factor Student-t copula, positive-definite covariance projection, and Bayesian conjugate distributions (Gamma-Poisson for TEF, Beta-Binomial for Vulnerability).
2. In `downtime_calibrator.py`: We decompose downtime into Primary Operational Loss (Outage Hours * Hourly Rate) and Secondary Loss (CapEx / response).
3. In `tower_payload_hydrator.py`: We take the tenant's revenue, currency, and hourly rate. To avoid the "10 EUR micro-risk bug" and inverted severities, we distribute the domain's allocated ALE pool to findings using ordinal severity weights: CRITICAL (10.0), HIGH (4.5), MEDIUM (1.8), LOW (0.8), and derive P90 = ALE * 1.5, Min = ALE * 0.4, Max = ALE * 2.2.
4. The actual outputs generated:
   - Molins (Spain, €1.144B Manufacturing): Hourly Rate = €13,061.29/h | Total Corporate ALE = €766,536 (0.067% of revenue) | Findings: Critical = €22k-€33k, High = €10k-€15k, Medium = €4k-€6k.
   - Starling Bank (UK, £665M FinTech): Hourly Rate = £140,000/h | Total ALE = £709,171 (0.11% of revenue) | Findings: Low = £3.5k-£18.5k.
   - Rede D'Or (Brazil, R$ 47B Healthcare): Hourly Rate = R$ 420,000/h | Total ALE = R$ 420,867,885 (0.89% of revenue) | Tower ALEs: R$ 36M to R$ 59M.

Provide an unsparing, authentic, highly professional peer review addressing:
1. WHAT THEY WOULD PRAISE: What parts of our engineering, mathematics, and architecture represent genuine Tier-1 sophistication rarely seen in cybersecurity tools?
2. WHAT THEY WOULD CRITIQUE / CALL OUT: What shortcuts, approximations, or non-standard practices would they immediately challenge? (e.g. static P90=1.5*ALE scalar derivation, top-down severity proportional allocation vs pure bottom-up scenario modeling).
3. EVALUATION OF THE 3 REAL CLIENT OUTPUTS:
   - Molins (€766k ALE on €1.14B): Is it believable to a FAIR actuary?
   - Starling Bank (£709k ALE on £665M): Is it believable to a FAIR actuary?
   - Rede D'Or (R$ 420M ALE on R$ 47B): Is it believable to a FAIR actuary?
4. EXECUTIVE VERDICT: Would an Open FAIR certification board approve this methodology as a legitimate commercial implementation of quantitative risk analysis, and what is the single next evolution to make it bulletproof?

Adopt a strict, authoritative, professorial, yet practical tone.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/audits/OPEN_FAIR_FELLOW_PEER_REVIEW.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved Open FAIR™ peer review to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:2500] + "\n... [TRUNCATED] ...")
print("=" * 80)
