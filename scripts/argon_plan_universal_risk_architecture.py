#!/usr/bin/env python3
"""Argon Strategic Rearchitecture Plan for Universal Open FAIR Actuarial Realism.

Consults gemini-4-argon to design a deterministic, multi-tenant architectural plan
to eradicate actuarial hallucinations (e.g., $10 ALE for HIGH risks, MEDIUM costing
4x more than CRITICAL) and synthesize universally coherent, mutually exclusive
risk taxonomy across any global vertical.
"""

from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

prompt = """You are 'gemini-4-argon', the Principal Staff Systems Architect, Chief Information Security Officer (CISO), and Actuarial Fellow.

CONTEXT:
Our AI pipeline dynamically evaluates and generates Open FAIR quantitative IT risks for enterprises worldwide ($10M SMBs to $500B Tier-1 globals) across 10 architectural domains (Towers T1 to T10).
We have detected severe systemic flaws in our risk generation and financial calibration engine.

EMPIRICAL SYMPTOMS (The 'Molins' test case exposed these global bugs):
1. The Absurdity of $10 Risks: Tower 9 (Digital Workplace) evaluated HIGH severity risks but assigned them an Annualized Loss Expectancy (ALE) of 10.02 Euros. No HIGH risk in a $1.1B company costs $10.
2. Inverted Severity Proportionality: In Tower 7 (ITSM), a synthetic MEDIUM risk was assigned an ALE of €31,000, while a verified CRITICAL risk was assigned only €7,600.
3. Decoupling of Asset Gravity: Tower 4 (Storage) assigned an ALE of €5,000 for the lack of redundancy in the primary NetApp SAN. If a central SAN fails, the entire factory stops (costing €13,000 PER HOUR). The model failed to correlate the risk finding to the systemic hourly downtime burn rate.
4. Taxonomic Hallucination & Duplication: The LLM invents duplicate risks across towers (e.g., a corporate M&A integration issue appears in T5, T7, and T8) instead of constraining risks to a canonical, mutually exclusive taxonomy.

MISSION:
Formulate a strictly universal, multi-tenant re-architecture plan (in 3 to 4 distinct phases) to solve the root causes.
The solution MUST NOT contain any hardcoded logic for specific clients (like Molins) or verticals. It must mathematically scale based on Corporate Annual Revenue, Hourly OpEx Burn, and precise industry archetypes (e.g., Healthcare, FinTech, Manufacturing).

CONSTRAINTS & 100% TECHNICAL ENGLISH LAW:
- Zero Spanish words allowed in code, architecture, schemas, or LLM prompts.
- All code logic, variables, exception names, and logging must be 100% Technical English.
- Target language translation occurs strictly via late-binding dictionaries (`locales.json`).
- Adhere to Hexagonal Architecture (Domain vs Application layers) and Domain-Driven Design (DDD).

OUTPUT REQUIREMENTS:
Design a precise, concrete architecture plan addressing:
1. PHASE 1: Actuarial Gravity Anchoring (How to mathematically force the LLM or Python domain logic to bind ALE floors/ceilings to the 'Hourly Downtime Burn' and 'Severity Tier').
2. PHASE 2: Cross-Tower Risk Orthogonality (How to implement a deduplication engine or taxonomy restrictor to prevent the LLM from inventing overlapping risks across T1-T10).
3. PHASE 3: Missing Systemic Risks Injection (How to ensure critical blindspots—like OT Ransomware lateral movement or Identity Hijacking—are deterministically evaluated if the LLM forgets them).

Be forensic, mathematically rigorous, and highly technical.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt
)
out_path = "docs/architecture/ARGON_UNIVERSAL_RISK_REARCHITECTURE_PLAN.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(response.text)
print(f"Plan saved to {out_path}")
