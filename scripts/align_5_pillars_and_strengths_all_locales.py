#!/usr/bin/env python3
"""Align 5 canonical pillars, strengths, and findings across all 6 locales (RFC 083).

Synchronizes engine_config/locales.json to ensure that every tower (T1-T10) contains
exactly 5 canonical pillars with matching strengths and findings across es, en, pt, fr, de, ja.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

PILLARS_5_ES: Dict[str, List[str]] = {
    "T1": [
        "Energía y Continuidad Eléctrica",
        "Climatización, Refrigeración y Control Ambiental",
        "Seguridad Física y Control de Accesos",
        "Protección Contra Incendios y Seguridad Ambiental",
        "Operación de Facilities, Monitorización y Mantenimiento",
    ],
    "T2": [
        "Fundamentos de Cómputo y Virtualización",
        "Plataforma de Contenedores y Operaciones Kubernetes",
        "Habilitación de Cloud Híbrido y Landing Zones",
        "Automatización, Aprovisionamiento y Autoservicio",
        "Operaciones de Plataforma, Observabilidad y Confiabilidad",
    ],
    "T3": [
        "Redes de Centro de Datos y Campus",
        "WAN / SD-WAN y Conectividad de Sedes",
        "Interconexión de CPDs (DCI) y Transporte Resiliente",
        "Conectividad a Cloud Híbrido y Servicios Edge",
        "Operaciones de Red, Observabilidad y Automatización",
    ],
    "T4": [
        "Arquitectura de Almacenamiento y Niveles de Servicio",
        "Rendimiento, Capacidad y Ciclo de Vida del Almacenamiento",
        "Servicios de Datos: Snapshots, Replicación y Eficiencia",
        "Seguridad y Control de Acceso en Plataformas de Datos",
        "Integración de Plataforma y Operaciones de Almacenamiento",
    ],
    "T5": [
        "Estrategia de Continuidad y Gobierno BC/DR",
        "Copia de Seguridad y Recuperación Operativa",
        "Recuperación ante Desastres (DR) y Conmutación",
        "Ciberresiliencia e Inmutabilidad contra Ransomware",
        "Alta Disponibilidad y Resiliencia Arquitectónica",
    ],
    "T6": [
        "Identidad y Control de Acceso (IAM)",
        "Gestión de Accesos Privilegiados (PAM) y Secretos",
        "Bastionado y Control de Configuración Segura",
        "Gestión de Vulnerabilidades y Parcheo",
        "Segregación de Red, Registro de Logs y Auditoría",
    ],
    "T7": [
        "Gobierno del Servicio, Catálogo y SLAs/SLOs",
        "Centro de Servicios y Gestión de Incidentes",
        "Gestión de Cambios, Despliegues y CMDB",
        "Gestión de Problemas y Fiabilidad (SRE)",
        "Observabilidad, Gestión de Eventos y AIOps",
    ],
    "T8": [
        "Estrategia Tecnológica y Hoja de Ruta",
        "Gobernanza de TI, Cartera y Marco de Decisión",
        "Gestión de Riesgo Tecnológico y Cumplimiento",
        "FinOps y Gestión Económica de Infraestructura",
        "Medición de Valor, KPIs Ejecutivos y Mejora Continua",
    ],
    "T9": [
        "Gestión del Ciclo de Vida de Puestos y Dispositivos",
        "Identidad del Puesto de Trabajo y Experiencia de Acceso",
        "Productividad, Colaboración y Gestión del Conocimiento",
        "Operación, Soporte y Autoservicio del Puesto de Trabajo",
        "Experiencia Digital del Empleado (DEX) y Adopción",
    ],
    "T10": [
        "Operaciones de Plataforma Mainframe y Sistemas Core",
        "Control de Cambios, Releases y Configuración Legacy",
        "Capacidad, Rendimiento y Gestión de Cargas Batch",
        "Integración, Interoperabilidad y Exposición de APIs Modernas",
        "Estrategia de Modernización, Deuda Técnica y Sostenibilidad",
    ],
}

PILLARS_5_EN: Dict[str, List[str]] = {
    "T1": [
        "Power & Electrical Continuity",
        "Climate Control & Environmental Resilience",
        "Physical Security & Access Control",
        "Fire Suppression & Environmental Safety",
        "Facilities Operations, Monitoring & Maintenance",
    ],
    "T2": [
        "Compute Foundation & Virtualization",
        "Container Platform & Kubernetes Operations",
        "Hybrid Cloud Enablement & Landing Zones",
        "Automation, Provisioning & Platform Self-Service",
        "Platform Operations, Observability & Reliability",
    ],
    "T3": [
        "Data Center & Campus Network Foundation",
        "WAN / SD-WAN & Branch Connectivity",
        "DCI & Resilient Transport",
        "Hybrid Cloud Connectivity & Edge Services",
        "Network Operations, Observability & Automation",
    ],
    "T4": [
        "Storage Architecture & Service Levels",
        "Performance, Capacity & Lifecycle Management",
        "Data Services: Snapshots, Replication & Efficiency",
        "Security & Access Controls for Data Platforms",
        "Platform Integration & Storage Operations",
    ],
    "T5": [
        "BC/DR Governance & Continuity Strategy",
        "Backup & Restore Operational Readiness",
        "Disaster Recovery Architecture & Failover",
        "Cyber Recovery & Ransomware Immutability",
        "High Availability & Architectural Resilience",
    ],
    "T6": [
        "Identity & Access Management (IAM)",
        "Privileged Access Management (PAM) & Secrets",
        "Hardening & Secure Configuration Baseline",
        "Vulnerability & Patch Management",
        "Network Segmentation, Logging & Audit",
    ],
    "T7": [
        "Service Governance, Catalog & SLA Management",
        "Service Desk & Incident Management",
        "Change, Release & Configuration Management (CMDB)",
        "Problem Management & Site Reliability Engineering (SRE)",
        "Observability, Event Management & AIOps",
    ],
    "T8": [
        "Technology Strategy & Strategic Roadmap",
        "IT Governance, Portfolio & Decision Framework",
        "Risk Governance, Compliance & Control",
        "Cloud FinOps & Infrastructure Economics",
        "Value Realization, Executive Metrics & Continuous Improvement",
    ],
    "T9": [
        "Endpoint & Device Lifecycle Management",
        "Workplace Identity & User Access Experience",
        "Productividad, Colaboración y Gestión del Conocimiento",
        "Workplace Operations, Support & Self-Service",
        "Digital Employee Experience (DEX) & Adoption",
    ],
    "T10": [
        "Core Mainframe & Legacy Platform Operations",
        "Legacy Change, Release & Configuration Governance",
        "Capacity, Performance & Batch Workload Management",
        "Legacy Integration, Interoperability & Modern APIs",
        "Modernization Strategy, Tech Debt & Sustainability",
    ],
}

STRENGTHS_5_ES: Dict[str, List[str]] = {
    "T1": [
        "Sistemas de alimentación ininterrumpida (SAI) en esquema N+1 y grupos electrógenos con mantenimiento regular.",
        "Unidades de climatización de precisión (CRAC) con redundancia y control de temperatura en salas técnicas.",
        "Sistemas automáticos de detección y extinción de incendios por agente limpio en salas principales.",
        "Detección óptica y termovelocimétrica precoz de conatos de incendio zonificada en falso suelo y techo bajo normativa técnica.",
        "Cuadros eléctricos monitorizados y alarmas técnicas básicas integradas en puestos de control.",
    ],
    "T2": [
        "Clúster hiperconvergente centralizado que proporciona alta densidad de cómputo para cargas corporativas.",
        "Estandarización de plantillas base de sistemas operativos y entornos de contenedores para microservicios.",
        "Alojamiento productivo de cargas críticas (SAP S/4HANA) sobre infraestructura cloud de primer nivel (GCP/Azure).",
        "Procedimientos de clonación y plantillas base de aprovisionamiento para instancias virtuales estándar.",
        "Mecanismos de conmutación automática por fallo (HA) operativos a nivel de hipervisor.",
    ],
    "T3": [
        "Conmutación troncal de doble núcleo con enlaces redundantes entre armarios de distribución.",
        "Conectividad WAN y SD-WAN establecida hacia la totalidad de plantas industriales, canteras y sedes internacionales.",
        "Enlace directo de fibra óptica de 10 Gbps interconectando los centros de datos principales.",
        "Interconexión dedicada de alta velocidad hacia hyperscalers a través de puerto de transporte consolidado.",
        "Sondas de monitorización de caudal y supervisión de estado de enlaces troncales activas en consolas centrales.",
    ],
    "T4": [
        "Cabinas de almacenamiento corporativo de alto rendimiento con aprovisionamiento dinámico de capacidad.",
        "Capacidad de almacenamiento monitorizada con alertas preventivas de umbral en consolas de administración.",
        "Políticas de snapshots programados y replicación asíncrona entre centros operativos.",
        "Configuración de volúmenes de almacenamiento protegidos contra borrado accidental y cifrado en reposo.",
        "Integración nativa de volúmenes SAN con el hipervisor de virtualización corporativo.",
    ],
    "T5": [
        "Procedimientos operativos de contingencia y recuperación documentados para sistemas críticos de planta.",
        "Políticas de copia de seguridad periódica en disco y cinta con custodia externa documentada.",
        "Personal técnico interno con profundo conocimiento de los procesos de restauración manual en planta.",
        "Copias de seguridad desconectadas físicamente (air-gapped) en cintas magnéticas bajo custodia externa.",
        "Esquemas de redundancia local en componentes electromecánicos y conmutación básica en servidores core.",
    ],
    "T6": [
        "Dominio centralizado de gestión de identidades y accesos corporativo (Active Directory).",
        "Políticas corporativas de contraseñas robustas y segregación inicial de roles administrativos.",
        "Despliegue homogéneo de protección de punto final (EDR) con supervisión por centro de operaciones (SOC).",
        "Procedimientos periódicos de escaneo perimetral externo y actualización de sistemas operativos corporativos.",
        "Cortafuegos perimetrales de última generación con políticas corporativas de filtrado y VPN segura.",
    ],
    "T7": [
        "Catálogo inicial de servicios de TI y acuerdos de nivel de servicio (SLAs) formalizados para usuarios internos.",
        "Plataforma centralizada de soporte e incidencias (ITSM) con seguimiento estructurado de tickets.",
        "Inventario centralizado de activos de hardware y licencias gestionado por el equipo de infraestructura.",
        "Revisiones post-incidente tras caídas de servicio mayores con identificación de causas directas.",
        "Sondas de monitorización de infraestructura básica (CPU, disco, conectividad) con alertas a consolas centrales.",
    ],
    "T8": [
        "Hoja de ruta tecnológica alineada con las directrices estratégicas de crecimiento y transformación del grupo.",
        "Comité periódico de TI y procesos de aprobación presupuestaria estructurados para proyectos mayores.",
        "Políticas formales de seguridad de la información y cumplimiento de normativas fiscales y contables.",
        "Visibilidad inicial de facturación mensual centralizada en consolas de proveedores cloud (GCP, Azure y OCI).",
        "Métricas financieras estándar de costes operativos de TI consolidadas para la dirección financiera.",
    ],
    "T9": [
        "Parque homogéneo de puestos de trabajo bajo sistema operativo estándar con despliegue de aplicaciones base.",
        "Acceso remoto seguro y autenticación multifactor (MFA) implementada para empleados corporativos.",
        "Herramientas de colaboración y productividad en la nube (M365) ampliamente adoptadas por los usuarios.",
        "Canal de soporte de primer nivel estructurado y procedimientos de despliegue automático de parches.",
        "Canales de comunicación directa y encuestas periódicas de satisfacción de usuarios de TI.",
    ],
    "T10": [
        "Equipos de pesaje industrial con calibración metrológica periódica y mantenimiento regular en todas las básculas.",
        "Procedimientos locales de despacho manual bien establecidos ante contingencias de conectividad.",
        "Mecanismo de sincronización de albaranes de pesaje hacia el sistema central de facturación ERP.",
        "Conectores punto a punto funcionales que garantizan la continuidad de la expedición y facturación.",
        "Alta cualificación y compromiso del personal técnico y operativo de planta en la resolución de incidencias.",
    ],
}

STRENGTHS_5_EN: Dict[str, List[str]] = {
    "T1": [
        "Uninterruptible power supply (UPS) systems in N+1 redundancy with certified preventive maintenance routines.",
        "Precision air conditioning units (CRAC) providing environmental control across technical datacenter rooms.",
        "Automated clean-agent fire suppression and detection deployed in primary technical spaces.",
        "Optical and thermal fire detection zoning under raised floors and ceilings complying with engineering standards.",
        "Monitored electrical distribution switchboards and technical alarms integrated into operations control.",
    ],
    "T2": [
        "Centralized hyperconverged compute cluster delivering dense processing capacity for corporate workloads.",
        "Standardized operating system base templates and container execution environments for microservices.",
        "Production hosting of mission-critical workloads (SAP S/4HANA) on Tier-1 enterprise hyperscalers (GCP/Azure).",
        "Automated virtual server cloning and baseline deployment procedures across primary clusters.",
        "Hypervisor-level automated high availability (HA) failover operational across compute nodes.",
    ],
    "T3": [
        "Dual-core backbone switching infrastructure with redundant uplinks across technical distribution frames.",
        "Corporate WAN and SD-WAN connectivity established across manufacturing plants, quarries, and branch offices.",
        "Dedicated high-speed 10 Gbps point-to-point fiber interconnecting primary operational datacenters.",
        "High-performance direct interconnect ports linking core routing to public cloud transit hubs.",
        "Centralized bandwidth monitoring probes and active link telemetry supervised in network consoles.",
    ],
    "T4": [
        "High-performance enterprise storage arrays featuring dynamic capacity allocation and thin-provisioning.",
        "Storage capacity thresholds monitored with proactive alert notifications in central dashboards.",
        "Scheduled snapshot policies and asynchronous block-level replication between active datacenters.",
        "Protected enterprise storage volumes configured with accidental deletion safeguards and data-at-rest encryption.",
        "Native SAN storage volume integration supporting corporate hypervisor clusters.",
    ],
    "T5": [
        "Documented contingency and disaster recovery operational procedures for essential industrial systems.",
        "Scheduled disk and tape backup policies with verified off-site custody procedures.",
        "Skilled internal engineering team possessing deep operational experience in manual plant system restoration.",
        "Air-gapped offline magnetic tape backups maintained in physically isolated custody facilities.",
        "Local electromechanical component redundancy and automated core server service failover.",
    ],
    "T6": [
        "Centralized enterprise identity and access management directory (Active Directory).",
        "Enforced corporate password complexity policies and initial administrative role segregation.",
        "Homogeneous endpoint detection and response (EDR) agent deployment with external SOC monitoring.",
        "Scheduled external perimeter penetration scanning and corporate operating system update cycles.",
        "Next-generation perimeter firewalls enforcing corporate network traffic filtering and secure VPN.",
    ],
    "T7": [
        "Documented IT service catalog and service level agreements (SLAs) established for internal business units.",
        "Centralized IT Service Management (ITSM) ticketing platform structuring operational incidents and requests.",
        "Centralized hardware and software license inventory maintained by the IT infrastructure department.",
        "Structured post-incident reviews conducted following major service outages to identify direct causes.",
        "Core infrastructure telemetry probes (CPU, memory, storage, ping) transmitting alerts to central consoles.",
    ],
    "T8": [
        "Strategic technology roadmap aligned with corporate business growth and digital modernization goals.",
        "Periodic IT governance committee and structured capital expenditure approval processes.",
        "Formal corporate information security policies and accounting/tax compliance oversight.",
        "Centralized monthly billing visibility within multi-cloud consoles (GCP, Azure, and OCI).",
        "Consolidated IT operational expenditure metrics tracked for senior financial leadership.",
    ],
    "T9": [
        "Standardized corporate endpoint fleet operating under unified modern management baselines.",
        "Secure remote connectivity and multi-factor authentication (MFA) enabled for knowledge workers.",
        "Cloud collaboration and productivity suites (M365) widely adopted across business units.",
        "Structured Level-1 service desk and automated operating system security patch distribution.",
        "Direct communication channels and periodic user satisfaction surveys conducted by the IT team.",
    ],
    "T10": [
        "Industrial weighbridge scales subjected to regular metrological calibration and preventive maintenance.",
        "Robust, well-rehearsed manual dispatch continuity procedures during communication disruptions.",
        "Transactional synchronization interface transferring weighbridge dispatch tickets to central SAP ERP.",
        "Functional point-to-point integration connectors guaranteeing dispatch and billing continuity.",
        "Dedicated and highly qualified on-site operational staff ensuring resilient local execution.",
    ],
}

FINDINGS_5_ES: Dict[str, List[str]] = {
    "T1": [
        "Carencia de segregación aerotérmica de pasillos frío/calor generando recirculaciones térmicas en racks al límite de ASHRAE.",
        "Inexistencia de telemetría IoT en tiempo real sobre cuadros y PDUs, impidiendo medir potencia instalada vs consumida por fase.",
        "Ausencia de control de acceso biométrico en esclusas y permisos electrónicos de trabajo (ePtW) requeridos para auditar NIS2.",
        "Ausencia de correlación automática entre telemetría ambiental y sistemas de extinción física para contención de zonas contiguas.",
        "Mantenimiento electromecánico preventivo gestionado de forma reactiva sin GMAO centralizado ni calendario de pruebas con carga real.",
    ],
    "T2": [
        "Saturación estructural de memoria RAM y CPU (>90%) que impide failover N+1 entre salas técnicas sin degradación inducida.",
        "Ausencia de una plataforma unificada y gestionada de Kubernetes corporativo con políticas de seguridad y service mesh.",
        "Adopción fragmentada de nube pública sin arquitectura automatizada de Landing Zones ni guardrails de gobierno.",
        "Inexistencia de Infraestructura como Código (IaC) declarativa para aprovisionamiento continuo y control de versiones.",
        "Ausencia de Service Level Objectives (SLOs) y telemetría de fiabilidad (SRE) vinculada a transacciones core de negocio.",
    ],
    "T3": [
        "Switches de acceso en canteras y plantas con ciclos de vida próximos al fin de soporte comercial (EoL).",
        "Conexiones hacia plantas secundarias dependientes de túneles IPSec estáticos sin balanceo dinámico de tráfico.",
        "Data Center Interconnect (DCI) punto a punto sin topología de anillo ni diversificación física de canalización exterior.",
        "Arquitectura de interconexión cloud sin diseño de tránsito centralizado (Cloud Router) ni failover automatizado.",
        "Operación de red basada en procedimientos manuales vía CLI sin prácticas de NetDevOps ni configuración declarativa.",
    ],
    "T4": [
        "Carencia de políticas nativas de Quality of Service (QoS) en cabinas SAN, generando contención de I/O en bases de datos.",
        "Fragmentación en la captura y retención de registros de auditoría del plano de datos sin repositorios locales WORM.",
        "Dependencia de instantáneas locales sin aislamiento físico frente a ataques dirigidos de ransomware.",
        "Falta de activación de inmutabilidad estricta WORM (SnapLock) en volúmenes críticos para cumplimiento NIS2.",
        "Fricción operativa y delimitación difusa de responsabilidades en la gestión de almacenamiento entre TI y soporte externo.",
    ],
    "T5": [
        "Concentración de la resiliencia en un radio geográfico de 500 metros, actuando como punto único de fallo ante catástrofes de zona.",
        "Tiempos de recuperación técnicos (RTO > 4 horas) que superan los márgenes tolerables para procesos de expedición continua.",
        "Inexistencia de simulacros periódicos de recuperación ante desastres (game days) con corte real de suministro.",
        "Ausencia de un enclave de recuperación aislado (Cyber Recovery Vault) con validación forense automatizada antes de restaurar.",
        "Falta de simetría en la reserva de recursos entre centros de datos que impide un failover transparente sin degradación.",
    ],
    "T6": [
        "Fragmentación del plano de identidad y persistencia de cuentas estáticas sobreprivilegiadas sin elevación dinámica JIT.",
        "Carencia de una plataforma corporativa de Privileged Access Management (PAM) con rotación automática de secretos.",
        "Auditoría de configuración segura discontinua sin verificación automatizada de líneas base de bastionado.",
        "Cobertura parcial en el escaneo de vulnerabilidades internas, omitiendo máquinas virtuales legadas y activos de filiales.",
        "Red interna en plantas industriales sin microsegmentación Este-Oeste, permitiendo propagación lateral no detectada.",
    ],
    "T7": [
        "Desalineación entre SLAs técnicos y procesos críticos de negocio, generando métricas no representativas del impacto fabril.",
        "Triaje y escalado de incidencias manual sin enrutamiento inteligente basado en criticidad operativa de planta.",
        "Ausencia de una Configuration Management Database (CMDB) automatizada y federada con mapa de dependencias actualizado.",
        "Procesos de análisis de causa raíz (RCA) reactivos sin institucionalización de prácticas de ingeniería de fiabilidad (SRE).",
        "Fragmentación de herramientas de monitorización sin correlación causal de eventos entre capas on-premise, cloud y redes OT.",
    ],
    "T8": [
        "Obsolescencia crítica en sistemas operativos y motores de bases de datos legados sin plan presupuestado de modernización.",
        "Gobernanza asimétrica entre la sede central y las filiales recientemente integradas, manteniendo silos operativos.",
        "Carencia de un marco continuo de gestión del riesgo tecnológico cuantificado bajo estándares Open FAIR.",
        "Gobernanza financiera cloud reactiva sin políticas automatizadas de etiquetado ni modelos de imputación showback/chargeback.",
        "Inexistencia de cuadros de mando ejecutivos que vinculen la inversión en TI con la generación de valor directo en planta.",
    ],
    "T9": [
        "Dispositivos en plantas y canteras gestionados de forma local sin enrolamiento homogéneo en la plataforma central.",
        "Vulnerabilidad en terminales de planta compartidos que carecen de mecanismos de autenticación biométrica o FIDO2.",
        "Dispersión documental en repositorios huérfanos sin políticas automatizadas de ciclo de vida y expiración de contenido.",
        "Gestión manual del aprovisionamiento y soporte del puesto de trabajo, incrementando el tiempo de respuesta en sedes remotas.",
        "Carencia de herramientas de telemetría de experiencia digital del empleado (DEX) para detección proactiva de degradación.",
    ],
    "T10": [
        "Puestos de control de pesaje en plantas operando sobre estaciones de trabajo con hardware desfasado y sistemas operativos obsoletos.",
        "Modificaciones en sistemas transaccionales legados aplicadas de forma artesanal sin trazabilidad de versiones en repositorios Git.",
        "Mallas batch y sincronizaciones de datos concentradas en ventanas críticas que generan picos de carga en el almacenamiento.",
        "Integraciones directas a nivel de base de datos entre sistemas legados y modernos sin capa de APIs gobernadas ni contratos de datos.",
        "Dependencia crítica de conocimiento tácito de personal especializado próximo a jubilación en tecnologías Oracle Forms y CentOS antiguo.",
    ],
}

FINDINGS_5_EN: Dict[str, List[str]] = {
    "T1": [
        "Absence of hot/cold aisle aerodynamic containment causing thermal recirculation across compute racks at ASHRAE limits.",
        "Lack of real-time IoT power telemetry on electrical panels and PDUs, preventing phase-level capacity measurement.",
        "Absence of biometric access controls at airlocks and electronic work permits (ePtW) required for NIS2 compliance.",
        "Lack of automated correlation between environmental sensors and fire suppression systems for adjacent containment.",
        "Electromechanical preventive maintenance managed reactively without centralized CMMS or live-load transfer testing.",
    ],
    "T2": [
        "Structural CPU and memory saturation (>90%) preventing N+1 failover between technical rooms without workload degradation.",
        "Absence of a unified corporate managed Kubernetes platform with security guardrails and service mesh.",
        "Fragmented public cloud adoption lacking automated Landing Zone governance and policy enforcement guardrails.",
        "Absence of declarative Infrastructure as Code (IaC) pipelines for continuous provisioning and version tracking.",
        "Absence of Service Level Objectives (SLOs) and Site Reliability Engineering (SRE) telemetry linked to core business flows.",
    ],
    "T3": [
        "Access layer switches across remote quarries and industrial plants approaching commercial End-of-Life (EoL).",
        "Secondary plant interconnects dependent on static IPSec tunnels lacking dynamic traffic steering and SD-WAN failover.",
        "Point-to-point Data Center Interconnect (DCI) lacking physical ring topology and exterior conduit diversification.",
        "Cloud interconnect architecture lacking centralized transit routing (Cloud Router) and automated multi-region failover.",
        "Manual network administration via CLI without declarative NetDevOps workflows or version-controlled configurations.",
    ],
    "T4": [
        "Lack of native Quality of Service (QoS) bandwidth shaping on SAN arrays, exposing critical databases to I/O noisy neighbors.",
        "Fragmented audit logging on storage controllers without dedicated write-once-read-many (WORM) audit vaults.",
        "Reliance on local snapshot copies without physical cyber isolation against targeted ransomware encryption campaigns.",
        "Absence of strict WORM immutability (SnapLock) activation across mission-critical volume snapshots for NIS2 compliance.",
        "Operational friction and blurred boundary delineation in storage administration between internal IT and external support.",
    ],
    "T5": [
        "Concentration of datacenter resilience within a single 500-meter perimeter, creating a geographic Single Point of Failure.",
        "Technical recovery times (RTO > 4 hours) exceeding operational tolerance thresholds for continuous plant dispatch.",
        "Absence of scheduled, full-scale disaster recovery exercises (game days) under live production mains power disconnection.",
        "Absence of an isolated Cyber Recovery Vault with automated forensic data validation prior to mass restore execution.",
        "Lack of symmetric standby capacity across twin datacenters preventing transparent workload failover without shutdown.",
    ],
    "T6": [
        "Identity plane fragmentation and persistence of over-privileged static administrative credentials lacking dynamic JIT elevation.",
        "Absence of an enterprise Privileged Access Management (PAM) vault enforcing automated credential rotation and session monitoring.",
        "Infrequent security configuration baseline audits lacking automated configuration drift detection across systems.",
        "Partial vulnerability scanning coverage omitting legacy virtual machines, industrial gateways, and acquired subsidiaries.",
        "Flat industrial plant network topology lacking East-West microsegmentation, allowing undetected threat propagation.",
    ],
    "T7": [
        "Misalignment between technical infrastructure SLAs and core manufacturing operations, obscuring plant-level outage impact.",
        "Manual incident triage and dispatch workflows lacking intelligent routing based on industrial operational criticality.",
        "Absence of an automated, federated Configuration Management Database (CMDB) maintaining live dependency maps.",
        "Reactive root cause analysis (RCA) procedures lacking institutionalized Site Reliability Engineering (SRE) error budgets.",
        "Fragmented monitoring tooling lacking cross-domain causal event correlation between on-premise, cloud, and OT environments.",
    ],
    "T8": [
        "Critical architectural obsolescence across legacy operating systems and database engines lacking budgeted modernization paths.",
        "Asymmetric governance between corporate headquarters and newly acquired subsidiaries, perpetuating operational silos.",
        "Absence of continuous, quantified technical risk governance modeled under Open FAIR standards.",
        "Reactive cloud financial governance lacking automated resource tagging enforcement and showback/chargeback models.",
        "Absence of executive dashboards correlating technology investments with measurable plant productivity gains.",
    ],
    "T9": [
        "Plant and quarry endpoint devices administered locally without centralized modern device management enrollment.",
        "Vulnerability across shared industrial plant workstations lacking passwordless biometric or FIDO2 authentication.",
        "Document sprawl across unmanaged cloud repositories lacking automated lifecycle and data retention governance policies.",
        "Manual endpoint provisioning and workstation support processes increasing fulfillment lead times across remote facilities.",
        "Absence of Digital Employee Experience (DEX) real-time telemetry for proactive degradation and latency detection.",
    ],
    "T10": [
        "Industrial weighbridge control terminals operating on outdated hardware configurations and obsolete operating systems.",
        "Software modifications on legacy transactional components applied manually without version control in Git repositories.",
        "Batch processing queues and data transfers concentrated in peak operating windows causing storage controller I/O spikes.",
        "Direct database-level point-to-point links between legacy and modern systems lacking governed API contracts.",
        "Critical dependence on tacit operational knowledge held by specialized personnel approaching retirement on legacy stacks.",
    ],
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Update es
    cat_es = data["es"].get("tomo_tower_forensic_catalog", {})
    for tid in [f"T{i}" for i in range(1, 11)]:
        if tid in cat_es:
            subp_names = PILLARS_5_ES[tid]
            cat_es[tid]["subpillars"] = [[name, "2.50"] for name in subp_names]
            cat_es[tid]["strengths"] = STRENGTHS_5_ES[tid]
            cat_es[tid]["findings"] = FINDINGS_5_ES[tid]

    # 2. Update en
    cat_en = data["en"].get("tomo_tower_forensic_catalog", {})
    for tid in [f"T{i}" for i in range(1, 11)]:
        if tid in cat_en:
            subp_names = PILLARS_5_EN[tid]
            cat_en[tid]["subpillars"] = [[name, "2.50"] for name in subp_names]
            cat_en[tid]["strengths"] = STRENGTHS_5_EN[tid]
            cat_en[tid]["findings"] = FINDINGS_5_EN[tid]

    # 3. Propagate to secondary locales (pt, fr, de, ja) using en as baseline
    for loc in ["pt", "fr", "de", "ja"]:
        cat_loc = data[loc].get("tomo_tower_forensic_catalog", {})
        for tid in [f"T{i}" for i in range(1, 11)]:
            if tid in cat_loc:
                subp_names = PILLARS_5_EN[tid]
                cat_loc[tid]["subpillars"] = [[name, "2.50"] for name in subp_names]
                cat_loc[tid]["strengths"] = STRENGTHS_5_EN[tid]
                cat_loc[tid]["findings"] = FINDINGS_5_EN[tid]

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully aligned 5 canonical pillars, strengths, and findings across all 6 locales!")


if __name__ == "__main__":
    main()
