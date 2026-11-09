#!/usr/bin/env python3
"""Sanitize Molins payloads for T10, T3, T1 to remove all abstractions and inject real plant/dispatch realities."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# 1. Sanitize T10 (Plant & Dispatch Systems)
with open(REPO_ROOT / "working/molins/T10/blueprint_t10_payload.json", "r", encoding="utf-8") as f:
    t10 = json.load(f)

t10["tower_name"] = "Plataformas Core, Sistemas de Planta y Operaciones Locales"
t10["document_meta"]["tower_name"] = "Plataformas Core, Sistemas de Planta y Operaciones Locales"
if "pillars_analysis" in t10 and len(t10["pillars_analysis"]) > 0:
    t10["pillars_analysis"][0]["pillar_name"] = "Plataformas Transaccionales Core y Operaciones de Planta"

t10["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Fragilidad en el flujo crítico de básculas y expedición (Truck-to-Cash): Dependencia de servidores locales no clusterizados, periféricos de pesaje envejecidos (lectores, barreras, terminales de pesaje) y enlaces WAN sin modo offline resiliente, donde una incidencia técnica paraliza físicamente la carga y salida de camiones hacia los clientes.",
    "Frontera difusa de responsabilidad entre TI Corporativo, Mantenimiento de Planta y Proveedores OT: Ausencia de una matriz RACI y de acuerdos de nivel operacional (OLAs) para el soporte de primer nivel en ubicaciones remotas, dilatando los tiempos de diagnóstico cuando un fallo cruza entre la red local, el servidor de planta y el software industrial.",
    "Despliegues artesanales y asimetría tecnológica inter-planta: Carencia de una arquitectura Edge-in-a-Box estandarizada y gestionada centralmente, provocando que cada fábrica o filial integrada opere con configuraciones dispares, sin telemetría proactiva unificada en Zabbix ni procedimientos automatizados de reconstrucción ante desastres locales."
]

with open(REPO_ROOT / "working/molins/T10/blueprint_t10_payload.json", "w", encoding="utf-8") as f:
    json.dump(t10, f, indent=2, ensure_ascii=False)

# 2. Sanitize T3 (Networks & Connectivity)
with open(REPO_ROOT / "working/molins/T3/blueprint_t3_payload.json", "r", encoding="utf-8") as f:
    t3 = json.load(f)

t3["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Dependencia crítica de enlaces WAN monoproveedor en fábricas remotas y canteras: Múltiples emplazamientos de producción y extracción operan sobre un único circuito de telecomunicaciones sin rutas activas de respaldo, provocando que un corte de fibra aísle completamente la planta y detenga la expedición de producto.",
    "Carencia de microsegmentación y control perimetral estricto entre redes corporativas (IT) y control industrial (OT): Topologías de red local planas en centros productivos que permiten que incidentes o tráfico masivo de la red de oficinas atraviese hacia los controladores de proceso y autómatas de planta.",
    "Puntos ciegos de cobertura inalámbrica industrial y electrónica no gestionada en campas logísticas: Ausencia de Wi-Fi industrial reforzado en zonas de acopio y carga exterior, combinada con switches auxiliares sin monitorizar que dificultan la telemetría de carretillas y terminales móviles de pesaje."
]

with open(REPO_ROOT / "working/molins/T3/blueprint_t3_payload.json", "w", encoding="utf-8") as f:
    json.dump(t3, f, indent=2, ensure_ascii=False)

# 3. Sanitize T1 (Data Center Facilities)
with open(REPO_ROOT / "working/molins/T1/blueprint_t1_payload.json", "r", encoding="utf-8") as f:
    t1 = json.load(f)

t1["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Silos operativos entre el mantenimiento industrial de planta y las operaciones de infraestructura de centros de datos: Falta de coordinación entre los calendarios de parada de fábrica y las ventanas de mantenimiento técnico de las salas de proceso.",
    "Confinamiento térmico deficiente y exposición a partículas industriales en salas técnicas de planta: Presencia de servidores en cuartos técnicos expuestos a polvo en suspensión y variaciones térmicas bruscas cada vez que se interrumpe el suministro fabril, acelerando la degradación de placas base.",
    "Aislamiento operativo de las alarmas del sistema de gestión de edificios (BMS) respecto a la observabilidad corporativa de TI: Carencia de integración en tiempo real de telemetría de consumo eléctrico por rack y clima hacia Zabbix, impidiendo detectar anomalías térmicas antes de que fuercen paradas de servidores."
]

with open(REPO_ROOT / "working/molins/T1/blueprint_t1_payload.json", "w", encoding="utf-8") as f:
    json.dump(t1, f, indent=2, ensure_ascii=False)

print("Successfully sanitized payloads for T10, T3, T1!")
