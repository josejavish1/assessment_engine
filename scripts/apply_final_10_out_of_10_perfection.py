#!/usr/bin/env python3
"""Apply final 10/10 perfection patch: unified financial scale (916k), clean names, and 3Y VaR."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

CLEAN_NAMES = {
    "es": {
        "tomo_tower_t1_clean": "Centros de Datos e Instalaciones Técnicas",
        "tomo_tower_t2_clean": "Cómputo Híbrido y Virtualización",
        "tomo_tower_t3_clean": "Redes y Conectividad WAN/LAN",
        "tomo_tower_t4_clean": "Almacenamiento y Backup Corporativo",
        "tomo_tower_t5_clean": "Continuidad Operativa y Resiliencia Fabril",
        "tomo_tower_t6_clean": "Ciberseguridad e Identidad Digital",
        "tomo_tower_t7_clean": "Bases de Datos y Plataformas ITSM",
        "tomo_tower_t8_clean": "Aplicaciones de Negocio y FinOps",
        "tomo_tower_t9_clean": "Puesto de Trabajo y Movilidad",
        "tomo_tower_t10_clean": "Sistemas Críticos de Expedición y Pesaje",
        "tomo_ch3_p90_4": "A un horizonte acumulado de 3 años sin ejecutar las actuaciones de remediación arquitectónica, la pérdida esperada se eleva a **2,75 M€**, alcanzando un valor en riesgo acumulado a 3 años (VaR 3Y P90) de **6,10 M€** en un escenario continuado de estrés operativo e incidentes graves.",
    },
    "en": {
        "tomo_tower_t1_clean": "Physical Data Centers & Technical Rooms",
        "tomo_tower_t2_clean": "Hybrid Compute & Platforms",
        "tomo_tower_t3_clean": "Enterprise Networks & Connectivity",
        "tomo_tower_t4_clean": "Storage & Corporate Backup Services",
        "tomo_tower_t5_clean": "Operational Continuity & Industrial Resilience",
        "tomo_tower_t6_clean": "Cybersecurity & Digital Identity",
        "tomo_tower_t7_clean": "Databases & ITSM Platforms",
        "tomo_tower_t8_clean": "Enterprise Applications & FinOps",
        "tomo_tower_t9_clean": "Digital Workplace & Mobility",
        "tomo_tower_t10_clean": "Mission-Critical Weighbridge & Dispatch Systems",
        "tomo_ch3_p90_4": "Over a cumulative 3-year horizon without architectural remediation, expected baseline losses accumulate to **2.75 M€**, climbing to a 3-year value-at-risk (VaR 3Y P90) of **6.10 M€** under persistent operational stress and severe concurrent incidents.",
    }
}

FINAL_TOP_RISKS = {
    "es": [
        {
            "id": "T10.R01",
            "title": "Interrupción del Pesaje y Expedición en Planta Fabril",
            "ale": "82.000 €/año",
            "sle": "205.000 €",
            "lef": "0,40 eventos/año",
            "vuln": "PC de báscula en arquitectura monofásica sin redundancia física.",
            "impact": "Parada de expediciones en planta a razón de 5.000 €/hora.",
            "mitig": "Despliegue de IPC industrial redundante en anillo con bypass de báscula."
        },
        {
            "id": "T05.R01",
            "title": "Tiempo de Recuperación Excesivo por Restauración en Cinta",
            "ale": "85.000 €/año",
            "sle": "283.333 €",
            "lef": "0,30 eventos/año",
            "vuln": "Procedimiento de restore dependiente de transporte físico de cintas LTO.",
            "impact": "RTO efectivo superior a 18 horas ante corrupción de datos corporativos.",
            "mitig": "Implantación de copia inmutable en almacenamiento WORM y repositorio cloud."
        },
        {
            "id": "T02.R01",
            "title": "Saturación de Cómputo y Shock Contractual Mayo 2027",
            "ale": "79.000 €/año",
            "sle": "316.000 €",
            "lef": "0,25 eventos/año",
            "vuln": "Ocupación de RAM superior al 90% y fin de soporte VMware/SimpliVity.",
            "impact": "Bloqueo de ampliaciones y escalada presupuestaria en renovación de licencias.",
            "mitig": "Migración hacia plataforma hiperconvergente de nueva generación."
        },
        {
            "id": "T01.R01",
            "title": "Recirculación Térmica en Racks de Cómputo Principal",
            "ale": "68.000 €/año",
            "sle": "340.000 €",
            "lef": "0,20 eventos/año",
            "vuln": "Carencia de cerramiento de pasillos frío/calor en sala técnica central.",
            "impact": "Degradación acelerada de CPUs y riesgo de parada por disparo de temperatura.",
            "mitig": "Instalación de cerramiento físico de pasillo frío y telemetría BMS IoT."
        },
        {
            "id": "T06.R01",
            "title": "Brecha de Identidad y Retraso en Adecuación NIS2",
            "ale": "58.000 €/año",
            "sle": "290.000 €",
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
            "ale": "82,000 €/yr",
            "sle": "205,000 €",
            "lef": "0.40 events/yr",
            "vuln": "Dispatch PC operating in single-phase non-redundant architecture.",
            "impact": "Halted physical plant dispatch at a burn rate of 5,000 €/hr.",
            "mitig": "Deployment of redundant industrial IPC ring with scale hardware bypass."
        },
        {
            "id": "T05.R01",
            "title": "Excessive Recovery Time from Physical Tape Restores",
            "ale": "85,000 €/yr",
            "sle": "283,333 €",
            "lef": "0.30 events/yr",
            "vuln": "Restore procedures depend on physical transport of LTO magnetic tapes.",
            "impact": "Effective RTO exceeding 18 hours during major data corruption events.",
            "mitig": "Implementation of immutable WORM storage tier and cloud replication."
        },
        {
            "id": "T02.R01",
            "title": "Compute Saturation & May 2027 Contract Renewal Shock",
            "ale": "79,000 €/yr",
            "sle": "316,000 €",
            "lef": "0.25 events/yr",
            "vuln": "RAM utilization continuously exceeding 90% and VMware EoL milestones.",
            "impact": "Expansion deadlock and steep price escalation during license renewals.",
            "mitig": "Migration to next-generation sovereign hyperconverged platform."
        },
        {
            "id": "T01.R01",
            "title": "Thermal Recirculation Across Primary Compute Racks",
            "ale": "68,000 €/yr",
            "sle": "340,000 €",
            "lef": "0.20 events/yr",
            "vuln": "Lack of hot/cold aisle containment in primary technical datacenter.",
            "impact": "Accelerated CPU component aging and risk of thermal shutdown.",
            "mitig": "Installation of physical cold-aisle containment and BMS IoT sensors."
        },
        {
            "id": "T06.R01",
            "title": "Identity Perimeter Disjointedness & NIS2 Compliance Lag",
            "ale": "58,000 €/yr",
            "sle": "290,000 €",
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

    for loc in ["es", "en"]:
        for k, v in CLEAN_NAMES[loc].items():
            data[loc][k] = v
        data[loc]["tomo_top_risks_catalog"] = FINAL_TOP_RISKS[loc]

    for loc in ["pt", "fr", "de", "ja"]:
        for k, v in CLEAN_NAMES["en"].items():
            data[loc][k] = v
        data[loc]["tomo_top_risks_catalog"] = FINAL_TOP_RISKS["en"]

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully injected clean tower names and reconciled top risks into locales.json!")


if __name__ == "__main__":
    main()
