#!/usr/bin/env python3
"""Adversarial Actuarial Deliberation Engine via gemini-4-argon (RFC 084).

Submits the quantitative risk dilemma to gemini-4-argon to evaluate 3 competing
architectural options for reconciling technical findings with financial exposure (ALE),
performing hostile adversarial attacks on each, and synthesizing the definitive design.
"""

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

OUTPUT_PATH = REPO_ROOT / "docs/architecture/RFC_084_ADVERSARIAL_ACTUARIAL_DELIBERATION_ARGON.md"


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Connecting to reasoning tier model: {model_name}...")

    prompt = """
Role: Chief Actuary, Principal Quantitative Risk Architect, and Senior Partner at McKinsey / Oliver Wyman / FAIR Institute.

CONTEXT OF THE ARCHITECTURAL DILEMMA (NOVEMBER 2026):
In our enterprise Assessment Engine, we evaluate IT/OT technological maturity (CMMI 1.00 to 5.00) across 10 domains (T1 to T10) and translate findings into financial risk exposure (Open FAIR™ Annual Loss Expectancy - ALE in €/year) for both individual technical annexes and the consolidated Tomo 1 Board report.

THE OBSERVED FAILURE MODE:
When we transitioned our primary evidence source from a high-level synthetic context document to raw, 347-turn interview audio transcripts, the operational reality of the client (Molins, a heavy cement manufacturer) changed dramatically:
- In Tower 2 (Compute & Virtualization), a hallucinated 4.20 Kubernetes capability was corrected down to 1.00 (non-existent in production).
- Severe physical RAM exhaustion was uncovered on SimpliVity hosts 3 & 4 carrying OT virtual machines, making N+1 datacenter failover impossible.
- CPD proximity (separated by only 500m without ring routing) was confirmed.

YET, THE TOWER'S FINANCIAL RISK EXPOSURE (ALE) REMAINED EXACTLY € 100,806 / YEAR.
Why? Because `TowerPayloadHydrator` currently enforces a TOP-DOWN FIXED-WEIGHT ALLOCATION: an authoritative dictionary in `financial_telemetry` assigns pre-set amounts to each tower (T1: 141,132 €, T2: 100,806 €, T5: 206,194 €), and scales all findings inside that tower so their sum equals that target.

The user correctly challenged: "If so many things changed, how can the risks and their financial quantification be the same? That must be an error!"

TASK:
Perform an uncompromising, deeply technical ADVERSARIAL DELIBERATION evaluating 3 distinct architectural options for solving this problem in production (November 2026).

THE 3 COMPETING ARCHITECTURAL OPTIONS:
1. OPTION 1: Top-Down Fixed Allocation with Proportional Redistribution (Current Baseline)
   - Macro corporate loss budget (e.g., 916,416 €) is pre-calibrated with the CFO/CRO as an upper envelope (~0.08% of revenue).
   - Each tower receives a fixed budget, and findings are proportionally scaled.

2. OPTION 2: Pure Unconstrained Bottom-Up Summation (Naive Open FAIR)
   - Every individual finding computes ALE independently: ALE = TEF × VULN × (Downtime × Hourly Cost).
   - Tower ALE is the raw sum of its findings. Portfolio ALE is the raw sum of all tower ALEs.
   - No top-down constraints or normalization.

3. OPTION 3: Hierarchical Bayesian FAIR-CAM with Copula-Driven Sub-Additive Aggregation (State of the Art)
   - Bottom-Up Control Efficacy: Pillar CMMI maturity score (1.00 to 5.00) dynamically modulates Vulnerability (VULN) via Beta-Binomial / FAIR-CAM calibration curves. Finding downtime is anchored to physical plant telemetry (e.g., weighbridge downtime at 5,000 €/h vs corporate ERP at 13,061 €/h).
   - Domain-Level Dynamic Flotation: A tower's ALE is NOT frozen; discovering that hosts 3 & 4 are saturated increases T2's ALE naturally.
   - Sub-Additive Portfolio Convolution: At the Tomo 1 portfolio level, domains are NOT summed linearly (which causes double-counting of simultaneous downtime). Instead, a copula-based convolution (or Fréchet bound sub-additivity) aggregates portfolio VaR and expected ALE, capturing cross-domain risk diversification.

REQUIRED ADVERSARIAL STRUCTURE:
1. EXECUTIVE SUMMARY & ARCHITECTURAL VERDICT.
2. RIGOROUS ADVERSARIAL ATTACK ON OPTION 1 (Failure modes, loss of economic causality, why sophisticated clients detect the "fixed pie" trick).
3. RIGOROUS ADVERSARIAL ATTACK ON OPTION 2 (The "Alarmist Consultant Fallacy", risk inflation, double-counting of concurrent downtime, CFO credibility collapse).
4. RIGOROUS ADVERSARIAL ATTACK ON OPTION 3 (Implementation complexity, explainability to non-actuarial executives, sensitivity to parameter drift, computational overhead).
5. THE DEFINITIVE ARCHITECTURAL RESOLUTION:
   - Which option should our engine adopt?
   - Exact mathematical formulation (equations for VULN calibration, SLE derivation, and Portfolio aggregation).
   - Concrete implementation architecture in Python (Hexagonal / Clean Architecture ports and adapters).
6. LEADERSHIP DECISION MEMO (A 1-page briefing for the CIO/CFO explaining why the numbers are trustworthy, reproducible, and tailored).

Generate the entire document in rigorous, professional Technical English. Maintain absolute intellectual honesty, zero flattery, and exhaustive mathematical precision.
"""

    print("Generating adversarial deliberation via gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    header = """---
status: Verified
owner: architecture-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
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
    print(f"Successfully generated adversarial deliberation report at: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
