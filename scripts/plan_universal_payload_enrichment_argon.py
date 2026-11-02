#!/usr/bin/env python3
"""Argon-4 Consultation: Universal Payload Enrichment Architecture (Zero Hardcoding, 100% English)."""

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

def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    # Context files
    polish_script_path = REPO_ROOT / "scripts/polish_payload_and_render.py"
    polish_code = polish_script_path.read_text(encoding="utf-8") if polish_script_path.exists() else "File not found."

    pipeline_path = REPO_ROOT / "src/assessment_engine/application/run_tower_pipeline.py"
    pipeline_code = pipeline_path.read_text(encoding="utf-8") if pipeline_path.exists() else "File not found."

    prompt = f"""
Role: Principal Systems Architect & Enterprise Data Pipeline Engineer (Google Tier-1 / Anthropic Core Infrastructure).

CONTEXT & THE ANTI-PATTERN:
Currently, there is a severe "Split-Brain" (Pet vs. Cattle) data asymmetry in our AS-IS deliverables. 
Tower 1 (T1) looks spectacular and forensically accurate because a manual script (`scripts/polish_payload_and_render.py`) was written exclusively to inject 21 advanced structural keys, local forensic evidence, and financial telemetry into `T1/blueprint_t1_payload.json`. 
Meanwhile, Towers 2 through 10 remain raw, holding only 11 basic keys, generic text, and English capability names failing to resolve against the multilingual taxonomy catalog.

THE GOAL:
Architect a definitive, bug-free, and universal solution to eradicate this anti-pattern. We need a deterministic `UniversalPayloadEnricher` (or similar architectural step) integrated into the core pipeline that applies the same high-tier forensic grounding, financial computation, and multilingual taxonomy resolution to ALL 10 towers dynamically.

MANDATORY LAWS FOR YOUR DESIGN:
1. ZERO BUGS, ZERO ANTI-PATTERNS: The design must be architecturally clean (e.g., Domain-Driven Design, distinct pipeline stages). No "hacks".
2. ZERO HARDCODING (UNIVERSAL ENTERPRISE READINESS):
   - The architecture must scale from a 50-person local firm to a Fortune 10 global conglomerate in any vertical (Banking, Aerospace, Retail).
   - Any ISO 4217 currency.
   - Any supported language (en, es, pt, fr, de, ja).
   - No hardcoded client names, no hardcoded tower names or IDs. Everything must be derived from tenant configuration (`document_meta`), `taxonomy_multilingual.json`, or the `cfo_actuarial_gate`.
3. 100% TECHNICAL ENGLISH CODEBASE RULES:
   - Your proposed Python code and architecture MUST contain ZERO Spanish words. 
   - All identifiers, docstrings, classes, variables, logs, and comments must be 100% Technical English.
   - Human languages (Spanish, Japanese, etc.) only exist as dynamic configuration values pulled at runtime.

AVAILABLE CONTEXT (The Anti-Pattern Script to deprecate):
```python
{polish_code[:4000]} # Truncated for brevity
```

AVAILABLE CONTEXT (The Core Pipeline - run_tower_pipeline.py):
```python
{pipeline_code[:4000]} # Truncated for brevity
```

YOUR TASK:
Provide a comprehensive Architectural RFC (Markdown format) outlining exactly how to design and implement the `UniversalPayloadEnricher`. 
- Define the directory structure and module names (e.g., `src/assessment_engine/application/universal_payload_enricher.py`).
- Provide the precise, 100% Technical English Python blueprints (class definitions, method signatures) for the enricher.
- Explain how it will hook into `run_tower_pipeline.py` or operate as an independent pipeline step for all `T1..T10` payloads.
- Guarantee the elimination of the split-brain and hardcoding issues.
"""

    print(f"Requesting architectural blueprint from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_027_UNIVERSAL_PAYLOAD_ENRICHMENT_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: UNIVERSAL ENRICHMENT ARCHITECTURE PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
