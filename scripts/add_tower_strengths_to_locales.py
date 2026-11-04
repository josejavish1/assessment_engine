#!/usr/bin/env python3
"""Add observed operational strengths to tomo_tower_forensic_catalog across all 6 locales."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

STRENGTHS_MAP = {
    "es": {
        "T1": [
            "Sistemas de alimentación ininterrumpida (SAI) configurados en esquema redundante N+1 con mantenimiento regular.",
            "Grupos electrógenos en topología de anillo con pruebas periódicas de arranque y conmutación.",
            "Sistemas automáticos de detección y extinción de incendios por agente limpio en salas principales."
        ],
        "T2": [
            "Clúster hiperconvergente centralizado que proporciona alta densidad de cómputo para cargas corporativas.",
            "Estandarización de imágenes base de sistemas operativos en servidores virtuales.",
            "Monitorización centralizada de disponibilidad y rendimiento de hipervisores."
        ],
        "T3": [
            "Conmutación troncal de doble núcleo con enlaces redundantes entre armarios de distribución.",
            "Perímetro protegido mediante cortafuegos corporativos de última generación con filtrado de tráfico.",
            "Interconexión SD-WAN activa que asegura comunicaciones cifradas entre centros operativos."
        ],
        "T4": [
            "Cabinas de almacenamiento corporativo de alto rendimiento con aprovisionamiento dinámico de capacidad.",
            "Políticas de snapshots programados y replicación asíncrona entre salas técnicas.",
            "Gestión estandarizada de volúmenes de datos con monitorización de IOPS y latencia."
        ],
        "T5": [
            "Políticas de copia de seguridad periódica en disco y cinta con custodia externa documentada.",
            "Procedimientos operativos de contingencia y recuperación documentados para sistemas críticos.",
            "Personal técnico interno con profundo conocimiento de los procesos de restauración manual."
        ],
        "T6": [
            "Dominio centralizado de gestión de identidades y accesos (Active Directory corporativo).",
            "Despliegue homogéneo de protección de punto final (EDR) con supervisión por centro de operaciones (SOC).",
            "Políticas corporativas de complejidad de contraseñas y filtrado de navegación web."
        ],
        "T7": [
            "Clústeres de bases de datos relacionales configurados con alta disponibilidad y planes de mantenimiento.",
            "Plataforma centralizada de soporte e incidencias (ITSM) con seguimiento de peticiones de usuario.",
            "Histórico transaccional protegido y procedimientos estandarizados de optimización de índices."
        ],
        "T8": [
            "Implantación madura del ERP corporativo que soporta de forma eficaz las operaciones y finanzas del grupo.",
            "Equipo técnico especializado con amplia experiencia en personalizaciones y flujos de negocio.",
            "Integraciones estables entre sistemas de gestión y plataformas periféricas de expedición."
        ],
        "T9": [
            "Parque homogéneo de puestos de trabajo bajo sistema operativo estándar con despliegue centralizado.",
            "Herramientas de colaboración y productividad en la nube ampliamente adoptadas por los usuarios.",
            "Gestión centralizada de dispositivos móviles corporativos mediante perfiles de seguridad."
        ],
        "T10": [
            "Equipos de pesaje industrial con calibración metrológica periódica y mantenimiento preventivo contratado.",
            "Procedimientos locales de despacho manual bien establecidos ante contingencias de comunicaciones.",
            "Alta cualificación y compromiso del personal técnico y operativo de planta en la resolución de incidencias."
        ],
    },
    "en": {
        "T1": [
            "Uninterruptible power supply (UPS) systems configured in redundant N+1 schemes with regular maintenance.",
            "Generator sets arranged in ring topology with scheduled periodic startup and transfer tests.",
            "Automated clean-agent fire detection and suppression systems operational across core technical rooms."
        ],
        "T2": [
            "Centralized hyperconverged compute cluster providing high computing density for corporate workloads.",
            "Standardized operating system base images deployed across production virtual machines.",
            "Centralized hypervisor availability and performance monitoring active."
        ],
        "T3": [
            "Dual-core backbone switching infrastructure with redundant uplinks across distribution cabinets.",
            "Perimeter defended by next-generation corporate firewalls with continuous traffic inspection.",
            "Active SD-WAN interconnectivity ensuring encrypted multi-site site-to-site communication."
        ],
        "T4": [
            "High-performance enterprise storage arrays with dynamic capacity thin-provisioning.",
            "Scheduled snapshot policies and asynchronous replication operational between primary facilities.",
            "Standardized data volume management with continuous IOPS and latency telemetry."
        ],
        "T5": [
            "Scheduled disk and tape backup policies with documented off-site vaulting procedures.",
            "Documented contingency and disaster recovery operational procedures for essential systems.",
            "Dedicated internal engineering team possessing deep hands-on expertise in manual system restoration."
        ],
        "T6": [
            "Centralized corporate identity and access management domain (Active Directory).",
            "Homogeneous endpoint detection and response (EDR) agent deployment with external SOC monitoring.",
            "Corporate password complexity enforcement and perimeter web filtering policies."
        ],
        "T7": [
            "Relational database clusters configured with high-availability standby instances and maintenance plans.",
            "Centralized IT Service Management (ITSM) platform tracking user incidents and service requests.",
            "Protected transactional history with established index maintenance and query optimization routines."
        ],
        "T8": [
            "Mature enterprise ERP platform effectively underpinning group operational and financial transactions.",
            "Skilled internal technical team with extensive domain knowledge in business processes.",
            "Stable integration interfaces connecting ERP core to peripheral plant dispatch systems."
        ],
        "T9": [
            "Standardized corporate workstation fleet operating under unified modern management baselines.",
            "Cloud collaboration and productivity suites widely adopted across business units.",
            "Centralized mobile device management (MDM) enforcing corporate device compliance policies."
        ],
        "T10": [
            "Industrial weighbridge scales subjected to regular metrological calibration and preventive vendor maintenance.",
            "Robust, well-rehearsed manual dispatch continuity procedures during communication disruptions.",
            "Highly qualified and dedicated on-site operational staff ensuring resilient local execution."
        ],
    }
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc in ["es", "en"]:
        cat = data[loc].get("tomo_tower_forensic_catalog", {})
        for t_id, s_list in STRENGTHS_MAP[loc].items():
            if t_id in cat:
                cat[t_id]["strengths"] = s_list

    # Propagate to secondary locales
    for loc in ["pt", "fr", "de", "ja"]:
        cat = data[loc].get("tomo_tower_forensic_catalog", {})
        for t_id, s_list in STRENGTHS_MAP["en"].items():
            if t_id in cat:
                cat[t_id]["strengths"] = s_list

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully added observed operational strengths across all 10 towers in all 6 locales!")


if __name__ == "__main__":
    main()
