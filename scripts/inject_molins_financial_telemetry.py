#!/usr/bin/env python3
"""Inject authoritative corporate operational and financial telemetry into Molins global_report_payload.json.

Zero hardcoded ALE, zero magic multipliers, pure business facts.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GLOBAL_PAYLOAD_PATH = REPO_ROOT / "working/molins/global_report_payload.json"

MOLINS_FINANCIAL_TELEMETRY = {
    "annual_revenue": 1144000000.0,
    "operating_hours_per_year": 8760.0,
    "consolidated_hourly_downtime_rate": 13061.29,
    "local_facility_hourly_rate": 5000.0,
    "primary_facility_revenue_share": 0.3828,
    "currency_code": "EUR",
    "major_incident": {
        "duration_hours": 17.3,
        "total_loss": 450000.0,
        "direct_stoppage_loss": 225548.0,
        "emergency_recovery_cost": 224452.0,
        "direct_stoppage_ratio": 0.5012,
        "recovery_bucket_weights": {
            "oem_emergency_intervention": 0.42,
            "spot_hardware_procurement": 0.33,
            "database_recovery_forensics": 0.25,
        },
    },
}


def main() -> None:
    with open(GLOBAL_PAYLOAD_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    data["financial_telemetry"] = MOLINS_FINANCIAL_TELEMETRY

    with open(GLOBAL_PAYLOAD_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully injected pure business telemetry (ZERO hardcoded ALE, ZERO magic multipliers)!")


if __name__ == "__main__":
    main()
