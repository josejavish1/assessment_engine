"""Consult gemini-4-argon for the ultimate Tier-1 architecture to make Tomo 1 (Consolidated Diagnostic) flawless."""

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

PROMPT = """You are 'gemini-4-argon', Lead Adversarial Red Team Chief Architect (SR 11-7 / Open FAIR / Basel III / Enterprise Architecture) at a top-tier global consulting firm in November 2026.

We have conducted a brutal adversarial review of our flagship executive deliverable: `Tomo 1: Diagnóstico AS-IS Consolidado` (The Executive Diagnostic Report for the CTO/CFO of Cementos Molins).

The review uncovered 5 FATAL FLAWS in Tomo 1:
1. **The 0 EUR Crisis Anomaly in Chapter 1:** In the Executive Summary (Chapter 1), the report states:
   - "Exposición Anual Promedio (ALE): 3.977.026 €"
   - "Impacto por Incidente Grave Único: hasta 0 €"
   - "Escenario de Crisis Anual Acumulada: 0 € / año"
   The compiler (`tomo_asis_ast_compiler.py`) failed to compute the tail risk (P90) and worst single incident, outputting literal "0 €" while claiming an average loss of 4M€.
2. **The 7,600% Split-Brain between Tomo 1 and the 10 Specialist Annexes:**
   - In Tomo 1's "Top 5 Corporate Risks" table, it shows:
     - PAM Compromise (T6): 822.717 €/year (LEF 4.20/yr, SLE 195.885 €)
     - vSphere HA Contention (T2): 320.706 €/year (SLE 159.555 €)
   - BUT in the 10 Specialist Annexes (which we recently calibrated with physical models), the actual values are:
     - PAM Compromise (T6): 19.984 €/year (LEF 0.12/yr, SLE 195.915 €)
     - vSphere HA Contention (T2): 4.178 €/year (LEF 2.04/yr, SLE 2.048 €)
   The Top 5 table in Tomo 1 was reading from a stale `corporate_top_risks` cache instead of dynamically aggregating the 10 live annexes!
3. **CMMI Maturity Score Drift:**
   - Page 1 says: "Global CMMI Maturity: 2,10 / 5,00"
   - Page 3 says: "Global Consolidated Index: 2,01 / 5,00"
   - Storage (T4) says 2,30 in Table 1 and 2,62 in Table 26.
4. **Database Dumps & Pipe Characters in Table 8:**
   - Table 8 (Systemic Risk Taxonomy) contains raw unparsed database dumps with pipe delimiters `|` inside parentheses.
5. **Double Counting of M&A Contracts:**
   - 450.000 € NOS contract in T8 vs duplicate 41.000 € in T2.

The user is furious and asks:
"What do we need to do to fix this once and for all, so that Tomo 1—the most important document of all—is perfect and ALWAYS generates perfectly? Ask gemini-4-argon to tell us how we should leave this report so that it is board-ready and flawless."

YOUR MANDATE:
Design the definitive, Top Tier-1 Master Architecture for `Tomo 1 Consolidated AS-IS`.
1. **Mathematical Monism & Zero-Cache Aggregation:** How must `Volume1AsisASTCompiler` be refactored so that Tomo 1 NEVER reads from static global caches or stale catalogs, but is strictly a **pure mathematical rollup** of the 10 live tower payloads?
2. **Tail Risk (P90) and Peak Incident Resolution:** How to guarantee that `worst_incident_cost` and `total_p90` are mathematically derived from the maximum single SLE and the portfolio copula, eradicating any possibility of "0 €"?
3. **Maturity Score Single Source of Truth (SSOT):** How to ensure that `global_cmmi_score` and domain scores match to the exact decimal across every single table and narrative in Tomo 1?
4. **Clean Executive Presentation:** What exact structure should Tomo 1 have so that a hostile CTO or CFO is impressed by its rigor rather than laughing at anomalies?

Provide a definitive, aggressive, and highly technical design document (Markdown format). No pleasantries. Only Tier-1 architectural solutions.
"""

print(f"Submitting Tomo 1 Master Architecture Audit to {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=PROMPT,
)

out_file = REPO_ROOT / "docs" / "audits" / "RED_TEAM_TOMO1_MASTER_ARCHITECTURE.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\nAudit complete. Wrote {len(response.text)} chars to {out_file.relative_to(REPO_ROOT)}")
