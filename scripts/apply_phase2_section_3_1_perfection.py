#!/usr/bin/env python3
"""Apply Phase 2 refinements to Section 3.1 catalogs in engine_config/locales.json across all languages."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
loc_path = REPO_ROOT / "engine_config/locales.json"

with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

# ----------------------------------------------------------------------
# 1. NATURALIZED CH3 INTRODUCTIONS (NO RAW ENGLISH LEFTOVERS)
# ----------------------------------------------------------------------
ch3_intro_by_tower_es = {
    "T1": "El presente capítulo ejecuta el diagnóstico técnico de las instalaciones físicas, suministro electromecánico y climatización de centros de datos en {client_name}. El análisis evalúa la solidez de las salas técnicas bajo tres vectores críticos: redundancia de potencia ininterrumpida (SAIs y grupos electrógenos), confinamiento y estabilidad térmica frente a condiciones ambientales fabriles, y disciplina procedimental en el mantenimiento de facilities.",
    "T2": "Este capítulo documenta el diagnóstico técnico de las plataformas de cómputo, hipervisores de virtualización y servicios de ejecución híbrida en {client_name}. La evaluación analiza la capacidad de los clústeres para absorber cargas de forma elástica, la contención de memoria RAM y CPU en hipervisores, y el modelo de aprovisionamiento de máquinas virtuales frente a paradigmas modernos de desacoplamiento.",
    "T3": "El presente capítulo aborda la evaluación arquitectónica de las redes de campus, conectividad troncal y enlaces distribuidos que vertebran las comunicaciones en {client_name}. El diagnóstico examina la resiliencia de los enlaces entre sedes centrales, fábricas y canteras, la segregación y seguridad del perímetro entre redes corporativas e industriales (IT/OT), y la capacidad de las electrónicas troncales para sostener el tráfico transaccional y de réplica.",
    "T4": "Este capítulo analiza la postura arquitectónica de las plataformas de almacenamiento masivo, cabinas corporativas y repositorios de respaldo en {client_name}. La auditoría examina la capacidad de las cabinas para responder a SLAs de latencia de bases de datos críticas, las políticas de retención e inmutabilidad contra ransomware, y el equilibrio entre coste de almacenamiento primario y secundario.",
    "T5": "El presente capítulo ejecuta el diagnóstico de continuidad de negocio y recuperación operativa ante desastres (BC/DR) en {client_name}. La evaluación contrasta los procedimientos de recuperación frente a los tiempos de tolerancia de la cadena de suministro industrial, analizando la viabilidad de conmutación entre salas técnicas, el respaldo de bases de datos clave y la autonomía de sedes remotas.",
    "T6": "Esta sección presenta la evaluación de la postura de ciberseguridad, gobierno de identidades y protección de infraestructura en {client_name}. El análisis audita el ciclo de vida de cuentas de usuario, el control de accesos privilegiados de administración, la visibilidad de telemetría de seguridad y la capacidad de contención frente a amenazas avanzadas bajo el marco regulatorio NIS2 y estándares ISO 27001.",
    "T7": "El presente capítulo evalúa la madurez en la entrega de servicios, soporte operativo y gestión de infraestructura (ITSM) en {client_name}. La auditoría analiza la formalización del catálogo de servicios, la disciplina en el control de cambios y CMDB, los tiempos de resolución de incidencias en planta y la integración de herramientas de observabilidad de sistemas.",
    "T8": "Este capítulo examina el modelo fiduciario, la visibilidad económica y la gobernanza estratégica de la tecnología (FinOps) en {client_name}. El análisis evalúa la previsibilidad y reparto de costes de infraestructura entre unidades de negocio, la optimización de licenciamiento de software, el control de la contratación externa y la alineación de la inversión técnica con las prioridades de la organización.",
    "T9": "El presente capítulo aborda el diagnóstico del puesto de trabajo digital, herramientas de colaboración y dispositivos de usuario en {client_name}. La evaluación analiza la homogeneidad del parque de equipos, los automatismos de despliegue y parcheo, la experiencia digital de los empleados de oficina y la adaptación de dispositivos para operarios en entornos fabriles y de logística.",
    "T10": "Este capítulo analiza la infraestructura de sistemas dedicados a operaciones de planta, básculas y expedición logística en {client_name}. La evaluación audita la robustez del hardware en puntos de pesaje, la resiliencia de los servidores de fábrica frente a caídas de telecomunicaciones y el grado de modernización del software transaccional de despacho de producto."
}

ch3_intro_by_tower_en = {
    "T1": "This chapter provides the technical diagnosis of physical facilities, electromechanical power distribution, and precision cooling governing datacenters across {client_name}. The assessment evaluates facility resilience across three critical vectors: uninterrupted power redundancy (UPS and diesel generators), thermal containment against harsh industrial environmental conditions, and facilities maintenance governance.",
    "T2": "This chapter documents the technical diagnosis of compute platforms, virtualization hypervisors, and hybrid execution environments across {client_name}. The evaluation scrutinizes host bin-packing capacity, hypervisor memory and CPU contention, and workload deployment models against modern decoupling architectures.",
    "T3": "This chapter delivers an architectural assessment of campus networks, enterprise backbone connectivity, and wide-area networks spanning communications across {client_name}. The diagnosis evaluates communications resilience across headquarters, manufacturing plants, and quarries, IT/OT network perimeter segmentation, and backbone latency stability.",
    "T4": "This chapter evaluates the architecture of enterprise storage arrays, primary SAN/NAS platforms, and backup repositories across {client_name}. The audit examines storage tiering latency SLAs for mission-critical databases, snapshot immutability defenses against ransomware, and storage lifecycle management.",
    "T5": "This chapter conducts the technical assessment of business continuity and disaster recovery capabilities (BC/DR) across {client_name}. The evaluation contrasts technical recovery procedures against physical manufacturing tolerances, validating split-site failover viability, database recoverability, and plant edge autonomy.",
    "T6": "This section evaluates the cybersecurity posture, identity governance, and infrastructure hardening baselines across {client_name}. The analysis audits identity lifecycle management, privileged access management (PAM) controls, threat telemetry visibility, and lateral movement containment under the NIS2 Directive and ISO 27001 standards.",
    "T7": "This chapter evaluates IT service management (ITSM) maturity, infrastructure operational support, and delivery workflows across {client_name}. The audit examines service catalog SLAs, change management and CMDB accuracy, plant incident response velocity, and monitoring telemetry integration.",
    "T8": "This chapter analyzes the fiduciary management, technological cost transparency, and strategic technology governance (FinOps) across {client_name}. The assessment evaluates infrastructure cost allocation across business units, enterprise software licensing optimization, vendor management discipline, and capital allocation alignment.",
    "T9": "This chapter delivers the assessment of the digital workplace, collaboration suites, and endpoint fleets across {client_name}. The evaluation audits workstation fleet homogeneity, automated provisioning and patch compliance, corporate employee DEX, and plant-floor kiosk adaptations.",
    "T10": "This chapter evaluates dedicated plant edge systems, weighbridge infrastructure, and shipping dispatch systems across {client_name}. The assessment audits weighbridge hardware resilience, plant-floor server autonomy during WAN disconnects, and transaction dispatch engine modernization."
}

# ----------------------------------------------------------------------
# 2. DYNAMIC TRANSVERSAL INTRODUCTIONS BY TOWER (BREAKING CLONE CADENCE)
# ----------------------------------------------------------------------
cross_cutting_debt_intro_by_tower_es = {
    "T1": "Más allá del diagnóstico por pilar, la auditoría identifica tres vulnerabilidades físicas y ambientales críticas en la infraestructura electromecánica y de climatización de los centros de datos:",
    "T2": "Más allá de la evaluación por capacidad, el análisis constata tres patrones estructurales de rigidez arquitectónica y saturación de recursos que condicionan la plataforma de cómputo:",
    "T3": "Más allá del análisis por componente, la auditoría identifica tres estrangulamientos críticos en la topología de comunicaciones y la segmentación de redes corporativas e industriales:",
    "T4": "Más allá de la revisión por nivel de servicio, el diagnóstico revela tres desalineaciones estructurales en la protección, persistencia y ciclo de vida del dato corporativo:",
    "T5": "Más allá del análisis por vector de continuidad, la auditoría constata tres puntos ciegos críticos en la postura de resiliencia y recuperación operativa de planta:",
    "T6": "Más allá del diagnóstico por control, la evaluación identifica tres brechas estructurales de exposición cibernética, gestión de identidades y cumplimiento regulatorio:",
    "T7": "Más allá del examen por proceso, la auditoría evidencia tres ineficiencias sistémicas en la entrega de soporte operativo y observabilidad de servicios de TI:",
    "T8": "Más allá de la evaluación de partidas presupuestarias, el análisis identifica tres vectores de ineficiencia fiduciaria, bloqueo contractual y opacidad en el gasto tecnológico:",
    "T9": "Más allá de la revisión por servicio de usuario, la auditoría constata tres fricciones de productividad, soporte manual y homogeneidad en el ecosistema del puesto de trabajo:",
    "T10": "Más allá del diagnóstico por componente local, la evaluación revela tres vulnerabilidades operativas críticas en la cadena física de expedición, básculas y despacho fabril:"
}

cross_cutting_debt_intro_by_tower_en = {
    "T1": "Beyond granular pillar findings, the audit identifies three critical physical and environmental vulnerabilities across datacenter power distribution and precision cooling infrastructure:",
    "T2": "Beyond isolated capacity metrics, the analysis confirms three structural patterns of architectural rigidity and resource contention constraining the compute estate:",
    "T3": "Beyond individual component reviews, the audit identifies three critical bottlenecks across network communications topology and industrial/corporate perimeter segmentation:",
    "T4": "Beyond service-level observations, the diagnosis reveals three structural misalignments across data persistence, storage tiering, and corporate backup protection:",
    "T5": "Beyond theoretical continuity plans, the audit confirms three critical blind spots across operational resilience, recovery testing, and plant supply chain survival:",
    "T6": "Beyond technical control checklists, the evaluation identifies three structural gaps across cybersecurity exposure, identity governance, and NIS2 regulatory compliance:",
    "T7": "Beyond isolated support tickets, the audit exposes three systemic operational inefficiencies across change discipline, service delivery, and observability workflows:",
    "T8": "Beyond traditional budget accounting, the analysis identifies three vectors of fiduciary inefficiency, contractual licensing lock-in, and technological cost opacity:",
    "T9": "Beyond end-user hardware inventories, the audit identifies three operational friction vectors across endpoint fleet heterogeneity, manual staging, and plant kiosk usability:",
    "T10": "Beyond local hardware components, the evaluation reveals three mission-critical operational vulnerabilities across physical weighbridges, dispatch gates, and factory logistics continuity:"
}

# ----------------------------------------------------------------------
# 3. HARMONIZED CMMI SCALE LEGEND WITH MATHEMATICAL THRESHOLDS
# ----------------------------------------------------------------------
maturity_scale_legend_es = "Escala CMMI (Umbral de tramo: ≥X,60): Nivel 1 - Inicial (<1,60) | Nivel 2 - Repetible (1,60-2,59) | Nivel 3 - Definido (2,60-3,59) | Nivel 4 - Gestionado (3,60-4,19) | Nivel 5 - Optimizado (≥4,20)"
maturity_scale_legend_en = "CMMI Maturity Scale (Threshold: ≥X.60): Level 1 - Initial (<1.60) | Level 2 - Repeatable (1.60-2.59) | Level 3 - Defined (2.60-3.59) | Level 4 - Managed (3.60-4.19) | Level 5 - Optimized (≥4.20)"

# ----------------------------------------------------------------------
# 4. SHARPENED TRANSVERSAL PATTERNS FOR T6, T8, T9 (D3 BOARD VALUE ELEVATION)
# ----------------------------------------------------------------------
sharpened_patterns_es = {
    "cross_cutting_debt_t6_p1": "1. Uso Generalizado de Cuentas Compartidas de Máximo Privilegio (Root/Admin) sin Bóveda PAM: La administración ordinaria mediante credenciales genéricas sin registro de sesiones anula la trazabilidad forense de cambios y genera una exposición sancionadora directa bajo la Directiva NIS2.",
    "cross_cutting_debt_t6_p3": "2. Retraso Acumulado en Ciclos de Parcheo de Hipervisores por Temor a Interrupción del Servicio: Servidores productivos con cientos de días de actividad continua sin reiniciar acumulan vulnerabilidades graves no remediadas para evitar paradas en aplicaciones legacy críticas.",
    "cross_cutting_debt_t6_p2": "3. Falta de Visibilidad y Correlación Centralizada de Eventos de Seguridad entre IT y OT: La monitorización en silos y la ausencia de correlación en un SIEM unificado impiden detectar a tiempo intrusiones o movimientos laterales que crucen el perímetro industrial hacia las líneas de producción.",
    "cross_cutting_debt_t8_p2": "2. Presión Fiduciaria por Licenciamiento Monolítico que Condiciona la Escalabilidad Técnica: Los costes de licencias de bases de datos por núcleo físico fuerzan a restringir los clústeres de cómputo (T2), supeditando la capacidad de memoria virtual al tope contractual de software para evitar sobrecostes millonarios.",
    "cross_cutting_debt_t9_p1": "1. Heterogeneidad en el Parque de Equipos y Elevado Coste Operativo por Aprovisionamiento Manual: La convivencia de múltiples marcas y gamas de portátiles junto con la preparación manual de puestos absorbe cientos de horas de técnicos de soporte y genera desajustes recurrentes de configuración.",
    "cross_cutting_debt_t9_p3": "3. Brecha Tecnológica y Fricción en Puestos Compartidos y Quioscos de Fábrica: Los terminales en básculas y plantas fabriles operan con sesiones genéricas y hardware no estandarizado, ralentizando la operativa de los trabajadores de turno y debilitando la autenticación corporativa."
}

sharpened_patterns_en = {
    "cross_cutting_debt_t6_p1": "1. Widespread Use of Shared Privileged Root/Admin Accounts Without PAM Vaulting: Routine administration using shared root/admin credentials without session recording destroys forensic auditability and incurs direct executive compliance exposure under the NIS2 Directive.",
    "cross_cutting_debt_t6_p3": "2. Accumulated Hypervisor Patching Debt Due to Service Interruption Fear: Production servers running for hundreds of days without reboots accumulate unpatched critical CVEs to avoid taking down legacy business dependencies.",
    "cross_cutting_debt_t6_p2": "3. Fragmented Security Telemetry and Lack of Centralized IT/OT Threat Correlation: Siloed monitoring and absent SIEM/EDR log aggregation delay detection of lateral threat traversal across corporate and industrial plant networks into manufacturing lines.",
    "cross_cutting_debt_t8_p2": "2. Fiduciary Lock-in from Core-Based Database Licensing Dictating Technical Scalability: High per-core database licensing penalties force aggressive hardware consolidation in Compute (T2), artificially capping virtual memory scalability to avoid steep software audit penalties.",
    "cross_cutting_debt_t9_p1": "1. Laptop Fleet Heterogeneity and Elevated Support Costs from Manual Staging: The coexistence of unstandardized laptop models and manual technician imaging consumes hundreds of support hours and generates recurrent driver and security drift.",
    "cross_cutting_debt_t9_p3": "3. Technological Disparity and Friction Across Plant Kiosks and Shared Shift Terminals: Factory-floor terminals and weighbridge desks rely on shared logins and non-standardized hardware, slowing down plant shift workers and weakening corporate authentication controls."
}

# Update Spanish in locales.json
if "es" in locales:
    locales["es"]["ch3_intro_by_tower"] = ch3_intro_by_tower_es
    locales["es"]["cross_cutting_debt_intro_by_tower"] = cross_cutting_debt_intro_by_tower_es
    locales["es"]["maturity_scale_legend"] = maturity_scale_legend_es
    locales["es"].update(sharpened_patterns_es)

# Update English in locales.json
if "en" in locales:
    locales["en"]["ch3_intro_by_tower"] = ch3_intro_by_tower_en
    locales["en"]["cross_cutting_debt_intro_by_tower"] = cross_cutting_debt_intro_by_tower_en
    locales["en"]["maturity_scale_legend"] = maturity_scale_legend_en
    locales["en"].update(sharpened_patterns_en)

# Synchronize mathematical symmetry across all other languages
base_keys = set(locales["en"].keys())
for lang in ["pt", "fr", "de", "ja"]:
    if lang in locales:
        for k in base_keys:
            if k not in locales[lang] or isinstance(locales[lang][k], dict):
                locales[lang][k] = locales["en"][k]

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print(f"Successfully applied Phase 2 Section 3.1 catalogs to {loc_path}!")
