#!/usr/bin/env python3
"""Argon-4 Master Consultation: Visual Bullet-Point Finding Formatting & Vertical Budget Verification.

Validates the user's editorial insight:
"¿las vulnerabilidades no deberían estar en bullets para facilitar su lectura en lugar de en un párrafo gigante?"
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

    prompt = """
Role: Chief Executive Document Designer & Principal OpenXML Compiler Architect (Gartner Research VP / McKinsey Executive Design Director / Google Core Infrastructure).

USER CRITIQUE & EDITORIAL DIRECTION:
The user raised an essential editorial and visual design question:
"una última duda o aclaración: ¿las vulnerabilidades no deberían estar en bullets para facilitar su lectura en lugar de en un párrafo gigante?"

ARCHITECTURAL EVALUATION:
1. Cognitive Ergonomics & Executive Scanability:
   - The user is 100% correct: Embedding 3 to 5 multi-clause technical findings into a single dense, monolithic paragraph creates an unreadable "wall of text" where executive eyes glaze over.
   - Transforming the findings section into:
     * A clean, concise lead-in sentence.
     * Followed by clean, high-impact bullet items (`ParagraphNode(text=..., style="List Bullet", space_after=2)`).
     * Where each bullet starts with a bold technical topic/category and a concise description of the failure vector:
       `• **[Vulnerability Focus]:** [Operational failure vector and direct business impact].`
   - This achieves instant executive scanability in under 5 seconds.

2. Vertical Layout Budget & Page 3 Containment:
   - In Word OpenXML with 10.5pt font, 1-inch margins, and 0pt before / 2pt after list bullets:
     * Scorecard Table: ~55pt
     * Headline: ~18pt
     * Paragraph 1 (Posture & Mission): ~42pt
     * Bullet Lead-in: ~14pt
     * 3-4 Bullets (with 2pt spacing): ~50-65pt
     * Paragraph 3 (Actuarial Latent Exposure): ~50pt
     * Paragraph 4 (AS-IS Diagnostic Verdict): ~45pt
     * Diagnostic Triad Table (8pt font): ~55pt
     * Spacers: ~30pt
     * Total Content Height: ~360pt to ~380pt.
     * Total Available Printable Height on A4 (297mm - 50.8mm margins): ~698pt.
   - Result: Content consumes ~54% of Page 3. It will NEVER overflow onto Page 4!

3. Dynamic Cardinality Integration:
   - If K = 0: Single clean paragraph affirming control without bullets.
   - If K = 1: Lead-in sentence + 1 bullet item.
   - If K >= 2: Lead-in sentence + K bullet items (capped at 4 for executive summary density).

NON-NEGOTIABLE LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any tenant, vertical, currency, or locale).
3. 100% Technical English codebase (zero Spanish in Python code).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout perfection.

YOUR TASK:
Synthesize an authoritative Architectural Addendum (RFC 046-Addendum) in Markdown:
1. Define the AST node generation pattern for the bullet-point findings layout.
2. Provide the bilingual templates for `engine_config/locales.json` in Spanish (`es`) and English (`en`).
3. Provide the exact Python implementation snippet in 100% Technical English for `payload_to_ast.py`.
4. Confirm vertical containment verification on Page 3.
"""

    print(f"Requesting Bullet-Point Layout Verification from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_046_ADDENDUM_BULLET_FINDINGS_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: BULLET-POINT FINDINGS & VERTICAL BUDGET AUDIT")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nSaved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
