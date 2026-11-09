#!/usr/bin/env python3
"""Remediate hardcoding violations in locales.json and establish universal, multi-tenant architecture."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
loc_path = REPO_ROOT / "engine_config/locales.json"

with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

# ----------------------------------------------------------------------
# 1. 100% UNIVERSAL, VERTICAL-AGNOSTIC CH3 INTRODUCTIONS (NO CLIENT/GEO/VENDOR LITERALS)
# ----------------------------------------------------------------------
ch3_intro_universal_es = {
    "T1": "La evaluación del dominio de {tower_title} en {client_name} examina la resiliencia, capacidad electromecánica y estabilidad física de la infraestructura crítica. Este capítulo documenta el diagnóstico técnico de las salas técnicas y centros de procesamiento, auditando la continuidad de suministro ininterrumpido de potencia, los sistemas de climatización y control ambiental, y los procedimientos de mantenimiento preventivo sobre los activos de soporte.",
    "T2": "Este capítulo documenta la evaluación arquitectónica de las plataformas de cómputo, hipervisores de virtualización y servicios de ejecución híbrida que vertebran {tower_title} en {client_name}. El diagnóstico analiza la capacidad de absorción y dimensionamiento de clústeres, la contención de recursos de CPU y memoria, y el ciclo de vida de los sistemas operativos frente a paradigmas modernos de desacoplamiento y automatización.",
    "T3": "El presente capítulo analiza la arquitectura de comunicaciones, redes de campus y enlaces de interconexión que articulan {tower_title} en {client_name}. La auditoría evalúa la resiliencia topológica frente a contingencias de transporte, la microsegmentación y control del perímetro entre zonas de confianza corporativas e industriales, y la estabilidad y latencia en el acceso a servicios críticos y sedes distribuidas.",
    "T4": "Este capítulo aborda el diagnóstico técnico de las plataformas de almacenamiento corporativo, cabinas primarias y repositorios de respaldo que integran {tower_title} en {client_name}. La evaluación audita el cumplimiento de SLAs de latencia y rendimiento de bases de datos, las defensas de inmutabilidad y aislamiento frente a ransomware, y la gobernanza del ciclo de vida y capacidad del almacenamiento.",
    "T5": "El presente capítulo examina la postura de resiliencia operativa y recuperación ante desastres (BC/DR) que gobierna {tower_title} en {client_name}. El análisis contrasta los procedimientos técnicos de conmutación y respaldo frente a las tolerancias de interrupción del negocio, evaluando la independencia física de recintos, la salvaguarda de repositorios clave y la autonomía de sedes ante caídas de servicios centrales.",
    "T6": "Esta sección presenta la evaluación de la postura de ciberseguridad, gestión de identidades y defensas de infraestructura que componen {tower_title} en {client_name}. El diagnóstico audita el control de accesos privilegiados de administración, la visibilidad de telemetría y detección proactiva de amenazas, el bastionado de sistemas y el cumplimiento de marcos normativos y de seguridad de la información.",
    "T7": "El presente capítulo evalúa la madurez en la entrega de servicios, soporte técnico y observabilidad de sistemas que conforman {tower_title} en {client_name}. La auditoría analiza la disciplina en el control de cambios, la precisión de la base de datos de configuración (CMDB), la eficacia en la resolución de incidencias y la correlación proactiva de eventos operativos hacia los procesos de negocio.",
    "T8": "Este capítulo examina el modelo fiduciario, la visibilidad económica y la gobernanza estratégica de la tecnología que integran {tower_title} en {client_name}. La evaluación analiza la previsibilidad y reparto de costes de infraestructura entre unidades de negocio, la optimización de acuerdos de licenciamiento de software y la alineación de la inversión técnica con las prioridades de la organización.",
    "T9": "El presente capítulo aborda el diagnóstico del puesto de trabajo digital, soluciones de colaboración y flota de dispositivos de usuario que articulan {tower_title} en {client_name}. El análisis evalúa la estandarización y homogeneidad del parque de equipos, la automatización del ciclo de vida y parcheo, la experiencia digital del usuario y la seguridad de acceso en puestos distribuidos y compartidos.",
    "T10": "Este capítulo analiza la infraestructura de plataformas operativas dedicadas, sistemas de ejecución de actividad y periféricos de campo que sustentan {tower_title} en {client_name}. La evaluación audita la robustez del hardware en puntos críticos de operación, la continuidad transaccional ante contingencias de red y el grado de modernización de los sistemas que soportan la actividad de negocio."
}

ch3_intro_universal_en = {
    "T1": "The evaluation of the {tower_title} domain across {client_name} examines electromechanical resilience, physical capacity, and critical facilities stability. This chapter documents the technical diagnosis of computer rooms and processing facilities, auditing uninterrupted power continuity, environmental cooling controls, and preventative maintenance governance over core operational assets.",
    "T2": "This chapter documents the architectural assessment of compute platforms, virtualization hypervisors, and hybrid execution environments comprising {tower_title} across {client_name}. The diagnosis examines cluster sizing and bin-packing capacity, CPU and memory contention, and guest operating system lifecycle management against modern decoupling paradigms.",
    "T3": "This chapter analyzes communications architecture, campus networks, and wide-area interconnection links comprising {tower_title} across {client_name}. The audit evaluates topological resilience against transport failures, microsegmentation and perimeter controls across trust boundaries, and latency stability across corporate services and distributed operating sites.",
    "T4": "This chapter addresses the technical diagnosis of enterprise storage platforms, primary arrays, and secondary backup repositories comprising {tower_title} across {client_name}. The evaluation audits database performance and latency SLA compliance, immutable ransomware protection and air-gapping defenses, and storage lifecycle capacity governance.",
    "T5": "This chapter examines the operational resilience and disaster recovery posture (BC/DR) governing {tower_title} across {client_name}. The analysis contrasts technical failover and recovery procedures against business disruption tolerances, evaluating physical facility independence, core data protection, and site operational autonomy during central outages.",
    "T6": "This section presents the evaluation of the cybersecurity posture, identity governance, and infrastructure defenses comprising {tower_title} across {client_name}. The diagnostic audits privileged access controls (PAM), threat detection and telemetry visibility, system hardening, and compliance with enterprise security and regulatory frameworks.",
    "T7": "This chapter evaluates service delivery maturity, operational technical support, and observability workflows comprising {tower_title} across {client_name}. The audit examines change control discipline, configuration management database (CMDB) accuracy, incident resolution efficacy, and proactive operational event correlation.",
    "T8": "This chapter examines the fiduciary model, technological financial transparency, and strategic technology governance comprising {tower_title} across {client_name}. The evaluation analyzes infrastructure cost predictability and showback across business units, software licensing optimization, and technological investment alignment with organizational priorities.",
    "T9": "This chapter addresses the diagnosis of the digital workplace, collaboration solutions, and user endpoint fleets comprising {tower_title} across {client_name}. The analysis evaluates device fleet standardization and homogeneity, automated lifecycle staging and patching, digital employee experience (DEX), and secure endpoint access across distributed workspaces.",
    "T10": "This chapter analyzes dedicated operational platforms, activity execution systems, and field peripherals underpinning {tower_title} across {client_name}. The evaluation audits hardware resilience at critical operating points, transactional continuity during network contingencies, and the modernization posture of core operational systems."
}

# ----------------------------------------------------------------------
# 2. PURE DATA-DRIVEN SCORECARD TEMPLATES (MATURITY MODULATED + ASYMMETRIC CONTRAST)
# ----------------------------------------------------------------------
scorecard_templates_es = {
    "scorecard_contrast_divergent_high": "Con una valoración técnica consolidada de {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_title} en {client_name} cuenta con una base tecnológica estructurada y procedimentada. La disciplina operativa alcanzada en {strongest_pillar_name} ({strongest_pillar_score}/5,0) proporciona una sólida plataforma de partida, situando el reto del área en optimizar la eficiencia y resolver la fricción residual en {weakest_pillar_name} ({weakest_pillar_score}/5,0) para maximizar el valor de negocio.",
    "scorecard_contrast_divergent_mid": "Evaluado en {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_title} en {client_name} sostiene la operativa cotidiana mediante procedimientos funcionales pero marcadamente artesanales. La solvencia demostrada en {strongest_pillar_name} ({strongest_pillar_score}/5,0) contrasta con el cuello de botella técnico que representa {weakest_pillar_name} ({weakest_pillar_score}/5,0), delimitando la frontera de estandarización necesaria para evitar que el crecimiento desborde la capacidad del equipo.",
    "scorecard_contrast_divergent_low": "Con una calificación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_title} en {client_name} opera bajo un nivel de exposición operativa severa. Si bien se constatan avances procedimentales en {strongest_pillar_name} ({strongest_pillar_score}/5,0), la resiliencia global se ve críticamente comprometida por la inmadurez en {weakest_pillar_name} ({weakest_pillar_score}/5,0), exigiendo priorizar su modernización estructural.",
    "scorecard_contrast_uniform": "Con una calificación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), el dominio de {tower_title} en {client_name} presenta un nivel de madurez homogéneo en todas sus capacidades evaluadas. El reto del área radica en elevar de forma coordinada los estándares de estandarización y automatización para consolidar la resiliencia operativa.",
    "scorecard_contrast_single": "Con una calificación técnica de {score_val} sobre 5,0 ({maturity_tier_label}), la capacidad evaluada de {weakest_pillar_name} en {client_name} define la postura operativa del dominio, requiriendo alinear sus controles con los objetivos de continuidad y servicio de la organización."
}

scorecard_templates_en = {
    "scorecard_contrast_divergent_high": "With a consolidated technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), the {tower_title} domain across {client_name} operates upon an established, disciplined engineering baseline. The maturity demonstrated in {strongest_pillar_name} ({strongest_pillar_score}/5.0) provides an enduring foundation, shifting the strategic challenge to optimizing efficiency and resolving residual friction in {weakest_pillar_name} ({weakest_pillar_score}/5.0) to maximize enterprise value.",
    "scorecard_contrast_divergent_mid": "Evaluated at {score_val} out of 5.0 ({maturity_tier_label}), the {tower_title} domain across {client_name} sustains baseline operations through functional but largely manual procedures. Operational stability demonstrated in {strongest_pillar_name} ({strongest_pillar_score}/5.0) contrasts with the technical bottleneck in {weakest_pillar_name} ({weakest_pillar_score}/5.0), defining the critical standardization boundary needed to scale reliably.",
    "scorecard_contrast_divergent_low": "Scoring a technical maturity of {score_val} out of 5.0 ({maturity_tier_label}), the {tower_title} domain across {client_name} operates under acute operational exposure. While procedural progress is evident in {strongest_pillar_name} ({strongest_pillar_score}/5.0), overall resilience is critically undermined by deficiencies in {weakest_pillar_name} ({weakest_pillar_score}/5.0), mandating prioritized structural remediation.",
    "scorecard_contrast_uniform": "Achieving a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}), the {tower_title} domain across {client_name} exhibits an even maturity distribution across all evaluated capabilities. The strategic focus must center on elevating engineering standardization and automation across the entire domain.",
    "scorecard_contrast_single": "Achieving a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}), the evaluated capability of {weakest_pillar_name} across {client_name} governs the domain's operational posture, requiring direct alignment with organizational service objectives."
}

# Update Spanish
locales["es"]["ch3_intro_by_tower"] = ch3_intro_universal_es
locales["es"].update(scorecard_templates_es)
# Remove old hardcoded ch3_scorecard_by_tower dict if present
if "ch3_scorecard_by_tower" in locales["es"]:
    del locales["es"]["ch3_scorecard_by_tower"]

# Update English
locales["en"]["ch3_intro_by_tower"] = ch3_intro_universal_en
locales["en"].update(scorecard_templates_en)
if "ch3_scorecard_by_tower" in locales["en"]:
    del locales["en"]["ch3_scorecard_by_tower"]

# Symmetrize pt, fr, de, ja
base_keys = set(locales["en"].keys())
for lang in ["pt", "fr", "de", "ja"]:
    if lang in locales:
        for k in base_keys:
            if k not in locales[lang] or isinstance(locales[lang][k], dict):
                locales[lang][k] = locales["en"][k]
        if "ch3_scorecard_by_tower" in locales[lang]:
            del locales[lang]["ch3_scorecard_by_tower"]

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print("Successfully established 100% universal, multi-tenant catalogs in locales.json!")
