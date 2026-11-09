#!/usr/bin/env python3
"""Adversarial Actuarial Audit across 6 Multi-Tenant Global Enterprises.

Consults gemini-4-argon to evaluate whether seasoned CFOs, CTOs, and Chief Risk Officers
would believe or reject the quantitative risk figures (Hourly Downtime Burn, Total ALE,
P90 Value-at-Risk, and Individual Risk Magnitudes) across diverse global industries:
1. Starling Bank (UK - Digital Challenger Bank - £665M GBP)
2. Geodis (France - Global Multimodal Logistics & Freight - €13.7B EUR)
3. Rede D'Or São Luiz (Brazil - Hospital & Healthcare Network - R$ 47B BRL)
4. Grupo Comercial Chedraui (Mexico - Grocery & Retail Conglomerate - $263B MXN)
5. Datadog (USA - Cloud Observability & Security SaaS - $2.13B USD)
6. Molins (Spain - Heavy Building Materials & Manufacturing - €1.144B EUR)
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

clients = {
    "starling_bank": {
        "name": "Starling Bank",
        "country": "United Kingdom",
        "industry": "Digital Challenger Banking & FinTech",
        "revenue": "£665,000,000 GBP",
        "hourly_burn": "£140,000 GBP/h",
        "total_ale": "£4,179,405 GBP (0.63% of revenue)",
        "p90_var": "£9,194,692 GBP",
        "sample_findings": [
            "T1 Data Center (Total ALE: £203,552 | Sample Finding ALE: £18,505)",
            "T5 Core Banking Resilience & DRP (Total ALE: £137,078 | Sample Finding ALE: £9,791)",
            "T6 Identity Governance & Cyber (Total ALE: £129,080 | Sample Finding ALE: £9,929)",
            "T8 Cloud FinOps & Strategy (Total ALE: £141,155 | Sample Finding ALE: £10,858)",
            "T3 Network & Connectivity (Total ALE: £49,404 | Sample Finding ALE: £3,800)",
            "T10 Legacy Core Systems (Total ALE: £48,902 | Sample Finding ALE: £3,493)",
        ],
    },
    "geodis": {
        "name": "Geodis (SNCF Group)",
        "country": "France",
        "industry": "Global Freight Forwarding, Logistics & Supply Chain",
        "revenue": "€13,700,000,000 EUR",
        "hourly_burn": "€310,000 EUR/h",
        "total_ale": "€244,281,383 EUR (1.78% of revenue)",
        "p90_var": "€537,419,043 EUR",
        "sample_findings": [
            "T3 Global WAN & Warehouse Mesh (Sample Finding ALE: ~€1.8M)",
            "T5 Supply Chain Continuous Availability (Sample Finding ALE: ~€3.2M)",
            "T7 TMS / WMS Operational Service Desk (Sample Finding ALE: ~€850k)",
        ],
    },
    "rede_d_or_sao_luiz": {
        "name": "Rede D'Or São Luiz",
        "country": "Brazil",
        "industry": "Integrated Hospital Network, Clinical Diagnostics & Healthcare",
        "revenue": "R$ 47,000,000,000 BRL",
        "hourly_burn": "R$ 420,000 BRL/h",
        "total_ale": "R$ 420,867,885 BRL (0.89% of revenue)",
        "p90_var": "R$ 925,909,346 BRL",
        "sample_findings": [
            "T1 Clinical Hospital Data Center (Sample Finding ALE: ~R$ 3.5M)",
            "T4 PACS Medical Imaging & EHR Storage (Sample Finding ALE: ~R$ 4.8M)",
            "T6 ICU Telemetry & Patient Data Privacy (Sample Finding ALE: ~R$ 2.9M)",
        ],
    },
    "grupo_comercial_chedraui": {
        "name": "Grupo Comercial Chedraui",
        "country": "Mexico",
        "industry": "Hypermarket, Supermarket & Omni-Channel Grocery Retail",
        "revenue": "$263,000,000,000 MXN",
        "hourly_burn": "$1,650,000 MXN/h",
        "total_ale": "$684,008,477 MXN (0.26% of revenue)",
        "p90_var": "$1,504,818,648 MXN",
        "sample_findings": [
            "T3 Store POS Network & Optical Fiber WAN (Sample Finding ALE: ~MXN $6.2M)",
            "T4 Warehouse Distribution Center Storage (Sample Finding ALE: ~MXN $8.1M)",
            "T9 Retail Point of Sale & Checkout Terminals (Sample Finding ALE: ~MXN $4.5M)",
        ],
    },
    "datadog": {
        "name": "Datadog, Inc.",
        "country": "United States",
        "industry": "Cloud Observability, APM & Security SaaS Platform",
        "revenue": "$2,130,000,000 USD",
        "hourly_burn": "$520,000 USD/h",
        "total_ale": "$3,486,730 USD (0.16% of revenue)",
        "p90_var": "$7,670,807 USD",
        "sample_findings": [
            "T2 Multi-Region Cloud Ingestion Clusters (Sample Finding ALE: ~$350k)",
            "T3 Global Transit VPC & Direct Connect Mesh (Sample Finding ALE: ~$280k)",
            "T6 Zero-Trust Service Mesh & Cloud IAM (Sample Finding ALE: ~$420k)",
        ],
    },
    "molins": {
        "name": "Molins",
        "country": "Spain",
        "industry": "Heavy Building Materials, Cement Kilns & Concrete Manufacturing",
        "revenue": "€1,144,000,000 EUR",
        "hourly_burn": "€13,061.29 EUR/h",
        "total_ale": "€766,536 EUR (0.067% of revenue)",
        "p90_var": "€1,149,804 EUR",
        "sample_findings": [
            "T2 Compute & SimpliVity RAM Saturation (Total ALE: €162,695 | Critical Finding: €33,339)",
            "T5 Continuity & Truck Weighbridge Stoppage (Total ALE: €115,468 | Critical Finding: €33,566)",
            "T8 IT Governance & Industrial OT Boundary (Total ALE: €109,028 | Critical Finding: €30,886)",
            "T6 Cyber & Shared Root Credentials in Plants (Total ALE: €96,384 | Critical Finding: €29,566)",
            "T1 Sant Vicenç Twin CPDs at 500m (Total ALE: €94,829 | Critical Finding: €22,795)",
            "T9 Digital Workplace in Delegations (Total ALE: €9,453 | High Finding: €2,251)",
        ],
    },
}

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)
print(f"Connecting to Reasoning model '{model_name}' for Cross-Enterprise Actuarial Audit...")

prompt = f"""You are 'gemini-4-argon', the Principal Staff Systems Architect, Lead Actuary, and Fortune 500 Chief Risk Officer.
Conduct an adversarial, rigorous, forensic audit of the quantitative risk figures generated for 6 diverse global enterprises.

