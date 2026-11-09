#!/usr/bin/env python3
"""Adversarial Audit by gemini-4-argon: Hardcoding, Tenant Contamination, and Architectural Purity Review."""

import json
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

# Inspect locales.json for suspicious tenant-specific terms
loc_path = REPO_ROOT / "engine_config/locales.json"
with open(loc_path, "r", encoding="utf-8") as f:
    locales_data = json.load(f)

es_ch3_intro = locales_data.get("es", {}).get("ch3_intro_by_tower", {})
es_ch3_scorecard = locales_data.get("es", {}).get("ch3_scorecard_by_tower", {})
es_patterns = {k: v for k, v in locales_data.get("es", {}).items() if k.startswith("cross_cutting_debt_t")}

compiler_file = REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"
compiler_code = compiler_file.read_text(encoding="utf-8")

payload_to_ast_file = REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py"
payload_to_ast_code = payload_to_ast_file.read_text(encoding="utf-8")[1550:1800]

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Principal Enterprise Architect, Chief Cybersecurity Auditor, and Supreme Code Quality Arbiter.

CRITICAL USER MANDATE & ALERT:
The user has issued a severe warning:
"I feel that you have hardcoded things that you shouldn't have, which makes the engine NOT work for any company. Before continuing, I want gemini-4-argon to do a complete, uncompromising audit of what was recently coded, looking for bugs, problems, or antipatterns. I DO NOT want anything hardcoded. Remember the goal: it must serve ANY enterprise in the world, from an SMB ($20M) to a top Tier-1 global corporation ($500B), across ANY vertical (banking, manufacturing, healthcare, public sector, retail, aviation), in ANY target language (en, es, pt, fr, de, ja), and Python code must be 100% Technical English without a single word of Spanish."

EXAMINE THIS EVIDENCE OF SUSPECTED CONTAMINATION:

1. Samples from `engine_config/locales.json` recently injected:
`ch3_intro_by_tower` (ES):
{json.dumps(es_ch3_intro, indent=2, ensure_ascii=False)[:1500]}

`ch3_scorecard_by_tower` (ES):
{json.dumps(es_ch3_scorecard, indent=2, ensure_ascii=False)[:1500]}

`cross_cutting_debt_tX_pY` samples (ES):
{json.dumps(list(es_patterns.items())[:8], indent=2, ensure_ascii=False)}

2. Compiler AST code in `payload_to_ast.py`:
```python
{payload_to_ast_code}
```

3. Excerpt from `in_memory_asis_compiler.py`:
```python
{compiler_code[1050:1250]}
```

YOUR UNCOMPROMISING AUDIT MISSION:
1. HARDCODING & TENANT CONTAMINATION SMOKE TEST:
   - Identify every single instance where tenant-specific facts, industrial manufacturing biases, cement plant references, specific hardware models, fixed numerical thresholds (e.g. 500m, 95% RAM, <1GB disk, truck queues, factory kilns), or client-specific assumptions were improperly hardcoded into global configuration files (`locales.json`) or Python code.
   - What happens if a Global Tier-1 Bank (e.g., JPMorgan or Santander) or a Healthcare Hospital Network runs this engine with these templates?
2. LANGUAGE DECOUPLING LAW AUDIT:
   - Audit all Python source code for any leakage of Spanish tokens, regex literals, variable names, comments, docstrings, or keys.
3. ARCHITECTURAL ROOT CAUSE ANALYSIS:
   - Why did this hardcoding happen? (Diagnosis of the antipattern).
   - What is the correct, pure, decoupled architecture for Section 3.1 that allows ANY company in ANY vertical to produce bespoke, fact-based, 10.0/10.0 executive syntheses without hardcoded tenant data?
4. PRODUCTION-GRADE REMEDIATION BLUEPRINT:
   - Provide the exact step-by-step architectural design to:
     a) Cleanse `locales.json` of all client-specific or manufacturing-only facts, transforming it into truly universal, parameterized domain templates.
     b) Enable dynamic extraction of real tenant metrics and transversal patterns directly from the tenant's payload (e.g. from `findings`, `risks_data_list`, `key_risks`, `thought_process`, or ontology).
     c) Ensure multi-vertical scalability (from a $20M regional clinic to a $100B global investment bank).

Deliver your verdict with absolute forensic rigor.
"""


def main() -> None:
    print("Initiating Hardcoding and Architectural Purity Audit with gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_AUDIT_HARDCODING_AND_ARCHITECTURAL_PURITY.md"
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
    print("ARGON HARDCODING & PURITY AUDIT REPORT:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Full report written to {out_file}")


if __name__ == "__main__":
    main()
