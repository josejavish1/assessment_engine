#!/usr/bin/env python3
"""Purge tenant-specific hardcoding and establish universal, parameterized domain catalogs in engine_config/locales.json."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
loc_path = REPO_ROOT / "engine_config/locales.json"

with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

# ----------------------------------------------------------------------
# 1. PURE UNIVERSAL DOMAIN INTRODUCTIONS (NO TENANT OR VERTICAL LOCK-IN)
# ----------------------------------------------------------------------
ch3_intro_universal_es = {
    "T1": "El presente capítulo ejecuta el diagnóstico técnico de la infraestructura física, suministro electromecánico y climatización de {tower_name} en {client_name}. La evaluación audita la resiliencia de las salas técnicas y centros de procesamiento examinando la continuidad de potencia ininterrumpida, la estabilidad y eficiencia térmica, y los procedimientos de mantenimiento preventivo sobre activos críticos.",
    "T2": "Este capítulo documenta la evaluación arquitectónica de las plataformas de cómputo, hipervisores de virtualización y entornos de ejecución híbrida que conforman {tower_name} en {client_name}. El diagnóstico examina la capacidad de absorción y dimensionamiento de clústeres, la contención de recursos de CPU y memoria, y el ciclo de vida de los sistemas operativos frente a paradigmas modernos de desacoplamiento.",
    "T3": "El presente capítulo analiza la arquitectura de comunicaciones, redes de campus y enlaces de interconexión que vertebran {tower_name} en {client_name}. La auditoría evalúa la resiliencia topológica frente a contingencias de transporte, la microsegmentación y control del perímetro entre zonas de confianza, y la estabilidad y latencia en el acceso a servicios corporativos y sedes distribuidas.",
    "T4": "Este capítulo aborda el diagnóstico técnico de las plataformas de almacenamiento corporativo, cabinas primarias y repositorios de respaldo que integran {tower_name} en {client_name}. La evaluación audita el cumplimiento de SLAs de latencia y rendimiento de bases de datos, las defensas de inmutabilidad y aislamiento frente a ransomware, y la gobernanza del ciclo de vida y capacidad del almacenamiento.",
    "T5": "El presente capítulo examina la postura de resiliencia operativa y recuperación ante desastres (BC/DR) que articula {tower_name} en {client_name}. El análisis contrasta los procedimientos técnicos de conmutación y respaldo frente a las tolerancias de interrupción del negocio, evaluando la independencia de recintos, la salvaguarda de repositorios clave y la autonomía de sedes ante caídas centrales.",
    "T6": "Esta sección presenta la evaluación de la postura de ciberseguridad, gestión de identidades y defensas de infraestructura que componen {tower_name} en {client_name}. El diagnóstico audita el control de accesos privilegiados de administración, la visibilidad de telemetría y detección de amenazas, el bastionado de sistemas y el cumplimiento de marcos normativos y de seguridad de la información.",
    "T7": "El presente capítulo evalúa la madurez en la entrega de servicios, soporte técnico y observabilidad de sistemas que conforman {tower_name} en {client_name}. La auditoría analiza la disciplina en el control de cambios, la precisión de la base de datos de configuración (CMDB), la eficacia en la resolución de incidencias y la correlación proactiva de eventos operativos.",
    "T8": "Este capítulo examina el modelo fiduciario, la visibilidad económica y la gobernanza estratégica de la tecnología que integran {tower_name} en {client_name}. La evaluación analiza la previsibilidad y reparto de costes de infraestructura entre unidades de negocio, la optimización de acuerdos de licenciamiento de software y la alineación del gasto técnico con los objetivos de la organización.",
    "T9": "El presente capítulo aborda el diagnóstico del puesto de trabajo digital, soluciones de colaboración y flota de dispositivos de usuario que articulan {tower_name} en {client_name}. El análisis evalúa la estandarización y homogeneidad del parque de equipos, la automatización del ciclo de vida y parcheo, la experiencia digital del usuario y la seguridad de acceso en puestos distribuidos.",
    "T10": "Este capítulo analiza la infraestructura de plataformas operativas dedicadas, sistemas de ejecución de actividad y periféricos de campo que sustentan {tower_name} en {client_name}. La evaluación audita la robustez del hardware en puntos críticos de operación, la continuidad transaccional ante contingencias de red y el grado de modernización de los sistemas que soportan la actividad de negocio."
}

ch3_intro_universal_en = {
    "T1": "This chapter executes the technical diagnosis of the physical facilities, electromechanical power distribution, and precision cooling governing {tower_name} across {client_name}. The evaluation audits critical room resilience, examining uninterruptible power continuity, thermal efficiency and containment, and preventative maintenance controls over core operational assets.",
    "T2": "This chapter documents the architectural assessment of compute platforms, virtualization hypervisors, and hybrid execution environments comprising {tower_name} across {client_name}. The diagnosis examines cluster sizing and bin-packing capacity, CPU and memory contention, and guest operating system lifecycle management against modern decoupling paradigms.",
    "T3": "This chapter analyzes communications architecture, campus networks, and wide-area interconnection links comprising {tower_name} across {client_name}. The audit evaluates topological resilience against transport failures, microsegmentation and perimeter controls across trust boundaries, and latency stability across corporate services and distributed operating sites.",
    "T4": "This chapter addresses the technical diagnosis of enterprise storage platforms, primary arrays, and secondary backup repositories comprising {tower_name} across {client_name}. The evaluation audits database performance and latency SLA compliance, immutable ransomware protection and air-gapping defenses, and storage lifecycle capacity governance.",
    "T5": "This chapter examines the operational resilience and disaster recovery posture (BC/DR) governing {tower_name} across {client_name}. The analysis contrasts technical failover and recovery procedures against business disruption tolerances, evaluating physical facility independence, core data protection, and site operational autonomy during central outages.",
    "T6": "This section presents the evaluation of the cybersecurity posture, identity governance, and infrastructure defenses comprising {tower_name} across {client_name}. The diagnostic audits privileged access controls (PAM), threat detection and telemetry visibility, system hardening, and compliance with enterprise security and regulatory frameworks.",
    "T7": "This chapter evaluates service delivery maturity, operational technical support, and observability workflows comprising {tower_name} across {client_name}. The audit examines change control discipline, configuration management database (CMDB) accuracy, incident resolution efficacy, and proactive operational event correlation.",
    "T8": "This chapter examines the fiduciary model, technological financial transparency, and strategic technology governance comprising {tower_name} across {client_name}. The evaluation analyzes infrastructure cost predictability and showback across business units, software licensing optimization, and technological investment alignment with organizational priorities.",
    "T9": "This chapter addresses the diagnosis of the digital workplace, collaboration solutions, and user endpoint fleets comprising {tower_name} across {client_name}. The analysis evaluates device fleet standardization and homogeneity, automated lifecycle staging and patching, digital employee experience (DEX), and secure endpoint access across distributed workspaces.",
    "T10": "This chapter analyzes the dedicated operational platforms, activity execution systems, and field peripherals underpinning {tower_name} across {client_name}. The evaluation audits hardware resilience at critical operating points, transactional continuity during network contingencies, and the modernization posture of core operational systems."
}

# ----------------------------------------------------------------------
# 2. PURE DATA-DRIVEN SCORECARD TEMPLATES (DYNAMIC PARAMETER BINDING)
# ----------------------------------------------------------------------
scorecard_template_es = "Con una calificación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_name} en {client_name} presenta su mayor área de exposición operativa en el vector de {weakest_pillar_name} ({weakest_pillar_score}/5,0). Las evidencias levantadas constatan que {primary_risk_synthesis}, lo que condiciona la resiliencia del dominio y exige priorizar su modernización arquitectónica."
scorecard_template_en = "Achieving a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}), the {tower_name} domain across {client_name} exhibits its primary operational exposure within the {weakest_pillar_name} capability ({weakest_pillar_score}/5.0). Forensic evidence indicates that {primary_risk_synthesis}, which constrains overall domain resilience and requires prioritized architectural modernization."

ch3_scorecard_universal_es = {f"T{i}": scorecard_template_es for i in range(1, 11)}
ch3_scorecard_universal_en = {f"T{i}": scorecard_template_en for i in range(1, 11)}

# ----------------------------------------------------------------------
# 3. UNIVERSAL STRUCTURAL TRANSVERSAL INTROS (NO MONOLITHIC CLONES)
# ----------------------------------------------------------------------
cross_cutting_debt_intro_by_tower_es = {
    "T1": "Más allá del diagnóstico individual por pilar, la auditoría identifica los principales patrones de fricción operativa y vulnerabilidades físicas en la infraestructura electromecánica:",
    "T2": "Más allá de la evaluación por capacidad, el análisis constata los patrones estructurales de rigidez arquitectónica y dimensionamiento que condicionan la plataforma de cómputo:",
    "T3": "Más allá del análisis por componente, la auditoría identifica los estrangulamientos críticos en la topología de comunicaciones y segmentación de redes corporativas e industriales:",
    "T4": "Más allá de la revisión por nivel de servicio, el diagnóstico revela las desalineaciones estructurales en la protección, persistencia y ciclo de vida del dato corporativo:",
    "T5": "Más allá del análisis por vector de continuidad, la auditoría constata los puntos ciegos críticos en la postura de resiliencia y recuperación operativa del negocio:",
    "T6": "Más allá del diagnóstico por control técnico, la evaluación identifica las brechas estructurales de exposición cibernética, gobierno de identidades y cumplimiento normativo:",
    "T7": "Más allá del examen por proceso, la auditoría evidencia las ineficiencias sistémicas en la entrega de soporte operativo, gobierno del cambio y observabilidad de servicios:",
    "T8": "Más allá de la evaluación presupuestaria, el análisis identifica los vectores de ineficiencia fiduciaria, gestión contractual y opacidad en el gasto tecnológico:",
    "T9": "Más allá de la revisión por servicio de usuario, la auditoría constata las fricciones operativas de homogeneidad, soporte y seguridad en el ecosistema del puesto de trabajo:",
    "T10": "Más allá del diagnóstico por componente local, la evaluación revela las vulnerabilidades operativas críticas en los sistemas dedicados a la operativa y ejecución del negocio:"
}

cross_cutting_debt_intro_by_tower_en = {
    "T1": "Beyond individual pillar findings, the audit identifies primary operational friction patterns and physical vulnerabilities across electromechanical infrastructure:",
    "T2": "Beyond isolated capacity metrics, the analysis confirms structural patterns of architectural rigidity and resource contention conditioning the compute estate:",
    "T3": "Beyond individual component reviews, the audit identifies critical bottlenecks across communications network topology and perimeter segmentation:",
    "T4": "Beyond service-level observations, the diagnosis reveals structural misalignments across data persistence, storage tiering, and corporate backup protection:",
    "T5": "Beyond theoretical continuity plans, the audit confirms critical blind spots across operational resilience, recovery testing, and business survival:",
    "T6": "Beyond technical control checklists, the evaluation identifies structural gaps across cybersecurity exposure, identity governance, and regulatory compliance:",
    "T7": "Beyond isolated support tickets, the audit exposes systemic operational inefficiencies across change discipline, service delivery, and observability workflows:",
    "T8": "Beyond traditional budget accounting, the analysis identifies vectors of fiduciary inefficiency, contractual lock-in, and technological cost opacity:",
    "T9": "Beyond end-user hardware inventories, the audit identifies operational friction vectors across endpoint fleet heterogeneity, manual staging, and workplace security:",
    "T10": "Beyond local hardware components, the evaluation reveals mission-critical operational vulnerabilities across dedicated operational activity systems:"
}

# Universal template keys
universal_keys_es = {
    "cross_cutting_debt_title": "Análisis Transversal de Deuda Tecnológica y Patrones de Riesgo Estructural",
    "cross_cutting_debt_intro": "Más allá del diagnóstico vertical por pilar, la auditoría identifica los principales patrones horizontales de fricción operativa y deuda técnica que condicionan el dominio:",
    "cross_cutting_debt_item_template": "{idx}. {pattern_title}: {pattern_description}",
    "maturity_scale_legend": "Escala CMMI (Umbral de tramo: ≥X,60): Nivel 1 - Inicial (<1,60) | Nivel 2 - Repetible (1,60-2,59) | Nivel 3 - Definido (2,60-3,59) | Nivel 4 - Gestionado (3,60-4,19) | Nivel 5 - Optimizado (≥4,20)"
}

universal_keys_en = {
    "cross_cutting_debt_title": "Cross-Cutting Technological Debt and Structural Risk Pattern Analysis",
    "cross_cutting_debt_intro": "Beyond granular pillar findings, the audit identifies primary horizontal operational friction patterns and technical debt conditioning the domain across vectors:",
    "cross_cutting_debt_item_template": "{idx}. {pattern_title}: {pattern_description}",
    "maturity_scale_legend": "CMMI Maturity Scale (Threshold: ≥X.60): Level 1 - Initial (<1.60) | Level 2 - Repeatable (1.60-2.59) | Level 3 - Defined (2.60-3.59) | Level 4 - Managed (3.60-4.19) | Level 5 - Optimized (≥4.20)"
}

# ----------------------------------------------------------------------
# 4. PURGE ALL HARDCODED cross_cutting_debt_tX_pY KEYS FROM ALL LOCALES
# ----------------------------------------------------------------------
for lang in list(locales.keys()):
    if isinstance(locales[lang], dict):
        keys_to_delete = [k for k in locales[lang].keys() if k.startswith("cross_cutting_debt_t") and "_p" in k]
        for k in keys_to_delete:
            del locales[lang][k]

# Inject clean universal keys
locales["es"]["ch3_intro_by_tower"] = ch3_intro_universal_es
locales["es"]["ch3_scorecard_by_tower"] = ch3_scorecard_universal_es
locales["es"]["cross_cutting_debt_intro_by_tower"] = cross_cutting_debt_intro_by_tower_es
locales["es"].update(universal_keys_es)

locales["en"]["ch3_intro_by_tower"] = ch3_intro_universal_en
locales["en"]["ch3_scorecard_by_tower"] = ch3_scorecard_universal_en
locales["en"]["cross_cutting_debt_intro_by_tower"] = cross_cutting_debt_intro_by_tower_en
locales["en"].update(universal_keys_en)

# Symmetrize pt, fr, de, ja
base_keys = set(locales["en"].keys())
for lang in ["pt", "fr", "de", "ja"]:
    if lang in locales:
        for k in base_keys:
            if k not in locales[lang] or isinstance(locales[lang][k], dict):
                locales[lang][k] = locales["en"][k]

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print(f"Successfully purged all hardcoded client/manufacturing strings and established pure universal catalogs in {loc_path}!")
