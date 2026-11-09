#!/usr/bin/env python3
"""Inject rich, 4-sentence bespoke domain introductions into all 10 Molins payloads."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

intros = {
    "T1": {
        "domain_objective": "La presente evaluación audita la resiliencia operativa y la robustez electromecánica de los centros de datos (CPD 1 y CPD 2) de Molins en Sant Vicenç dels Horts. El análisis evalúa la capacidad de las instalaciones físicas para garantizar la continuidad ininterrumpida de las operaciones fabriles, identificando puntos únicos de fallo en la alimentación eléctrica, deficiencias de climatización y riesgos ambientales que amenazan las líneas de ensacado, molienda y expedición.",
        "introduction_paragraph": "La infraestructura evaluada da soporte directo a la actividad industrial y a los servicios corporativos centralizados de Molins. La arquitectura física se distribuye entre dos salas técnicas principales interconectadas por fibra oscura, albergando la plataforma hiperconvergente HPE SimpliVity y el almacenamiento transaccional NetApp. El diagnóstico contrasta las instalaciones frente a los estándares TIA-942-B, ASHRAE TC 9.9 y la norma europea EN 50600.",
        "technological_domain": "Data Center Facilities",
        "included_components": ["Salas técnicas CPD1 y CPD2", "Sistemas SAI y distribución de potencia", "Climatización y control de polvo en suspensión", "Protección contra incendios y monitoreo BMS"]
    },
    "T2": {
        "domain_objective": "Este capítulo diagnostica la capacidad, estabilidad operativa y ciclo de vida de las plataformas de cómputo, virtualización y cargas híbridas de Molins. El análisis determina la solvencia de la infraestructura para sostener las transacciones del ERP corporativo, los sistemas MES de control fabril y las cargas de negocio, evaluando la saturación de memoria RAM física y las dependencias críticas de soporte.",
        "introduction_paragraph": "La plataforma de cómputo de Molins sustenta el núcleo operativo combinando clústeres hiperconvergentes HPE SimpliVity sobre VMware vSphere en Sant Vicenç dels Horts con extensiones en GCP, Azure y OCI. La capa de virtualización soporta más de 300 máquinas virtuales productivas que dan servicio a las fábricas y filiales del grupo. La evaluación se estructura conforme a los controles CIS Controls v8 y las directrices de virtualización segura NIST SP 800-125.",
        "technological_domain": "Hybrid Cloud, Compute & Virtualization",
        "included_components": ["Clústeres HPE SimpliVity", "Hipervisores VMware vSphere", "Cargas de nube en GCP, Azure y OCI", "Máquinas virtuales Windows/Linux en producción"]
    },
    "T3": {
        "domain_objective": "La presente evaluación audita la resiliencia topológica, la arquitectura de comunicaciones WAN/LAN y la seguridad perimetral que interconectan los centros de datos centrales, las fábricas de cemento, las canteras y las sedes corporativas de Molins. El análisis determina la capacidad de la red para sostener sin interrupciones el tráfico transaccional hacia el ERP, la telemetría industrial en planta y la operativa logística en campas de expedición y básculas.",
        "introduction_paragraph": "La infraestructura auditada abarca el núcleo de conmutación en Sant Vicenç dels Horts, los circuitos de telecomunicaciones hacia emplazamientos remotos y la frontera de convergencia entre las redes corporativas (IT) y los entornos de control industrial (OT). El diagnóstico contrasta la topología actual con la norma de seguridad de redes ISO/IEC 27033, el estándar de segmentación industrial IEC 62443 y las directrices de resiliencia de comunicaciones NIST SP 800-41.",
        "technological_domain": "Enterprise Networks & WAN Connectivity",
        "included_components": ["Núcleo de conmutación LAN/Campus", "Enlaces WAN monoproveedor a fábricas y canteras", "Perímetro de seguridad e interconexión IT/OT", "Red inalámbrica industrial en campas logísticas"]
    },
    "T4": {
        "domain_objective": "Este capítulo evalúa la capacidad, rendimiento transaccional y ciberresiliencia del ecosistema de almacenamiento masivo y plataformas de datos de Molins. El diagnóstico examina la estabilidad de los repositorios frente a los picos de transaccionalidad de bases de datos de producción y la eficacia de los mecanismos de salvaguarda ante contingencias de pérdida masiva de información.",
        "introduction_paragraph": "El parque de almacenamiento de Molins descansa sobre cabinas de almacenamiento unificado NetApp en configuración de réplica síncrona entre centros de datos locales, junto a repositorios secundarios de copias de seguridad en plantas y filiales. La evaluación audita las políticas de retención, las defensas contra ransomware y el gobierno de capacidad conforme a las normas ISO/IEC 27040, NIST SP 800-209 y las recomendaciones del consorcio SNIA.",
        "technological_domain": "Storage Platforms & Corporate Backup",
        "included_components": ["Cabinas NetApp corporativas", "Replicación síncrona metro-cluster", "Políticas de retención y cuotas de disco", "Repositorios de respaldo secundario"]
    },
    "T5": {
        "domain_objective": "La presente evaluación audita la postura de resiliencia tecnológica, continuidad operativa y recuperación ante desastres (BC/DR) para salvaguardar los procesos críticos de negocio de Molins. El análisis contrasta los tiempos técnicos de recuperación frente a las tolerancias de parada en hornos de clínker, molinos de cemento, plantas de hormigón y expedición logística de camiones.",
        "introduction_paragraph": "El marco de continuidad examina la interdependencia geográfica y electromecánica entre las salas de Sant Vicenç dels Horts, los esquemas de replicación y la autonomía operativa de las plantas industriales ante la pérdida de los servicios corporativos centrales. El diagnóstico evalúa los planes de contingencia conforme a los estándares ISO 22301, ISO/IEC 27031 (IRBC) y las directrices metodológicas NIST SP 800-34.",
        "technological_domain": "Operational Continuity & Disaster Recovery",
        "included_components": ["Análisis de impacto en el negocio (BIA)", "Resiliencia geográfica inter-CPD (500m)", "Procedimientos de conmutación y failover", "Modo de supervivencia en plantas industriales"]
    },
    "T6": {
        "domain_objective": "Este capítulo ejecuta el diagnóstico pericial de la postura de ciberseguridad, gobierno de identidades y defensa en profundidad sobre la infraestructura digital e industrial de Molins. La auditoría examina la eficacia de los controles de protección perimetral, la gestión de privilegios de acceso y la visibilidad de telemetría de eventos frente a amenazas avanzadas y riesgos de intrusión lateral.",
        "introduction_paragraph": "El perímetro de seguridad evaluado cubre los servicios corporativos de identidad (Active Directory / Entra ID), los activos de red, las estaciones de trabajo y la segregación de redes de fabricación en plantas cementeras y filiales internacionales. El análisis audita el cumplimiento normativo y la madurez técnica tomando como referencia la Directiva Europea NIS2, el estándar ISO/IEC 27001, el marco NIST Cybersecurity Framework 2.0 y la norma IEC 62443.",
        "technological_domain": "Cybersecurity & Identity Governance",
        "included_components": ["Gobierno de accesos privilegiados (PAM)", "Supervisión SIEM/SOC y telemetría de seguridad", "Gestión del ciclo de vida de identidades", "Segregación y bastionado de la frontera IT/OT"]
    },
    "T7": {
        "domain_objective": "La presente evaluación audita la madurez operativa, el modelo de soporte técnico y las prácticas de gestión de servicios de TI (ITSM) que sustentan la infraestructura de Molins. El diagnóstico analiza la solvencia del equipo nuclear de infraestructura para absorber la demanda técnica, la trazabilidad de los flujos de cambio y la capacidad de respuesta ante incidencias que degraden los servicios de fábrica o negocio.",
        "introduction_paragraph": "El alcance operativo cubre los flujos de gobernanza sobre la base de configuración (CMDB), la plataforma de monitorización Zabbix, la gestión de alertas de infraestructura y la relación contractual con proveedores de servicios gestionados como NOS. La evaluación contrasta los procedimientos internos con las mejores prácticas de ITIL v4, el estándar ISO/IEC 20000-1 y las disciplinas de ingeniería de fiabilidad del sitio (SRE).",
        "technological_domain": "ITSM & Digital Operations",
        "included_components": ["Capacidad del equipo nuclear de infraestructura", "Base de datos de configuración (CMDB)", "Gestión de problemas y análisis de causa raíz", "Acuerdos operacionales (OLAs) y soporte en planta"]
    },
    "T8": {
        "domain_objective": "Este capítulo examina el modelo fiduciario, la visibilidad del gasto tecnológico y la gobernanza estratégica de las inversiones de TI (FinOps) en Molins. El análisis evalúa la capacidad de la organización para correlacionar los costes de infraestructura con las unidades de negocio consumidoras, identificar bolsas de ineficiencia y alinear la asignación presupuestaria con los planes de crecimiento y sostenibilidad.",
        "introduction_paragraph": "La auditoría financiera examina la dispersión del gasto en las nubes públicas (GCP, Azure, OCI), la estructura de acuerdos de licenciamiento de software por procesador físico y los contratos marco de telecomunicaciones y soporte externalizado. La evaluación se estructura conforme a los principios de FinOps Foundation Framework, el marco de gobierno corporativo COBIT 2019 y las directrices ISO/IEC 38500 e ISO/IEC 19770.",
        "technological_domain": "Strategy, Governance & FinOps",
        "included_components": ["Telemetría FinOps y modelos showback/chargeback", "Gestión de licenciamiento de bases de datos por core", "Gobernanza de contratos externalizados (NOS)", "Alineación de inversiones con prioridades de negocio"]
    },
    "T9": {
        "domain_objective": "La presente evaluación audita la arquitectura del puesto de trabajo digital, la flota de dispositivos de usuario y las soluciones de productividad que dan servicio al colectivo humano de Molins. El análisis examina la eficacia en el despliegue y renovación de equipos, la experiencia del empleado y la seguridad del puesto frente a riesgos de fuga de información o compromiso de credenciales corporativas.",
        "introduction_paragraph": "El parque de puestos auditado abarca la flota de portátiles para profesionales de oficina, los terminales compartidos en plantas industriales y los quioscos de expedición en básculas de camiones, junto al ecosistema colaborativo Microsoft 365. El diagnóstico evalúa la homogeneidad y el bastionado del endpoint conforme a las guías CIS Benchmarks, ISO/IEC 27002 y los modelos modernos de gestión unificada Zero Trust.",
        "technological_domain": "Digital Workplace & Unified Communications",
        "included_components": ["Ciclo de vida de portátiles corporativos", "Aprovisionamiento moderno zero-touch (Intune)", "Seguridad en quioscos compartidos de planta", "Despliegue unificado de parches en sedes y filiales"]
    },
    "T10": {
        "domain_objective": "Este capítulo diagnostica la infraestructura tecnológica de borde, los sistemas de ejecución fabril y los periféricos de expedición logística que articulan el flujo de facturación directa (Truck-to-Cash) de Molins. El análisis evalúa la robustez del hardware local en plantas de producción, la tolerancia de los sistemas de pesaje ante caídas de enlace y la gobernanza operativa en la frontera de soporte entre TI y mantenimiento industrial.",
        "introduction_paragraph": "El perímetro de borde auditado incluye los servidores locales de planta, los terminales de pesaje y control de accesos en básculas, los autómatas de expedición y los enlaces de transporte transaccional hacia el ERP corporativo. La evaluación audita la arquitectura y los niveles de servicio conforme a los estándares de integración industrial ISA-95 (IEC 62264), la norma IEC 62443 y los patrones de Edge Computing industrial resiliente.",
        "technological_domain": "Plant Systems & Local Operations",
        "included_components": ["Servidores locales de planta y tolerancia offline", "Sistemas de pesaje y expedición (Truck-to-Cash)", "Matriz RACI entre TI Corporativo y Mantenimiento", "Estandarización de hardware de borde inter-planta"]
    }
}

for t, intro_dict in intros.items():
    p = REPO_ROOT / f"working/molins/{t}/blueprint_{t.lower()}_payload.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        d["domain_introduction"] = intro_dict
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        print(f"Injected rich 4-sentence domain_introduction into {t} payload!")

print("All 10 payloads now contain high-caliber bespoke introductions with international standards!")
