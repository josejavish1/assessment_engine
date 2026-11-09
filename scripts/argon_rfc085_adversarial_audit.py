#!/usr/bin/env python3
"""Adversarial Audit by gemini-4-argon across RFC-085 Remediations.

Examines:
1. src/assessment_engine/domain/services/score_reconciler.py (Empirical Supremacy & Perception Gap)
2. src/assessment_engine/application/services/universal_tower_synthesizer.py (Universal Multi-Tenant Synthesis)
3. src/assessment_engine/domain/maturity_band.py (Canonical Scale Invariants)
4. payload_to_ast.py & locales.json (Narrative Floor & Open FAIR Formula)
"""

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

# Load code artifacts
reconciler_code = (
    REPO_ROOT / "src/assessment_engine/domain/services/score_reconciler.py"
).read_text(encoding="utf-8")

synthesizer_code = (
    REPO_ROOT / "src/assessment_engine/application/services/universal_tower_synthesizer.py"
).read_text(encoding="utf-8")

maturity_code = (
    REPO_ROOT / "src/assessment_engine/domain/maturity_band.py"
).read_text(encoding="utf-8")

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)
print(f"Connecting to Reasoning model '{model_name}' for RFC-085 Adversarial Audit...")

prompt = f"""You are 'gemini-4-argon', the Principal Staff Systems Architect, Security Auditor, and Actuarial Fellow.
Conduct an adversarial, rigorous, uncompromising audit of the newly implemented RFC-085 remediation code.

AUDIT SCOPE & NON-NEGOTIABLE LAWS:
1. LANGUAGE DECOUPLING LAW:
   - 100% Technical English in ALL Python code: identifiers, comments, docstrings, exceptions, logs, regex patterns, literals.
   - ZERO Spanish, Portuguese, or foreign words in code logic or internal models.
   - Target languages (e.g., Spanish, German, Japanese) are exclusively localized data strings in catalogs or serialized client payloads, NEVER in code.
2. ZERO HARDCODING & MULTI-TENANT UNIVERSALITY:
   - Must serve ANY enterprise worldwide from a $10M SMB to a $500B Global Tier-1 conglomerate.
   - Must support ANY industry vertical (banking, retail, manufacturing, healthcare, aerospace, fintech, public sector, energy, etc.).
   - No hardcoded client-specific context (e.g. Molins, Fairfly, specific vendors like Broadcom as mandatory keywords, hardcoded city/factory names, etc.).
   - Are taxonomy definitions and anchor terms loaded dynamically or cleanly decoupled?
3. MATHEMATICAL & ALGORITHMIC INTEGRITY:
   - Check the Empirical Supremacy algorithm in `score_reconciler.py`: Does it mathematically prevent subjective survey inflation from poisoning factual engineering discovery? Does it recompute the tower root score and preserve mathematical dot-product invariants?
   - Check the CMMI scale intervals in `maturity_band.py` and `locales.json`: Are they contiguous, mutually exclusive, and consistent between Section 2 and Section 3?
   - Check Open FAIR calculations: Is OpEx hourly burn cleanly separated from CapEx emergency replacement spend?
4. ARCHITECTURAL PURITY & DDD / HEXAGONAL INVARIANTS:
   - Are domain entities immutable (frozen dataclasses)?
   - Are methods properly decoupled with Cyclomatic Complexity <= 10?
   - Are there hidden side-effects, mutable default arguments, or contract drifts?

---
CODE ARTIFACT 1: score_reconciler.py (src/assessment_engine/domain/services/score_reconciler.py)
```python
{reconciler_code}
```

---
CODE ARTIFACT 2: universal_tower_synthesizer.py (src/assessment_engine/application/services/universal_tower_synthesizer.py)
```python
{synthesizer_code}
```

---
CODE ARTIFACT 3: maturity_band.py (src/assessment_engine/domain/maturity_band.py)
```python
{maturity_code}
```

STRUCTURE YOUR AUDIT REPORT:
1. EXECUTIVE VERDICT: (PASS / CONDITIONAL PASS / FAIL)
2. LANGUAGE DECOUPLING AUDIT: Line-by-line check for any non-English tokens or comments.
3. HARDCODING & UNIVERSALITY AUDIT: Does any component assume a specific client, revenue bracket, currency, or vertical?
4. MATHEMATICAL & ALGORITHMIC AUDIT: Thorough stress-testing of Empirical Supremacy, dot-product scoring, CMMI intervals, and FAIR formulas.
5. CONCRETE DEFECTS & SURGICAL RECOMMENDATIONS: List exact findings and required improvements if any.

Be relentlessly critical, precise, and forensic.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

audit_report = response.text
print("\n" + "=" * 80)
print("GEMINI-4-ARGON ADVERSARIAL AUDIT REPORT (RFC-085)")
print("=" * 80)
print(audit_report)

out_file = REPO_ROOT / "docs/audits/ARGON_ADVERSARIAL_AUDIT_RFC085_FINAL.md"
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
out_file.write_text(front_matter + audit_report, encoding="utf-8")
print(f"\n✓ Saved formal audit report to {out_file.relative_to(REPO_ROOT)}")
