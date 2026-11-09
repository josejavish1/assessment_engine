#!/usr/bin/env python3
"""Adversarial Audit by gemini-4-argon across RFC 084 Implementation (Phases 1, 2, and 3).

Examines:
1. src/assessment_engine/application/services/semantic_epistemic_router.py
2. src/assessment_engine/application/services/actuarial_inference_engine.py
3. src/assessment_engine/application/services/cross_tower_nexus.py
4. in_memory_asis_compiler.py (derive_in_memory_fair_risks integration)
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

# Load the source code of the three newly implemented services
router_code = (
    REPO_ROOT / "src/assessment_engine/application/services/semantic_epistemic_router.py"
).read_text(encoding="utf-8")

actuarial_code = (
    REPO_ROOT / "src/assessment_engine/application/services/actuarial_inference_engine.py"
).read_text(encoding="utf-8")

nexus_code = (
    REPO_ROOT / "src/assessment_engine/application/services/cross_tower_nexus.py"
).read_text(encoding="utf-8")

compiler_section = (
    REPO_ROOT / "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"
).read_text(encoding="utf-8")[475:680]

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)
print(f"Connecting to Reasoning model '{model_name}' for adversarial audit...")

audit_prompt = f"""You are 'gemini-4-argon', the Principal Staff Systems Architect, Security Auditor, and Actuarial Fellow.
Your task is to conduct an adversarial, rigorous, uncompromising audit of the newly implemented RFC 084 code.
Look for ANY bugs, edge cases, hardcoding, language leaks, or architectural antipatterns.

NON-NEGOTIABLE LAWS & EVALUATION CRITERIA:
1. LANGUAGE DECOUPLING LAW:
   - 100% Technical English in ALL Python code: identifiers, comments, docstrings, exceptions, logs, regex patterns, literals.
   - ZERO Spanish, Portuguese, or foreign words in code logic or internal models.
   - Target languages (e.g. Spanish, German, Japanese) are exclusively localized data strings in catalogs or serialized client payloads, NEVER in code.
2. ZERO HARDCODING & MULTI-TENANT UNIVERSALITY:
   - Must serve ANY enterprise worldwide from a $10M SMB to a $500B Global Tier-1 conglomerate.
   - Must support ANY industry vertical (banking, retail, manufacturing, healthcare, aerospace, fintech, public sector, energy, etc.).
   - No hardcoded client-specific context (e.g. Molins, Fairfly, specific vendors like Broadcom as mandatory keywords, hardcoded city/factory names, etc.).
   - Are taxonomy definitions and anchor terms loaded dynamically or cleanly decoupled?
3. MATHEMATICAL & ALGORITHMIC INTEGRITY:
   - FAIR & Bayesian calculations: Check LEF, SLE, ALE, and VaR90 formulas for division-by-zero, negative numbers, overflow, or rounding bugs.
   - DAG Acyclicity & Topological Sort: Check graph edge addition, cycle detection, and Kahn's algorithm invariants.
   - Unbounded Transcripts: Can the router handle 100,000 transcript turns without memory exhaustion or cubic time complexity?
4. ARCHITECTURAL PURITY & DDD / HEXAGONAL INVARIANTS:
   - Are domain entities immutable (frozen dataclasses)?
   - Are methods properly decoupled with Cyclomatic Complexity <= 10?
   - Are there hidden side-effects, mutable default arguments, or contract drifts?

---
CODE ARTIFACT 1: SemanticEpistemicRouter (src/assessment_engine/application/services/semantic_epistemic_router.py)
```python
{router_code}
```

---
CODE ARTIFACT 2: ActuarialInferenceEngine (src/assessment_engine/application/services/actuarial_inference_engine.py)
```python
{actuarial_code}
```

---
CODE ARTIFACT 3: CrossTowerNexusEngine (src/assessment_engine/application/services/cross_tower_nexus.py)
```python
{nexus_code}
```

---
CODE ARTIFACT 4: Compiler Derivation Integration (in_memory_asis_compiler.py)
```python
{compiler_section}
```

AUDIT REPORT REQUIREMENTS:
Structure your adversarial report with:
1. EXECUTIVE VERDICT: (PASS / CONDITIONAL PASS / FAIL)
2. LANGUAGE DECOUPLING AUDIT: Line-by-line check for any non-English tokens or comments.
3. HARDCODING & UNIVERSALITY AUDIT: Does any component assume a specific client, revenue bracket, currency, or vertical?
4. MATHEMATICAL & ALGORITHMIC AUDIT: Thorough stress-testing of FAIR calculations, DAG invariants, and scaling behavior.
5. CONCRETE CODE LEVEL DEFECTS & SURGICAL RECOMMENDATIONS: List exact lines and proposed surgical improvements.

Be relentlessly critical and forensic.
"""

response = client.models.generate_content(
    model=model_name,
    contents=audit_prompt,
)

audit_report = response.text
print("\n" + "=" * 80)
print("GEMINI-4-ARGON ADVERSARIAL AUDIT REPORT")
print("=" * 80)
print(audit_report)

# Save the audit report to docs/audits/
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
audit_file = REPO_ROOT / "docs/audits/ARGON_ADVERSARIAL_AUDIT_RFC084_PHASES_1_2_3.md"
audit_file.write_text(front_matter + audit_report, encoding="utf-8")
print(f"\n✓ Saved formal audit report to {audit_file.relative_to(REPO_ROOT)}")
