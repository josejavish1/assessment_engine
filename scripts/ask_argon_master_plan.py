#!/usr/bin/env python3
"""
Invoke gemini-4-argon to architect the Global Tier-1 Multi-Phase Master Plan.
Prompt is 100% in Technical English, requesting an unsparing, exhaustive architectural blueprint.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def generate_argon_master_plan() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: GLOBAL TIER-1 MULTI-PHASE MASTER PLAN")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    prompt = """
You are Gemini-4-Argon, the Principal Systems Architect and Actuarial Fellow overseeing the autonomous evolution of the Enterprise Assessment Engine.

CONTEXT & STRATEGIC MISSION:
The Assessment Engine generates comprehensive, executive-grade IT Infrastructure and Architecture Due Diligence reports (Consolidated Master Volume + 10 Specialist Domain Annexes) for enterprise clients worldwide.
The user mandates that this engine must become the absolute GLOBAL #1 TIER-1 SOLUTION IN THE WORLD — surpassing McKinsey, Gartner, Bain, and Big-4 technical due diligence in depth, mathematical rigor, aesthetic design, and zero-hallucination accuracy.
It must operate universally across:
1. Any Industry Vertical (Manufacturing, Banking & Capital Markets, Healthcare & Life Sciences, Retail & E-Commerce, Energy & Utilities, Telecommunications, SaaS & Digital Native, Public Sector).
2. Any Scale (from Mid-Market $50M revenue to Fortune 10 Global Conglomerates $100B+).
3. Any Target Deliverable Language (starting with English, Spanish, Portuguese, German, French, Japanese) without data drift or linguistic leaks.

NON-NEGOTIABLE CORE ARCHITECTURAL INVARIANTS:
1. 100% Technical English Codebase: Zero Spanish in code, variables, function signatures, docstrings, comments, log messages, schemas, prompts, or test cases. Spanish and other target languages exist strictly as externalized localized data (e.g. in `engine_config/locales.json`).
2. Zero Hardcoding: Absolutely no hardcoded company names, brand profiles, country mappings, statutory laws, or synthetic metrics in Python source code. All configuration must be declarative, catalog-driven, and loaded from externalized JSON/YAML schemas.
3. Zero Workarounds / Clean Architecture: No presentation-layer regex hacks or ad-hoc formatters to clean upstream data. Clean Hexagonal / Ports & Adapters architecture: Domain -> Application -> Adapters -> Compilers. Fix the baseline at rest.
4. Absolute Empirical Orthodoxy: Pure distinction between client-verified empirical facts and derived actuarial estimates. Zero synthetic patch versions (e.g., no fabricated 'Update 3') and zero unverified ratios.
5. Strict SSOT Mathematical Consistency: Complete actuarial alignment between executive summaries (Scorecard Page 3) and quantitative risk assessments (Open FAIR Chapter 4 ALE, Max SLE, P90 tail risk). Zero data divergence.
6. Tier-1 Visual Aesthetics: Clean vertical layout budgets, executive whitespace pacing (e.g. 80% balanced page occupancy), and harmonized typography adhering to international editorial standards.

YOUR MANDATE:
Draft the definitive, exhaustive, production-grade MASTER BLUEPRINT in clean Markdown format to be stored at `docs/architecture/ARGON_GLOBAL_TIER1_MASTER_PLAN.md`.

Structure the plan into a multi-phase roadmap covering:
- Phase 1: Declarative Invariant Enforcement & Complete Codebase Decoupling (Eradicating any lingering non-English tokens, inline catalogs, or hardcoded fallbacks).
- Phase 2: Dynamic Multi-Vertical Ontology & Context Ingestion Engine (Universal adaptation to any enterprise topology: OT/SCADA, Cloud-native K8s, Legacy Mainframe/iSeries, Hybrid Datacenter).
- Phase 3: Actuarial Rigor & Pure Open FAIR Simulation Coupling (Bayesian inference coupled with Monte Carlo status-quo loss modeling without heuristics).
- Phase 4: Zero-Defect Document Compilation & Multi-Language Layout Symphony (Universal vertical height budgeting, 1-page executive cockpits, and 6-language typography).
- Phase 5: Automated Continuous Quality Gate Tribunal (Automated AST guards, mutation testing, diacritics linters, and adversarial cross-deliverable audits).

Be ultra-specific, rigorous, and technical. Include concrete architecture diagrams, data schemas, algorithmic formulas, and test invariants.
"""

    cfg = types.GenerateContentConfig(
        temperature=0.2,
        thinking_config=types.ThinkingConfig(thinking_budget=4096),
        http_options=types.HttpOptions(timeout=300000),
    )

    print("Generating comprehensive Master Plan (this may take 1-2 minutes for deep reasoning)...")
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=cfg,
    )

    content = resp.text or ""
    if not content:
        raise RuntimeError("Received empty response from cognitive engine.")

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_GLOBAL_TIER1_MASTER_PLAN.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(content, encoding="utf-8")

    print(f"Master Plan successfully generated and saved to: {out_file} ({len(content)} characters)")
    return out_file

if __name__ == "__main__":
    try:
        generate_argon_master_plan()
    except Exception as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(1)
