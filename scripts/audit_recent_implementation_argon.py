#!/usr/bin/env python3
"""Adversarial Audit by gemini-4-argon of recent Section 3.2 implementation and compiler changes."""

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

diff_res = subprocess.run(
    ["git", "diff", "origin/main", "--", "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py", "src/assessment_engine/adapters/compilers/payload_to_ast.py"],
    capture_output=True,
    text=True,
    cwd=REPO_ROOT,
)
git_diff = diff_res.stdout

# Read current in_memory_asis_compiler.py
compiler_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py").read_text(encoding="utf-8")
payload_to_ast_sec3 = (REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py").read_text(encoding="utf-8")[2000:2300]

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = f"""You are 'gemini-4-argon', the Principal Staff Security & Software Engineering Auditor.
You are tasked with conducting an adversarial, uncompromising audit of the recent compiler implementation.

CONTEXT & NON-NEGOTIABLE LAWS:
1. LANGUAGE DECOUPLING LAW: 100% Technical English in ALL Python code (identifiers, comments, docstrings, exceptions, logs, regex patterns, literals). ZERO Spanish words or phrases in .py files. All localized strings/lexemes MUST reside strictly in engine_config/locales.json.
2. ZERO HARDCODING & UNIVERSAL TENANT SCALABILITY: Must work seamlessly for ANY enterprise worldwide (from $20M SMB to $500B Global Tier-1), ANY vertical (banking, retail, manufacturing, healthcare, public sector), in ANY target locale (en, es, pt, fr, ja, de). No magic strings or hardcoded client context.
3. ALGORITHMIC & NUMERICAL INTEGRITY: No unhandled exceptions, zero-division hazards, off-by-one errors, or unintended variable shadowing.
4. COGNITIVE & EDITORIAL EXCELLENCE: Eliminates repetitive walls of text, ensures natural asymmetric paragraphing, and avoids template fatigue.

HERE IS THE RELEVANT COMPILER IMPLEMENTATION CODE TO AUDIT:
```python
{compiler_code[850:1220]}
```

AND HERE IS THE GIT DIFF:
```diff
{git_diff[:4000]}
```

YOUR MANDATE:
1. Scrutinize the code line-by-line for any violations of the Language Decoupling Law (look specifically at regex patterns, dictionaries, variable values, or helper functions that contain Spanish text).
2. Check for universal scaling and hardcoding bugs (does it assume Spanish? does it break on German or English? does it handle edge cases where there are 0 findings or 1 sentence?).
3. Identify any code smells, antipatterns, or algorithmic flaws in paragraph chunking or score enrouting.
4. Provide a concrete, prioritized list of defects found and the exact surgical fixes required to bring the code to 100% compliance.

Respond with extreme rigor and technical precision.
"""


def main() -> None:
    print("Initiating adversarial code audit with gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_ADVERSARIAL_IMPLEMENTATION_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("=" * 80)
    print("ARGON AUDIT REPORT:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Full audit report written to {out_file}")


if __name__ == "__main__":
    main()
