"""Consult gemini-4-argon for the exact step-by-step code implementation plan for the Pillar Synthesis and Semantic Gatekeeper."""

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

PROMPT = """You are 'gemini-4-argon', Lead AI Systems Architect & Principal Software Engineer for Tier-1 Enterprise Assessments in November 2026.

The user has mandated a structural overhaul of how we generate the Section 3 narratives (`asis_architecture_description`) for the 50 pillars across our 10 technology towers.
Currently, `UniversalTowerSynthesizer` uses a "Macro-Prompt" approach, asking the LLM to generate the entire tower and all its pillars in one shot. This causes "Semantic Anemia" (some pillars output 1 sentence) due to token budgeting and evidence sparsity.

We must build an automated, foolproof, Tier-1 pipeline replacement that guarantees exactly 250-400 words of 10/10 technical narrative PER PILLAR, zero hallucinations, and zero cross-domain contamination.

YOUR MANDATE:
Write a ruthless, detailed, step-by-step implementation specification in Markdown (`docs/architecture/PILLAR_SYNTHESIS_TIER1_SPEC.md`).
The implementation must define:

1. **Phase 1: Atomic Asynchronous Generation (Map-Reduce)**
   - Deconstruct the monolothic generation. Specify a new class `PillarForensicSynthesizer` that operates per-pillar.
   - Use `asyncio.gather` to execute the generation concurrently for all pillars in a tower.

2. **Phase 2: Negative Space & 4-Slot Architecture Prompting**
   - Provide the EXACT prompt template or logic needed. The prompt MUST force the LLM to write 4 distinct slots:
     1. Empirical Baseline (State & Evidence).
     2. Failure Mechanics & Adjacent Inference (Deducing operational reality from the environment if direct evidence is sparse).
     3. Architectural Risk Debt & Vulnerability.
     4. Factual Business & Firmographic Impact.
   - Strict Instruction: DO NOT hallucinate vendor names if not in evidence. DO NOT use boilerplate ("It is essential to have..."). DO NOT mention survey scores.

3. **Phase 3: The Semantic Gatekeeper & Retry Loop**
   - Specify a `SemanticGatekeeper` class.
   - It must validate: `250 <= word_count <= 450`.
   - It must run a `ContaminationCheck`: E.g., if processing T9 (Workplace), reject if the text contains "servidor físico", "SAN", "NetApp", "BGP", etc. (Provide a mechanism to pass forbidden lists per tower).
   - If a constraint fails, it throws a custom `SemanticQualityError(feedback)`.
   - The synthesizer catches this and triggers an autonomous retry (`max_retries=3`), appending the feedback: "REJECTED: {feedback}. Rewrite to fix this."

4. **Phase 4: Integration with `UniversalTowerSynthesizer`**
   - Specify exactly how to wire `PillarForensicSynthesizer.synthesize_pillar(...)` inside `UniversalTowerSynthesizer.synthesize_tower(...)`.

Output ONLY the Markdown specification document. Include exact file paths, Python class signatures, and critical method logic to guide the coding phase perfectly.
"""

print(f"Submitting Pillar Synthesis Specification query to {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=PROMPT,
)

out_file = REPO_ROOT / "docs" / "architecture" / "PILLAR_SYNTHESIS_TIER1_SPEC.md"
out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(response.text, encoding="utf-8")
print(f"\nSpec complete. Wrote {len(response.text)} chars to {out_file.relative_to(REPO_ROOT)}")