For EACH of the 6 enterprises:
Evaluate whether a cynical, seasoned CFO, Head of Operational Risk, and Board Audit Committee would BELIEVE or REJECT the numbers.

Specifically evaluate for each company:
1. Hourly Downtime Burn Rate: Is the hourly cost of total outage realistic given the business model, annual turnover, and operational hours?
2. Total Annualized Loss Expectancy (ALE): Is the corporate IT risk pool believable (as a percentage of revenue and in absolute local currency), or is it an absurd hallucination?
   - Compare: Geodis (€244M ALE on €13.7B = 1.78%) vs. Molins (€766k ALE on €1.14B = 0.067%) vs. Datadog ($3.48M on $2.13B = 0.16%) vs. Starling (£4.18M on £665M = 0.63%) vs. Rede D'Or (R$ 420M on R$ 47B = 0.89%) vs. Chedraui (MXN $684M on $263B = 0.26%).
   - Which ones are calibrated to perfection? Which ones are distorted?
3. Individual Risk Magnitudes: Are the sample finding ALEs credible for that industry and asset gravity?
4. Final Verdict per Company: (BELIEVABLE & BOARD-READY / OVERESTIMATED / UNDERESTIMATED / REJECTED).
5. Root-Cause Actuarial Synthesis: What exact mathematical formula or parameter governs the divergence, and what is the optimal universal calibration range across verticals?

DATA PAYLOAD OF AUDITED ENTERPRISES:
{json.dumps(clients, indent=2)}

Format your evaluation with executive clarity, quantitative precision, and zero consultant filler.
"""

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
)

out_file = REPO_ROOT / "docs/audits/ARGON_MULTI_ENTERPRISE_ACTUARIAL_AUDIT.md"
out_file.write_text(response.text, encoding="utf-8")
print(f"\n✓ Saved formal audit report to {out_file.relative_to(REPO_ROOT)}")
print("\n" + "=" * 80)
print(response.text[:2500] + "\n... [TRUNCATED] ...")
print("=" * 80)
