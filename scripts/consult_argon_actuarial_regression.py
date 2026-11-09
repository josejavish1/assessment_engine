#!/usr/bin/env python3
"""Consult gemini-4-argon about the actuarial regression."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier

COPULA_FILE = REPO_ROOT / "src/assessment_engine/domain/bayesian_fair_copula_engine.py"
HYDRATOR_FILE = REPO_ROOT / "src/assessment_engine/application/services/tower_payload_hydrator.py"

PROMPT = f"""You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Quality Gatekeeper.

THE PROBLEM:
We had previously resolved the actuarial/financial risk calculations so that they matched a total portfolio ALE of 916,416 EUR for our client "Molins" (with realistic standalone numbers like 141k for T1, 100k for T2, etc., and a worst-case scenario for T1 of 352k based on a 2.5x multiplier and >16 hours of downtime).
However, after our most recent code changes, the numbers have artificially compressed and regressed:
- The total consolidated ALE is now ~452k EUR.
- T1's standalone ALE dropped to ~35k EUR.
- T1's worst-case scenario dropped to ~48k EUR (which implies less than 4 hours of downtime, totally unrealistic for an industrial datacenter serving a 1.1B EUR revenue company with a 13k/h downtime cost).

MANDATES:
1. ZERO HARDCODING. You cannot hardcode "Molins" or specific numbers like "916416" or "13061.29" into the logic. The solution must scale dynamically for ANY company ($20M to $500B+) and any vertical.
2. 100% Technical English.

ANALYSIS AND PLAN REQUIRED:
1. Analyze the mathematical or architectural regression in `bayesian_fair_copula_engine.py` or `tower_payload_hydrator.py` that is causing this artificial sub-additive compression and short downtime hours. (Hint: look at the diversification ratio, copula correlation, or how `evaluate_portfolio` is allocating risk vs. standalone risk, and how RTO limits/modes are parameterized).
2. Propose a phased, zero-hardcoding architectural plan to fix the actuarial math so that the metrics (ALE, worst-case scenario, downtime hours) dynamically reflect the true scale of the company's financial telemetry (without just hardcoding the old numbers).

Here is the current code for BayesianFairCopulaEngine:
```python
{COPULA_FILE.read_text(encoding="utf-8")}
```

Here is the current code for TowerPayloadHydrator:
```python
{HYDRATOR_FILE.read_text(encoding="utf-8")}
```
"""

def main():
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print("Consulting Argon...")
    response = client.models.generate_content(model=model, contents=PROMPT)
    print("=" * 80)
    print(response.text)
    print("=" * 80)

if __name__ == "__main__":
    main()
