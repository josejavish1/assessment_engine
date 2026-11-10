#!/usr/bin/env python3
"""Argon Strategic Consultation: Master Plan for Universal 10/10 Quality.

Consults gemini-4-argon to formulate a phased, foolproof architectural plan to achieve
a guaranteed 10/10 deliverable quality for ANY company worldwide (mid-size to Top-Tier),
in any vertical, and any language.
Mandates: Zero bugs, zero antipatterns, zero hardcoding, 100% Technical English codebase.
"""

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
print(f"Connecting to Reasoning model '{model_name}' for Universal Master Plan...")

prompt = """You are 'gemini-4-argon', the Principal Staff Systems Architect, Lead Actuary, and Fortune 500 Chief Risk Officer.

THE USER'S MANDATE:
"Before we start programming, we need to think deeply about how to approach this and in how many phases to guarantee it is bug-free and that we will be #1 in the world, for any vertical, in any language. The code MUST be 100% in English, not a single Spanish word (Spanish is only for chat and the deliverable output). Increase deliverable quality to 100%. I want gemini-4-argon to design a master plan with zero bugs, zero problems, and zero antipatterns. Zero hardcoding. The goal is to serve any company in the world, from mid-size to Top-Tier."

YOUR MISSION:
Design the ultimate, phased architectural roadmap to elevate this Assessment Engine to a guaranteed, universal 10/10 quality standard.
You must eradicate the remaining bottlenecks (like the 0.055 router broadcast threshold, missing niche taxonomies, and GIGO variance) without introducing new antipatterns.

CONSTRAINTS & RULES:
1. 100% Technical English Codebase: Every entity, variable, log, prompt, and test must be in English. Localization happens strictly at the edge (JSON locale files).
2. Zero Hardcoding: No client names, no specific vendors in hardcoded arrays. Everything must be declarative or ontologically driven.
3. Universal Scaling: Must work identically for a €20M regional trucking company and a $50B global investment bank.
4. Bug-Free Delivery: Propose strict, automated CI/CD gating and architectural invariants to prevent regressions.

STRUCTURE THE MASTER PLAN INTO SPECIFIC PHASES:
- Phase 1: Epistemic Router & Evidence Purity (Fixing the 0.055 bleed and enforcing Winner-Takes-Primary).
- Phase 2: Autonomous Ontological Expansion (Handling unknown verticals like Aerospace or Nuclear without code changes).
- Phase 3: Deliverable Synthesis & Semantic Firewalls (Validating LLM output against cross-tower contamination before saving).
- Phase 4: CI/CD Quality Gates & Invariants (How to mathematically prove the 10/10 standard on every commit).

Provide a highly authoritative, technical, and concrete engineering blueprint in Markdown. Do not include pleasantries.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/architecture/ARGON_UNIVERSAL_10_OUT_OF_10_MASTER_PLAN.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved strategic master plan to {out_file.relative_to(REPO_ROOT)}")
