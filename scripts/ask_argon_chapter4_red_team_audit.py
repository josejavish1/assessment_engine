#!/usr/bin/env python3
"""
Invoke gemini-4-argon as a Top-Tier Adversarial Red Team Panel on the Universal Chapter 4 Master Plan.
Evaluates:
1. Code refactoring purity, Hexagonal architecture, Pydantic V2 schema resilience.
2. Universal scalability (CMMI 1-5, $50M to $100B, 8 vertical industries).
3. Open FAIR actuarial validity vs hidden heuristic anti-patterns.
4. Multi-language output & executive deliverable perfection across all 10 towers.
"""

import sys
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.genai_client import create_genai_client, get_model, ModelTier
from google.genai import types

def run_chapter4_red_team_audit() -> Path:
    print("=" * 80)
    print("  INVOKING GEMINI-4-ARGON: TOP TIER-1 CODE REFACTORING RED TEAM PANEL")
    print("=" * 80)

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Target Cognitive Engine: {model_name}")

    master_plan_path = _REPO_ROOT / "docs" / "architecture" / "ARGON_UNIVERSAL_CHAPTER_4_MASTER_PLAN.md"
    if not master_plan_path.exists():
        raise FileNotFoundError(f"Master plan not found at {master_plan_path}")

    master_plan_content = master_plan_path.read_text(encoding="utf-8")

    prompt = f"""
You are the Lead Adversarial Reviewer of a Tier-1 Global Code Refactoring & Quantitative Risk Red Team, comprising:
1. Principal Software Architect (Staff/Principal Engineer, ex-Google/AWS, specialist in Domain-Driven Design, Hexagonal Architecture, Pydantic V2, and AST Compilation).
2. Fellow of the Society of Actuaries & Open FAIR Accredited Master (specialist in Enterprise Operational Risk Quantification).
3. Senior Partner in Technical Due Diligence (ex-McKinsey/Gartner, specialist in Board & CIO Executive Deliverables).

MISSION:
Conduct an unsparing, exhaustive, and mathematically rigorous ADVERSARIAL RED TEAM AUDIT of the proposed Universal Chapter 4 Master Plan.
The user demands to know:
- Is this plan TRULY the best possible architecture in the world for Chapter 4?
- Can it genuinely serve ANY company in the world (any size from $50M to $100B+, any vertical, any maturity from CMMI 1.0 to 5.0) without tactical patches?
- Does it eradicate all split-brain anti-patterns and hallucinations bit-for-bit?
- Will the compiled Chapter 4 output be 100% flawless across all 10 specialist towers and 6 deliverable languages?

INPUT DOCUMENT TO AUDIT:
```markdown
{master_plan_content}
```

AUDIT MANDATE & DIMENSIONS TO INVESTIGATE:
1. STRUCTURAL CODE REFACTORING & ARCHITECTURAL PURITY:
   - Audit the proposed Pydantic V2 schemas (`Chapter4SynthesisPayload`, `ChronicOperationalDragBreakdown`, `ProbabilisticOutageALEBreakdown`). Are they truly immutable and protected against presentation mutation?
   - Is the separation between Domain (synthesis & math) and Adapters/Compilers (AST projection) strictly preserved?
   - Are there any lingering circular dependencies, hidden global singletons, or unhandled null-safety exceptions?

2. ACTUARIAL RIGOR & THE OPEN FAIR REALITY CHECK:
   - Does decoupling Chronic Operational Drag (COD) from Probabilistic Event ALE genuinely solve the "actuarial fallacy"?
   - Is the Portfolio Sub-Additivity Factor ($\Psi_{{\text{{portfolio}}}}$) mathematically legitimate, or does it risk hiding real exposure?
   - Is the Actuarial Significant Figures Rounding Policy robust against edge cases (e.g., hyper-low risk environments < 5.000 € vs hyper-critical multi-billion conglomerates)?

3. UNIVERSAL MATURITY DYNAMICS (CMMI 1.0 TO 5.0) & MULTI-VERTICAL RESILIENCE:
   - Does the loss mutation equation hold true for an OT factory (like Molins), a Tier-1 Investment Bank, a Cloud SaaS provider, and a Critical Healthcare System?
   - Where are the potential breaking points when scaling to Fortune 10 enterprises?

4. RADICAL CLUTTER PURGE & DELIVERABLE USER EXPERIENCE:
   - Is permanently deleting the 4 textbook didactic tables and cryptic machine codes (`RVS01`) safe? Does the executive reader lose any legally necessary audit trail?
   - How does the clean 5x5 heatmap with human-readable titles perform across all 10 towers?

5. ADVERSARIAL STRESS TEST & CONCRETE CODE ENHANCEMENTS:
   - Identify the TOP 3 most subtle failure modes or edge cases in the proposed implementation.
   - For each failure mode, provide the concrete, production-grade enhancement or invariant to make it 100% bulletproof.

6. FINAL VERDICT & SIGN-OFF:
   - Provide a formal certification verdict: [APPROVED WITH ENHANCEMENTS / REJECTED].
   - State whether this architecture sets a new global benchmark for enterprise technical due diligence.

Write your complete adversarial report in clean Markdown format to be stored at `docs/architecture/ARGON_CHAPTER_4_RED_TEAM_VERDICT.md`.
100% Technical English. Be ruthless, forensic, and mathematically uncompromising.
"""

    cfg = types.GenerateContentConfig(
        temperature=0.2,
        thinking_config=types.ThinkingConfig(thinking_budget=8192),
        http_options=types.HttpOptions(timeout=300000),
    )

    print("Running deep adversarial audit with Gemini-4-Argon Red Team...")
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=cfg,
    )

    verdict_content = resp.text or ""
    if not verdict_content:
        raise RuntimeError("Received empty response from adversarial red team.")

    out_file = _REPO_ROOT / "docs" / "architecture" / "ARGON_CHAPTER_4_RED_TEAM_VERDICT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(verdict_content, encoding="utf-8")

    print(f"Red Team Audit Report successfully generated and saved to: {out_file} ({len(verdict_content)} characters)")
    return out_file

if __name__ == "__main__":
    try:
        run_chapter4_red_team_audit()
    except Exception as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(1)
