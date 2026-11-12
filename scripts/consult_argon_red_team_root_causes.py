"""Red Team Adversarial Audit of the Universal Epistemic & Actuarial Architecture Proposal."""

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

PROMPT = """You are 'gemini-4-argon', acting as the Lead Adversarial Red Team Chief Architect (SR 11-7 / Open FAIR / Basel III / Solvency II).

The user has uncovered two massive, systemic crises in the risk quantification and deliverable generation engine:

CRISIS A: The 19 Disappeared Pillars & Broken Numbering
The client questionnaire and architectural taxonomy define 61 assessed pillars across 10 technology towers (e.g. 7 pillars in T10, 6 in T1, 5 in T7, etc.).
However, in the compiled deliverables, only 42 risk cards appear:
- 19 pillars were silently dropped by a naive quarantine filter (`if boilerplate: continue`).
- In Torre 10, the cards jump: `[RVS02], [RVS03], [RVS04], [RVS06], [RVS07]`. The client asks: "Why is the last card RVS07 if there are only 5 cards? Where are RVS01 and RVS05?!"
- Critical physical capabilities vanished: In Torre 1 (Data Center), Power & Electrical Continuity (RVS01) and Climate Control / HVAC (RVS02) disappeared from the deliverable! In Torre 7 (ITSM), Service Desk, Incident Burndown, and SRE disappeared, leaving only 2 cards!

CRISIS B: Actuarial Distortion (The 8-Hour Outage Fallacy & Numerical Disconnects)
Across the remaining cards, severe common-sense and model risk failures persist:
1. Minor operational friction is modeled as catastrophic 8-hour factory blackouts:
   - A Linux log partition filling up `/var/log` is modeled as an 8-HOUR PLANT BLACKOUT costing 62,688 €! (In reality, an engineer clears disk space in 15-30 minutes, or at most degrades one local VM).
   - Missing 802.1X NAC in a precast plant is modeled as an 8-HOUR PLANT BLACKOUT costing 62,688 €! (In reality, lacking NAC is an unauthorized access vulnerability, not a physical power cut).
   - Missing DRP documentation is modeled as an 8-HOUR PLANT BLACKOUT!
2. Major financial and operational realities are trivialized:
   - USB manual laptop imaging: 350 laptops * 3.5h = 1,225 hours of engineer toil (~55,000 €/year). The table printed 20 €/year because it assigned frequency = 1 event/year!
   - NOS captive telecom contract: Burns 450,000 €/year in duplicate OpEx according to the interview. The table assigned 9,940 €/year!
   - Shared root/full admin credentials: Complete control plane compromise risk assigned 3,295 €/year!
   - Test VM decommissioning: Borrows 30,000 € in consulting cleanup cost to delete 10 VMs on an on-premise cluster!
   - Kubernetes test lab in Molins: Assigned ~43,000 €/year in a cement company that doesn't use Kubernetes in production!

--- OUR ARCHITECTURAL PROPOSAL TO SOLVE THIS FOR 100% OF ENTERPRISES ---

1. HIERARCHICAL EPISTEMIC RESOLUTION (No Silent Dropping, No Numbering Gaps):
- Every assessed capability in the enterprise taxonomy must have an immutable, 1-to-1 canonical risk identifier (`RVS01` to `RVS0N`), strictly preserved with zero gaps.
- The 4-Tier Epistemic Truth Hierarchy:
  * Tier 1 (Interview Ground Truth): Extracted verbatim speech turns from interviews (e.g. UPS batteries in CPD 2, NetApp 4h SnapMirror, weighbridge serial convertors).
  * Tier 2 (Audited Corporate Documentation): CMDB inventories, Active Directory exports, official public filings (EINF/10-K).
  * Tier 3 (Calibrated Industry Sector Priors): If unmentioned in the interview, hydrate using sector benchmark empirical failure mechanisms (e.g. for heavy manufacturing, power generator fuel degradation or HVAC chiller compressor thermal trips), NOT generic robotic strings!
  * Tier 4 (Unquantified Governance Gap): If a capability is purely a survey questionnaire response with zero empirical signal, render it with status `UNQUANTIFIED_MATURITY_GAP` (ALE = 0 €, RTO = 0h) in a dedicated Governance & Compliance table, NEVER silently skipping it from the index!

2. FIVE-TIER LOSS DURATION & RECOVERY TIME PHYSICS:
- Completely banish the "8-hour default outage" for non-catastrophic events.
- Classify RTO and downtime duration by physical failure mode:
  * Tier A: Operational Friction & Configuration Maintenance (Disk space, log rotation, VM cleanup): RTO = 0.25h - 0.5h (15 to 30 minutes), localized to a single VM/service ($alpha = 0.01$).
  * Tier B: Network Edge & Device Replacement (Serial-to-Ethernet, FortiGate CPE, switch): RTO = 1.0h - 2.0h, localized to single plant/quarry ($alpha = 0.05 - 0.10$).
  * Tier C: Engineering Toil (Manual imaging, provisioning without Terraform): Modeled as cumulative annual labor hours ($H_{toil} \times Wage$), NOT downtime outages!
  * Tier D: Major Infrastructure Disaster (Transformer explosion, ransomware encryption, core SAN failure): RTO = 8.0h - 24.0h, enterprise-wide ($alpha = 0.70 - 1.0$).
  * Tier E: Pure Financial / Contractual Inefficiency (NOS contract, Broadcom licensing): RTO = 0.0h, modeled as OpEx cash-flow leakage (Ledger B).

3. DUAL-LEDGER PRESENTATION (IFRS/GAAP Compliant):
- Ledger A: Stochastic Annualized Loss Expectancy (ALE, Probability < 1.0). For unplanned risk events (ransomware, outages, fires, breaches).
- Ledger B: Deterministic OpEx Waste & Toil (Probability = 1.0, 100% certain annual cash drain). For guaranteed recurring waste (NOS duplicate contract 450,000 €/year, manual laptop imaging 55,000 €/year).
- Never mix Ledger B into Euler stochastic diversification! Deterministic OpEx waste has 0% diversification discount.

--- YOUR ADVERSARIAL RED TEAM MANDATE ---

Critique this proposal ruthlessly. Search for every hidden flaw, edge case, and failure mode:
1. EPISTEMIC ROUTING: Can the router guarantee that in ANY enterprise (Starling Bank, Molins, Rede D'Or, E.ON), silent pillars are never dropped and never get robotic text? What if an interview doesn't mention something?
2. ACTUARIAL PHYSICS: Is the 5-tier loss duration model mathematically sound under Open FAIR and SR 11-7? How should blast radius ($alpha$) be mathematically bounded so local plant events never multiply corporate group revenue?
3. DUAL-LEDGER: How should Ledger A (Stochastic ALE) and Ledger B (Deterministic OpEx) be presented in Tomo 1 and Chapter 4 so that the Board and CFO get complete transparency without double-counting?
4. WHAT DID WE MISS? What dangerous trap or blindspot is still lurking in our proposed architecture?

Respond in 100% Technical English with supreme adversarial rigor.
"""


def main() -> None:
    print(f"Submitting Red Team Adversarial Review to {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=PROMPT,
    )
    report = response.text
    out_file = REPO_ROOT / "docs" / "audits" / "RED_TEAM_ROOT_CAUSE_REMEDIATION_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(report, encoding="utf-8")

    print(f"\nRed Team Report written to: {out_file}\n")
    print("=" * 80)
    print(report[:4500] + ("\n... [TRUNCATED]" if len(report) > 4500 else ""))


if __name__ == "__main__":
    main()
