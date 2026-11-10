#!/usr/bin/env python3
"""Execute Multidisciplinary Actuarial Tribunal audit on all 10 towers for two contrasting enterprises."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.domain.actuarial.calculators import PolymorphicActuarialEngine
from assessment_engine.domain.actuarial.financial_profile import (
    IndustryArchetype,
    TenantFinancialProfile,
)
from assessment_engine.domain.actuarial.vectors import (
    AvailabilityOutageVector,
    CapitalInefficiencyVector,
    ProductivityToilVector,
    RegulatoryBreachVector,
)
from assessment_engine.domain.models.telemetry import PolymorphicFinancialTelemetry
from assessment_engine.domain.taxonomy.archetype_registry import (
    get_actuarial_archetype_registry,
)
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

# Benchmark Client A: Starling Bank (Tier-1 Cloud-Native FinTech)
STARLING_PROFILE = TenantFinancialProfile(
    tenant_id="starling_bank",
    annual_revenue=Decimal("140000000.00"),
    industry_archetype=IndustryArchetype.CONTINUOUS_DIGITAL_FINTECH,
    currency_code="GBP",
    explicit_hourly_burn_override=Decimal("140000.00"),
)

STARLING_SCORES = {
    "T1": 4.19,
    "T2": 4.40,
    "T3": 4.50,
    "T4": 4.30,
    "T5": 4.60,
    "T6": 4.70,
    "T7": 4.40,
    "T8": 4.50,
    "T9": 4.30,
    "T10": 4.70,
}

# Benchmark Client B: Molins (Mid-Market Heavy Manufacturing / OT)
MOLINS_PROFILE = TenantFinancialProfile(
    tenant_id="molins",
    annual_revenue=Decimal("38000000.00"),
    industry_archetype=IndustryArchetype.PROCESS_MANUFACTURING_OT,
    currency_code="EUR",
)

MOLINS_SCORES = {
    "T1": 2.60,
    "T2": 2.70,
    "T3": 2.80,
    "T4": 2.90,
    "T5": 2.50,
    "T6": 2.40,
    "T7": 2.80,
    "T8": 2.50,
    "T9": 2.70,
    "T10": 2.80,
}


def build_actuarial_matrix(profile: TenantFinancialProfile, scores: dict[str, float]) -> str:
    telemetry = PolymorphicFinancialTelemetry.from_tenant_profile(profile)
    registry = get_actuarial_archetype_registry()

    lines = []
    lines.append(f"### Enterprise: {profile.tenant_id.upper()} ({profile.industry_archetype.value})")
    lines.append(f"- **Annual Turnover:** {profile.annual_revenue:,.2f} {telemetry.currency_iso}")
    lines.append(f"- **Hourly Outage Burn:** {telemetry.availability.hourly_revenue_at_risk:,.2f} {telemetry.currency_iso}/hr")
    lines.append(f"- **Annual IT OPEX:** {telemetry.capital_efficiency.annual_it_opex:,.2f} {telemetry.currency_iso}")
    lines.append(f"- **Annual Cloud Infrastructure Spend:** {telemetry.capital_efficiency.annual_cloud_infrastructure_spend:,.2f} {telemetry.currency_iso}")
    lines.append(f"- **Total Impacted Headcount:** {telemetry.productivity.total_impacted_ftes:,} FTEs @ {telemetry.productivity.fully_burdened_hourly_rate:,.2f} {telemetry.currency_iso}/hr")
    lines.append(f"- **Total PII Accounts Governed:** {telemetry.regulatory.total_pii_records_managed:,} records")
    lines.append("")
    lines.append("| Tower | Loss Archetype | CMMI Score | Annualized Loss (ALE) | Single Loss (P50 SLE) | Annual Freq (LEF) | Tail Exposure (P90) | Macroeconomic Context Ratio |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |")

    for i in range(1, 11):
        t_id = f"T{i}"
        mapping = registry.get_mapping_for_tower(t_id)
        sc = scores[t_id]
        vector = PolymorphicActuarialEngine.calculate_loss_vector(t_id, telemetry, maturity_score=sc)

        ale_str = f"{vector.annualized_loss_expectancy:,.0f} {telemetry.currency_iso}"
        sle_str = f"{vector.probable_loss_magnitude:,.0f} {telemetry.currency_iso}"
        lef_str = f"{vector.loss_event_frequency_annual:.2f}/yr"
        p90_str = f"{vector.confidence_interval_95_high:,.0f} {telemetry.currency_iso}"

        # Calculate macro ratio
        if isinstance(vector, AvailabilityOutageVector):
            ratio_str = f"{vector.projected_annual_downtime_hours:.1f} hrs downtime/yr"
        elif isinstance(vector, CapitalInefficiencyVector):
            pct_cloud = (vector.annual_addressable_waste / telemetry.capital_efficiency.annual_cloud_infrastructure_spend) * 100.0
            ratio_str = f"{pct_cloud:.1f}% of cloud spend waste"
        elif isinstance(vector, ProductivityToilVector):
            total_payroll = telemetry.productivity.total_impacted_ftes * telemetry.productivity.annual_working_hours_per_fte * telemetry.productivity.fully_burdened_hourly_rate
            pct_payroll = (vector.annualized_loss_expectancy / total_payroll) * 100.0
            ratio_str = f"{vector.equivalent_fte_capacity_burned:.1f} FTEs burned ({pct_payroll:.1f}% payroll)"
        elif isinstance(vector, RegulatoryBreachVector):
            pct_turnover = (vector.statutory_penalty_exposure / telemetry.regulatory.annual_global_turnover) * 100.0
            ratio_str = f"Fine cap: {pct_turnover:.2f}% turnover"
        else:
            ratio_str = "N/A"

        lines.append(
            f"| **{t_id}** ({mapping.canonical_tower_name}) | `{mapping.primary_archetype.value}` | {sc:.2f} | **{ale_str}** | {sle_str} | {lef_str} | {p90_str} | {ratio_str} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    print("1. Extracting quantitative actuarial matrices across all 10 towers...")
    starling_matrix = build_actuarial_matrix(STARLING_PROFILE, STARLING_SCORES)
    molins_matrix = build_actuarial_matrix(MOLINS_PROFILE, MOLINS_SCORES)

    full_telemetry_dump = f"{starling_matrix}\n\n{molins_matrix}"
    print("   ✓ Actuarial matrices successfully generated.")

    tribunal_prompt = f"""You are the Supreme Multidisciplinary Actuarial Tribunal for the Assessment Engine.
