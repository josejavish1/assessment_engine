#!/usr/bin/env python3
"""Argon Strategic Consultation: Universal Scale, Vertical, and Language Guarantee.

Consults gemini-4-argon on whether the Minto Pyramid 4-Block Executive Summary
and Master Plan 100% guarantee universal excellence across:
1. Scale: Mid-market (€15M) to Global Top-Tier ($50B)
2. Verticals: Banking (Starling UK), Healthcare (Rede D'Or BR), Manufacturing (Molins ES), Retail (Chedraui MX), SaaS (Datadog US), and Public Sector.
3. Language: English, Spanish, Portuguese, German, Japanese.

Identifies what specific adjustments are required to make this guarantee mathematically
and architecturally irrefutable.
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

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)
print(f"Connecting to Reasoning model '{model_name}' for Universal Guarantee Analysis...")

prompt = """You are 'gemini-4-argon', the Principal Staff Systems Architect, Lead Actuary, and Fortune 500 Chief Risk Officer.

THE USER'S QUESTION:
"Remember that the goal is that it serves ANY company in the world from mid-size to top tier 1 globally, of any vertical, in any language. Does this guarantee it? Meaning whether it's Molins (Spain Manufacturing), or the UK company (Starling Bank FinTech), or the Brazilian one (Rede D'Or Healthcare) that we have in the code, or do we need to make adjustments to the plan?"

MISSION:
Evaluate whether the Minto Pyramid 4-Block Executive Summary and the 4-Phase Master Plan truly guarantee 10/10 performance across all dimensions:
1. Scale Invariance: From a €15M mid-market manufacturing/logistics business to a $50B global money-center bank.
2. Vertical Agnosticism: From UK Digital Banking (Faster Payments, DORA, PRA) to Brazilian Healthcare (73 hospitals, Tasy/MV EHR, LGPD, ANVISA) to Heavy Cement Manufacturing (Molins, SimpliVity, weighbridges) to Public Sector Ministries.
3. Linguistic Decoupling: 100% English internal reasoning and data contracts, localized dynamically at the edge into Spanish, Portuguese, English, etc.

CRITICAL INQUIRY:
- Does the current plan already guarantee this, or are there 2-3 specific adjustments we MUST make to prevent mid-market companies from sounding like Fortune 50 banks, or healthcare companies from receiving industrial rhetoric?
- How do we parameterize the `ExecutiveSummaryAST` so that scale, vertical, and language are dynamically injected without ANY hardcoding?

Provide an unsparing, concrete architectural diagnosis with the exact adjustments required to make the universal guarantee 100% bulletproof.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/architecture/ARGON_UNIVERSAL_SCALE_AND_VERTICAL_GUARANTEE.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved Universal Guarantee report to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:2500] + "\n... [TRUNCATED] ...")
print("=" * 80)
