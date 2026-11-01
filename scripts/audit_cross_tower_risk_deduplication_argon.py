#!/usr/bin/env python3
"""Consulting gemini-4-argon on Cross-Tower Risk Deduplication and Tangential Risk Governance."""

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

prompt = """
Role: Chief Risk Officer (Open FAIR Fellow) & Global Enterprise Architecture Director.

USER'S BRILLIANT & SHARP QUESTION:
The user asks:
"Solo una duda, ¿pero los riesgos entre torres que sean iguales o tangenciales cómo se gestionan para que no se contabilicen doble?"
(Just one doubt, but how are risks across towers that are identical or tangential managed so they are not double-counted?)

THE PROBLEM IN MULTI-TOWER ENTERPRISE ASSESSMENTS:
In a multi-tower assessment (e.g. T1 Data Center, T2 Network, T3 Cloud, T4 Workplace, T5 Cybersecurity, T6 Governance):
Multiple towers often touch the exact same underlying failure mode or physical asset:
- Example A:
  * Tower 1 (Data Center): Flags lack of backup power to the core network distribution rack.
  * Tower 2 (Network): Flags lack of redundant core switch uplinks.
  * Tower 5 (Cybersecurity): Flags unsegmented plant VLANs exposed to lateral movement.
- Example B:
  * Tower 1 (Data Center): Flags lack of automated backup replication to secondary site.
  * Tower 5 (Cybersecurity): Flags ransomware recovery risk due to unverified offline backups.
  * Tower 6 (Governance): Flags lack of documented Disaster Recovery Plan (DRP) and RPO/RTO SLAs.

If each Tower Specialist generates their own standalone technical annex with independent ALE figures, and an executive sums them up, the company experiences massive **Cross-Tower Double/Triple Counting**!

YOUR TASK:
Provide an authoritative, clear, and definitive architectural answer:
1. THE OPEN FAIR STANDARD LAW ON CROSS-TOWER RISKS:
   - Why risk belongs to the ASSET and LOSS MECHANISM, not to the consulting tower (consulting lenses vs physical asset reality).
2. THE CROSS-TOWER DEDUPLICATION MECHANISM (THE ARCHITECTURAL PATTERN):
   - Explain the "Primary Custodian Tower" (Single Point of Actuarial Truth) pattern.
   - How tangential or shared risks are referenced across towers as "Contributing Dependencies" without duplicating the ALE.
   - Explain how individual Tower Annexes (Anexos Técnicos) display tangential risks (Informative / Linked) vs Primary risks (Quantified ALE).
3. MULTI-TOWER PORTFOLIO CONSOLIDATION IN THE MASTER BUSINESS CASE:
   - How the central `ActuarialLedgerSSOT` aggregates all towers across the enterprise into a non-overlapping global ALE.
4. CONCRETE DATA SCHEMA & IMPLEMENTATION RULE:
   - Provide the schema structure (`primary_tower`, `shared_towers`, `is_cross_tower_dependency`) ensuring zero double-counting in code.
"""

print(f"Requesting cross-tower deduplication guidance from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: CROSS-TOWER RISK DEDUPLICATION & GOVERNANCE ARCHITECTURE")
print("=" * 80)
print(response.text)
print("=" * 80)
