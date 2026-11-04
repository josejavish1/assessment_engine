#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 073 Exhaustive AS-IS Pipeline Forensic Audit.

Conducts an exhaustive, line-by-line adversarial audit of the entire AS-IS generation stack:
1. All 10 technical tower annexes (payload_to_ast.py, asis_*_chapter.py, render_tower_annex.py).
2. Consolidated Volume 1 (tomo_asis_ast_compiler.py, build_global_report_payload.py).
3. Configuration catalogs (engine_config/locales.json, locales_asis_annex.json).
4. Actuarial engines and currency scale models.

Enforces:
- Zero single-tenant bias or hidden hardcoding (names, locations, dates, equipment, formulas).
- Universal multi-tenant scalability (mid-market $10M to Top Tier-1 $100B, any vertical, any currency, any language).
- 100% Technical English codebase, symbols, docstrings, and comments.
- Zero split-brain across compilers and data schemas.
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
    get_fallback_model,
    get_model,
)


def read_snippet(path: Path, max_lines: int = 150) -> str:
    if not path.exists():
        return f"[File {path.name} not found]"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[:max_lines])


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    payload_to_ast_snippet = read_snippet(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/payload_to_ast.py", 200
    )
    tomo_compiler_snippet = read_snippet(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py", 200
    )
    fair_chapter_snippet = read_snippet(
        REPO_ROOT / "src/assessment_engine/adapters/compilers/asis_fair_chapter.py", 150
    )
    global_payload_builder_snippet = read_snippet(
        REPO_ROOT / "src/assessment_engine/application/build_global_report_payload.py", 150
    )

    prompt = f"""
Role: Principal Global Systems Architect, Chief Quality Gatekeeper, and Distinguished Enterprise Auditor (Tier-1 Advisory: Google Cloud / Gartner Fellow / McKinsey Partner).

MISSION OBJECTIVE:
Conduct an uncompromising, exhaustive adversarial audit of the entire AS-IS assessment generation pipeline across BOTH individual tower annexes (T1 through TN) and the consolidated Volume 1 report (Tomo 1 AS-IS). 

The platform user is deeply concerned that subtle biases, implicit hardcodings, hidden assumptions, or architectural split-brains from the initial prototype client ("Molins") might remain buried in the codebase. When an entirely different enterprise arrives tomorrow—whether a regional hospital in Stockholm, a megabank in Tokyo, a public transit network in London, or a retail giant in Chicago—the engine must operate flawlessly with ZERO single-tenant bias, ZERO bugs, and MAXIMUM deliverable quality.

MANDATORY LAWS UNDER REVIEW:
1. Universal Multi-Tenancy & Zero Hardcoding:
   - The platform MUST serve ANY enterprise in the world:
     * Revenue scale: $10M mid-market to $100B Global Fortune 500.
     * Industry vertical: Banking/Insurance (DORA, Basel III), Healthcare (HIPAA, HITRUST), Retail/Logistics (PCI-DSS), Critical Infrastructure/Manufacturing (NIS2, IEC 62443), Public Sector.
     * Currency & Scale: USD ($), EUR (€), JPY (¥), GBP (£), CHF (Fr.). Non-decimal currencies (JPY) and large integers must never suffer from hardcoded default scale assumptions (e.g. defaulting to 100,000,000 in JPY).
     * Language: English, Spanish, Portuguese, French, German, Japanese.
   - Zero hardcoded client names, subsidiaries, plant locations, specific hardware models, vendor renewal dates (e.g. May 2027), or industrial manufacturing processes (e.g. weighbridges, bagging lines).
2. Dynamic N-Domain Polymorphism:
   - No unconditional assumption of exactly 10 towers (T1..T10). If an enterprise contracts 3 towers (e.g. Cloud, Cyber, Data) or uses custom alphanumeric identifiers (e.g. SEC-01, PLAT-02), the pipeline must gracefully compile with ZERO phantom towers or artificial fallback pollution.
3. 100% Technical English Codebase:
   - Absolute prohibition of Spanish words in Python code, class names, method signatures, variables, docstrings, comments, log messages, or test files. Spanish is strictly an external delivery translation target in `engine_config/locales.json`.
4. Pure SSOT & Zero Split-Brain:
   - Compilers must bind 100% dynamically to live data payloads (`tower_payloads`, `global_payload`). Static localization catalogs must only supply generic linguistic framing with dynamic tokens (`{{client_name}}`, `{{facility_scope}}`), never static inventory or fake findings.

CODE ARTIFACTS UNDER AUDIT (SAMPLE RELEVANT EXCERPTS):

--- COMPONENT 1: Per-Tower AST Engine (`payload_to_ast.py`) ---
{payload_to_ast_snippet}

--- COMPONENT 2: Consolidated Volume 1 AST Compiler (`tomo_asis_ast_compiler.py`) ---
{tomo_compiler_snippet}

--- COMPONENT 3: FAIR Risk Quantitative Matrix (`asis_fair_chapter.py`) ---
{fair_chapter_snippet}

--- COMPONENT 4: Global Payload Aggregator (`build_global_report_payload.py`) ---
{global_payload_builder_snippet}

REQUIRED DELIVERABLE STRUCTURE (RFC 073):
Deliver a comprehensive, production-grade architectural audit report structured as follows:

1. Executive Verdict & Risk Heatmap:
   - Overall Architectural Purity Score (0 to 10).
   - High-level risk assessment of the entire AS-IS pipeline across all 10 capability domains and the consolidated volume.
2. Exhaustive Forensic Finding Log (Categorized by Critical, High, Medium, Low):
   - For every finding: cite exact file path, line numbers/functions, root cause, and concrete failure scenario on a non-manufacturing tenant (e.g. a hospital or bank).
   - Scrutinize:
     * Catalog pollution or hidden literals.
     * Silent parametric revenue/downtime fallbacks and currency misscaling.
     * Rigid 10-tower loops or legacy hardcoded regexes (e.g. `^T(10|[1-9])$`).
     * Residual Spanish identifiers (e.g. `tomo`, `tarifas_hora`, `tecnico_medio`).
     * Thread-safety risks (e.g. shared state in matplotlib chart generation).
3. The Definitive Elimination Plan:
   - Step-by-step technical blueprints for eradicating each identified defect.
   - Exact Python implementation guidelines in 100% Technical English.
4. Universal Multi-Tenant Certification Checklist:
   - Formal verification criteria to empirically prove that any enterprise in the world will receive a 100% tailored, bias-free, board-grade assessment.
"""

    print(f"Submitting RFC 073 full AS-IS audit prompt to {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
    except Exception as e:
        print(f"Error querying primary model {model_name}: {e}")
        fallback = get_fallback_model(model_name)
        if fallback:
            print(f"Falling back to {fallback}...")
            response = client.models.generate_content(
                model=fallback,
                contents=prompt,
            )
        else:
            raise

    out_file = REPO_ROOT / "docs/architecture/RFC_073_EXHAUSTIVE_FULL_ASIS_AUDIT_AND_PURITY_BLUEPRINT_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("RFC 073 EXHAUSTIVE AS-IS AUDIT GENERATED SUCCESSFULLY")
    print("=" * 80)
    print(f"Output saved to: {out_file.relative_to(REPO_ROOT)} ({len(response.text):,} characters)")


if __name__ == "__main__":
    main()
