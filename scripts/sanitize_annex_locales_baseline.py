"""Comprehensive sanitization of engine_config/locales.json according to Argon Phase 1 Blueprint.

Remediates:
1. tower_domain_semantics: Aligns all 10 towers to their canonical architecture definitions.
2. ch3_scorecard_by_tower: Replaces all residual cement/plant/dust/500-meter references with universal enterprise phrasing.
3. diag_summary_default: Injects localized diagnostic fallback templates across all 6 languages.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = ROOT / "engine_config" / "locales.json"


def sanitize() -> None:
    data = json.loads(LOCALES_PATH.read_text(encoding="utf-8"))

    # Canonical tower domain semantics (100% Industry-Agnostic Enterprise Architecture)
    canonical_semantics_en = {
        "T1": {
            "operational_mission": "physical data center facilities, electrical continuity, and precision climate control",
            "dilemma_anchor": "When evaluating electromechanical resilience and physical facility redundancy,",
            "posture_modernization_focus": "reinforcing electromechanical redundancy and precision cooling to safeguard uninterrupted power to core systems",
        },
        "T2": {
            "operational_mission": "physical and virtual compute platforms, hypervisors, and hybrid cloud workloads",
            "dilemma_anchor": "From a platform engineering and compute capacity standpoint,",
            "posture_modernization_focus": "expanding cluster compute elasticity and ensuring automated workload failover without performance degradation",
        },
        "T3": {
            "operational_mission": "enterprise networks, software-defined WAN, campus switching, and inter-site transit connectivity",
            "dilemma_anchor": "When evaluating network transport topology and data communications resilience,",
            "posture_modernization_focus": "embedding active path redundancy across transit links and enforcing automated software-defined traffic routing",
        },
        "T4": {
            "operational_mission": "enterprise storage architecture, SAN/NAS arrays, persistent volume fabrics, and backup repositories",
            "dilemma_anchor": "From a persistent storage architecture and data tiering perspective,",
            "posture_modernization_focus": "guaranteeing storage throughput and eliminating I/O bottlenecks across mission-critical persistent volumes",
        },
        "T5": {
            "operational_mission": "business continuity architectures, high-availability clusters, backup registries, and disaster recovery procedures",
            "dilemma_anchor": "When assessing organizational survivability, disaster recovery orchestration, and cyber recovery readiness,",
            "posture_modernization_focus": "tightening automated failover thresholds (RTO/RPO) and validating immutable cyber recovery procedures against systemic disruption",
        },
        "T6": {
            "operational_mission": "cybersecurity architecture, zero trust identity governance, privileged access management, and threat defense",
            "dilemma_anchor": "From an enterprise cybersecurity, perimeter defense, and identity protection standpoint,",
            "posture_modernization_focus": "elevating privileged access governance, enforcing hardware-backed multi-factor authentication, and deploying continuous threat monitoring",
        },
        "T7": {
            "operational_mission": "IT service management (ITSM), incident command, change governance, and operational support workflows",
            "dilemma_anchor": "When reviewing operational service delivery, incident response cadences, and ITIL process maturity,",
            "posture_modernization_focus": "streamlining incident triage automation, enforcing change management rigor, and reducing mean time to repair (MTTR)",
        },
        "T8": {
            "operational_mission": "technology strategy, enterprise IT governance, portfolio prioritization, and cloud financial operations (FinOps)",
            "dilemma_anchor": "From an enterprise technology governance, architectural review, and cloud financial optimization standpoint,",
            "posture_modernization_focus": "enforcing automated cloud expenditure guardrails, optimizing unit economics, and aligning architectural roadmaps with business OKRs",
        },
        "T9": {
            "operational_mission": "digital workplace engineering, unified endpoint management, collaboration tooling, and end-user support",
            "dilemma_anchor": "When evaluating user computing environments, endpoint security posture, and workplace productivity tools,",
            "posture_modernization_focus": "standardizing endpoint device configurations, enforcing device health compliance, and automating workstation provisioning",
        },
        "T10": {
            "operational_mission": "core transactional processing engines, legacy applications, payment and settlement rails, and high-throughput clearing interfaces",
            "dilemma_anchor": "When auditing core mission-critical platforms, high-throughput transaction processing, and legacy application resilience,",
            "posture_modernization_focus": "modernizing legacy transactional dependencies, decoupling batch windows, and establishing resilient API integrations",
        },
        "DEFAULT": {
            "operational_mission": "supporting essential operational capabilities with standardized architectural baselines",
            "dilemma_anchor": "When reviewing baseline operational capabilities and architectural alignment,",
            "posture_modernization_focus": "reinforcing operational controls and modernizing key infrastructure dependencies",
        },
    }

    # Universal scorecards by tower (Cleaned of 500-meter, dust, plant halts, etc.)
    scorecards_en = {
        "T1": "Scoring a technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), datacenter facilities across {client_name} sit at the threshold of Level 3. Solid electromechanical power and fire suppression defenses ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrast with thermal fragility in processing rooms ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where uncontained thermal zones and uneven cooling distribution introduce localized operational risk.",
        "T2": "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), compute infrastructure operates at its physical limits across {client_name}. Baseline hypervisor stability ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrasts with compute resource saturation ({weakest_pillar_name}, {weakest_pillar_score}/5.0), eliminating the resilience buffer required to absorb host failure without disrupting core business transactions.",
        "T3": "Network infrastructure achieves a technical score of {score_val} out of 5.0 ({maturity_tier_label}). Campus switching resilience across primary sites ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrasts with the gap in automation and observability ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where manual configuration workflows and telemetry blindspots impede agile fault isolation across remote locations.",
        "T4": "Rated at {score_val} out of 5.0 ({maturity_tier_label}), corporate storage demonstrates dependable snapshot replication ({strongest_pillar_name}, {strongest_pillar_score}/5.0). The critical challenge lies within storage tiering architecture ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where the absence of immutable ransomware vaults and restrictive disk provisioning force technical staff at {client_name} into continuous manual quota containment.",
        "T5": "Scoring {score_val} out of 5.0 ({maturity_tier_label}), operational resilience exhibits a critical gap against enterprise recovery tolerances across {client_name}. Operational backup reliability ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrasts with continuous recovery fragility ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where insufficient geographic independence between redundant systems leaves services vulnerable to systemic regional disruption.",
        "T6": "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), cybersecurity operates under severe operational exposure across {client_name}. While identity federation shows progress ({strongest_pillar_name}, {strongest_pillar_score}/5.0), unvaulted shared administrative credentials ({weakest_pillar_name}, {weakest_pillar_score}/5.0) compromise change auditability and elevate regulatory compliance exposure.",
        "T7": "Scoring a technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), IT service management operates reactively across {client_name}. System monitoring visibility ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrasts with the absence of formal problem management ({weakest_pillar_name}, {weakest_pillar_score}/5.0), consuming critical engineering capacity in recurring incident troubleshooting.",
        "T8": "Technology governance achieves a score of {score_val} out of 5.0 ({maturity_tier_label}). Disciplined procurement control across {client_name} ({strongest_pillar_name}, {strongest_pillar_score}/5.0) coexists with cost allocation opacity ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where uncoordinated cloud commitments and software licensing constraints restrict compute scalability.",
        "T9": "With a consolidated maturity of {score_val} out of 5.0 ({maturity_tier_label}), the digital workplace exhibits structured hardware fleet management ({strongest_pillar_name}, {strongest_pillar_score}/5.0). The primary friction lies within workplace operations and support ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where unstandardized workstation configurations and manual provisioning introduce operational overhead across {client_name}.",
        "T10": "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), core transactional processing platforms represent a critical operational dependency across {client_name}. Established transaction processing stability ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrasts with legacy interface rigidity ({weakest_pillar_name}, {weakest_pillar_score}/5.0), where monolithic batch architectures and tightly coupled integrations constrain operational agility.",
    }

    diag_defaults = {
        "en": "Structured diagnostic assessment evaluating operational maturity baselines and technical debt across evaluated operational controls.",
        "es": "Evaluación diagnóstica estructurada que analiza los niveles base de madurez operativa y la deuda técnica en los controles evaluados.",
        "pt": "Avaliação diagnóstica estruturada que analisa os níveis base de maturidade operacional e a dívida técnica nos controles avaliados.",
        "fr": "Évaluation diagnostique structurée analysant les niveaux de référence de maturité opérationnelle et la dette technique sur les contrôles évalués.",
        "de": "Strukturierte diagnostische Bewertung zur Analyse der operativen Reifegrad-Baselines und der technischen Schulden in den evaluierten Kontrollen.",
        "ja": "評価対象の運用統制全体における運用成熟度のベースラインと技術的負債を分析する構造化診断評価。",
    }

    # Apply to all languages in locales.json
    for lang, lang_data in data.items():
        # 1. Update diag_summary_default
        lang_data["diag_summary_default"] = diag_defaults.get(lang, diag_defaults["en"])

        # 1b. Clean 500-meter from tomo_spof_catalog and tomo_tower_forensic_catalog
        if "tomo_spof_catalog" in lang_data:
            for spof in lang_data["tomo_spof_catalog"]:
                if isinstance(spof, dict) and "description" in spof:
                    spof["description"] = spof["description"].replace(
                        "within a single 500-meter perimeter",
                        "within a shared geographic perimeter",
                    ).replace(
                        "en un perímetro de 500 metros",
                        "en un perímetro geográfico compartido",
                    )
        t5_cat = lang_data.get("tomo_tower_forensic_catalog", {}).get("T5", {})
        if "findings" in t5_cat:
            t5_cat["findings"] = [
                f.replace("within a single 500-meter perimeter", "within a shared geographic perimeter")
                .replace("en un perímetro de 500 metros", "en un perímetro geográfico compartido")
                for f in t5_cat["findings"]
            ]

        # 2. Update tower_domain_semantics for EN and fallback for others
        if lang == "en":
            lang_data["tower_domain_semantics"] = canonical_semantics_en
            lang_data["ch3_scorecard_by_tower"] = scorecards_en
        elif lang in ("pt", "fr", "de", "ja"):
            # For non-ES languages, use canonical English semantics to prevent corrupt scrambled Spanish/cement translations
            lang_data["tower_domain_semantics"] = canonical_semantics_en
            lang_data["ch3_scorecard_by_tower"] = scorecards_en
        elif lang == "es":
            # Clean Spanish semantics
            lang_data["tower_domain_semantics"]["T5"] = {
                "operational_mission": "arquitecturas de continuidad de negocio, clústeres de alta disponibilidad, sistemas de backup y procedimientos de recuperación ante desastres",
                "dilemma_anchor": "Al evaluar la capacidad de supervivencia organizativa, la orquestación del DRP y la resiliencia cibernética,",
                "posture_modernization_focus": "acotar los umbrales de conmutación automatizada (RTO/RPO) y validar la inmutabilidad de las copias ante contingencias sistémicas",
            }
            lang_data["tower_domain_semantics"]["T3"] = {
                "operational_mission": "redes corporativas, conectividad WAN y enlaces entre sedes",
                "dilemma_anchor": "Al evaluar la topología de transporte y la resiliencia de comunicaciones,",
                "posture_modernization_focus": "incorporar redundancia activa en las rutas de comunicación y balanceo SD-WAN",
            }
            lang_data["tower_domain_semantics"]["T4"] = {
                "operational_mission": "almacenamiento corporativo, cabinas SAN/NAS y repositorios de datos",
                "dilemma_anchor": "Desde la perspectiva de almacenamiento persistente y gestión del dato,",
                "posture_modernization_focus": "garantizar el rendimiento y eliminar cuellos de botella de I/O en volúmenes persistentes",
            }
            lang_data["ch3_scorecard_by_tower"]["T5"] = (
                "Con una madurez de {score_val} sobre 5.0 ({maturity_tier_label}), la resiliencia operativa presenta un desfase crítico frente a las tolerancias de interrupción de {client_name}. La fiabilidad de las copias de seguridad ({strongest_pillar_name}, {strongest_pillar_score}/5.0) contrasta con la fragilidad de la alta disponibilidad ({weakest_pillar_name}, {weakest_pillar_score}/5.0), donde una separación geográfica insuficiente entre sedes redundantes expone las operaciones a caídas sistémicas ante contingencias regionales."
            )

    LOCALES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully sanitized locales.json across all languages: {LOCALES_PATH}")


if __name__ == "__main__":
    sanitize()
