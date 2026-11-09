#!/usr/bin/env python3
"""Verify dynamic actuarial elasticity and sensitivity when findings change."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
from assessment_engine.domain.actuarial_reconciler import ActuarialReconciler

GLOBAL_PAYLOAD = REPO_ROOT / "working/molins/global_report_payload.json"


def compute_dynamic_allocations(additional_t2_spofs: int = 0) -> dict[str, int]:
    with open(GLOBAL_PAYLOAD) as f:
        gp = json.load(f)

    fin = gp.get("financial_telemetry", {})
    revenue = float(fin.get("annual_revenue", 1144000000.0))
    risk_factor = float(fin.get("baseline_risk_factor", 0.000801))
    corporate_pool = int(round(revenue * risk_factor))
    base_rate = float(fin.get("consolidated_hourly_downtime_rate", 13061.29))
    plant_rate = float(fin.get("local_facility_hourly_rate", 5000.0))

    raw_scores: list[tuple[str, Decimal]] = []

    for i in range(1, 11):
        code = f"T{i}"
        p_file = REPO_ROOT / f"working/molins/{code}/blueprint_{code.lower()}_payload.json"
        if not p_file.exists():
            continue
        with open(p_file) as pf:
            data = json.load(pf)

        rate = plant_rate if code == "T10" else base_rate
        cmmi = float(data.get("exact_score") or data.get("score") or 2.5)
        vuln = max(0.12, min(0.95, (5.0 - cmmi) / 4.0))

        t_score = 0.0
        for pil in data.get("pillars_analysis", []):
            for hc in pil.get("health_check_asis", []):
                sev = str(hc.get("severity") or "").upper()
                txt = str(hc.get("finding") or "").lower()
                is_spof = any(w in txt for w in ["spof", "single point of failure", "saturacion", "saturación", "obsolescencia", "sin redundancia"])

                if is_spof or sev == "CRITICAL":
                    alpha = 0.85 if code in ("T1", "T2", "T5") else 0.70
                    hours = 16.0 if is_spof else 12.0
                    tef = 0.45
                elif sev == "HIGH":
                    alpha = 0.40
                    hours = 7.0
                    tef = 0.30
                else:
                    alpha = 0.20
                    hours = 3.5
                    tef = 0.20

                t_score += tef * vuln * (hours * alpha * rate)

        if code == "T2" and additional_t2_spofs > 0:
            for _ in range(additional_t2_spofs):
                t_score += 0.45 * vuln * (16.0 * 0.85 * rate)

        raw_scores.append((code, Decimal(str(round(t_score, 2)))))

    reconciled = ActuarialReconciler.reconcile_domain_allocations(
        target_corporate_ale=corporate_pool,
        domain_raw_exposures=raw_scores,
    )
    return reconciled


def main() -> None:
    print("=" * 80)
    print("VERIFYING DYNAMIC ELASTICITY OF ACTUARIAL ALLOCATION ENGINE")
    print("=" * 80)

    baseline = compute_dynamic_allocations(additional_t2_spofs=0)
    print(f"Total Corporate Pool: {sum(baseline.values()):,} EUR")
    print("\nBaseline Dynamic Allocations (Derived from Findings):")
    for code, val in sorted(baseline.items(), key=lambda x: int(x[0][1:])):
        print(f"  {code}: {val:>10,} EUR | Worst Crisis (2.5x): {round(val * 2.5):>10,} EUR")

    # Now simulate discovering 2 new catastrophic SPOF vulnerabilities in T2
    stress_t2 = compute_dynamic_allocations(additional_t2_spofs=2)
    print("\nAfter Discovering 2 New Critical SPOFs in T2 (SimpliVity RAM + K8s):")
    for code in sorted(baseline.keys(), key=lambda x: int(x[1:])):
        old_v = baseline[code]
        new_v = stress_t2[code]
        diff = new_v - old_v
        print(f"  {code}: {new_v:>10,} EUR ({diff:>+8,} EUR)")

    assert stress_t2["T2"] > baseline["T2"], "ELASTICITY FAILED: T2 did not increase when findings increased!"
    assert sum(stress_t2.values()) == sum(baseline.values()), "CONSERVATION FAILED: Pool sum drifted!"
    print("\n✓ ELASTICITY & CONSERVATION TESTS PASSED: Finding changes dynamically move the needle!")


if __name__ == "__main__":
    main()
