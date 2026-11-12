"""Consult gemini-4-argon for the Tier-1 architecture to solve the Semantic Density Failure (Anemia Narrativa)."""

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

PROMPT = """You are 'gemini-4-argon', Lead Adversarial Red Team Chief Architect (Enterprise Architecture / IT Strategy) at a top-tier global consulting firm in November 2026.

We have encountered a SEVERE architectural flaw in our Assessment Engine's data pipeline (The "Semantic Density Failure" or "Anemia Narrativa"):
Across our 10 technology towers, the payloads (`blueprint_tx_payload.json`) have severely degraded semantic density in the `asis_architecture_description` fields for certain pillars. 

Out of 50 pillars analyzed:
- 18 are "Solid" (100-300 words, rich context).
- 13 are "Acceptable" (75-100 words).
- 11 are "Poor" (40-70 words, generic).
- 8 are "Dismal" (< 40 words, often just 1 or 2 sentences of meaningless boilerplate like "The self-assessment projected a score of 3.5").

The user explicitly rejected any "tactical patch" (like just manually writing paragraphs for the 19 failing pillars) and demands a ROOT CAUSE, TIER-1 ARCHITECTURAL SOLUTION. They want to know *why* this happens structurally and how a Top Tier 1 team in Nov 2026 would fix it at the pipeline level so that EVERY pillar consistently scores a 9/10 in semantic density and business value, WITHOUT hallucinations.

YOUR MANDATE:
Design the ultimate Master Architecture to permanently solve this Semantic Density Failure.
1. **Root Cause Analysis:** Why does an LLM-driven ingestion pipeline produce rich narratives for some pillars (like Networking or VMware) but degenerate into 1-sentence boilerplate for others (like Storage Security or Landing Zones)? (Hint: Look at the "Split-Brain" processing, lack of ontological grounding for specific sub-domains, or absence of localized firmographic telemetry).
2. **The Tier-1 Structural Solution:** Design a deterministic mechanism (e.g., a "Semantic Amplifier Agent", "RAG-Anchored Synthesis", "Ontological Knowledge Graph Injection", or "Multi-Agent Debate Protocol") that forces the pipeline to extract and articulate real value for every pillar. How do we guarantee 150+ words of rich, empirical, Molins-specific context per pillar without hallucinating facts not in the raw interview transcripts?
3. **Execution Plan:** Provide the exact architectural design pattern to implement in the ingestion pipeline (e.g., how to restructure the extraction prompts, what intermediate validation layers to add before writing the `blueprint_payload.json`).

Provide a definitive, aggressive, and highly technical design document (Markdown format). No pleasantries. Only Tier-1 architectural solutions.
"""

print(f"Submitting Semantic Density Failure Architecture Audit to {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=PROMPT,
)

out_file = REPO_ROOT / "docs" / "audits" / "RED_TEAM_SEMANTIC_DENSITY_ARCHITECTURE.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\nAudit complete. Wrote {len(response.text)} chars to {out_file.relative_to(REPO_ROOT)}")
