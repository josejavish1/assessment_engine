#!/usr/bin/env python3
"""Run an adversarial code and anti-pattern audit with Gemini-4-Argon across server.py and ExecutiveFastAssessmentJourney.tsx."""

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

server_py_path = REPO_ROOT / "server.py"
frontend_tsx_path = REPO_ROOT / "web" / "src" / "components" / "ExecutiveFastAssessmentJourney.tsx"

server_content = server_py_path.read_text(encoding="utf-8")
frontend_content = frontend_tsx_path.read_text(encoding="utf-8")

AUDIT_PROMPT = f"""You are 'gemini-4-argon', Supreme Cognitive Arbiter, Chief Quality Officer, and Master of Software Integrity.

USER DIRECTIVE & RIGID CONSTRAINTS:
"Antes de continuar, quiero que le digas a gemini-4-argon que haga una revisión completa de lo que acabas de programar y busque bugs, problemas o antipatrones, no quiero nada hardcodeado recuerda que el objetivo es que sirva para cualquier empresa del mundo desde mediana a top tier 1 mundial, de cualquier vertical, en cualquier idioma, y el código debe estar 100% en ingles nada de español ni una sola palabra, el español solo es el idioma que hablamos tu y yo y uno de los idiomas de la salida de los entregables."

YOUR MISSION:
Perform a ruthless, adversarial forensic code audit of our two primary active files:
1. `server.py`
2. `web/src/components/ExecutiveFastAssessmentJourney.tsx`

You must audit against four non-negotiable vectors:

### VIRTUE 1: ZERO HARDCODING & TRUE UNIVERSAL MULTI-TENANCY
- Hunt down any hardcoded customer or enterprise names (e.g. `if "molins" in email`, `if "starling" in raw`, `if "rededor"` in Python).
- Hunt down inline frontend ternary switches (e.g. `context.country === 'ES' && currentLocale === 'es' ? 'España' : ...` or `context.industry === 'heavy_manufacturing' ? ...`).
- Hunt down hardcoded fallback strings for regulatory frameworks (e.g. `: 'Directiva NIS2 · Directiva CER · RGPD' : 'DORA · NIS2 · RGPD'`).
- Explain why these break when a mid-sized firm in Poland, Germany, Japan, Egypt, or the US enters, and prescribe the universal, declarative architectural pattern to replace them.

### VIRTUE 2: 100% TECHNICAL ENGLISH CODEBASE POLICY (LANGUAGE DECOUPLING)
- Hunt down every single occurrence of Spanish words inside:
  - Python files (comments, variable names, default dicts, exception strings).
  - TypeScript / TSX files (inline strings, JSX text that is not wrapped in `t()`, comments, variable names, interface fields).
- Ensure that Spanish ONLY exists as translation data values inside `engine_config/locales_ui.json` and client deliverable documents.

### VIRTUE 3: DATA INTEGRITY & REGULATORY ONTOLOGY
- Audit how `regulatory_jurisdictions.json` is resolved in `server.py`.
- Identify edge cases: what if a country or industry code is unknown? What if an enterprise operates in a jurisdiction not in the map?
- How should the backend generically extract entity name, jurisdiction, currency, and sector from ANY corporate email domain without a hardcoded if-chain? (e.g. parsing MX/WHOIS/DNS/TLD/heuristics or extensible declarative registry `engine_config/enterprise_registry.json`).

### VIRTUE 4: ARCHITECTURAL PURITY & ROBUSTNESS
- Check for race conditions, broken states, unhandled exceptions, and dead code in both backend and frontend.
- Check Playwright test defensibility.

---
### CODE UNDER AUDIT: `server.py` (Excerpts around auth and resolve_context):
```python
{server_content[5000:15000]}
```

---
### CODE UNDER AUDIT: `web/src/components/ExecutiveFastAssessmentJourney.tsx` (Excerpts around Tab 1, Tab 2, and readouts):
```tsx
{frontend_content[15000:26000]}
```

Provide a structured, ruthless, line-by-line audit report followed by concrete, actionable refactoring code specifications.
Respond in 100% Technical English with supreme precision.
"""

def main() -> None:
    print(f"Submitting Adversarial Code Audit to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=AUDIT_PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_ADVERSARIAL_CODE_AND_ANTIPATTERN_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")
    print(f"Adversarial Audit successfully generated and saved to: {out_file}")
    print("\n--- FIRST 60 LINES OF ARGON AUDIT REPORT ---")
    print("\n".join(report.splitlines()[:60]))

if __name__ == "__main__":
    main()
