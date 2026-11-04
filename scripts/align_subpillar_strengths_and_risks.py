#!/usr/bin/env python3
"""Align subpillar strengths semantically and unify risk IDs across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

ALIGNED_STRENGTHS_ES = {
    "T1": [
        "Sistemas de alimentación ininterrumpida (SAI) en esquema N+1 y grupos electrógenos con mantenimiento regular.",
        "Unidades de climatización de precisión (CRAC) con redundancia y control de temperatura en salas técnicas.",
        "Sistemas automáticos de detección y extinción de incendios por agente limpio en salas principales.",
        "Cuadros eléctricos monitorizados y alarmas técnicas básicas integradas en puestos de control."
    ],
    "T2": [
        "Clúster hiperconvergente centralizado que proporciona alta densidad de cómputo para cargas corporativas.",
        "Alojamiento productivo de cargas críticas (SAP S/4HANA) sobre infraestructura cloud de primer nivel (GCP/Azure).",
        "Estandarización de plantillas base de sistemas operativos para despliegues de servidores virtuales.",
        "Mecanismos de conmutación automática por fallo (HA) operativos a nivel de hipervisor."
    ],
    "T3": [
        "Conmutación troncal de doble núcleo con enlaces redundantes entre armarios de distribución.",
        "Conectividad WAN y SD-WAN establecida hacia la totalidad de plantas industriales, canteras y sedes internacionales.",
        "Perímetro protegido mediante cortafuegos corporativos de última generación con filtrado de tráfico.",
        "Sondas de monitorización de caudal y supervisión de estado de enlaces troncales activas."
    ],
    "T4": [
        "Cabinas de almacenamiento corporativo de alto rendimiento con aprovisionamiento dinámico de capacidad.",
        "Políticas de snapshots programados y replicación asíncrona entre centros operativos.",
        "Configuración de volúmenes de almacenamiento protegidos contra borrado accidental.",
        "Políticas definidas de archivado y depuración periódica de datos no estructurados."
    ],
    "T5": [
        "Políticas de copia de seguridad periódica en disco y cinta con custodia externa documentada.",
        "Procedimientos operativos de contingencia y recuperación documentados para sistemas críticos.",
        "Personal técnico interno con profundo conocimiento de los procesos de restauración manual en planta.",
        "Copias de seguridad desconectadas físicamente (air-gapped) en cintas magnéticas de custodia."
    ],
    "T6": [
        "Dominio centralizado de gestión de identidades y accesos corporativo (Active Directory).",
        "Cortafuegos perimetrales de última generación con políticas corporativas de filtrado y VPN.",
        "Políticas corporativas de contraseñas robustas y segregación inicial de roles administrativos.",
        "Despliegue homogéneo de protección de punto final (EDR) con supervisión por centro de operaciones (SOC)."
    ],
    "T7": [
        "Clústeres de bases de datos relacionales configurados con instancias en alta disponibilidad.",
        "Rutinas programadas de mantenimiento de índices, estadísticas y verificación de integridad en motores SQL/Oracle.",
        "Plataforma centralizada de soporte e incidencias (ITSM) con seguimiento de peticiones y SLAs.",
        "Inventario centralizado de activos de hardware y licencias gestionado por el equipo de TI."
    ],
    "T8": [
        "Implantación madura del ERP corporativo que soporta de forma eficaz las operaciones y finanzas del grupo.",
        "Visibilidad inicial de facturación mensual centralizada en consolas de proveedores cloud (GCP, Azure y OCI).",
        "Integraciones estables entre sistemas de gestión central y plataformas periféricas de expedición.",
        "Acuerdos corporativos consolidados de licenciamiento con fabricantes de software estratégicos."
    ],
    "T9": [
        "Herramientas de colaboración y productividad en la nube ampliamente adoptadas por los usuarios.",
        "Parque homogéneo de puestos de trabajo bajo sistema operativo estándar con despliegue centralizado.",
        "Acceso remoto seguro y aplicaciones de autoservicio disponibles para empleados corporativos.",
        "Canal de soporte de primer nivel estructurado y procedimientos de despliegue automatizado de parches."
    ],
    "T10": [
        "Equipos de pesaje industrial con calibración metrológica periódica y mantenimiento preventivo contratado.",
        "Alta cualificación y compromiso del personal técnico y operativo de planta en la resolución de incidencias.",
        "Procedimientos locales de despacho manual bien establecidos ante contingencias de comunicaciones.",
        "Mecanismo de sincronización de albaranes de pesaje hacia el sistema central de facturación."
    ],
}

ALIGNED_STRENGTHS_EN = {
    "T1": [
        "Uninterruptible power supply (UPS) systems in N+1 redundancy and generator sets with regular maintenance.",
        "Computer Room Air Conditioning (CRAC) precision cooling units with redundancy in technical rooms.",
        "Automated clean-agent fire detection and suppression systems operational across core computer rooms.",
        "Monitored electrical switchboards and basic facility alarms integrated into control consoles."
    ],
    "T2": [
        "Centralized hyperconverged compute cluster providing high computing density for corporate workloads.",
        "Production hosting of mission-critical workloads (SAP S/4HANA) on Tier-1 enterprise cloud (GCP/Azure).",
        "Standardized operating system base templates for virtual server provisioning.",
        "Automated hypervisor-level high availability (HA) failover mechanisms operational."
    ],
    "T3": [
        "Dual-core backbone switching infrastructure with redundant links across distribution frames.",
        "WAN and SD-WAN connectivity established across all manufacturing plants, quarries, and international sites.",
        "Perimeter defended by next-generation corporate firewalls with continuous traffic filtering.",
        "Bandwidth monitoring probes and core uplink status supervision actively operational."
    ],
    "T4": [
        "High-performance enterprise storage arrays with dynamic capacity thin-provisioning.",
        "Scheduled snapshot policies and asynchronous replication operational between operating facilities.",
        "Storage volume protections against accidental deletion actively configured.",
        "Documented lifecycle policies for archiving and periodic purging of unstructured data."
    ],
    "T5": [
        "Scheduled disk and tape backup policies with documented off-site vaulting procedures.",
        "Documented contingency and disaster recovery operational procedures for essential systems.",
        "Skilled internal engineering team with deep operational experience in manual on-site system restoration.",
        "Air-gapped offline magnetic tape backups maintained under secure off-site custody."
    ],
    "T6": [
        "Centralized corporate identity and access management domain (Active Directory).",
        "Next-generation perimeter firewalls enforcing corporate traffic filtering and secure VPN.",
        "Corporate password complexity enforcement and baseline administrative role segregation.",
        "Homogeneous endpoint detection and response (EDR) agent deployment with external SOC monitoring."
    ],
    "T7": [
        "Relational database clusters configured with high-availability standby instances.",
        "Scheduled index maintenance, table statistics, and integrity verification routines in SQL/Oracle.",
        "Centralized IT Service Management (ITSM) platform tracking service requests and SLAs.",
        "Centralized hardware and software license inventory maintained by the IT infrastructure team."
    ],
    "T8": [
        "Mature enterprise ERP platform effectively underpinning group operational and financial transactions.",
        "Centralized monthly billing visibility within multi-cloud consoles (GCP, Azure, and OCI).",
        "Stable integration interfaces connecting ERP core to peripheral plant dispatch systems.",
        "Consolidated corporate enterprise licensing agreements with strategic software vendors."
    ],
    "T9": [
        "Cloud collaboration and productivity suites (M365) widely adopted across business units.",
        "Standardized corporate workstation fleet operating under unified modern management baselines (Intune).",
        "Secure remote access and self-service workplace portals available for corporate staff.",
        "Structured Level-1 service desk and automated operating system security patch deployment."
    ],
    "T10": [
        "Industrial weighbridge scales subjected to regular metrological calibration and preventive maintenance.",
        "Dedicated and highly qualified on-site operational staff ensuring resilient local execution.",
        "Robust, well-rehearsed manual dispatch continuity procedures during communication disruptions.",
        "Transactional synchronization interface transferring weighbridge dispatch tickets to central SAP ERP."
    ],
}

TOP_RISKS_ALIGNED = {
    "es": [
        {
            "id": "T10.R01",
            "title": "Interrupción del Pesaje y Expedición en Planta Fabril",
            "ale": "42.000 €/año",
            "sle": "105.000 €",
            "lef": "0,40 eventos/año",
            "vuln": "PC de báscula en arquitectura monofásica sin redundancia física.",
            "impact": "Parada de expediciones en planta a razón de 5.000 €/hora.",
            "mitig": "Despliegue de IPC industrial redundante en anillo con bypass de báscula."
        },
        {
            "id": "T05.R01",
            "title": "Tiempo de Recuperación Excesivo por Restauración en Cinta",
            "ale": "38.500 €/año",
            "sle": "128.333 €",
            "lef": "0,30 eventos/año",
            "vuln": "Procedimiento de restore dependiente de transporte físico de cintas LTO.",
            "impact": "RTO efectivo superior a 18 horas ante corrupción de datos corporativos.",
            "mitig": "Implantación de copia inmutable en almacenamiento WORM y repositorio cloud."
        },
        {
            "id": "T02.R01",
            "title": "Saturación de Cómputo y Shock Contractual Mayo 2027",
            "ale": "36.500 €/año",
            "sle": "146.000 €",
            "lef": "0,25 eventos/año",
            "vuln": "Ocupación de RAM superior al 90% y fin de soporte VMware/SimpliVity.",
            "impact": "Bloqueo de ampliaciones y escalada presupuestaria en renovación de licencias.",
            "mitig": "Migración hacia plataforma hiperconvergente de nueva generación."
        },
        {
            "id": "T01.R01",
            "title": "Recirculación Térmica en Racks de Cómputo Principal",
            "ale": "32.000 €/año",
            "sle": "160.000 €",
            "lef": "0,20 eventos/año",
            "vuln": "Carencia de cerramiento de pasillos frío/calor en sala técnica central.",
            "impact": "Degradación acelerada de CPUs y riesgo de parada por disparo de temperatura.",
            "mitig": "Instalación de cerramiento físico de pasillo frío y telemetría BMS IoT."
        },
        {
            "id": "T06.R01",
            "title": "Brecha de Identidad y Retraso en Adecuación NIS2",
            "ale": "28.000 €/año",
            "sle": "140.000 €",
            "lef": "0,20 eventos/año",
            "vuln": "Cuentas privilegiadas compartidas y coexistencia de dominios Secil.",
            "impact": "Riesgo de compromiso de credenciales corporativas y sanción regulatoria.",
            "mitig": "Unificación de bosques de identidad, despliegue de PAM y MFA forzoso."
        }
    ],
    "en": [
        {
            "id": "T10.R01",
            "title": "Disruption of Plant Weighbridge and Dispatch Systems",
            "ale": "42,000 €/yr",
            "sle": "105,000 €",
            "lef": "0.40 events/yr",
            "vuln": "Dispatch PC operating in single-phase non-redundant architecture.",
            "impact": "Halted physical plant dispatch at a burn rate of 5,000 €/hr.",
            "mitig": "Deployment of redundant industrial IPC ring with scale hardware bypass."
        },
        {
            "id": "T05.R01",
            "title": "Excessive Recovery Time from Physical Tape Restores",
            "ale": "38,500 €/yr",
            "sle": "128,333 €",
            "lef": "0.30 events/yr",
            "vuln": "Restore procedures depend on physical transport of LTO magnetic tapes.",
            "impact": "Effective RTO exceeding 18 hours during major data corruption events.",
            "mitig": "Implementation of immutable WORM storage tier and cloud replication."
        },
        {
            "id": "T02.R01",
            "title": "Compute Saturation & May 2027 Contract Renewal Shock",
            "ale": "36,500 €/yr",
            "sle": "146,000 €",
            "lef": "0.25 events/yr",
            "vuln": "RAM utilization continuously exceeding 90% and VMware EoL milestones.",
            "impact": "Expansion deadlock and steep price escalation during license renewals.",
            "mitig": "Migration to next-generation sovereign hyperconverged platform."
        },
        {
            "id": "T01.R01",
            "title": "Thermal Recirculation Across Primary Compute Racks",
            "ale": "32,000 €/yr",
            "sle": "160,000 €",
            "lef": "0.20 events/yr",
            "vuln": "Lack of hot/cold aisle containment in primary technical datacenter.",
            "impact": "Accelerated CPU component aging and risk of thermal shutdown.",
            "mitig": "Installation of physical cold-aisle containment and BMS IoT sensors."
        },
        {
            "id": "T06.R01",
            "title": "Identity Perimeter Disjointedness & NIS2 Compliance Lag",
            "ale": "28,000 €/yr",
            "sle": "140,000 €",
            "lef": "0.20 events/yr",
            "vuln": "Shared privileged administrative accounts and disjointed Secil forests.",
            "impact": "Credential compromise risk and regulatory compliance exposure.",
            "mitig": "Identity forest consolidation, PAM deployment, and mandatory MFA."
        }
    ]
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Update subpillar strengths in es and en
    for loc in ["es", "en"]:
        cat = data[loc].get("tomo_tower_forensic_catalog", {})
        s_map = ALIGNED_STRENGTHS_ES if loc == "es" else ALIGNED_STRENGTHS_EN
        for t_id, s_list in s_map.items():
            if t_id in cat:
                cat[t_id]["strengths"] = s_list

        # 2. Update top risks catalog with unified risk IDs
        data[loc]["tomo_top_risks_catalog"] = TOP_RISKS_ALIGNED[loc]

    # Propagate to secondary locales
    for loc in ["pt", "fr", "de", "ja"]:
        cat = data[loc].get("tomo_tower_forensic_catalog", {})
        for t_id, s_list in ALIGNED_STRENGTHS_EN.items():
            if t_id in cat:
                cat[t_id]["strengths"] = s_list
        data[loc]["tomo_top_risks_catalog"] = TOP_RISKS_ALIGNED["en"]

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully aligned subpillar strengths and unified risk IDs across all 6 locales!")


if __name__ == "__main__":
    main()
