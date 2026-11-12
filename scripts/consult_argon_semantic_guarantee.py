"""Consult gemini-4-argon on how to permanently and architecturally guarantee 250-400 words of 9/10 zero-hallucination technical narrative per pillar at the pipeline level."""

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

PROMPT = """You are 'gemini-4-argon', Lead AI Systems Architect & Red Team Auditor for Tier-1 Enterprise Assessments in November 2026.

The user has identified an architectural weakness in our workflow:
Yesterday, to fix the "anemia narrativa" of Section 3 (where several pillars had only 1-2 generic sentences, scoring 2/10), we ran a standalone script that called Gemini and wrote directly into the `blueprint_tx_payload.json` files on disk.
While the resulting text was rated 9.4/10, the user correctly pointed out:
"You patched the JSON artifacts directly. That's a cheat/workaround. If we run a new client tomorrow (or regenerate from raw inputs), how does the engine guarantee at the pipeline level that EVERY pillar in Section 3 generates 250-400 words of high-density, forensic technical value specifically about that pillar, with strict domain isolation and ZERO hallucinations?"

We need to answer the user with absolute architectural rigor:
1. **The Root Cause in the Current Pipeline:** Why did the raw synthesis pipeline (`UniversalTowerSynthesizer`) produce 1-sentence paragraphs for some pillars (like Landing Zones, Storage Security, or Disaster Recovery) while writing 200+ words for VMware or Networking? (Analyze prompt looseness, evidence sparsity for specific pillars, lack of min/max word count guardrails, lack of deductive expansion protocols).
2. **The Tier-1 Engine Architecture to Guarantee 250-400 Words (9/10 Quality) Deterministically:**
   How do we build this into the core pipeline so it runs automatically for ANY client?
   - **Protocol 1: The 4-Slot Micro-Dossier & Deductive Negative-Space Expansion:** If an interview has 0 words about "Storage Security", how does the LLM write 250 words about storage security without hallucinating non-existent tools? (Deducing operational reality from adjacent confirmed facts, e.g., root access, lack of RBAC, shared admin credentials).
   - **Protocol 2: Pre-Commit Quality Gate & Self-Correction Loop (The Semantic Gatekeeper Barrier):** How the pipeline programmatically rejects any pillar synthesis with < 250 words or generic boilerplate and forces an autonomous reasoning re-draft before the JSON payload is committed to disk.
   - **Protocol 3: Domain Isolation & Anti-Contamination Firewall:** How the pipeline prevents cross-domain contamination (e.g. preventing concrete factory servers from being mentioned in the Workplace/EUC tower).
3. **Actionable Roadmap:** Exactly what components in `src/assessment_engine/` must be updated (e.g., `universal_tower_synthesizer.py`, a new `PillarSemanticSynthesizer`, prompt registries, and pre-commit validators).

Provide a definitive, executive-grade architectural response in Spanish, direct, sober, and free of hype.
"""

print(f"Submitting Root-Cause Semantic Guarantee Query to {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=PROMPT,
)

out_file = REPO_ROOT / "docs" / "audits" / "ROOT_CAUSE_SEMANTIC_GUARANTEE_ARCHITECTURE.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\nAudit complete. Wrote {len(response.text)} chars to {out_file.relative_to(REPO_ROOT)}")