You consist of 4 independent, adversarial, and uncompromising experts:

1. JUDGE 1: Certified Open FAIR Lead Actuary (Evaluating mathematical lineage, LEF * SLE = ALE, Pert/log-normal tail risk, and non-negativity).
2. JUDGE 2: Corporate Chief Financial Officer (Evaluating macroeconomic realism, boundedness against cloud spend, payroll, and revenue, and commercial defensibility).
3. JUDGE 3: Skeptical Client CTO (Evaluating technical cause-and-effect, domain physics, absence of clearing outage fallacies in FinOps/Workplace, and operational credibility).
4. JUDGE 4: Regulatory Compliance & Audit Partner (Evaluating statutory penalty caps under DORA/GDPR/PRA, evidence calibration, and governance defensibility).

HERE IS THE COLD, HARD QUANTITATIVE DATA EXTRACTED FROM THE POLYMORPHIC FAIR ENGINE FOR 2 CONTRASTING ENTERPRISES:

{full_telemetry_dump}

YOUR MANDATE:
Conduct a rigorous forensic review of these numbers:
1. Examine each of the 10 towers across both clients (Starling Bank vs Molins).
2. Evaluate:
   - Does each tower reflect its true economic loss archetype? (e.g. Is FinOps evaluating cloud waste instead of downtime? Is Workplace evaluating FTE toil?)
   - Are the numbers bounded realistically? (Does FinOps waste exceed cloud spend? Does Workplace toil exceed payroll? Does security fine exceed 4% turnover?)
   - Does maturity progression work? (Notice Starling at ~4.5 maturity vs Molins at ~2.6 maturity).
3. For each of the 4 Judges, provide their specific analysis, critiques, and verdicts.
4. Conclude with a Table of Pass/Fail verdicts for each of the 10 towers, followed by a Final Binding Certification.

Format your response in 100% Technical English with strict, unsparing technical precision.
"""

    print(f"2. Submitting actuarial matrices to {model_name} (Multidisciplinary Tribunal)...")
    response = client.models.generate_content(
        model=model_name,
        contents=tribunal_prompt,
    )
    tribunal_report = response.text

    out_file = REPO_ROOT / "docs" / "audits" / "ARGON_MULTIDISCIPLINARY_ACTUARIAL_TRIBUNAL.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(tribunal_report, encoding="utf-8")

    print(f"\nTribunal Verdict Report written to: {out_file}\n")
    print("=" * 80)
    print(tribunal_report[:4000])
    if len(tribunal_report) > 4000:
        print("\n... [Report Truncated for CLI Display] ...\n")


if __name__ == "__main__":
    main()
