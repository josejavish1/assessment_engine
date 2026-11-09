#!/usr/bin/env python3
"""Adversarial Architectural and Anti-Pattern Audit by gemini-4-argon.

Evaluates recent codebase changes, identifies hardcoding anti-patterns,
and formulates the definitive multi-phase blueprint for universal enterprise delivery.
"""

from __future__ import annotations

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

# 1. Read the newly created build_client_delivery_suite.py
delivery_script_path = REPO_ROOT / "scripts/build_client_delivery_suite.py"
delivery_script_code = delivery_script_path.read_text(encoding="utf-8") if delivery_script_path.exists() else ""

# 2. Read git diff of modified src files to capture exact recent edits
git_diff_file = REPO_ROOT / "docs/architecture/ARGON_DEEP_AUDIT_HARDCODING_AND_LANGUAGE_PURITY.md"

# 3. Read excerpts of recent changes in tomo_asis_ast_compiler.py, localization.py, config_loader.py
compiler_path = REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py"
compiler_code = compiler_path.read_text(encoding="utf-8")
compiler_snippet = compiler_code[2320:2450] if len(compiler_code) > 2450 else compiler_code[:1000]

localization_path = REPO_ROOT / "src/assessment_engine/infrastructure/localization.py"
localization_code = localization_path.read_text(encoding="utf-8")
loc_snippet = localization_code[180:230] if len(localization_code) > 230 else localization_code[:500]

# 4. Check locales.json for residual tenant-specific catalog text
locales_path = REPO_ROOT / "engine_config/locales.json"
locales_data = json.loads(locales_path.read_text(encoding="utf-8"))
en_catalog_t10 = locales_data.get("en", {}).get("tomo_tower_forensic_catalog", {}).get("T10", {})

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Principal Enterprise Architect, Chief Cybersecurity Auditor, and Supreme Code Quality Arbiter for the Assessment Engine.

CRITICAL USER MANDATE & ALERT:
The user has stopped the execution after catching a severe anti-pattern:
"What are you doing hardcoding things in build_client_delivery_suite.py? Isn't what you just did an anti-pattern? That is NOT how it should work! Our premise before writing code is: we must think deeply about how we approach it and in how many phases to guarantee zero bugs, zero anti-patterns, and world-class Tier-1 quality for ANY company in the world (from a $20M SMB to a $500B global multinational, across ANY vertical, in ANY language), with 100% Technical English code without a single word of Spanish. I have the feeling you are touching too many things and breaking things. Before continuing, I want gemini-4-argon to do a complete, adversarial audit of what was recently coded, uncover all bugs, problems, or anti-patterns, and design the definitive, bug-free, zero-hardcoding architectural plan."

EVIDENCE UNDER AUDIT:

1. ANTI-PATTERN IN `scripts/build_client_delivery_suite.py`:
Examine how the author handled domain profiles:
```python
{delivery_script_code[4500:5800]}
```
Notice: `if "Starling" in client_name:` with bespoke text blocks for T1, T3, T5, T6, T8, T10!

2. CHANGES IN `tomo_asis_ast_compiler.py` (Subpillar resolution):
```python
{compiler_snippet}
```

3. RESIDUAL TEXT IN `engine_config/locales.json` (`tomo_tower_forensic_catalog.T10`):
```json
{json.dumps(en_catalog_t10, indent=2)[:800]}
```
Notice the cement plant weighbridge terminology residing in global config!

4. CURRENT GIT STATUS OF TOUCHED FILES:
- `scripts/build_client_delivery_suite.py` (New deliverable builder)
- `scripts/build_synthetic_control_fixture.py` (5 synthetic benchmark clients: UK Starling Bank, BR Rede D'Or, FR Geodis, MX Chedraui, US Datadog)
- `src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py` (Subpillar precedence adjustment)
- `src/assessment_engine/infrastructure/localization.py` (Currency formatting enhancement)
- `src/assessment_engine/infrastructure/config_loader.py` (Industry profile normalization)
- `tests/functional/test_synthetic_control_delivery.py` (21 functional tests)

YOUR UNCOMPROMISING AUDIT MISSION:

SECTION 1: FORENSIC CODE REVIEW & ANTI-PATTERN DISSECTION
- Brutally analyze the `if "Starling" in client_name:` antipattern in `scripts/build_client_delivery_suite.py`. Why is this a catastrophic architectural smell?
- Identify any other hacks, shortcuts, or fragile assumptions introduced in the recent changes.
- Check if anything in the existing production code or regression tests was broken or corrupted.

SECTION 2: RESIDUAL HARDCODING IN THE BASELINE
- Explain why `tomo_tower_forensic_catalog` in `locales.json` contains industrial cement/weighbridge text.
- Why did the AST compiler fall back to this text?
- How should static fallback catalogs be cleansed so they are truly generic and parameterized without tenant bias?

SECTION 3: TARGET UNIVERSAL ARCHITECTURE FOR ARTIFACT GENERATION
- How MUST the assessment engine pipeline ingest raw inputs (transcription .docx + assessment_responses.txt) and generate the full deliverable suite (Tomo 1 AS-IS DOCX + Specialist Annexes) for ANY company in the world WITHOUT ANY hardcoding?
- What is the exact data contract between:
  a) Raw evidence (transcripts & responses)
  b) AI Intelligence harvesting / evidence ledger (`evidence_vault.json`, `raptor_tree.json`)
  c) Actuarial FAIR / Monte Carlo policy engine (`policy_engine.py`)
  d) Tower payload hydrator / blueprint generator (`blueprint_{{tower}}_payload.json`)
  e) Declarative AST Document Compiler (`tomo_asis_ast_compiler.py` -> DOCX)

SECTION 4: DEFINITIVE MULTI-PHASE MASTER REMEDIATION PLAN
- Provide a rigorous, phased roadmap (Phase 1, Phase 2, Phase 3...) detailing:
  - Exact files to refactor or cleanse.
  - How to eliminate `if client_name == ...` forever.
  - How to ensure 100% Technical English codebase adhering to the Language Decoupling Law.
  - How to certify that the 5 benchmark clients (Starling Bank, Rede D'Or, Geodis, Chedraui, Datadog) compile with 10.0/10.0 perfection without a single line of client-specific code in the engine.

Deliver your verdict with absolute technical authority, zero sugarcoating, and staff-principal engineering depth.
"""

def main() -> None:
    print(f"Submitting uncompromising audit request to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    audit_report = response.text
    out_file = REPO_ROOT / "docs/audits/ARGON_ADVERSARIAL_HARDCODING_AND_ARCHITECTURE_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(audit_report, encoding="utf-8")
    print(f"\nAudit completed successfully. Report written to: {out_file}\n")
    print("=" * 80)
    print(audit_report[:3000])
    print("\n... [Report Truncated for CLI Display. See full document in docs/audits/] ...\n")

if __name__ == "__main__":
    main()
