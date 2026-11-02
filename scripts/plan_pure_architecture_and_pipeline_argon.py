#!/usr/bin/env python3
"""Argon-4 Consultation: Pure Pipeline Architecture, Elimination of Secondary Template Anti-Patterns, and Zero-Hardcoding Lexical Governance (RFC 033)."""

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
Role: Principal Systems Architect, Chief Compiler Engineer & Executive Editorial Director (Google Tier-1 / Anthropic Core Infrastructure).

USER'S CRITICAL DIALECTICAL CHALLENGE:
The user raised two fundamental architectural objections:
1. "pero una duda, porque mantenemos (approved_annex_t2.template_payload.json) no es un antipatrón? creí que todas las torres tenian el mismo core."
   - Why do we have separate `approved_annex_{tower}.template_payload.json` files alongside `blueprint_{tower}_payload.json`?
   - Is splitting the pipeline between a "blueprint payload" and an "approved annex template payload" a split-brain anti-pattern?
   - Shouldn't there be a SINGLE canonical payload contract per tower (`EnrichedTowerPayload` / `blueprint_{tower}_payload.json`) that contains all necessary data for rendering, so that all towers (T1 through T10) share the exact same core pipeline without juggling secondary artifact files?
   - Moreover, manually editing or patching a JSON artifact on disk (`approved_annex_t2.template_payload.json`) is a non-reproducible manual hack that fails for any other client or when the pipeline is regenerated.

2. "no tengo claro que esta sea la mejor solución 'Supresión Definitiva de \"Fabril\":'"
   - Is embedding hardcoded Python regexes like `re.sub(r"\\bfabril\\b", "de planta", ...)` inside the document compiler (`payload_to_ast.py`) an anti-pattern?
   - YES: In a universal engine designed for any enterprise (from a hospital to an investment bank or pharmaceutical company in any country), hardcoding Spanish words like "fabril" in Python compiler code is hardcoded domain leakage!
   - How should lexical tone and natural register be governed properly, purely, and universally without hardcoding language-specific regexes in Python code?

3. SINGLE-PAGE EXECUTIVE SUMMARY ARCHITECTURE:
   - The user explicitly requested:
     a) Keep ONLY the main heading "1. Resumen Ejecutivo" (remove subheadings 1.1 and 1.2, and remove the separate financial table).
     b) Embed a transparent, credible justification for the CIO directly into the narrative prose of Page 1 explaining where the financial figures come from (e.g. Expected Annual Loss [ALE] calculated from quantified failure frequencies across evaluated risks multiplied by the hourly downtime cost of 10,000 €/h, versus the P90 tail risk representing severe concurrent outages during peak operational/dispatch windows).
     c) Render the Executive Scorecard Table and the Executive Diagnostic Triad Table (Strength, Gap, Bottleneck) cleanly on Page 1, followed by a Page Break.

NON-NEGOTIABLE LAWS:
1. ZERO BUGS, ZERO ANTI-PATTERNS: Flawless architectural design.
2. ZERO HARDCODING (UNIVERSAL GLOBAL ENTERPRISE READINESS):
   - The engine must scale to ANY company in the world: mid-market to Global Fortune 10, across any vertical (finance, healthcare, retail, manufacturing, SaaS), in any currency and language.
   - Zero hardcoded client names, zero hardcoded domain regexes, zero hardcoded words in Python code.
3. 100% TECHNICAL ENGLISH CODEBASE:
   - All Python code, method names, variables, and docstrings must be 100% Technical English.

YOUR TASK:
Emit a comprehensive architectural plan (RFC 033) in Markdown:
1. Deep architectural analysis of the `approved_annex_*.template_payload.json` artifact: Explain why maintaining two separate JSON payloads is an anti-pattern, and how to unify the pipeline so that `EnrichedTowerPayload` (the single 21-key contract) is the ONLY source of truth consumed by `payload_to_ast.py`.
2. Analysis of the "fabril" regex anti-pattern: Explain why regex word-patching in Python compiler code violates architectural purity, and specify the pure upstream solution (neutral prompt engineering in `annex_executive_synthesizer.yaml` and dynamic parameterization).
3. The definitive single-heading Chapter 1 AST compiler implementation (zero subheadings, inline CIO financial justification, scorecard table, triad table, and clean page break).
4. Concrete, production-ready Python code snippets in 100% Technical English.
"""

    print(f"Requesting RFC 033 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_033_PURE_PIPELINE_UNIFICATION_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 033 ARCHITECTURAL PLAN")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nPlan saved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
