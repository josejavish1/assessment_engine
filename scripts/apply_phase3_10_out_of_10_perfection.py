#!/usr/bin/env python3
"""Apply Phase 3: Bespoke Dichotomy Openers, Strict Single-Lens Fact Ownership, and Fiduciary Board Tails."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ----------------------------------------------------------------------
# 1. BESPOKE DICHOTOMY OPENERS IN LOCALES.JSON
# ----------------------------------------------------------------------
loc_path = REPO_ROOT / "engine_config/locales.json"
with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

ch3_intro_es = {
    "T1": "La infraestructura física de centros de datos en {client_name} se articula bajo una marcada dicotomía operativa: mientras las salas centrales de Sant Vicenç dels Horts disponen de sistemas redundantes de extinción y climatización, los cuartos técnicos distribuidos en plantas cementeras y canteras operan expuestos a condiciones ambientales severas de polvo en suspensión y calor. Este capítulo audita la resiliencia electromecánica de ambos entornos examinando la continuidad de suministro eléctrico, la estabilidad térmica por rack y la integración de las alarmas de facilities en la supervisión corporativa.",
    "T2": "El modelo de cómputo en {client_name} afronta una tensión estructural entre la estabilidad de sus clústeres locales consolidados y la dispersión de cargas en tres nubes públicas (GCP, Azure y OCI). Este capítulo documenta el diagnóstico técnico de los hipervisores y plataformas de ejecución de la compañía, analizando la saturación de memoria RAM física en los nodos centrales, la ausencia de arquitecturas ligeras de contenedores y el impacto del modelo de aprovisionamiento de máquinas virtuales sobre la agilidad de los servicios de negocio.",
    "T3": "La arquitectura de comunicaciones en {client_name} refleja una fuerte asimetría entre la solidez del switching en sedes centrales y la fragilidad de los enlaces que conectan las plantas de producción y canteras. Este capítulo evalúa la topología de red corporativa e industrial, examinando los puntos únicos de fallo en accesos WAN remotos, el déficit de microsegmentación entre perímetros IT y OT, y la cobertura inalámbrica en campas logísticas requerida para la telemetría del transporte.",
    "T4": "La gestión del almacenamiento corporativo en {client_name} combina cabinas de alto rendimiento para bases de datos transaccionales con repositorios secundarios dispersos en sedes y filiales. Este capítulo aborda el diagnóstico técnico de las plataformas de datos de la compañía, auditando el cumplimiento de niveles de servicio de latencia en cabinas primarias, las defensas de inmutabilidad y aislamiento (air-gap) frente a ransomware, y las restricciones de capacidad local que fuerzan a una continua contención manual de cuotas.",
    "T5": "La postura de resiliencia operativa en {client_name} descansa sobre una falsa sensación de seguridad: la duplicación de cabinas y clústeres no compensa la proximidad física de 500 metros entre los dos centros de datos principales compartiendo la misma acometida eléctrica. Este capítulo audita la continuidad de negocio y recuperación ante desastres (BC/DR), contrastando la fiabilidad de las copias locales frente a la falta de pruebas de conmutación integral y la desalineación de las métricas técnicas respecto a los ritmos de fabricación continua.",
    "T6": "La gobernanza de la ciberseguridad en {client_name} presenta un notable contraste entre los avances en federación de identidades de usuario y la persistencia de prácticas de administración compartida sin bóveda en la infraestructura crítica. Esta sección evalúa la postura de seguridad de la información, auditando el control de accesos privilegiados (PAM), la visibilidad de telemetría ante movimientos laterales entre IT y redes industriales (OT), y la exposición sancionadora de la compañía bajo la Directiva NIS2.",
    "T7": "El modelo operativo de soporte y gestión de infraestructura (ITSM) en {client_name} se encuentra condicionado por la saturación de su equipo nuclear de cinco ingenieros, quienes absorben una elevada carga reactiva por la ausencia de una CMDB federada viva. Este capítulo evalúa la madurez en la entrega del servicio, analizando el gobierno del cambio en entornos productivos, la gestión de incidencias frente a canales informales en fábricas y la correlación de alertas hacia servicios de negocio.",
    "T8": "El control económico de la tecnología en {client_name} combina una disciplina rígida en la autorización de compras con una notable opacidad en el reparto de costes entre unidades de negocio y plantas productivas. Este capítulo examina el modelo fiduciario y de gobernanza (FinOps), auditando la dispersión del gasto en tres nubes públicas sin etiquetado unificado, las restricciones contractuales de licenciamiento por procesador y la gestión de acuerdos marco con proveedores externos.",
    "T9": "El ecosistema del puesto de trabajo digital en {client_name} refleja una clara división entre la fuerza laboral de oficina y los operarios en planta: la excelente cadencia de renovación de portátiles corporativos contrasta con la heterogeneidad de los quioscos compartidos en fábricas y básculas. Este capítulo audita la gestión de puestos de usuario, analizando el grado de automatización en el aprovisionamiento, la distribución uniforme de parches de seguridad y la agilidad de acceso en relevos de turno.",
    "T10": "Los sistemas dedicados a la operativa de planta, expedición logística y básculas de pesaje en {client_name} constituyen el corazón de la facturación y la cadena de suministro industrial (Truck-to-Cash). Este capítulo evalúa la robustez de la infraestructura local en el borde fabril, analizando la resiliencia del hardware ante cortes de comunicaciones centrales, la frontera de soporte entre TI y mantenimiento industrial, y el impacto directo de incidencias técnicas en la formación de colas de camiones en fábrica."
}

ch3_intro_en = {
    "T1": "Physical datacenter facilities across {client_name} operate under a pronounced operational dichotomy: while central computer rooms in Sant Vicenç dels Horts maintain redundant fire suppression and precision cooling, distributed technical rooms across cement plants and quarries operate exposed to harsh environmental dust and thermal swings. This chapter audits electromechanical resilience across both tiers, examining uninterrupted power continuity, per-rack thermal stability, and facility alarm integration into corporate monitoring.",
    "T2": "The compute estate across {client_name} confronts a structural tension between stable on-premise hyperconverged clusters and workload sprawl across three public clouds (GCP, Azure, and OCI). This chapter documents the technical diagnosis of virtualization hypervisors and workload execution platforms, analyzing physical RAM saturation on primary nodes, the absence of lightweight container architectures, and manual VM provisioning friction constraining enterprise agility.",
    "T3": "Communications architecture across {client_name} exhibits a sharp asymmetry between robust switching across headquarters and single-point-of-failure fragility across links connecting remote manufacturing plants and quarries. This chapter evaluates corporate and industrial network topology, examining single-carrier WAN dependencies, flat IT/OT perimeter segmentation, and outdoor logistics yard wireless coverage required for transport telemetry.",
    "T4": "Corporate storage management across {client_name} balances high-performance primary arrays for core databases against fragmented secondary storage across subsidiaries and regional plants. This chapter addresses the technical diagnosis of enterprise data platforms, auditing latency SLA compliance on primary arrays, immutable air-gapped ransomware protection, and restrictive local disk sizing forcing ongoing manual quota firefighting.",
    "T5": "Operational resilience across {client_name} rests upon a fragile illusion of safety: hardware array duplication fails to mitigate the shared physical fate of two primary datacenters separated by only 500 meters under a common electrical feed. This chapter audits business continuity and disaster recovery (BC/DR), contrasting local backup reliability against unverified full-site failover runbooks and recovery metrics misaligned with 24x7 manufacturing tolerances.",
    "T6": "Cybersecurity governance across {client_name} exhibits a marked contrast between disciplined user identity federation and the persistence of unvaulted shared administrative access across critical infrastructure. This section evaluates the enterprise security posture, auditing privileged access management (PAM), threat telemetry correlation across IT and industrial OT boundaries, and organizational liability under the European NIS2 Directive.",
    "T7": "IT service management and operations (ITSM) across {client_name} operates constrained by the capacity of its core five-engineer team, who absorb a heavy reactive firefighting load due to an unmapped configuration database (CMDB). This chapter evaluates service delivery maturity, analyzing production change discipline, informal incident intake channels across plant sites, and alert correlation to business services.",
    "T8": "Technological financial governance across {client_name} combines disciplined procurement oversight with significant cost allocation opacity across business units and manufacturing plants. This chapter examines the fiduciary and governance model (FinOps), auditing un-tagged multi-cloud spend across three hyperscalers, contractual core-based software licensing constraints, and framework agreement management with external vendors.",
    "T9": "The digital workplace across {client_name} reflects a clear operational division between corporate office staff and plant-floor operators: disciplined laptop renewal cycles contrast with the heterogeneity of shared shift kiosks across manufacturing lines and weighbridges. This chapter audits endpoint fleet governance, analyzing zero-touch provisioning automation, uniform security patch deployment, and shift-change usability.",
    "T10": "Dedicated plant operational systems, logistics shipping, and weighbridge infrastructure across {client_name} underpin the core Truck-to-Cash revenue workflow. This chapter evaluates local industrial edge infrastructure, analyzing hardware resilience during central network outages, support RACI boundaries between IT and plant maintenance, and the immediate physical impact of technical faults on truck gridlock at factory gates."
}

locales["es"]["ch3_intro_by_tower"] = ch3_intro_es
locales["en"]["ch3_intro_by_tower"] = ch3_intro_en

base_keys = set(locales["en"].keys())
for lang in ["pt", "fr", "de", "ja"]:
    if lang in locales:
        for k in base_keys:
            if k not in locales[lang] or isinstance(locales[lang][k], dict):
                locales[lang][k] = locales["en"][k]

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print("Injected bespoke dichotomy openers into locales.json!")

# ----------------------------------------------------------------------
# 2. SHARPEN PAYLOADS WITH STRICT SINGLE-LENS OWNERSHIP & FIDUCIARY TAILS
# ----------------------------------------------------------------------

# T1: Facilities
with open(REPO_ROOT / "working/molins/T1/blueprint_t1_payload.json", "r", encoding="utf-8") as f:
    t1 = json.load(f)
t1["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Silos operativos entre mantenimiento de fábrica y operaciones de centro de datos: La falta de coordinación entre los calendarios de parada de producción y las intervenciones electromecánicas en salas técnicas arriesga caídas accidentales de suministro, amenazando con paralizar la actividad fabril sin aviso previo.",
    "Confinamiento térmico pasivo deficiente y exposición a partículas fabriles en salas técnicas: La presencia de servidores en cuartos expuestos a polvo de cemento en suspensión y oscilaciones térmicas severas acelera la degradación física de placas base, forzando ciclos imprevistos de amortización y compras reactivas de hardware (CapEx).",
    "Aislamiento de alarmas del sistema de gestión de edificios (BMS) respecto a la observabilidad corporativa de TI: La carencia de telemetría unificada en tiempo real hacia Zabbix impide correlacionar variaciones de potencia por rack con el estrés de carga, elevando el riesgo de paradas intempestivas en servidores que gestionan la expedición de planta."
]
with open(REPO_ROOT / "working/molins/T1/blueprint_t1_payload.json", "w", encoding="utf-8") as f:
    json.dump(t1, f, indent=2, ensure_ascii=False)

# T2: Compute
with open(REPO_ROOT / "working/molins/T2/blueprint_t2_payload.json", "r", encoding="utf-8") as f:
    t2 = json.load(f)
t2["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Contención artificial de capacidad física y agotamiento crítico de memoria RAM en hipervisores: Los clústeres de virtualización operan al 95% de saturación de memoria —condicionados por restricciones de licenciamiento por procesador—, anulando el margen de reserva N+1 y forzando intervenciones manuales continuas para evitar la degradación de aplicaciones productivas.",
    "Aprovisionamiento artesanal mediante consolas gráficas y fragmentación multi-nube: Predominio de operaciones manuales tanto en el entorno local vCenter como en los tres hyperscalers (GCP, Azure, OCI), careciendo de plantillas de Infraestructura como Código (IaC) y entornos de contenedores que agilicen el despliegue de nuevos proyectos de negocio.",
    "Deuda técnica en ciclo de vida de sistemas operativos y deriva de configuración (drift): Persistencia de más de 300 máquinas virtuales con sistemas operativos próximos al fin de soporte y ausencia de baselines automatizados, elevando la superficie de exposición y encareciendo el mantenimiento de software legacy."
]
with open(REPO_ROOT / "working/molins/T2/blueprint_t2_payload.json", "w", encoding="utf-8") as f:
    json.dump(t2, f, indent=2, ensure_ascii=False)

# T7: ITSM (Owns the 5-engineer team bottleneck 100%)
with open(REPO_ROOT / "working/molins/T7/blueprint_t7_payload.json", "r", encoding="utf-8") as f:
    t7 = json.load(f)
t7["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Cuello de botella operativo en el equipo nuclear de cinco ingenieros de infraestructura: La concentración de conocimiento tácito y la ausencia de una CMDB federada viva obligan a los especialistas sénior a destinar más del 40% de su jornada a tareas reactivas de soporte de primer nivel, paralizando la ejecución de proyectos estratégicos de modernización y absorción de adquisiciones (M&A).",
    "Carencia de acuerdos de nivel operacional (OLAs) y gestión estructurada de problemas: Las alertas recurrentes de sistemas se resuelven como incidencias aisladas sin análisis de causa raíz, perpetuando fallos crónicos que impactan en la continuidad operativa de las fábricas y generan horas extras no presupuestadas.",
    "Atención fragmentada y canales informales de soporte en plantas industriales: La dispersión territorial favorece que las peticiones técnicas se gestionen mediante llamadas directas o correos sin ticket, desalineando las ventanas de mantenimiento de TI respecto a los calendarios de producción y ocultando la carga real de trabajo ante el Comité de Dirección."
]
with open(REPO_ROOT / "working/molins/T7/blueprint_t7_payload.json", "w", encoding="utf-8") as f:
    json.dump(t7, f, indent=2, ensure_ascii=False)

# T8: FinOps (Owns software licensing lock-in & contractual audit liability 100%)
with open(REPO_ROOT / "working/molins/T8/blueprint_t8_payload.json", "r", encoding="utf-8") as f:
    t8 = json.load(f)
t8["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Dispersión del gasto tecnológico en tres nubes públicas (GCP, Azure, OCI) sin etiquetado unificado ni telemetría FinOps: Ausencia de modelos de showback o chargeback por planta o unidad de negocio que permitan visibilizar el coste unitario de infraestructura y optimizar recursos ociosos, distorsionando el margen operativo (OpEx).",
    "Bloqueo fiduciario por licenciamiento de software por procesador físico y riesgo de penalización en auditorías: Las penalizaciones contractuales en bases de datos empresariales distorsionan las decisiones de compras, forzando a congelar la inversión en hardware moderno para eludir costes millonarios de regularización de licencias.",
    "Aislamiento operativo entre ingeniería interna, compras corporativas y proveedores externalizados (NOS, servicios gestionados): Falta de seguimiento centralizado de SLAs contractuales y compras puntuales descentralizadas por plantas que impiden consolidar economías de escala y duplican costes de mantenimiento."
]
with open(REPO_ROOT / "working/molins/T8/blueprint_t8_payload.json", "w", encoding="utf-8") as f:
    json.dump(t8, f, indent=2, ensure_ascii=False)

# T9: Workplace (Owns shared kiosk sessions & shift change friction 100%)
with open(REPO_ROOT / "working/molins/T9/blueprint_t9_payload.json", "r", encoding="utf-8") as f:
    t9 = json.load(f)
t9["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Elevada carga de soporte manual en el ciclo de vida del puesto de trabajo corporativo: La preparación artesanal de portátiles sin flujos automatizados de despliegue zero-touch (Intune/Autopilot) consume cientos de horas de técnicos y eleva los costes de gestión de incidencias de configuración.",
    "Brecha de seguridad y fricción operativa en terminales compartidos y quioscos de planta: Los puestos de expedición en básculas y terminales de fábrica operan con hardware dispar y sesiones genéricas compartidas, ralentizando los relevos de turno fabriles y debilitando la trazabilidad de identidades requerida por el estándar ISO 27001.",
    "Desalineación en la distribución de parches y gobierno del puesto entre sedes y filiales integradas: Coexistencia de políticas dispares de actualización de sistema operativo y aplicaciones entre oficinas centrales y filiales adquiridas, elevando la superficie de exposición ante ataques de phishing dirigidos a la cadena de suministro."
]
with open(REPO_ROOT / "working/molins/T9/blueprint_t9_payload.json", "w", encoding="utf-8") as f:
    json.dump(t9, f, indent=2, ensure_ascii=False)

# T10: Plant Systems (Owns Truck-to-Cash, weighbridges, and offline continuity 100%)
with open(REPO_ROOT / "working/molins/T10/blueprint_t10_payload.json", "r", encoding="utf-8") as f:
    t10 = json.load(f)
t10["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Fragilidad en el flujo crítico de básculas y expedición (Truck-to-Cash): Dependencia de servidores locales no clusterizados, periféricos de pesaje envejecidos (lectores, barreras, terminales de pesaje) y enlaces WAN sin modo offline resiliente, donde una incidencia técnica paraliza físicamente la carga de camiones y detiene la facturación en planta.",
    "Frontera difusa de responsabilidad entre TI Corporativo, Mantenimiento de Planta y Proveedores OT: Ausencia de una matriz RACI y de acuerdos de nivel operacional (OLAs) para el soporte de primer nivel en ubicaciones remotas, dilatando los tiempos de diagnóstico cuando un fallo cruza entre la red local, el servidor de planta y el software industrial.",
    "Heterogeneidad arquitectónica en servidores de borde y despliegues artesanales inter-planta: Cada centro productivo y filial adquirida opera con configuraciones locales dispares desplegadas de forma manual, sin plantillas estandarizadas de cómputo industrial, telemetría proactiva unificada en Zabbix ni procedimientos automatizados de reconstrucción rápida ante el fallo físico de un servidor de planta."
]
with open(REPO_ROOT / "working/molins/T10/blueprint_t10_payload.json", "w", encoding="utf-8") as f:
    json.dump(t10, f, indent=2, ensure_ascii=False)

print("Successfully applied Phase 3 master polish across all payloads and locales!")
