#!/usr/bin/env python3
"""Argon Strategic Consultation: Robust Universal Epistemic Modality Classification.

Addresses user's critical insight:
A regex of Spanish verb stems in Python code is fragile, weak, hardcoded, and fails
for global enterprises speaking German, Japanese, French, or using subtle English phrasing.

Consults gemini-4-argon to design a bulletproof, 100% Technical English, scale-invariant,
and multilingual epistemic modality classification architecture:
1. Universal Zero-Shot Structured Classification Contract (any language in the world).
2. External Declarative Multilingual Grammar Catalog (zero non-English words in Python).
3. Closed-World Memory Isolation in Volume 1.
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
print(f"Connecting to Reasoning model '{model_name}' for Robust Modality Architecture...")

prompt = """You are 'gemini-4-argon', Principal Staff Systems Architect, Lead Researcher in NLP and Knowledge Representation, and Former Tech Lead at Google Research.

THE USER'S CHALLENGE (100% accurate, deep, and uncompromising):
"The feeling I have is that this regex approach is really weak. Remember that I do NOT want anything hardcoded. Remember the goal is that it serves ANY company in the world from mid-size to top tier 1 globally, of any vertical, in ANY language. And the code MUST be 100% in English, not a single Spanish word (Spanish is only for chat and deliverable output). We have to think of another way of programming this that is MUCH MORE ROBUST to classify everything into:
- FACT_PRODUCTION_ASIS (Active empirical reality in production)
- ASPIRATIONAL_TOBE (Future desire, wish, plan, PoC intent)
- TECHNICAL_ABSENCE_GAP (Explicit confirmation of non-existence or void)
in a solid, unshakeable way."

WHY THE PREVIOUS REGEX ATTEMPT WAS UNACCEPTABLE:
- A Python regex with Spanish/Portuguese verb stems fails completely on German, Japanese, French, or nuance in English.
- Hardcoding language stems inside Python violates the 100% Technical English Codebase Law.
- It is brittle and vulnerable to phrasing variations.

YOUR MISSION:
Design a production-grade, Tier-1 architecture to classify epistemic modality that:
1. Works natively for ANY human language (English, Spanish, German, Japanese, French, Portuguese, Arabic, etc.) without code changes.
2. Contains ZERO non-English words in Python code (all contracts, variables, docstrings, and logic in pure Technical English).
3. Eliminates regex heuristics in favor of a robust, deterministic, or structured neural approach.
4. Explains how an enterprise platform (like Palantir or Anthropic) performs this modality classification at ingestion time.

Structure your response with technical precision, exact data contracts, and zero fluff.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/architecture/ROBUST_UNIVERSAL_EPISTEMIC_MODALITY_ARCHITECTURE.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved Robust Modality Architecture to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:2500] + "\n... [TRUNCATED] ...")
print("=" * 80)
