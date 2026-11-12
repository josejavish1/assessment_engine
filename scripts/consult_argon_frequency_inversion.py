"""Consult gemini-4-argon for the Tier-1 architecture to solve the Frequency Inversion Fallacy."""

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

PROMPT = """You are 'gemini-4-argon', Lead Adversarial Red Team Chief Architect (SR 11-7 / Open FAIR / Basel III / Solvency II) at a top-tier global consulting firm in November 2026.

We have encountered another SEVERE architectural flaw in our Assessment Engine's actuarial output that destroys credibility:
**The Frequency Inversion Fallacy (Polaridad Invertida):**
1. **Catastrophic Outages (High Impact, Low Frequency):** The model assigns a Threat Event Frequency (TEF/LEF) of 1.12 to 1.40 times PER YEAR to events like a total cold crash of the Data Center, a major fiber cut, or a full Ransomware lockout. This is empirically absurd. A factory doesn't lose all power to its datacenter every 8 months. These events have an industry-standard MTBF of 5 to 10 years (LEF ~0.10 - 0.20).
2. **Operational Friction & Fleet Toil (Low Impact, High Frequency):** For a "disk full" or "SQL lock" or "unpatched endpoint" issue (Tier A friction), the model assigns an LEF of 0.25 (once every 4 years). This is equally absurd. In a fleet of 60 servers and 350 laptops, log rotations and disk cleanups trigger PagerDuty alerts 12 to 24 times A YEAR. Because it multiplies a frequency of 0.25 against a tiny SLE (e.g., 150 EUR for an hour of sysadmin time), we get laughably small ALEs like 42 EUR/year or 77 EUR/year for the entire company.

The current system relies on a naive linear mapping from the CMMI Maturity Score directly to TEF (e.g. Score 1.0 -> 1.4 events/year, Score 3.0 -> 0.25 events/year) without understanding the *physics* of the threat.

The user explicitly rejected any "tactical patch" (like hardcoding a few IF statements) and demands a ROOT CAUSE, TIER-1 ARCHITECTURAL SOLUTION aligned with the state-of-the-art in November 2026 (e.g. IEEE 493 Gold Book standards, Uptime Institute priors, FAIR Fleet Scaling).

YOUR MANDATE:
Design the ultimate Master Architecture to permanently solve this Frequency Inversion.
1. **Bayesian Threat Event Frequency (TEF) Matrix by Physics Archetype:** How do we decouple the CMMI score from the absolute frequency, and instead use the CMMI score to *modulate* a physics-based Bayesian prior? (e.g. A CATASTROPHIC_OUTAGE has a base prior of 0.10/yr, modulated up to 0.20 if CMMI is 1.0. An ENGINEERING_FRICTION has a base prior of 12.0/yr, modulated up to 24.0 if CMMI is 1.0).
2. **Fleet Volume Scaling for Friction:** How do we mathematically ensure that "disk full" is treated as a Poisson process across N servers (Fleet Volume), so that $\\lambda_{fleet} = N \\times \\lambda_{node}$?
3. **Execution Plan:** Provide the exact file paths to modify (e.g., `input_resolver.py`, `parameter_packs/*.json`, `finding_archetype_resolver.py`) and the strict invariant rules to enforce.

Provide a definitive, aggressive, and highly technical design document (Markdown format). No pleasantries. Only Tier-1 architectural solutions.
"""

print(f"Submitting Frequency Inversion Architecture Audit to {model_name}...")
response = client.models.generate_content(
    model=model_name,
    contents=PROMPT,
)

out_file = REPO_ROOT / "docs" / "audits" / "RED_TEAM_FREQUENCY_INVERSION_ARCHITECTURE.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\nAudit complete. Wrote {len(response.text)} chars to {out_file.relative_to(REPO_ROOT)}")
