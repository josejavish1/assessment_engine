#!/usr/bin/env python3
"""Consulting gemini-4-argon on Universal Tower Scenario Architecture and Anti-Pattern Prevention."""

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
Role: Chief Software Architect (Enterprise Systems) & Principal Risk Fellow (Open FAIR).

CONTEXT & USER QUESTION:
The user raises a crucial architectural doubt regarding the proposed scenario consolidation:
"pero es que esto que programamos sirve para cualquier torre no? esto aplica para todos? todas las empresas tendrán 4 fichas? ¿esto es correcto o es un antipatrón? no se, me parece lógico pero no tengo claro como hacerlo sin tener un antipatron, ¿que nos diría gemini-4-argon?"

THE USER'S CONCERN:
1. Is fixing the number of scenarios to "4 cards" an anti-pattern? (YES, hardcoding 4 cards for all companies and all towers would violate our Zero-Hardcoding mandate!).
2. How must this work universally across ALL towers (T1 Data Center, T2 Network, T3 Cloud, T4 Workplace, T5 Cybersecurity, etc.)?
3. How does a Tier-1 global enterprise platform structure this dynamically so that:
   - A mid-market firm or small scope might have 2 or 3 scenarios.
   - A complex Fortune 10 enterprise or multi-domain tower might have 5 or 6 scenarios.
   - The engine does NOT hardcode scenario names, scenario counts, or company-specific assumptions in Python code.
4. How do granular audit findings dynamically map to their parent failure scenario without manual hand-coding?

YOUR TASK:
Provide an authoritative, clear, and comprehensive architectural response:
1. Direct Answer: Confirm why hardcoding a static number of scenarios (like "4") is an anti-pattern, and how a true Tier-1 platform handles variable scenario counts ($K \ge 1$).
2. The Universal Scenario Pattern: How scenarios are defined declaratively in the taxonomy / tower configuration (`engine_config/towers/*.json` or blueprint payloads) rather than hardcoded in Python.
3. Dynamic Finding-to-Scenario Mapping: Explain how granular audit findings attach to their parent failure scenario (e.g. by Pillar, by failure domain, or by explicit declarative mapping in payload/CSV).
4. Concrete Python/AST Contract: The exact data structure and compiler method that renders $K$ scenario cards dynamically for any tower, any company, any currency, and any vertical.
"""

print(f"Requesting architectural guidance from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: UNIVERSAL SCENARIO ARCHITECTURE & ANTI-PATTERN PREVENTION")
print("=" * 80)
print(response.text)
print("=" * 80)
