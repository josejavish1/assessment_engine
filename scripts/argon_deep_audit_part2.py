#!/usr/bin/env python3
"""Part 2 Deep Audit by gemini-4-argon: Inspecting chunking, transitions, demonstratives, and Language Decoupling."""

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

compiler_code = (REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py").read_text(encoding="utf-8")
chunk_to_audit = compiler_code[850:1255]

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

AUDIT_PROMPT = f"""You are 'gemini-4-argon', the Principal Staff Security & Software Engineering Auditor.
Audit the following implementation in `src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py`:

```python
{chunk_to_audit}
```

NON-NEGOTIABLE CORE LAWS:
1. LANGUAGE DECOUPLING LAW:
   - 100% Technical English in Python code (no Spanish literals, comments, docstrings, regex patterns, or string keys).
   - Look specifically at `_TRANSITION_MARKERS_RE` and `demonstrative_article_map`! Are there hardcoded Spanish phrases/words in Python code? If so, why is this an antipattern and how should they be moved to `engine_config/locales.json`?
2. ZERO HARDCODING & MULTI-LOCALE SUPPORT:
   - Does `_chunk_monolithic_paragraph` work for Japanese, German, Portuguese, French, and English?
   - In Japanese there are no spaces (`word.split()` fails if text has no spaces!). How should word/character counting behave for CJK (Chinese, Japanese, Korean) vs space-separated alphabets?
   - How does `demonstrative_article_map` behave for languages without grammatical gender (e.g. English "the", Japanese where articles don't exist)?
3. NUMERICAL & CONTROL FLOW INTEGRITY:
   - In `derive_in_memory_maturity_matrix`, how are `max_delta` and `min_score` calculated? Can an empty `pillars_analysis` cause an unhandled crash or invalid min_score = 5.0?
   - Is `hammer_para` replacement safe if `arch_paras` is empty?

Provide:
1. Explicit defect breakdown with Severity.
2. Exact, production-grade Python code replacements adhering to 100% Technical English and clean architecture.
"""


def main() -> None:
    print("Initiating Part 2 deep audit with gemini-4-argon...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )

    out_file = REPO_ROOT / "docs/audits/ARGON_ADVERSARIAL_IMPLEMENTATION_AUDIT_PART2.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("=" * 80)
    print("ARGON PART 2 AUDIT REPORT:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"Full audit report written to {out_file}")


if __name__ == "__main__":
    main()
