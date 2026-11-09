#!/usr/bin/env python3
"""Generate granular 50-pillar CMMI progression matrix with bilingual support (EN/ES) and universal fallbacks."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
output_path = REPO_ROOT / "engine_config/policies/cmmi_progression_matrix.json"

# Detailed 50-pillar milestones
pillar_definitions = {
    # Tower 1: Data Center Facilities
    "T1.P1": {
        "domain": "Power & Electrical Distribution",
        "L1_to_L2": {
            "en": [
                "Eliminate single points of failure (SPOF) in critical electrical distribution and panelboards",
                "Formalize periodic preventive maintenance schedules with certified battery and generator load tests",
                "Deploy baseline telemetric power metering on input switchgear and emergency transfers"
            ],
            "es": [
                "Eliminar puntos únicos de fallo (SPOF) en la distribución eléctrica crítica y cuadros generales de baja tensión",
                "Formalizar calendarios periódicos de mantenimiento preventivo con ensayos certificados de baterías y grupo electrógeno",
                "Desplegar medición telemétrica básica en interruptores de cabecera y sistemas de transferencia automática"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Integrate real-time digital power analytics (iPDUs, branch circuit monitors) into central DCIM/BMS",
                "Establish dual-bus (2N) active-active power distribution feeds to all production server racks",
                "Formalize N+1 redundancy validation procedures under simulated utility outage load"
            ],
            "es": [
                "Integrar analítica digital de potencia en tiempo real (iPDUs y monitorización de circuitos) en el sistema central BMS/DCIM",
                "Implantar distribución eléctrica de doble rama (2N) activo-activo hasta las fuentes de alimentación de cada rack",
                "Formalizar procedimientos periódicos de validación de redundancia N+1 bajo corte simulado de acometida"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Automate dynamic load-shedding and intelligent failover between independent electrical feeds",
                "Deploy AI-driven continuous Power Usage Effectiveness (PUE) optimization and phase balancing",
                "Implement predictive thermal and harmonic distortion analytics for switchgear lifecycle management"
            ],
            "es": [
                "Automatizar el deslastre dinámico de cargas y la conmutación inteligente entre acometidas eléctricas independientes",
                "Desplegar optimización continua del PUE y balanceo de fases en tiempo real mediante analítica avanzada",
                "Implantar monitorización predictiva de distorsión armónica y degradación de condensadores en cuadros y SAIs"
            ]
        }
    },
    "T1.P2": {
        "domain": "Precision Cooling & HVAC",
        "L1_to_L2": {
            "en": [
                "Transition from comfort air conditioners to dedicated precision cooling (CRAC/CRAH) units",
                "Implement cold or hot aisle containment curtains to prevent thermal recirculation",
                "Establish continuous ambient temperature and relative humidity threshold alarms"
            ],
            "es": [
                "Sustituir equipos de climatización de confort por unidades de climatización de precisión (CRAC/CRAH) con control de humedad",
                "Implantar cerramientos de pasillo frío o caliente para erradicar la recirculación térmica en los racks",
                "Configurar sondas ambientales continuas con umbrales de alerta temprana de temperatura y humedad relativa"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Enforce rigid structural aisle containment with automated differential pressure regulation",
                "Establish dual-circuit redundant chiller and piping distribution without single points of failure",
                "Integrate environmental telemetry into centralized BMS with automated fan speed modulation"
            ],
            "es": [
                "Instalar confinamiento térmico rígido de pasillos con regulación automática de presión diferencial",
                "Establecer doble circuito hidráulico redundante de agua glicolada sin puntos únicos de fallo en bombeo",
                "Integrar la telemetría térmica en el BMS centralizado con modulación automática de velocidad de ventiladores EC"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Deploy computational fluid dynamics (CFD) continuous thermal modeling linked to server workload telemetry",
                "Integrate automated free-cooling economizers maximizing seasonal thermodynamic efficiency",
                "Implement autonomous variable-refrigerant modulation adjusting dynamically to compute cluster load"
            ],
            "es": [
                "Desplegar modelado térmico continuo por dinámica de fluidos (CFD) correlacionado con la telemetría de las cargas IT",
                "Integrar economizadores de enfriamiento gratuito (free-cooling) maximizando la eficiencia termodinámica estacional",
                "Implantar modulación autónoma de refrigerante variable ajustada dinámicamente a la disipación de los servidores"
            ]
        }
    },
    "T1.P3": {
        "domain": "Physical Security & Access Control",
        "L1_to_L2": {
            "en": [
                "Eliminate shared physical keys and deploy electronic badge readers on all technical room perimeters",
                "Implement comprehensive CCTV coverage of all data hall ingress points with 30-day retention",
                "Establish a formal visitor logging protocol with mandatory escort requirements for external technicians"
            ],
            "es": [
                "Eliminar llaves físicas compartidas e implantar control de acceso electrónico por tarjeta en todas las salas técnicas",
                "Desplegar circuito cerrado de televisión (CCTV) con cobertura total de accesos y retención mínima de 30 días",
                "Formalizar un libro de registro de visitas con acompañamiento obligatorio para técnicos y proveedores externos"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Deploy multi-factor physical authentication (badge plus biometric verification) for core server rooms",
                "Implement individualized rack-level electronic locking with automated badge audit logging",
                "Integrate physical access telemetry with corporate SIEM for automated off-hours intrusion alerting"
            ],
            "es": [
                "Implantar doble factor de autenticación física (tarjeta más biometría) en las salas técnicas principales",
                "Desplegar cerraduras electrónicas a nivel de rack individual con registro de auditoría de apertura por usuario",
                "Integrar los eventos de acceso físico en el SIEM corporativo con alertas automatizadas ante aperturas fuera de horario"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Deploy automated video analytics detecting tailgating and unauthorized cabinet access in real time",
                "Implement dynamic zero-trust physical access policies tied to active change management work orders",
                "Achieve continuous audit compliance automation with cryptographically verifiable physical access trails"
            ],
            "es": [
                "Desplegar analítica de vídeo con detección automatizada de accesos no autorizados en proximidad (tailgating)",
                "Vincular el acceso físico a órdenes de trabajo activas en la herramienta de cambios mediante políticas Zero Trust",
                "Automatizar auditorías continuas de acceso físico con pistas de auditoría criptográficamente verificables"
            ]
        }
    },
    "T1.P4": {
        "domain": "Fire Detection & Suppression",
        "L1_to_L2": {
            "en": [
                "Inspect, certify, and maintain clean-agent chemical fire suppression tanks and discharge nozzles",
                "Deploy aspirating early warning smoke detection (VESDA) across all technical ceiling and underfloor voids",
                "Establish documented emergency shutdown and localized power interlock testing procedures"
            ],
            "es": [
                "Inspeccionar, retimbrar y certificar botellas y boquillas de extinción por agente limpio en todas las salas",
                "Desplegar sistemas de detección precoz de humo por aspiración (VESDA) en ambiente y falsos suelos/techos",
                "Documentar y ensayar procedimientos de corte de emergencia (EPO) y consignas de desenergización selectiva"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Implement cross-zoned smoke detection interlocks preventing accidental chemical suppression discharges",
                "Establish automated HVAC damper shutdown and pressure relief venting calibrated for gaseous discharge",
                "Integrate fire panel events into central BMS and external emergency response monitoring stations"
            ],
            "es": [
                "Implantar doble enclavamiento cruzado de detección para prevenir disparos accidentales de gas",
                "Instalar compuertas de corte de climatización y compuertas de sobrepresión calibradas para descarga de gas",
                "Integrar la central de incendios con el BMS central y con la central receptora de alarmas de emergencia"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Deploy localized cabinet-level micro-environment suppression for high-density specialized compute racks",
                "Automate non-destructive acoustic and integrity testing of suppression enclosures without room discharge",
                "Implement unified emergency command automation orchestrating power, cooling, and evacuation workflows"
            ],
            "es": [
                "Desplegar microextinción localizada por rack para armarios de muy alta densidad de cómputo",
                "Automatizar ensayos acústicos y de hermeticidad (Door Fan Test) de la sala sin disrupción de la operativa",
                "Implantar orquestación unificada de emergencias que coordine corte de potencia, clima y evacuación"
            ]
        }
    },
    "T1.P5": {
        "domain": "DCIM, Facilities Operations & Maintenance",
        "L1_to_L2": {
            "en": [
                "Consolidate physical asset inventories into an authoritative digital rack-layout database",
                "Establish SLA-backed maintenance contracts covering generators, UPS modules, and HVAC systems",
                "Implement structured shift handover logs and formalized physical change-window checklists"
            ],
            "es": [
                "Consolidar el inventario de equipamiento físico en una base de datos digital de alzado de racks",
                "Formalizar contratos de mantenimiento con SLAs garantizados para grupos electrógenos, SAIs y climatizadoras",
                "Implantar partes de guardia estructurados y listas de verificación para ventanas de mantenimiento físico"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Deploy enterprise DCIM software integrating real-time telemetry from power, thermal, and space sensors",
                "Implement automated capacity management forecasting rack space, power availability, and cooling margins",
                "Formalize Mean Time to Repair (MTTR) tracking and vendor escalation management for all facility components"
            ],
            "es": [
                "Desplegar una plataforma DCIM profesional que integre telemetría de potencia, clima y espacio en tiempo real",
                "Implantar gestión automatizada de capacidad proyectando espacio en rack, potencia disponible y margen de frío",
                "Formalizar métricas de tiempo medio de reparación (MTTR) y cuadros de escalado para incidencias de facilities"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Implement digital twin facility modeling simulating capacity impacts before hardware installations",
                "Automate work order execution and predictive maintenance dispatch based on real-time runtime hours",
                "Achieve autonomous facility optimization integrating telemetry with environmental ESG metrics"
            ],
            "es": [
                "Implantar gemelo digital (Digital Twin) de la sala para simular impactos térmicos y eléctricos antes de instalar servidores",
                "Automatizar órdenes de trabajo y mantenimiento predictivo basadas en horas reales de funcionamiento de componentes",
                "Alcanzar optimización autónoma de facilities integrando telemetría energética con métricas corporativas de sostenibilidad (ESG)"
            ]
        }
    },

    # Tower 2: Hybrid Compute & Platforms
    "T2.P1": {
        "domain": "Compute Foundation & Virtualization",
        "L1_to_L2": {
            "en": [
                "Standardize hypervisor configurations and eliminate standalone unmanaged virtualization hosts",
                "Establish automated hypervisor high availability (HA) with configured memory and CPU admission controls",
                "Implement baseline host hardware monitoring correlating CPU, RAM, and storage controller alerts"
            ],
            "es": [
                "Estandarizar las configuraciones de hipervisores y eliminar servidores de virtualización aislados sin gestión central",
                "Configurar alta disponibilidad (HA) con control formal de admisión de memoria RAM y reservas de capacidad",
                "Implantar monitorización continua del hardware de los servidores correlacionando alertas de CPU, memoria y controladoras"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Deploy dynamic distributed resource scheduling (DRS) balancing workloads across cluster nodes automatically",
                "Implement automated host patch baselines supporting rolling non-disruptive hypervisor updates",
                "Formalize compute capacity planning linking historical workload growth to physical refresh cycles"
            ],
            "es": [
                "Desplegar balanceo dinámico de recursos (DRS) equilibrando las máquinas virtuales entre nodos de forma automática",
                "Implantar líneas base de parches en hipervisores con actualizaciones continuas sin disrupción del servicio",
                "Formalizar la planificación de capacidad de cómputo vinculando el histórico de consumo a los ciclos de renovación"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Automate compute infrastructure deployment using Infrastructure as Code (IaC) with declarative host profiles",
                "Integrate predictive host failure detection triggering automated live migrations prior to hardware crashes",
                "Deploy cross-cloud workload placement dynamically optimizing compute cost, latency, and compliance"
            ],
            "es": [
                "Automatizar el despliegue de hipervisores mediante Infraestructura como Código (IaC) y perfiles declarativos",
                "Integrar detección predictiva de degradación de hardware con migración en caliente desatendida antes de fallos",
                "Implantar orquestación híbrida de cargas optimizando dinámicamente coste, latencia y soberanía del dato"
            ]
        }
    },
    "T2.P2": {
        "domain": "Container Platforms & Kubernetes Operations",
        "L1_to_L2": {
            "en": [
                "Establish baseline container runtime standards and eliminate ad-hoc untracked Docker instances",
                "Deploy a centralized enterprise container registry with automated vulnerability scanning on push",
                "Standardize container base images and define base resource requests/limits for all deployed pods"
            ],
            "es": [
                "Estandarizar entornos de ejecución de contenedores y eliminar instancias Docker aisladas sin soporte corporativo",
                "Desplegar un registro corporativo de imágenes (Container Registry) con escaneo automatizado de vulnerabilidades",
                "Estandarizar imágenes base mínimas y definir límites obligatorios de CPU y memoria (requests/limits) por contenedor"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Deploy managed Kubernetes clusters with automated control-plane lifecycle and version upgrades",
                "Implement declarative GitOps deployment workflows (ArgoCD/Flux) enforcing version-controlled configurations",
                "Enforce role-based access control (RBAC), namespace isolation, and network policies across all clusters"
            ],
            "es": [
                "Desplegar clústeres gestionados de Kubernetes con ciclo de vida y actualizaciones automáticas del plano de control",
                "Implantar flujos declarativos de GitOps asegurando que todas las configuraciones estén versionadas en repositorios de código",
                "Aplicar control de acceso granular (RBAC), aislamiento estricto por namespaces y políticas de red entre microservicios"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Implement dynamic horizontal pod autoscaling (HPA) and cluster autoscaling tied to business queue metrics",
                "Deploy service mesh telemetry (Istio/Linkerd) providing mutual TLS (mTLS) and distributed tracing",
                "Achieve multi-cluster fleet management with policy-as-code admission controllers and automated self-healing"
            ],
            "es": [
                "Implantar autoescalado horizontal elástico de pods y nodos ajustado en tiempo real a la demanda del negocio",
                "Desplegar malla de servicios (Service Mesh) proporcionando cifrado mTLS automático y trazabilidad distribuida",
                "Consolidar gestión federada de múltiples clústeres con controladores de admisión basados en políticas y autorremediación"
            ]
        }
    },
    "T2.P3": {
        "domain": "Hybrid Cloud Enablement & Landing Zones",
        "L1_to_L2": {
            "en": [
                "Establish unified cloud management accounts with foundational identity integration and MFA enforcement",
                "Deploy standard cloud network virtual networks (VPCs/VNets) with centralized ingress/egress filtering",
                "Define basic cloud resource tagging policies associating workloads with owners and cost centers"
            ],
            "es": [
                "Centralizar la administración de suscripciones cloud con integración de identidad federada y MFA obligatorio",
                "Desplegar redes virtuales estandarizadas (VPCs/VNets) con control centralizado de entrada y salida de tráfico",
                "Implantar políticas básicas de etiquetado obligatorio vinculando cada recurso en la nube a un responsable y centro de coste"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Implement an enterprise Cloud Landing Zone utilizing Infrastructure as Code (Terraform/Bicep)",
                "Establish dedicated private connectivity (Direct Connect / ExpressRoute / Cloud Interconnect) to on-premise hubs",
                "Enforce policy-as-code guardrails (Azure Policy / AWS Organizations) blocking unapproved services"
            ],
            "es": [
                "Implementar una Landing Zone corporativa modular desplegada 100% mediante Infraestructura como Código (Terraform)",
                "Establecer conectividad privada dedicada de alta velocidad (ExpressRoute/Interconnect) hacia los centros de datos locales",
                "Implantar barreras de seguridad automatizadas (Policy-as-Code) que impidan el despliegue de configuraciones no conformes"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Achieve multi-region active-active cloud capability with automated cross-region latency routing",
                "Deploy autonomous cloud governance pipelines auto-remediating security and configuration drifts",
                "Implement workload portability pipelines enabling frictionless workload mobility between cloud and on-prem"
            ],
            "es": [
                "Consolidar arquitectura multirregión en alta disponibilidad con enrutamiento dinámico optimizado por latencia",
                "Desplegar gobernanza cloud autónoma con autorremediación de desvíos de seguridad y cumplimiento normativo",
                "Implantar pipelines de portabilidad que permitan mover cargas de trabajo entre cloud y on-premise sin fricción"
            ]
        }
    },
    "T2.P4": {
        "domain": "Automation, Provisioning & Self-Service",
        "L1_to_L2": {
            "en": [
                "Standardize OS gold images and catalog baseline virtual machine specifications",
                "Establish formal resource quotas per business unit to prevent hypervisor memory starvation",
                "Enforce mandatory ownership tagging and expiration schedules for all non-production workloads"
            ],
            "es": [
                "Estandarizar plantillas maestras (Gold Images) y catalogar especificaciones base para máquinas virtuales",
                "Establecer cuotas formales de asignación de CPU y memoria por unidad de negocio para evitar inanición de recursos",
                "Implantar etiquetado obligatorio de propietario y fecha de caducidad en todas las cargas de trabajo no productivas"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Deploy an automated self-service provisioning catalog with role-based access control (RBAC)",
                "Implement automated lifecycle governance deprovisioning idle test environments on scheduled dates",
                "Integrate approval workflows connecting ticketing systems directly to automated provisioning APIs"
            ],
            "es": [
                "Desplegar un catálogo de aprovisionamiento en autoservicio con control de acceso basado en roles (RBAC)",
                "Implantar políticas de ciclo de vida con desmantelamiento automático de entornos de prueba en fechas programadas",
                "Integrar flujos de aprobación conectando la herramienta de ticketing directamente a las APIs de aprovisionamiento"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Automate full-stack Infrastructure as Code pipelines embedding testing, security, and provisioning gates",
                "Deploy self-healing automation scripts auto-remediating infrastructure capacity constraints and service halts",
                "Implement ephemeral developer environments created dynamically on pull-request and destroyed on merge"
            ],
            "es": [
                "Automatizar pipelines de Infraestructura como Código que incluyan validación de seguridad y pruebas antes de desplegar",
                "Desplegar scripts autorreparables que resuelvan cuellos de botella de capacidad y caídas de servicio sin intervención humana",
                "Implantar entornos efímeros para desarrollo creados automáticamente por evento de código y destruidos al finalizar"
            ]
        }
    },
    "T2.P5": {
        "domain": "Platform Operations, Observability & SRE",
        "L1_to_L2": {
            "en": [
                "Consolidate host and hypervisor monitoring into a centralized dashboard with threshold alerts",
                "Formalize baseline operational runbooks for hypervisor host reboots, maintenance, and storage alerts",
                "Implement automated daily backup and snapshot verification reporting for virtualization hosts"
            ],
            "es": [
                "Centralizar la monitorización de servidores e hipervisores en un panel unificado con alertas de umbral",
                "Formalizar manuales operativos para reinicio de nodos, ventanas de mantenimiento y alertas de almacenamiento",
                "Implantar informes diarios automatizados de verificación de copias de seguridad de las configuraciones de host"
            ]
        },
        "L2_to_L3": {
            "en": [
                "Deploy unified metrics, logs, and traces correlation across physical, virtual, and cloud infrastructure",
                "Establish formal Service Level Indicators (SLIs) and Objectives (SLOs) for platform compute availability",
                "Implement automated root-cause analysis workflows linking hypervisor events to guest VM degradations"
            ],
            "es": [
                "Desplegar correlación unificada de métricas, trazas y registros entre infraestructura física, virtual y cloud",
                "Establecer indicadores (SLIs) y objetivos (SLOs) de nivel de servicio para la disponibilidad de la plataforma de cómputo",
                "Implantar análisis de causa raíz automatizado vinculando eventos del hipervisor con la degradación de máquinas virtuales"
            ]
        },
        "L3_to_L4": {
            "en": [
                "Deploy AIOps anomaly detection anticipating memory leaks, storage queue bottlenecks, and host saturation",
                "Implement continuous chaos engineering experiments validating cluster resilience during unannounced node cuts",
                "Achieve closed-loop automated self-remediation resolving 80%+ of repetitive infrastructure incidents"
            ],
            "es": [
                "Desplegar analítica predictiva (AIOps) anticipando fugas de memoria, colas de disco y saturación de hosts",
                "Implantar ingeniería del caos (Chaos Engineering) validando la resiliencia del clúster ante apagados imprevistos de nodos",
                "Alcanzar autorremediación en bucle cerrado resolviendo de forma autónoma más del 80% de las alertas repetitivas"
            ]
        }
    }
}

# Add default fallback matrix for all 10 towers so any pillar ID (T3.P1 .. T10.P5) maps seamlessly
# We generate them dynamically based on domain typologies
typology_archetypes = {
    "T3": "NETWORK",
    "T4": "STORAGE",
    "T5": "RESILIENCE",
    "T6": "SECURITY",
    "T7": "ITSM",
    "T8": "GOVERNANCE",
    "T9": "WORKPLACE",
    "T10": "LEGACY"
}

# Load the previously enriched matrix for the generic typologies
old_matrix_path = REPO_ROOT / "engine_config/policies/cmmi_progression_matrix.json"
old_typologies = {}
if old_matrix_path.exists():
    with open(old_matrix_path, "r", encoding="utf-8") as f:
        old_data = json.load(f)
        old_typologies = old_data.get("typologies", {})

# Populate all 50 pillars
full_pillar_catalog = dict(pillar_definitions)

pillar_names_map = {
    "T3.P1": "Datacenter & Campus Switching",
    "T3.P2": "WAN & SD-WAN Connectivity",
    "T3.P3": "Datacenter Interconnect & DCI",
    "T3.P4": "Hybrid Cloud Connectivity & Edge",
    "T3.P5": "NetDevOps & Network Automation",
    "T4.P1": "Primary Storage Architecture (SAN/NAS)",
    "T4.P2": "Storage Performance, Capacity & Lifecycle",
    "T4.P3": "Data Services: Snapshots & Replication",
    "T4.P4": "Storage Security & Access Governance",
    "T4.P5": "Storage Operations & Platform Integration",
    "T5.P1": "BC/DR Strategy & Governance",
    "T5.P2": "Backup & Operational Recovery",
    "T5.P3": "Disaster Recovery & Failover",
    "T5.P4": "Cyber Recovery & Immutability",
    "T5.P5": "High Availability & Architectural Resilience",
    "T6.P1": "Identity & Access Management (IAM)",
    "T6.P2": "Privileged Access Management (PAM)",
    "T6.P3": "Hardening & Secure Configuration",
    "T6.P4": "Vulnerability & Patch Management",
    "T6.P5": "Network Segmentation & Security Logging",
    "T7.P1": "Service Governance, Catalog & SLAs",
    "T7.P2": "Service Desk & Incident Management",
    "T7.P3": "Change, Release & CMDB",
    "T7.P4": "Problem Management & SRE",
    "T7.P5": "Observability, Event Management & AIOps",
    "T8.P1": "Technology Strategy & Roadmap",
    "T8.P2": "IT Governance, Portfolio & Decision Framework",
    "T8.P3": "Technological Risk & Compliance",
    "T8.P4": "FinOps & Infrastructure Economics",
    "T8.P5": "Value Measurement & Executive KPIs",
    "T9.P1": "Workplace Lifecycle & Device Management",
    "T9.P2": "Digital Identity & Workplace Access",
    "T9.P3": "Collaboration & Knowledge Platforms",
    "T9.P4": "Workplace Support & Self-Service",
    "T9.P5": "Digital Employee Experience (DEX)",
    "T10.P1": "Core Transactional Engines & Mainframe",
    "T10.P2": "Legacy Configuration & Change Control",
    "T10.P3": "Batch Workloads, Capacity & Performance",
    "T10.P4": "Legacy Integration, Middleware & APIs",
    "T10.P5": "Technical Debt & Modernization Strategy",
}

for t_num in range(3, 11):
    t_code = f"T{t_num}"
    typ_key = typology_archetypes.get(t_code, "GOVERNANCE")
    typ_data = old_typologies.get(typ_key, {})

    for p_num in range(1, 6):
        p_id = f"{t_code}.P{p_num}"
        p_domain = pillar_names_map.get(p_id, f"Capability {p_id}")

        full_pillar_catalog[p_id] = {
            "domain": p_domain,
            "L1_to_L2": typ_data.get("L1_to_L2", {
                "en": ["Establish baseline standardized configurations", "Document operational procedures", "Implement proactive monitoring"],
                "es": ["Establecer configuraciones estándar base", "Documentar procedimientos operativos", "Implantar monitorización proactiva"]
            }),
            "L2_to_L3": typ_data.get("L2_to_L3", {
                "en": ["Deploy centralized management tooling", "Formalize operational SLAs", "Automate routine maintenance tasks"],
                "es": ["Desplegar herramientas de gestión centralizada", "Formalizar SLAs operativos", "Automatizar tareas de mantenimiento rutinario"]
            }),
            "L3_to_L4": typ_data.get("L3_to_L4", {
                "en": ["Automate policy enforcement pipelines", "Deploy predictive analytics", "Implement continuous resiliency validation"],
                "es": ["Automatizar pipelines de políticas de cumplimiento", "Desplegar analítica predictiva", "Implantar validación continua de resiliencia"]
            })
        }

final_structure = {
    "$schema": "https://enterprise-architecture.internal/schemas/cmmi-matrix-v2.json",
    "version": "2.0.0",
    "catalog_metadata": {
        "title": "Universal 50-Pillar Granular CMMI v2.0 Progression Matrix",
        "description": "Deterministic, scale-invariant capability progression milestones mapped 1:1 to canonical enterprise assessment capabilities.",
        "standards": ["CMMI Services v2.0", "COBIT 2019", "ISO/IEC 20000-1", "NIST CSF v2.0"]
    },
    "pillars": full_pillar_catalog,
    "tower_fallbacks": old_typologies,
    "universal_default": {
        "L1_to_L2": {
            "en": ["Eliminate unmanaged operational silos", "Establish formal baseline procedures", "Deploy basic health monitoring"],
            "es": ["Eliminar silos operativos no gestionados", "Establecer procedimientos base formales", "Desplegar monitorización básica de salud"]
        },
        "L2_to_L3": {
            "en": ["Deploy centralized management platform", "Formalize service SLAs with business stakeholders", "Automate routine maintenance workflows"],
            "es": ["Desplegar plataforma de gestión centralizada", "Formalizar SLAs de servicio con las áreas de negocio", "Automatizar flujos de mantenimiento rutinario"]
        },
        "L3_to_L4": {
            "en": ["Implement policy-as-code automation", "Deploy predictive telemetry and analytics", "Achieve closed-loop automated self-remediation"],
            "es": ["Implantar automatización de políticas como código", "Desplegar telemetría y analítica predictiva", "Alcanzar autorremediación en bucle cerrado"]
        }
    }
}

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_structure, f, indent=2, ensure_ascii=False)

print(f"Successfully generated granular 50-pillar progression matrix at {output_path} ({len(full_pillar_catalog)} pillars)!")
