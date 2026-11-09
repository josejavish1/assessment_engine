#!/usr/bin/env python3
"""Apply the exact 4 surgical interventions prescribed by gemini-4-argon to reach 10.0/10.0."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ----------------------------------------------------------------------
# 1. FIX T6, T2, T5, T10 PAYLOAD PATTERNS
# ----------------------------------------------------------------------

# T6 (Cybersecurity)
with open(REPO_ROOT / "working/molins/T6/blueprint_t6_payload.json", "r", encoding="utf-8") as f:
    t6 = json.load(f)
t6["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Gobernanza deficiente de accesos privilegiados y cuentas compartidas sin bóveda (PAM): Uso extendido de credenciales administrativas genéricas (root/admin) en servidores e infraestructura de red sin rotación automatizada ni grabación de sesiones, impidiendo atribuir acciones críticas y vulnerando los requisitos de trazabilidad de la Directiva NIS2.",
    "Ceguera de detección correlacionada (SIEM/SOC) y desprotección en la frontera IT/OT: Ausencia de agregación centralizada de telemetría de seguridad y respuesta activa 24x7, dejando las redes industriales de planta y filiales sin detección temprana ante movimientos laterales o intrusiones.",
    "Gestión artesanal del ciclo de vida de identidades y persistencia de sistemas obsoletos: Procesos manuales de alta, cambio y baja de usuarios entre sedes centrales, filiales y contratas, combinados con servidores fuera de soporte (EoL) en producción que carecen de microsegmentación o controles compensatorios auditables."
]
with open(REPO_ROOT / "working/molins/T6/blueprint_t6_payload.json", "w", encoding="utf-8") as f:
    json.dump(t6, f, indent=2, ensure_ascii=False)

# T2 (Compute)
with open(REPO_ROOT / "working/molins/T2/blueprint_t2_payload.json", "r", encoding="utf-8") as f:
    t2 = json.load(f)
t2["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Contención artificial de capacidad física y agotamiento de memoria RAM en hipervisores: Los clústeres de virtualización operan al límite de su memoria física —condicionados por restricciones de licenciamiento por procesador—, anulando la capacidad de absorción ante caídas de nodos host y forzando intervenciones manuales para evitar la degradación de cargas productivas.",
    "Aprovisionamiento artesanal mediante consolas gráficas y fragmentación multi-nube: Predominio de operaciones manuales tanto en el entorno local vCenter como en los tres hyperscalers (GCP, Azure, OCI), careciendo de plantillas de Infraestructura como Código (IaC) y entornos de contenedores que agilicen el despliegue de aplicaciones.",
    "Deuda técnica en sistemas operativos y dependencia de perfiles técnicos únicos: Persistencia de servidores con sistemas operativos próximos al fin de soporte y ausencia de control automatizado de deriva de configuración (drift), agravada por la concentración del conocimiento de orquestación y bases de datos en especialistas individuales sin runbooks formalizados."
]
with open(REPO_ROOT / "working/molins/T2/blueprint_t2_payload.json", "w", encoding="utf-8") as f:
    json.dump(t2, f, indent=2, ensure_ascii=False)

# T5 (Resilience)
with open(REPO_ROOT / "working/molins/T5/blueprint_t5_payload.json", "r", encoding="utf-8") as f:
    t5 = json.load(f)
t5["cross_capabilities_analysis"]["common_deficiency_patterns"] = [
    "Riesgo de fallo de modo común por proximidad geográfica entre centros de datos (500 metros): El diseño de recuperación corporativo descansa en dos salas técnicas ubicadas en el mismo polígono industrial de Sant Vicenç dels Horts bajo idéntica acometida eléctrica y ambiental, invalidando la protección ante siniestros graves de emplazamiento.",
    "Desconexión entre capacidades técnicas de replicación y compromisos de negocio (RTO/RPO): Pese a disponer de cabinas NetApp duplicadas y clústeres locales, Molins carece de un Análisis de Impacto de Negocio (BIA) formalizado que alinee los tiempos de recuperación informática con la tolerancia máxima de parada en hornos, molienda y expedición.",
    "Pruebas de recuperación circunscritas a componentes aislados y dependencia de conocimiento tácito: Las validaciones de contingencia se limitan a conmutaciones parciales de infraestructura sin ejecutar simulacros integrales extremo a extremo ni disponer de modos de supervivencia autónoma en plantas remotas, dependiendo de la intervención manual de ingenieros clave durante una crisis."
]
with open(REPO_ROOT / "working/molins/T5/blueprint_t5_payload.json", "w", encoding="utf-8") as f:
    json.dump(t5, f, indent=2, ensure_ascii=False)

# T10 (Plant & Dispatch)
with open(REPO_ROOT / "working/molins/T10/blueprint_t10_payload.json", "r", encoding="utf-8") as f:
    t10 = json.load(f)
t10["cross_capabilities_analysis"]["common_deficiency_patterns"][2] = (
    "Heterogeneidad arquitectónica en servidores de borde y despliegues artesanales inter-planta: Cada centro productivo y filial adquirida opera con configuraciones locales dispares desplegadas de forma manual, sin plantillas estandarizadas de cómputo industrial, telemetría proactiva unificada en Zabbix ni procedimientos automatizados de reconstrucción rápida ante el fallo físico de un servidor de planta."
)
with open(REPO_ROOT / "working/molins/T10/blueprint_t10_payload.json", "w", encoding="utf-8") as f:
    json.dump(t10, f, indent=2, ensure_ascii=False)

print("Applied sharpened patterns to T6, T2, T5, T10 payloads!")

# ----------------------------------------------------------------------
# 2. ERADICATE ENGLISH STRINGS IN LOCALES CH3 INTROS
# ----------------------------------------------------------------------
loc_path = REPO_ROOT / "engine_config/locales.json"
with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

ch3_intro_es = {
    "T1": "El presente capítulo ejecuta el diagnóstico técnico de las instalaciones físicas, suministro electromecánico y climatización de centros de datos en {client_name}. La evaluación audita la resiliencia de las salas técnicas y centros de procesamiento examinando la continuidad de potencia ininterrumpida, la estabilidad y eficiencia térmica, y los procedimientos de mantenimiento preventivo sobre activos críticos.",
    "T2": "Este capítulo documenta la evaluación arquitectónica de las plataformas de cómputo, hipervisores de virtualización y servicios de ejecución híbrida en {client_name}. El diagnóstico examina la capacidad de absorción y dimensionamiento de clústeres, la contención de recursos de CPU y memoria, y el ciclo de vida de los sistemas operativos frente a paradigmas modernos de desacoplamiento.",
    "T3": "El presente capítulo analiza la arquitectura de comunicaciones, redes de campus y enlaces distribuidos que vertebran las comunicaciones en {client_name}. La auditoría evalúa la resiliencia topológica frente a contingencias de transporte, la microsegmentación y control del perímetro entre zonas de confianza, y la estabilidad y latencia en el acceso a servicios corporativos y sedes distribuidas.",
    "T4": "Este capítulo aborda el diagnóstico técnico de las plataformas de almacenamiento masivo, cabinas corporativas y repositorios de respaldo en {client_name}. La evaluación audita el cumplimiento de SLAs de latencia y rendimiento de bases de datos, las defensas de inmutabilidad y aislamiento frente a ransomware, y la gobernanza del ciclo de vida y capacidad del almacenamiento.",
    "T5": "El presente capítulo examina la postura de resiliencia operativa y recuperación ante desastres (BC/DR) en {client_name}. El análisis contrasta los procedimientos técnicos de conmutación y respaldo frente a las tolerancias de interrupción del negocio, evaluando la independencia de recintos, la salvaguarda de repositorios clave y la autonomía de sedes ante caídas centrales.",
    "T6": "Esta sección presenta la evaluación de la postura de ciberseguridad, gobierno de identidades y protección de infraestructura en {client_name}. El diagnóstico audita el control de accesos privilegiados de administración, la visibilidad de telemetría y detección de amenazas, el bastionado de sistemas y el cumplimiento de marcos normativos y de seguridad de la información.",
    "T7": "El presente capítulo evalúa la madurez en la entrega de servicios, soporte técnico y observabilidad de infraestructura (ITSM) en {client_name}. La auditoría analiza la disciplina en el control de cambios, la precisión de la base de datos de configuración (CMDB), la eficacia en la resolución de incidencias y la correlación proactiva de eventos operativos.",
    "T8": "Este capítulo examina el modelo fiduciario, la visibilidad económica y la gobernanza estratégica de la tecnología (FinOps) en {client_name}. La evaluación analiza la previsibilidad y reparto de costes de infraestructura entre unidades de negocio, la optimización de acuerdos de licenciamiento de software y la alineación del gasto técnico con los objetivos de la organización.",
    "T9": "El presente capítulo aborda el diagnóstico del puesto de trabajo digital, soluciones de colaboración y flota de dispositivos de usuario en {client_name}. El análisis evalúa la estandarización y homogeneidad del parque de equipos, la automatización del ciclo de vida y parcheo, la experiencia digital del usuario y la seguridad de acceso en puestos distribuidos.",
    "T10": "Este capítulo analiza la infraestructura de sistemas dedicados a operaciones de planta, básculas de pesaje y expedición logística en {client_name}. La evaluación audita la robustez del hardware en puntos críticos de operación, la continuidad transaccional ante contingencias de red y el grado de modernización de los sistemas que soportan la actividad de negocio."
}

ch3_intro_en = {
    "T1": "This chapter executes the technical diagnosis of physical facilities, electromechanical power distribution, and precision cooling governing datacenters across {client_name}. The evaluation audits critical room resilience, examining uninterruptible power continuity, thermal efficiency and containment, and preventative maintenance controls over core operational assets.",
    "T2": "This chapter documents the architectural assessment of compute platforms, virtualization hypervisors, and hybrid execution environments across {client_name}. The diagnosis examines cluster sizing and bin-packing capacity, CPU and memory contention, and guest operating system lifecycle management against modern decoupling paradigms.",
    "T3": "This chapter analyzes communications architecture, campus networks, and wide-area interconnection links across {client_name}. The audit evaluates topological resilience against transport failures, microsegmentation and perimeter controls across trust boundaries, and latency stability across corporate services and distributed operating sites.",
    "T4": "This chapter addresses the technical diagnosis of enterprise storage platforms, primary arrays, and secondary backup repositories across {client_name}. The evaluation audits database performance and latency SLA compliance, immutable ransomware protection and air-gapping defenses, and storage lifecycle capacity governance.",
    "T5": "This chapter examines the operational resilience and disaster recovery posture (BC/DR) across {client_name}. The analysis contrasts technical failover and recovery procedures against business disruption tolerances, evaluating physical facility independence, core data protection, and site operational autonomy during central outages.",
    "T6": "This section presents the evaluation of the cybersecurity posture, identity governance, and infrastructure defenses across {client_name}. The diagnostic audits privileged access controls (PAM), threat detection and telemetry visibility, system hardening, and compliance with enterprise security and regulatory frameworks.",
    "T7": "This chapter evaluates service delivery maturity, operational technical support, and observability workflows (ITSM) across {client_name}. The audit examines change control discipline, configuration management database (CMDB) accuracy, incident resolution efficacy, and proactive operational event correlation.",
    "T8": "This chapter examines the fiduciary model, technological financial transparency, and strategic technology governance (FinOps) across {client_name}. The evaluation analyzes infrastructure cost predictability and showback across business units, software licensing optimization, and technological investment alignment with organizational priorities.",
    "T9": "This chapter addresses the diagnosis of the digital workplace, collaboration solutions, and user endpoint fleets across {client_name}. The analysis evaluates device fleet standardization and homogeneity, automated lifecycle staging and patching, digital employee experience (DEX), and secure endpoint access across distributed workspaces.",
    "T10": "This chapter analyzes the dedicated operational platforms, plant weighbridges, and shipping dispatch infrastructure across {client_name}. The evaluation audits hardware resilience at critical operating points, transactional continuity during network contingencies, and the modernization posture of core operational systems."
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

print("Updated locales.json with pure localized domain introductions!")
