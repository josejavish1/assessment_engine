"""Refactor engine_config/towers/T1/tower_definition_T1.json to 100% canonical Technical English."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T1_DEF_PATH = ROOT / "engine_config" / "towers" / "T1" / "tower_definition_T1.json"


def refactor_t1() -> None:
    data = json.loads(T1_DEF_PATH.read_text(encoding="utf-8"))

    data["tower_name"] = "Physical Data Center & Facilities"
    data["purpose"] = (
        "The Physical Data Center & Facilities domain covers all physical infrastructure and mechanical systems "
        "required to sustain enterprise IT operations: technical facilities, electrical power distribution, "
        "HVAC climate control, physical perimeter security, fire suppression, and facility monitoring."
    )

    data["maturity_scale"] = [
        {"level": 1, "label": "Initial", "operational_reading": "Capability is ad-hoc, unmeasured, or heavily dependent on heroic individual efforts."},
        {"level": 2, "label": "Managed", "operational_reading": "Capability exists with baseline operational controls but lacks automated validation."},
        {"level": 3, "label": "Defined", "operational_reading": "Capability is formalized, standardized, and consistently enforced across facilities."},
        {"level": 4, "label": "Quantitatively Managed", "operational_reading": "Capability is industrialised, governed with continuous telemetry, and statistically controlled."},
        {"level": 5, "label": "Optimizing", "operational_reading": "Capability demonstrates predictive continuous improvement and automated failover orchestration."}
    ]

    data["score_bands"] = [
        {"min": 1.00, "max": 1.59, "label": "Level 1 - Initial"},
        {"min": 1.60, "max": 2.59, "label": "Level 2 - Managed"},
        {"min": 2.60, "max": 3.59, "label": "Level 3 - Defined"},
        {"min": 3.60, "max": 4.59, "label": "Level 4 - Quantitatively Managed"},
        {"min": 4.60, "max": 5.00, "label": "Level 5 - Optimized"}
    ]

    pillars_english = [
        {
            "pillar_id": "T1.P1",
            "pillar_name": "Power & Electrical Continuity",
            "weight_pct": 24,
            "kpis": [
                {
                    "kpi_id": "T1.P1.K1",
                    "kpi_name": "Guaranteed Electrical Autonomy (UPS & Backup Generators)",
                    "questions": [{
                        "question_id": "T1.P1.K1.PR1",
                        "question_text": "What is the certified autonomous runtime of critical facility loads under complete utility power loss?"
                    }]
                },
                {
                    "kpi_id": "T1.P1.K2",
                    "kpi_name": "Switching Test Cadence & Controlled Failover Verification",
                    "questions": [{
                        "question_id": "T1.P1.K2.PR1",
                        "question_text": "How frequently and under what operational methodology are automated transfer switches (ATS) and emergency generators tested under full load?"
                    }]
                },
                {
                    "kpi_id": "T1.P1.K3",
                    "kpi_name": "Power Distribution Redundancy & Single Points of Failure Elimination",
                    "questions": [{
                        "question_id": "T1.P1.K3.PR1",
                        "question_text": "How are single points of failure (SPOFs) in dual-cord electrical distribution paths identified and mitigated across server racks?"
                    }]
                },
                {
                    "kpi_id": "T1.P1.K4",
                    "kpi_name": "Electrical Capacity Utilization & Planned Headroom Management",
                    "questions": [{
                        "question_id": "T1.P1.K4.PR1",
                        "question_text": "How is electrical load capacity monitored against provisioned thresholds to prevent circuit overload and manage expansion headroom?"
                    }]
                }
            ]
        },
        {
            "pillar_id": "T1.P2",
            "pillar_name": "Climate Control & Environmental Resilience",
            "weight_pct": 20,
            "kpis": [
                {
                    "kpi_id": "T1.P2.K1",
                    "kpi_name": "Environmental Threshold Compliance & Continuous Thermal Telemetry",
                    "questions": [{
                        "question_id": "T1.P2.K1.PR1",
                        "question_text": "How are ambient temperature and relative humidity monitored and controlled in accordance with ASHRAE TC 9.9 standards?"
                    }]
                },
                {
                    "kpi_id": "T1.P2.K2",
                    "kpi_name": "Thermal Hotspot Mitigation & Per-Rack Power Density Governance",
                    "questions": [{
                        "question_id": "T1.P2.K2.PR1",
                        "question_text": "How are airflow containment, cold/hot aisle layouts, and thermal hotspots managed across high-density server enclosures?"
                    }]
                },
                {
                    "kpi_id": "T1.P2.K3",
                    "kpi_name": "HVAC Cooling Resiliency (N+1 / 2N) & Concurrent Maintainability",
                    "questions": [{
                        "question_id": "T1.P2.K3.PR1",
                        "question_text": "What level of cooling redundancy (N+1 or 2N) is maintained, and can chillers/CRAC units be serviced concurrently without thermal degradation?"
                    }]
                }
            ]
        },
        {
            "pillar_id": "T1.P3",
            "pillar_name": "Physical Security & Access Control",
            "weight_pct": 16,
            "kpis": [
                {
                    "kpi_id": "T1.P3.K1",
                    "kpi_name": "Zoned Physical Access Control & Biometric Multi-Factor Authentication",
                    "questions": [{
                        "question_id": "T1.P3.K1.PR1",
                        "question_text": "What multi-layered physical security controls and biometric validation mechanisms govern ingress to critical whitespace and caged suites?"
                    }]
                },
                {
                    "kpi_id": "T1.P3.K2",
                    "kpi_name": "Vendor Escort Protocols, Room Access Logging & Permits to Work",
                    "questions": [{
                        "question_id": "T1.P3.K2.PR1",
                        "question_text": "How are third-party vendor visits, room access logs, and permits to work managed and audited for physical facility changes?"
                    }]
                },
                {
                    "kpi_id": "T1.P3.K3",
                    "kpi_name": "CCTV Surveillance Coverage, Access Logs & Tamper-Proof Audit Retention",
                    "questions": [{
                        "question_id": "T1.P3.K3.PR1",
                        "question_text": "What is the coverage, retention period, and tamper-resistance of CCTV surveillance and physical biometric access audit trails?"
                    }]
                }
            ]
        },
        {
            "pillar_id": "T1.P4",
            "pillar_name": "Fire Suppression & Environmental Safety",
            "weight_pct": 22,
            "kpis": [
                {
                    "kpi_id": "T1.P4.K1",
                    "kpi_name": "Early Fire Detection (VESDA/Aspirating Smoke) & Room Compartmentalization",
                    "questions": [{
                        "question_id": "T1.P4.K1.PR1",
                        "question_text": "How are very early warning aspirating smoke detection systems (VESDA) and fire-rated room barriers deployed and tested?"
                    }]
                },
                {
                    "kpi_id": "T1.P4.K2",
                    "kpi_name": "Clean Agent Gaseous Fire Suppression & Discharge System Certification",
                    "questions": [{
                        "question_id": "T1.P4.K2.PR1",
                        "question_text": "What gaseous clean-agent suppression systems (e.g. FM-200, Novec 1230, Inergen) protectWhitespace, and how frequently are room integrity tests conducted?"
                    }]
                },
                {
                    "kpi_id": "T1.P4.K3",
                    "kpi_name": "Environmental Perimeter Hazards: Water Ingress, Flood & Contaminant Mitigation",
                    "questions": [{
                        "question_id": "T1.P4.K3.PR1",
                        "question_text": "What water-detection rope telemetry, flood mitigation barriers, and particulate contaminant controls protect technical rooms?"
                    }]
                }
            ]
        },
        {
            "pillar_id": "T1.P5",
            "pillar_name": "Facilities Operations, Monitoring & Maintenance",
            "weight_pct": 18,
            "kpis": [
                {
                    "kpi_id": "T1.P5.K1",
                    "kpi_name": "Continuous Infrastructure Telemetry (DCIM/BMS) & Unified Alarm Triage",
                    "questions": [{
                        "question_id": "T1.P5.K1.PR1",
                        "question_text": "How does the building management system (BMS) and DCIM platform monitor facility sensors and alert on anomalous conditions 24/7?"
                    }]
                },
                {
                    "kpi_id": "T1.P5.K2",
                    "kpi_name": "Preventive Maintenance Schedules, Vendor SLAs & Spares Inventory",
                    "questions": [{
                        "question_id": "T1.P5.K2.PR1",
                        "question_text": "What preventive maintenance cadences, vendor response SLAs, and on-site spare part inventories protect critical power and cooling gear?"
                    }]
                },
                {
                    "kpi_id": "T1.P5.K3",
                    "kpi_name": "Facility Capacity Planning & Lifecycle Refresh (Space, Power, Cooling)",
                    "questions": [{
                        "question_id": "T1.P5.K3.PR1",
                        "question_text": "How is long-term capacity utilization across floor space, power circuits, and cooling loops modeled to anticipate equipment end-of-life?"
                    }]
                }
            ]
        }
    ]

    data["pillars"] = pillars_english

    # Re-sync questions lookup flat array
    all_questions = []
    for pil in pillars_english:
        for k in pil["kpis"]:
            for q in k["questions"]:
                all_questions.append({
                    "question_id": q["question_id"],
                    "question_text": q["question_text"],
                    "pillar_id": pil["pillar_id"],
                    "kpi_id": k["kpi_id"],
                    "kpi_name": k["kpi_name"]
                })
    data["questions"] = all_questions

    T1_DEF_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Refactored {T1_DEF_PATH.name} to 100% canonical Technical English.")


if __name__ == "__main__":
    refactor_t1()
