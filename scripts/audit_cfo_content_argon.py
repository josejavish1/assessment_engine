#!/usr/bin/env python3
"""Consulting gemini-4-argon on whether an Adversarial CFO Validation Loop is an Anti-Pattern or a Best Practice."""

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
Role: Chief Quality Officer (Tier-1 Systems Architecture) & Principal AI Governance Fellow.

USER'S INQUIRY & QUESTION:
The user asks:
"Es que yo incluso estaba pensando en poner un debate adversarial con un CFO duro para que valide los números, aunque no sé si eso es un antipatrón."
(I was even thinking of setting up an adversarial debate with a tough CFO to validate the numbers, although I don't know if that's an anti-pattern.)

THE ARCHITECTURAL DILEMMA:
In generative AI and automated enterprise advisory systems:
Is introducing an adversarial persona (e.g., "A Skeptical Industrial CFO") to interrogate and validate risk figures an anti-pattern, or is it a best practice?

YOUR ANALYSIS MUST DELIVER:
1. THE DANGER / ANTI-PATTERN ZONE:
   - When DOES an adversarial debate become an anti-pattern? (e.g., nondeterministic runtime negotiation, vibe-based bargaining over numbers, adding unrepeatable LLM churn in the document compilation loop).
2. THE BEST PRACTICE / TIER-1 ARTIFACT ZONE:
   - When is it an elite architectural pattern? (e.g., offline Adversarial Evaluation Gates / Red-Teaming, pre-flight actuarial contract validation, automated stress-testing before payload compilation).
3. HOW TO IMPLEMENT IT CORRECTLY (IF USED):
   - What deterministic boundary checks must the CFO agent enforce? (Physical downtime floors, revenue proportionality bounds, double-counting checks, hypothesis framing vs catastrophic language).
   - Where in the architecture must it live? (In the evaluation/payload generation pipeline, NEVER in the document rendering AST bridge).
4. DEFINITIVE VERDICT & ACTIONABLE RECOMMENDATION:
   - A clear, authoritative verdict for our platform.
"""

print(f"Requesting architectural opinion from {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

print("\n" + "=" * 80)
print("GEMINI-4-ARGON: ADVERSARIAL CFO EVALUATION GATE ANALYSIS")
print("=" * 80)
print(response.text)
print("=" * 80)
