#!/usr/bin/env python3
"""Adversarial Code, Hygiene, and Architecture Audit by gemini-4-argon."""

import json
import subprocess
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

# Read locales.json ch3_intro_by_tower
loc_path = REPO_ROOT / "engine_config/locales.json"
with open(loc_path, "r", encoding="utf-8") as f:
    loc_data = json.load(f)

es_intros = loc_data.get("es", {}).get("ch3_intro_by_tower", {})
en_intros = loc_data.get("en", {}).get("ch3_intro_by_tower", {})
es_scorecards = loc_data.get("es", {}).get("ch3_scorecard_by_tower", {})
es_cross_intros = loc_data.get("es", {}).get("cross_cutting_debt_intro_by_tower", {})

# Read Python code touched
payload_to_ast_path = REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py"
ast_code = payload_to_ast_path.read_text(encoding="utf-8")

compiler_path = REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"
compiler_code = compiler_path.read_text(encoding="utf-8")

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = f"""You are 'gemini-4-argon', the Principal Staff Security & Software Engineering Auditor.

THE USER HAS RE-ISSUED THIS STRICT DIRECTIVE:
"Before continuing, I want gemini-4-argon to do a complete, uncompromising review of what was recently coded, searching for bugs, problems, or antipatterns. I DO NOT want anything hardcoded. Remember the goal: it must serve ANY enterprise in the world, from an SMB ($20M) to a top Tier-1 global corporation ($500B), across ANY vertical (banking, retail, manufacturing, healthcare, public sector, tech), in ANY target language (en, es, pt, fr, de, ja), and Python code must be 100% Technical English without a single word of Spanish."

SCRUTINIZE THE FOLLOWING EVIDENCE:

1. `ch3_intro_by_tower` (ES) recently injected into `engine_config/locales.json`:
{json.dumps(es_intros, indent=2, ensure_ascii=False)[:2500]}

2. `ch3_scorecard_by_tower` (ES) in `engine_config/locales.json`:
{json.dumps(es_scorecards, indent=2, ensure_ascii=False)[:2500]}

3. Compiler Python Code in `payload_to_ast.py` (lines 1640-2050):
```python
{ast_code[1640:2050]}
```

4. Compiler Python Code in `in_memory_asis_compiler.py` (lines 880-1200):
```python
{compiler_code[880:1200]}
```

YOUR AUDIT MANDATE:
1. TENANT / CLIENT HARDCODING IN GLOBAL CONFIGS:
   - Examine `ch3_intro_by_tower` and `ch3_scorecard_by_tower` in `locales.json`!
   - Did the engineer inject specific tenant names or specific geographic locations (e.g., "Sant Vicenç dels Horts"), specific industrial sectors ("plantas cementeras y canteras"), or specific vendor assumptions into `engine_config/locales.json`?
   - What happens when a Tier-1 Bank (e.g. JPMorgan), a Healthcare System, or a Retail Chain runs this engine? Will they see "Sant Vicenç dels Horts" or "cement plants and quarries"?
   - Flag every single hardcoded violation in `locales.json`.
2. LANGUAGE DECOUPLING LAW (100% TECHNICAL ENGLISH IN PYTHON):
   - Check all Python code in `payload_to_ast.py` and `in_memory_asis_compiler.py`.
   - Are there any Spanish comments, docstrings, variable names, regexes, or string literals in Python?
3. ARCHITECTURAL CLEANLINESS & UNIVERSAL TENANT SCALING:
   - How should Section 3.1 introductions and scorecard commentary be designed so that:
     a) `engine_config/locales.json` remains 100% universal, tenant-agnostic, and vertical-agnostic (pure parameterized templates with NO client or geographic literals).
     b) Any specific client context (like Molins's "Sant Vicenç dels Horts" or a bank's "London/New York trading floors") comes dynamically from the tenant's payload (`blueprint_data["domain_introduction"]` or `blueprint_data["document_meta"]`), NEVER from `locales.json`.
4. BUGS, RUNTIME RISKS & ANTIPATTERNS:
   - Check for potential `IndexError`, `KeyError`, `AttributeError`, or `TypeError`.
   - Check fallback behavior when a tenant has 0 findings or fewer than 3 pillars.

Deliver an unsparing, exhaustive forensic audit report in English Markdown.
"""


def main() -> None:
    print("Initiating adversarial code audit with gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_ADVERSARIAL_HARDCODING_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    front_matter = """---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
doc_type: operational
diataxis: reference
verification_mode: editorial
---

"""
    out_file.write_text(front_matter + response.text, encoding="utf-8")

    print("=" * 80)
    print("ARGON ADVERSARIAL AUDIT REPORT:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Full audit report written to {out_file}")


if __name__ == "__main__":
    main()
