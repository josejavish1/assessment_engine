#!/usr/bin/env python3
"""Argon-4 Architectural Plan for 5 Visual and Structural Deliverable Defects.

Formulates an ironclad, zero-hardcoding RFC to resolve:
1. Cover Page Spurious Split (Page 2 empty).
2. Table of Contents: Native Word TOC widget & accurate dynamic pagination.
3. Duplicate Heading Numbering ('2. 1. Executive Summary') caused by template auto-numbering.
4. Pillar Name Key Mismatch in Table 3.2 ('Pillar' literal display).
5. Risk Card Header Codes ([RVS03] T1.P2.K1) -> Human-readable capability titles.
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


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    payload_to_ast_path = REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py"
    docx_compiler_path = REPO_ROOT / "src/assessment_engine/adapters/compilers/docx_compiler.py"

    p2ast_code = payload_to_ast_path.read_text(encoding="utf-8")
    docx_code = docx_compiler_path.read_text(encoding="utf-8")

    prompt = f"""
Role: Principal Systems Architect, Chief Compiler Engineer & Executive Editorial Director (Tier-1 Management Consulting / McKinsey / Gartner).

CONTEXT & PROBLEM STATEMENT:
A human-like visual forensic audit of the newly regenerated AS-IS deliverable Word/PDF documents for Molins (Tower 1 and Tower 2) revealed 5 visual and structural defects that degrade C-level executive polish:

1. DEFECT 1: COVER PAGE SPLIT ACROSS TWO PAGES (Page 2 nearly blank)
   - In `payload_to_ast.py` (`_build_cover_and_toc`), the subtitle 'Technical Annex: Physical Data Center...' is emitted as a `HeadingNode(level=1)`.
   - In `docx_compiler.py` (`_compile_heading`), every `level=1` heading triggers `p.paragraph_format.page_break_before = True`.
   - This pushes 'Technical Annex...' and 'Cliente: MOLINS' to Page 2, leaving Page 1 with only the main title and Page 2 with massive awkward white space, pushing the Table of Contents to Page 3!
   - Root Cause: A cover page subtitle is NOT an outline chapter heading; it should be styled as a Cover Subtitle paragraph without triggering chapter-level page breaks or outline entries.

2. DEFECT 2: TABLE OF CONTENTS NOT A NATIVE WORD TOC WIDGET & PAGE NUMBER DESYNCHRONIZATION
   - The user noticed: 'A parte de que por supuesto el índice no ha sido generado con una tabla de contenido'.
   - Currently, TOC is compiled as a series of normal text paragraphs with right-aligned tab stops.
   - Word users clicking on it see plain text—there is no interactive TOC container, no hyperlink to document targets, and no native Word 'Update Table' control.
   - Crucially, the static page numbers ('Pág. 3', 'Pág. 4', 'Pág. 6', 'Pág. 10', 'Pág. 18') are hardcoded in `locales.json` and completely desynchronized from the actual physical pages of the document (e.g., Chapter 1 physically begins on Page 4, not Page 3).

3. DEFECT 3: DUPLICATE CHAPTER NUMBERING ON HEADINGS ('2. 1. Resumen Ejecutivo')
   - In `docx_compiler.py`, headings are assigned template styles: `Heading 1`, `Heading 2`.
   - The corporate Word template (`tower_annex_template.docx`) already has Word multi-level list auto-numbering configured on `Heading 1` ('1.', '2.', '3.') and `Heading 2` ('1.1.', '1.2.', etc.).
   - Our code in `payload_to_ast.py` passes titles that ALREADY have numbers prepended in the string: '1. Resumen Ejecutivo', '2. Objetivo, Alcance...'.
   - When Word opens the file, Word appends its automatic style number in front of our string number, rendering:
     '2. 1. Resumen Ejecutivo y Tesis Estratégica'
     '3. 2. Objetivo, Alcance y Marco Metodológico'
     '3.1. 1. Objetivo y Alcance'

4. DEFECT 4: PILLAR NAMES IN SECTION 3.2 COLLAPSE TO LITERAL 'Pillar'
   - In Section 3.2 (Maturity Dashboard Table), the rows display:
     `Pillar | 1,70 | Crítico (F)`
     `Pillar | 2,30 | Básico (D)`
     ...
   - Root Cause: In `payload_to_ast.py` line 703, the loop reads `p.get('pillar_id')` and `p.get('pillar_name')`.
   - But in the synthesized JSON (`blueprint_t1_payload.json` / `blueprint_t2_payload.json`), the keys are spelled with a single 'l': `'pilar_id'` and `'pilar_name'`.
   - Both lookups return `None`, falling back to the default `'Pillar'`.

5. DEFECT 5: RISK CARD HEADERS DISPLAY RAW CODES ('[RVS03] T1.P2.K1')
   - In Chapter 4, the risk cards header displays: `[RVS03] T1.P2.K1` instead of resolving the actual human-readable capability name from the taxonomy catalog.
   - Root Cause: `hc.get('capability')` contains the raw KPI code `T1.P2.K1`, but `resolver.resolve_capability_name()` only looks up capability text in `_capabilities_index` without resolving KPI codes from `taxonomy_multilingual.json`.

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless design using clean architectural patterns.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - Must scale across any enterprise size (mid-market to Global Fortune 10).
   - Any industry vertical.
   - Any ISO 4217 currency.
   - Any ISO language (en, es, pt, fr, de, ja).
   - Zero hardcoded client names, zero fixed page numbers, zero hardcoded strings.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, class names, method signatures, variables, docstrings, and comments must be 100% Technical English.

RELEVANT CODE EXCERPTS:
payload_to_ast.py (Cover & TOC):
```python
{p2ast_code[320:1000]}
```

docx_compiler.py (Headings & TOC):
```python
{docx_code[700:900]}
```

YOUR TASK:
Emit a comprehensive architectural plan (RFC 028) in Markdown:
1. Provide exact, surgical designs for each of the 5 defects.
2. For Defect 1: Show the exact AST node and docx compiler styling to keep the Cover Page strictly on Page 1 without triggering a page break.
3. For Defect 2: Specify how to construct a true native Word Table of Contents field that Microsoft Word recognizes, updates, and clicks through, with zero schema errors and without requiring static hardcoded page numbers in locales.json.
4. For Defect 3: Explain how to cleanly strip or decouple manual numbering prefixes from heading strings before assigning Word's auto-numbered `Heading` styles.
5. For Defect 4: Provide the resilient dictionary lookup (`pillar_id` / `pilar_id`, `pillar_name` / `pilar_name`, `pillar_label` / `pilar_label`).
6. For Defect 5: Show the KPI-to-capability taxonomy lookup so risk card headers display rich, human-readable titles across all languages.
7. Include complete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 028 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_028_VISUAL_DEFECTS_REMEDIATION_PLAN_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 028 VISUAL DEFECTS REMEDIATION PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
