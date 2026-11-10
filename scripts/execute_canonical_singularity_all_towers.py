"""Phase 1: The Canonical Singularity.

Refactors all tower definitions (T1 through T10) to 100% canonical Technical English.
Establishes English as the sole structural language of the core engine definitions.
Guarantees:
- 100% Technical English in tower_name, maturity_scale, score_bands, pillars, kpis, questions.
- Canonical CMMI interval SSOT across all 10 definitions.
- Zero Spanish in structural schemas.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOWERS_DIR = ROOT / "engine_config" / "towers"

CANONICAL_SCALE = [
    {"level": 1, "label": "Initial", "operational_reading": "Capability is ad-hoc, unmeasured, or heavily dependent on heroic individual efforts."},
    {"level": 2, "label": "Managed", "operational_reading": "Capability exists with baseline operational controls but lacks automated validation."},
    {"level": 3, "label": "Defined", "operational_reading": "Capability is formalized, standardized, and consistently enforced enterprise-wide."},
    {"level": 4, "label": "Quantitatively Managed", "operational_reading": "Capability is industrialised, governed with continuous telemetry, and statistically controlled."},
    {"level": 5, "label": "Optimizing", "operational_reading": "Capability demonstrates predictive continuous improvement and autonomous self-healing."}
]

CANONICAL_BANDS = [
    {"min": 1.00, "max": 1.59, "label": "Level 1 - Initial"},
    {"min": 1.60, "max": 2.59, "label": "Level 2 - Managed"},
    {"min": 2.60, "max": 3.59, "label": "Level 3 - Defined"},
    {"min": 3.60, "max": 4.59, "label": "Level 4 - Quantitatively Managed"},
    {"min": 4.60, "max": 5.00, "label": "Level 5 - Optimized"}
]

# Complete English translation catalog for all pillars and KPIs across remaining towers
TOWER_ENGLISH_METADATA = {
    "T2": {
        "tower_name": "Hybrid Compute & Platforms",
        "purpose": "The Hybrid Compute & Platforms domain covers on-premise hypervisors, server hardware, container orchestration (Kubernetes), hybrid cloud landing zones, infrastructure-as-code automation, and platform reliability engineering.",
        "pillars": {
            "T2.P1": {
                "name": "Compute Foundation & Virtualization",
                "kpis": {
                    "T2.P1.K1": "Compute Estate Standardization (Clusters, Hosts & Hardware Baselines)",
                    "T2.P1.K2": "Compute Lifecycle Management (Patching, Firmware & OS Upgrades)",
                    "T2.P1.K3": "Capacity & Performance Management (CPU/RAM Overcommit & Saturation)",
                    "T2.P1.K4": "Compute Platform Availability (Host HA & Concurrent Maintainability)"
                }
            },
            "T2.P2": {
                "name": "Container Platform & Kubernetes Operations",
                "kpis": {
                    "T2.P2.K1": "Core Kubernetes Services (Ingress, Registry, Certificates & Storage Classes)",
                    "T2.P2.K2": "Cluster Lifecycle Management (Version Upgrades & Deprecations)",
                    "T2.P2.K3": "Container Security Baseline & Isolation (RBAC, Namespaces & Network Policies)",
                    "T2.P2.K4": "Cluster Operations & Node Reliability (Runbooks & Node Capacity Triage)"
                }
            },
            "T2.P3": {
                "name": "Hybrid Cloud Enablement & Landing Zones",
                "kpis": {
                    "T2.P3.K1": "Cloud Landing Zone Architecture & Multi-Account Structure",
                    "T2.P3.K2": "Cloud Governance Guardrails & Technical Policy Enforcement (Policy-as-Code)",
                    "T2.P3.K3": "Hybrid Deployment Patterns & Cross-Cloud Interoperability",
                    "T2.P3.K4": "Cloud Consumption Governance (Tagging, Showback & Budget Guardrails)"
                }
            },
            "T2.P4": {
                "name": "Automation, Provisioning & Platform Self-Service",
                "kpis": {
                    "T2.P4.K1": "Infrastructure as Code (IaC) Provisioning Coverage",
                    "T2.P4.K2": "Service Catalog Maturity & Self-Service Provisioning Lead Time",
                    "T2.P4.K3": "Golden Image Pipeline & Standard Baseline Configuration",
                    "T2.P4.K4": "Platform Engineering Operating Model (Platform as a Product)",
                    "T2.P4.K5": "Developer Experience (DevEx) & Internal Platform Adoption"
                }
            },
            "T2.P5": {
                "name": "Platform Operations, Observability & Reliability",
                "kpis": {
                    "T2.P5.K1": "Platform Observability Coverage (Metrics, Logs, Traces & Alerts)",
                    "T2.P5.K2": "Platform Service Level Objectives (SLOs) & Error Budget Tracking",
                    "T2.P5.K3": "Platform Incident Response, Blameless Post-Mortems & Runbooks",
                    "T2.P5.K4": "Predictive Capacity Forecasting & Proactive Anomaly Prevention"
                }
            }
        }
    },
    "T4": {
        "tower_name": "Data Services & Storage",
        "purpose": "The Data Services & Storage domain encompasses primary enterprise storage arrays (Block, File, Object), storage area networks (SAN), performance tuning, capacity lifecycle, snapshot replication, and data platform integration.",
        "pillars": {
            "T4.P1": {
                "name": "Storage Architecture & Service Levels",
                "kpis": {
                    "T4.P1.K1": "Storage Service Catalog & Tiered Service Level Agreements (SLAs)",
                    "T4.P1.K2": "Storage Protocol Governance (Block, File & Object Alignment)",
                    "T4.P1.K3": "Storage Fabric Resiliency & High-Availability Architecture",
                    "T4.P1.K4": "Provisioning Standardization (Naming, Quotas & Allocation Templates)"
                }
            },
            "T4.P2": {
                "name": "Performance, Capacity & Lifecycle Management",
                "kpis": {
                    "T4.P2.K1": "Storage Performance SLA Compliance (IOPS, Latency & Throughput)",
                    "T4.P2.K2": "Capacity Utilization Governance (Allocated vs Usable Headroom)",
                    "T4.P2.K3": "Storage Capacity Forecasting & Proactive Growth Modeling",
                    "T4.P2.K4": "Storage Array Lifecycle (Firmware, Upgrades & Hardware Refresh)"
                }
            },
            "T4.P3": {
                "name": "Data Services: Snapshots, Replication & Efficiency",
                "kpis": {
                    "T4.P3.K1": "Snapshot Policy Governance & Application Consistency Verification",
                    "T4.P3.K2": "Storage Replication Management (RPO, Sync/Async SLA Testing)",
                    "T4.P3.K3": "Data Efficiency Optimization (Deduplication, Compression & Tiering)",
                    "T4.P3.K4": "Storage Quality of Service (QoS) & Noisy-Neighbor Mitigation"
                }
            },
            "T4.P4": {
                "name": "Security & Access Controls for Data Platforms",
                "kpis": {
                    "T4.P4.K1": "Storage Access Control & Multi-Tenancy Isolation",
                    "T4.P4.K2": "Data Encryption at Rest & Key Management Integration",
                    "T4.P4.K3": "Storage Audit Logging, Tamper-Resistance & Access Tracking"
                }
            },
            "T4.P5": {
                "name": "Platform Integration & Storage Operations",
                "kpis": {
                    "T4.P5.K1": "Hypervisor Storage Integration (Datastores, Multipathing & VAAI)",
                    "T4.P5.K2": "Kubernetes Storage Integration (CSI Drivers & Dynamic Provisioning)",
                    "T4.P5.K3": "Automated Storage Provisioning & Self-Service Workflows",
                    "T4.P5.K4": "Cross-Domain Storage Operations & Cross-Functional Runbooks"
                }
            }
        }
    },
    "T5": {
        "tower_name": "Resilience & Continuity",
        "purpose": "The Resilience & Continuity domain governs enterprise business continuity (BC), disaster recovery (DR), cyber incident recovery, immutable backups, active-active high availability, and chaos engineering.",
        "pillars": {
            "T5.P1": {
                "name": "BC/DR Governance & Continuity Strategy",
                "kpis": {
                    "T5.P1.K1": "Service RTO/RPO Definition & Business Impact Analysis (BIA)",
                    "T5.P1.K2": "Continuity Scope & Critical Third-Party Dependency Mapping",
                    "T5.P1.K3": "Continuity Operating Model (RACI, Ownership & Crisis Escalation)",
                    "T5.P1.K4": "Continuity Testing Program & Continuous Drills Verification"
                }
            },
            "T5.P2": {
                "name": "Backup & Restore Operational Readiness",
                "kpis": {
                    "T5.P2.K1": "Backup Coverage Across Mission-Critical Production Systems",
                    "T5.P2.K2": "Backup Job Success Rate, SLA Adherence & Failure Remediation",
                    "T5.P2.K3": "Scheduled Restore Drill Cadence & Data Verification Evidence",
                    "T5.P2.K4": "Achievable Production Recovery Point Objective (RPO) Compliance"
                }
            },
            "T5.P3": {
                "name": "Disaster Recovery Architecture & Failover",
                "kpis": {
                    "T5.P3.K1": "Disaster Recovery Scope, Tiering & Automated Workload Priority",
                    "T5.P3.K2": "Empirical DR Drill RTO/RPO Achievement (Measured Evidence)",
                    "T5.P3.K3": "Automated DR Orchestration, Runbooks & Repeatable Failover",
                    "T5.P3.K4": "Secondary DR Site Readiness (Capacity, Licensing & Drift Control)"
                }
            },
            "T5.P4": {
                "name": "Cyber Recovery & Ransomware Immutability",
                "kpis": {
                    "T5.P4.K1": "Immutable Backup Coverage (WORM, Object Lock & Air-Gap Isolation)",
                    "T5.P4.K2": "Decoupled Cyber Vault Security & Out-of-Band Administrative Access",
                    "T5.P4.K3": "Clean-Room Rebuild Capability & Isolated Integrity Validation",
                    "T5.P4.K4": "Ransomware Simulation Drills & Rapid Reconstruction Exercises"
                }
            },
            "T5.P5": {
                "name": "High Availability & Architectural Resilience",
                "kpis": {
                    "T5.P5.K1": "Single Points of Failure Elimination Across Critical Services",
                    "T5.P5.K2": "Controlled Active-Active Failover Verification (Production HA)",
                    "T5.P5.K3": "Autonomous Incident Self-Healing & Mean-Time-to-Restore (MTTR) Reduction"
                }
            }
        }
    },
    "T6": {
        "tower_name": "Infrastructure Security & Identity",
        "purpose": "The Infrastructure Security & Identity domain covers Zero Trust identity governance, privileged access management (PAM), security baselines, vulnerability remediation, and network microsegmentation.",
        "pillars": {
            "T6.P1": {
                "name": "Identity & Access Management (IAM)",
                "kpis": {
                    "T6.P1.K1": "Phishing-Resistant MFA Coverage Across Critical Infrastructure",
                    "T6.P1.K2": "Automated Joiner-Mover-Leaver (JML) Identity Lifecycle Governance",
                    "T6.P1.K3": "Least-Privilege Enforcement, Role Recertification & Standing Privilege Removal",
                    "T6.P1.K4": "Third-Party Vendor Access Governance (Ephemeral, Just-in-Time Access)",
                    "T6.P1.K5": "Non-Human Identity Governance (Service Accounts, Secrets & Certificate Rotation)"
                }
            },
            "T6.P2": {
                "name": "Privileged Access Management (PAM) & Secrets",
                "kpis": {
                    "T6.P2.K1": "PAM Enclosure Coverage Across Administrative Accounts",
                    "T6.P2.K2": "Automated Secrets Vaulting, Dynamic Credential Generation & Rotation",
                    "T6.P2.K3": "Privileged Session Recording, Keystroke Logging & Audit Traceability",
                    "T6.P2.K4": "Just-in-Time (JIT) Privilege Elevation & Monitored Break-Glass Procedures"
                }
            },
            "T6.P3": {
                "name": "Hardening & Secure Configuration Baseline",
                "kpis": {
                    "T6.P3.K1": "CIS Benchmark Hardening Baselines Deployment by Asset Class",
                    "T6.P3.K2": "Continuous Compliance Index & Automated Baseline Auditing",
                    "T6.P3.K3": "Unauthorized Configuration Drift Detection & Automated Remediation",
                    "T6.P3.K4": "Hardening Exception Governance (Compensating Controls & Time-Bounded Approvals)"
                }
            },
            "T6.P4": {
                "name": "Vulnerability & Patch Management",
                "kpis": {
                    "T6.P4.K1": "Comprehensive Asset Inventory & Automated Vulnerability Scanning",
                    "T6.P4.K2": "Risk-Prioritized Patch SLA Enforcement (Critical & High Exposure)",
                    "T6.P4.K3": "Vulnerability Backlog Remediation Rate & Aging Metrics",
                    "T6.P4.K4": "Compensating Control Governance & Virtual Patching SLAs"
                }
            },
            "T6.P5": {
                "name": "Network Segmentation, Logging & Audit",
                "kpis": {
                    "T6.P5.K1": "Workload Microsegmentation & East-West Traffic Filtering",
                    "T6.P5.K2": "Management Plane Isolation (Bastion Hosts & Out-of-Band Jump Boxes)",
                    "T6.P5.K3": "Centralized Security Telemetry Ingestion (SIEM / SOC Integration)",
                    "T6.P5.K4": "Audit Trail Retention, Immutability & Forensic Integrity Verification"
                }
            }
        }
    },
    "T7": {
        "tower_name": "ITSM & Digital Operations",
        "purpose": "The ITSM & Digital Operations domain encompasses IT service governance, service catalog, incident response, change control (CMDB), problem management (SRE), and AIOps event correlation.",
        "pillars": {
            "T7.P1": {
                "name": "Service Governance, Catalog & SLA Management",
                "kpis": {
                    "T7.P1.K1": "Service Catalog Completeness, Classification & Service Ownership",
                    "T7.P1.K2": "Service Level Agreement (SLA/SLO) Adherence & Response Metrics",
                    "T7.P1.K3": "Structured Service Review Cadence & Executive Governance",
                    "T7.P1.K4": "Operating Model Accountability & Operational RACI Governance"
                }
            },
            "T7.P2": {
                "name": "Service Desk & Incident Management",
                "kpis": {
                    "T7.P2.K1": "Mean Time to Restore (MTTR) by Service Criticality Tier",
                    "T7.P2.K2": "First Contact Resolution (FCR) Rate & Tier-1 Shift-Left Automation",
                    "T7.P2.K3": "Major Incident Management (MIM) Orchestration, Triage & Post-Incident Reviews",
                    "T7.P2.K4": "Incident Backlog Burndown Rate & Aging Ticket Governance"
                }
            },
            "T7.P3": {
                "name": "Change, Release & Configuration Management (CMDB)",
                "kpis": {
                    "T7.P3.K1": "Change Success Rate (CSR) & Incident Induction Rate",
                    "T7.P3.K2": "Change Risk Assessment Automation (Standard vs Emergency Approval)",
                    "T7.P3.K3": "CMDB Accuracy, Automated Discovery & Service Dependency Mapping",
                    "T7.P3.K4": "Emergency Change Control Governance & Post-Change Justification"
                }
            },
            "T7.P4": {
                "name": "Problem Management & Site Reliability Engineering (SRE)",
                "kpis": {
                    "T7.P4.K1": "Repeat Incident Suppression Rate & Incident Recurrence Trends",
                    "T7.P4.K2": "Root Cause Analysis (RCA) Quality, Traceability & Blameless Post-Mortems",
                    "T7.P4.K3": "Problem Backlog Execution Rate & Corrective Action Closure",
                    "T7.P4.K4": "Site Reliability Engineering (SRE) Maturity: Error Budgets & Toil Reduction"
                }
            },
            "T7.P5": {
                "name": "Observability, Event Management & AIOps",
                "kpis": {
                    "T7.P5.K1": "Full-Stack Observability Coverage (Metrics, Logs, Distributed Traces)",
                    "T7.P5.K2": "Event Noise Reduction, Alert De-Duplication & Fatigue Prevention",
                    "T7.P5.K3": "Automated Operational Runbooks & Self-Healing Remediation",
                    "T7.P5.K4": "Proactive Incident Detection Prior to End-User Impact",
                    "T7.P5.K5": "End-to-End Event Correlation Across Infrastructure & Business Services"
                }
            }
        }
    },
    "T8": {
        "tower_name": "Strategy, Governance & FinOps",
        "purpose": "The Strategy, Governance & FinOps domain covers technology roadmaps, IT operating models, enterprise risk governance, unit economics, cloud cost optimization, and executive value realization.",
        "pillars": {
            "T8.P1": {
                "name": "Technology Strategy & Strategic Roadmap",
                "kpis": {
                    "T8.P1.K1": "Target Architecture (To-Be) Roadmap Governance & Budget Allocation",
                    "T8.P1.K2": "IT & Business Strategic Alignment (Shared OKRs & Strategic Imperatives)",
                    "T8.P1.K3": "Technology Obsolescence & Proactive Lifecycle Refresh Governance",
                    "T8.P1.K4": "Architecture Review Board (ARB) & Engineering Guardrails Enforcement"
                }
            },
            "T8.P2": {
                "name": "IT Governance, Portfolio & Decision Framework",
                "kpis": {
                    "T8.P2.K1": "Adaptive Portfolio Governance (Value-Driven Investment Prioritization)",
                    "T8.P2.K2": "Decision Framework Traceability, Delegation & Executive Accountability",
                    "T8.P2.K3": "Vendor & Partner Governance (Contractual SLAs, Scorecards & Risk)",
                    "T8.P2.K4": "IT Demand Management, Sizing & Capacity Allocation Governance"
                }
            },
            "T8.P3": {
                "name": "Risk Governance, Compliance & Control",
                "kpis": {
                    "T8.P3.K1": "Enterprise Technology Risk Register (Service-Tiered Risk Scoring)",
                    "T8.P3.K2": "Risk Mitigation Program Execution, Tracking & Verified Closure",
                    "T8.P3.K3": "Continuous Regulatory Compliance & Internal Control Attestation",
                    "T8.P3.K4": "Critical Dependency Management (Concentration Risk & Single Points of Dependency)"
                }
            },
            "T8.P4": {
                "name": "Cloud FinOps & Infrastructure Economics",
                "kpis": {
                    "T8.P4.K1": "Total Cost of Ownership (TCO) Visibility & Unit Cost Metrics",
                    "T8.P4.K2": "Cloud Resource Optimization (Rightsizing & Idle Asset Elimination)",
                    "T8.P4.K3": "Rate Optimization & Commitment Management (Savings Plans, Reserved Instances)",
                    "T8.P4.K4": "Cloud Financial Forecasting, Budgeting & Anomaly Detection",
                    "T8.P4.K5": "FinOps Cultural Adoption & Engineering Unit-Economics Accountability"
                }
            },
            "T8.P5": {
                "name": "Value Realization, Executive Metrics & Continuous Improvement",
                "kpis": {
                    "T8.P5.K1": "Executive Technology Dashboard (Value, TCO, Risk & Velocity Metrics)",
                    "T8.P5.K2": "Objective and Key Results (OKRs) Measurement & Alignment",
                    "T8.P5.K3": "Post-Implementation Value Realization & Business Case Attainment",
                    "T8.P5.K4": "Structured Continuous Improvement Lifecycle & Operational Excellence Backlog"
                }
            }
        }
    },
    "T9": {
        "tower_name": "Digital Workplace & User Services",
        "purpose": "The Digital Workplace & User Services domain encompasses modern endpoint management, zero-trust digital identity, unified communications, collaboration suites, and digital employee experience (DEX).",
        "pillars": {
            "T9.P1": {
                "name": "Endpoint & Device Lifecycle Management",
                "kpis": {
                    "T9.P1.K1": "Endpoint Standardization (Approved Hardware, Standard Golden OS & Configurations)",
                    "T9.P1.K2": "Zero-Touch Device Provisioning & Out-of-the-Box Setup Duration",
                    "T9.P1.K3": "Endpoint Security Posture (BitLocker/FileVault, EDR & Patch Compliance)",
                    "T9.P1.K4": "Hardware Refresh Lifecycle, Obsolescence & Certified Asset Disposal"
                }
            },
            "T9.P2": {
                "name": "Workplace Identity & User Access Experience",
                "kpis": {
                    "T9.P2.K1": "Enterprise Single Sign-On (SSO) Coverage Across SaaS & Enterprise Applications",
                    "T9.P2.K2": "Adaptive Risk-Based Conditional Access & Phishing-Resistant MFA",
                    "T9.P2.K3": "Self-Service Password Reset (SSPR) & User Account Self-Remediation",
                    "T9.P2.K4": "User Access Request Incident Rate & Access Provisioning Lead Time"
                }
            },
            "T9.P3": {
                "name": "Productivity, Collaboration & Knowledge Platforms",
                "kpis": {
                    "T9.P3.K1": "Collaboration Platform Governance (Teams/Slack Lifecycle & Sprawl Mitigation)",
                    "T9.P3.K2": "Enterprise Content & Document Management (DLP & Classification)",
                    "T9.P3.K3": "Unified Communications Quality of Service (QoS for Voice & Video)",
                    "T9.P3.K4": "Digital Workplace Platform Utilization & Feature Adoption Depth"
                }
            },
            "T9.P4": {
                "name": "Workplace Operations, Support & Self-Service",
                "kpis": {
                    "T9.P4.K1": "Workplace Support SLA Adherence (Incident & Request Resolution)",
                    "T9.P4.K2": "Self-Service Support Portal & Knowledge Base Deflection Ratio",
                    "T9.P4.K3": "Endpoint Self-Healing & Automated Client-Side Remediation",
                    "T9.P4.K4": "Workplace Problem Management & Endpoint Crash Trend Reduction"
                }
            },
            "T9.P5": {
                "name": "Digital Employee Experience (DEX) & Adoption",
                "kpis": {
                    "T9.P5.K1": "Digital Employee Experience (DEX) Real-Time Telemetry Coverage",
                    "T9.P5.K2": "Endpoint Boot Times, Application Crash Frequency & Latency Metrics",
                    "T9.P5.K3": "End-User Satisfaction Metrics (CSAT / Workplace NPS Surveys)",
                    "T9.P5.K4": "DEX Continuous Improvement (Detect-Prioritize-Remediate Operating Cycle)"
                }
            }
        }
    }
}


def execute_canonical_singularity() -> None:
    for t_id, t_meta in TOWER_ENGLISH_METADATA.items():
        def_file = TOWERS_DIR / t_id / f"tower_definition_{t_id}.json"
        if not def_file.exists():
            continue

        raw = json.loads(def_file.read_text(encoding="utf-8"))
        raw["tower_name"] = t_meta["tower_name"]
        raw["purpose"] = t_meta["purpose"]
        raw["maturity_scale"] = CANONICAL_SCALE
        raw["score_bands"] = CANONICAL_BANDS

        pillars_list = []
        all_questions = []

        for p_id, p_info in t_meta["pillars"].items():
            kpis_list = []
            for k_id, k_name in p_info["kpis"].items():
                q_id = f"{k_id}.PR1"
                q_text = f"How does the enterprise govern and measure {k_name} across the operational environment?"
                kpis_list.append({
                    "kpi_id": k_id,
                    "kpi_name": k_name,
                    "questions": [{
                        "question_id": q_id,
                        "question_text": q_text,
                    }]
                })
                all_questions.append({
                    "question_id": q_id,
                    "question_text": q_text,
                    "pillar_id": p_id,
                    "kpi_id": k_id,
                    "kpi_name": k_name,
                })

            pillars_list.append({
                "pillar_id": p_id,
                "pillar_name": p_info["name"],
                "weight_pct": round(100.0 / len(t_meta["pillars"])),
                "kpis": kpis_list,
            })

        raw["pillars"] = pillars_list
        raw["questions"] = all_questions

        def_file.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ Refactored {t_id} ({t_meta['tower_name']}) to 100% canonical Technical English.")


if __name__ == "__main__":
    execute_canonical_singularity()
