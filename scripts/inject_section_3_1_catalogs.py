#!/usr/bin/env python3
"""Inject bespoke, tier-1 domain catalogs for Section 3.1 into engine_config/locales.json across all 10 towers."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
loc_path = REPO_ROOT / "engine_config/locales.json"

with open(loc_path, "r", encoding="utf-8") as f:
    locales = json.load(f)

# ----------------------------------------------------------------------
# 1. BESPOKE CH3 INTRODUCTIONS BY TOWER (ES & EN)
# ----------------------------------------------------------------------
ch3_intro_by_tower_es = {
    "T1": "El presente capítulo ejecuta el diagnóstico técnico de las instalaciones físicas, suministro electromecánico y climatización de {tower_name} en {client_name}. El análisis evalúa la solidez de los centros de datos propios bajo tres vectores críticos: redundancia de potencia ininterrumpida (SAIs y grupos electrógenos), confinamiento y estabilidad térmica frente a condiciones ambientales fabriles, y disciplina procedimental en el mantenimiento de facilities.",
    "T2": "Este capítulo documenta el diagnóstico técnico de las plataformas de cómputo, virtualización y servicios de ejecución que conforman el dominio de {tower_name} en {client_name}. La evaluación analiza la capacidad de los clústeres para absorber cargas de forma elástica, la contención de memoria RAM y CPU en hipervisores, y el modelo de aprovisionamiento de máquinas virtuales frente a paradigmas modernos de desacoplamiento.",
    "T3": "El presente capítulo aborda la evaluación arquitectónica de las redes de campus, conectividad troncal y enlaces distribuidos que vertebran {tower_name} en {client_name}. El diagnóstico examina la resiliencia de las comunicaciones entre sedes centrales, fábricas y canteras, la segregación y seguridad del perímetro entre redes corporativas e industriales (IT/OT), y la capacidad de los enlaces troncales para sostener el tráfico transaccional y de réplica.",
    "T4": "Este capítulo analiza la postura arquitectónica de las plataformas de almacenamiento masivo, cabinas corporativas y repositorios de respaldo que integran {tower_name} en {client_name}. La auditoría examina la capacidad de las cabinas para responder a SLAs de latencia de bases de datos críticas, las políticas de retención e inmutabilidad contra ransomware, y el equilibrio entre coste de almacenamiento primario y secundario.",
    "T5": "El presente capítulo ejecuta el diagnóstico de continuidad de negocio y recuperación operativa ante desastres que articula {tower_name} en {client_name}. La evaluación contrasta los procedimientos de recuperación frente a los tiempos de tolerancia de la cadena de suministro industrial, analizando la viabilidad de conmutación entre salas técnicas, el respaldo de bases de datos clave y la autonomía de sedes remotas.",
    "T6": "Esta sección presenta la evaluación de la postura de ciberseguridad, gobierno de identidades y protección de infraestructura que componen {tower_name} en {client_name}. El análisis audita el ciclo de vida de cuentas de usuario, el control de accesos privilegiados de administración, la visibilidad de telemetría de seguridad y la capacidad de contención frente a amenazas avanzadas en entornos híbridos e industriales.",
    "T7": "El presente capítulo evalúa la madurez en la entrega de servicios, soporte operativo y gestión de infraestructura que conforman {tower_name} en {client_name}. La auditoría analiza la formalización del catálogo de servicios, la disciplina en el control de cambios y CMDB, los tiempos de resolución de incidencias en planta y la integración de herramientas de observabilidad de sistemas.",
    "T8": "Este capítulo examina el modelo fiduciario, la visibilidad económica y la gobernanza estratégica de la tecnología que integran {tower_name} en {client_name}. El análisis evalúa la previsibilidad y reparto de costes de infraestructura entre unidades de negocio, la optimización de licenciamiento de software, el control de la contratación externa y la alineación de la inversión técnica con las prioridades de la organización.",
    "T9": "El presente capítulo aborda el diagnóstico del puesto de trabajo digital, herramientas de colaboración y dispositivos de usuario que articulan {tower_name} en {client_name}. La evaluación analiza la homogeneidad del parque de equipos, los automatismos de despliegue y parcheo, la experiencia digital de los empleados de oficina y la adaptación de dispositivos para operarios en entornos fabriles y de logística.",
    "T10": "Este capítulo analiza la infraestructura de sistemas dedicados a operaciones de planta, expedición y control logístico que sustentan {tower_name} en {client_name}. La evaluación audita la robustez del hardware en básculas y puntos de pesaje, la resiliencia de los servidores de fábrica frente a caídas de telecomunicaciones y el grado de modernización del software transaccional de despacho de producto."
}

ch3_intro_by_tower_en = {
    "T1": "This chapter provides the technical diagnosis of physical facilities, electromechanical power distribution, and precision cooling governing {tower_name} across {client_name}. The assessment evaluates datacenter resilience across three critical vectors: uninterrupted power redundancy (UPS and diesel generators), thermal containment against harsh industrial environmental conditions, and facilities maintenance governance.",
    "T2": "This chapter documents the technical diagnosis of compute platforms, hypervisors, and workload execution environments comprising {tower_name} across {client_name}. The evaluation scrutinizes host bin-packing capacity, hypervisor memory and CPU contention, and workload deployment models against modern decoupling architectures.",
    "T3": "This chapter delivers an architectural assessment of campus networks, enterprise backbone connectivity, and wide-area networks spanning {tower_name} across {client_name}. The diagnosis evaluates communications resilience across headquarters, manufacturing plants, and quarries, IT/OT network perimeter segmentation, and backbone latency stability.",
    "T4": "This chapter evaluates the architecture of enterprise storage arrays, primary SAN/NAS platforms, and backup repositories comprising {tower_name} across {client_name}. The audit examines storage tiering latency SLAs for mission-critical databases, snapshot immutability defenses against ransomware, and storage lifecycle management.",
    "T5": "This chapter conducts the technical assessment of business continuity and disaster recovery capabilities governing {tower_name} across {client_name}. The evaluation contrasts technical recovery procedures against physical manufacturing tolerances, validating split-site failover viability, database recoverability, and plant edge autonomy.",
    "T6": "This section evaluates the cybersecurity posture, identity governance, and infrastructure hardening baselines comprising {tower_name} across {client_name}. The analysis audits identity lifecycle management, privileged access management (PAM) controls, threat telemetry visibility, and lateral movement containment across hybrid and industrial networks.",
    "T7": "This chapter evaluates IT service management maturity, infrastructure operational support, and delivery workflows comprising {tower_name} across {client_name}. The audit examines service catalog SLAs, change management and CMDB accuracy, plant incident response velocity, and monitoring telemetry integration.",
    "T8": "This chapter analyzes the fiduciary management, technological cost transparency, and strategic governance comprising {tower_name} across {client_name}. The assessment evaluates infrastructure cost allocation across business units, enterprise software licensing optimization, vendor management discipline, and capital allocation alignment.",
    "T9": "This chapter delivers the assessment of the digital workplace, collaboration suites, and endpoint fleets comprising {tower_name} across {client_name}. The evaluation audits workstation fleet homogeneity, automated provisioning and patch compliance, corporate employee DEX, and plant-floor kiosk adaptations.",
    "T10": "This chapter evaluates the dedicated plant edge systems, weighbridge infrastructure, and shipping dispatch systems governing {tower_name} across {client_name}. The assessment audits weighbridge hardware resilience, plant-floor server autonomy during WAN disconnects, and transaction dispatch engine modernization."
}

# ----------------------------------------------------------------------
# 2. BESPOKE CH3 SCORECARD COMMENTARY BY TOWER (ES & EN)
# ----------------------------------------------------------------------
ch3_scorecard_by_tower_es = {
    "T1": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). Las salas técnicas sostienen con continuidad la operación fabril de {client_name}; no obstante, la exposición a polvo industrial y la falta de telemetría de consumo eléctrico por rack exigen modernizar las instalaciones primarias para blindar la alimentación de los clústeres críticos.",
    "T2": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). El entorno de cómputo sostiene con solvencia las transacciones de negocio de {client_name}; sin embargo, se constatan restricciones de memoria RAM en los nodos centrales y una dependencia de aprovisionamiento manual de máquinas virtuales que limita la elasticidad operativa.",
    "T3": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). La conectividad garantiza la operativa ordinaria entre las sedes corporativas de {client_name}; no obstante, la dependencia de enlaces monoproveedor en fábricas remotas y la limitada microsegmentación IT/OT introducen riesgos de aislamiento y seguridad que deben resolverse.",
    "T4": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). Las cabinas corporativas proporcionan almacenamiento fiable a las bases de datos de {client_name}; si bien la ausencia de bloqueo inmutable (WORM) contra ransomware y la gestión restrictiva de espacio local requieren una modernización de la arquitectura de almacenamiento.",
    "T5": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). Las copias locales permiten recuperar incidencias menores en {client_name}; sin embargo, la reducida distancia física entre salas técnicas (500m) y la falta de simulacros periódicos de failover dejan a la organización expuesta a contingencias graves de suministro o planta.",
    "T6": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). Las defensas perimetrales protegen el acceso corporativo de {client_name}; no obstante, el uso histórico de cuentas de administración compartidas sin bóveda PAM y la fragmentación de registros de auditoría elevan el riesgo operativo y normativo residual.",
    "T7": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). El equipo de soporte atiende con dedicación las incidencias cotidianas de {client_name}; sin embargo, la falta de una CMDB con mapa vivo de dependencias y la resolución reactiva de problemas generan esfuerzo manual recurrente en la operación.",
    "T8": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). La gestión económica mantiene un control estricto de las compras tecnológicas en {client_name}; si bien la falta de modelos FinOps de reparto de costes por planta y la dispersión en la contratación de herramientas externas impiden optimizar el gasto de TI.",
    "T9": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). El parque de portátiles corporativos presenta una alta tasa de renovación en {client_name}; no obstante, la coexistencia de modelos heterogéneos y la gestión manual de configuraciones en puestos de fábrica generan disparidad en la experiencia de usuario.",
    "T10": "La plataforma alcanza una puntuación técnica de {score_val} sobre 5,0 ({maturity_tier_label}). Los sistemas de expedición aseguran el pesaje y salida de producto en {client_name}; si bien la dependencia de código transaccional heredado y la fragilidad de periféricos en báscula ante cortes de red generan riesgo de colas físicas en planta."
}

ch3_scorecard_by_tower_en = {
    "T1": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). Facilities sustain daily factory operations across {client_name}; however, industrial dust exposure and absent per-rack power telemetry necessitate targeted infrastructure upgrades to protect mission-critical equipment.",
    "T2": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). The compute estate reliably processes business transactions across {client_name}; however, hypervisor RAM exhaustion and manual VM provisioning models constrain operational elasticity.",
    "T3": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). Network infrastructure ensures baseline communications across {client_name}; however, single-carrier dependencies at remote industrial sites and flat IT/OT perimeters present availability and security risks.",
    "T4": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). Enterprise storage arrays deliver dependable capacity for core databases across {client_name}; however, the absence of immutable (WORM) ransomware protection and restrictive VM local disk sizing require storage modernization.",
    "T5": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). Local operational backups absorb minor hardware faults across {client_name}; however, physical proximity between primary and secondary datacenters (500m) and unverified failover runbooks expose operations to correlated outages.",
    "T6": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). Perimeter defenses shield corporate systems across {client_name}; however, reliance on unvaulted shared root/admin credentials and fragmented audit telemetry increase operational and regulatory risk.",
    "T7": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). Technical staff diligently remediate daily operational requests across {client_name}; however, an unmapped CMDB and reactive firefighting generate continuous administrative toil.",
    "T8": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). Financial management maintains disciplined procurement oversight across {client_name}; however, absent FinOps cost-allocation models and fragmented software agreements hinder technology spend optimization.",
    "T9": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). The corporate laptop fleet exhibits structured renewal cycles across {client_name}; however, endpoint heterogeneity and manual workstation setup across industrial plants cause user experience friction.",
    "T10": "The domain achieves a technical maturity score of {score_val} out of 5.0 ({maturity_tier_label}). Dispatch systems reliably weigh and release product shipments across {client_name}; however, reliance on legacy monolithic transactional code and weighbridge sensitivity to WAN cuts create truck queuing risks."
}

# ----------------------------------------------------------------------
# 3. BESPOKE TRANSVERSAL STRUCTURAL DEBT PATTERNS BY TOWER (ES & EN)
# ----------------------------------------------------------------------
patterns_es = {
    # Tower 1: Facilities
    "cross_cutting_debt_t1_p1": "1. Aislamiento Operativo BMS y Carencia de Telemetría Dinámica de Potencia: Las alarmas de los sistemas de gestión de edificios (BMS) operan en silos aislados de la monitorización de TI, impidiendo correlacionar en tiempo real las variaciones de consumo eléctrico por rack con el estrés de carga de los servidores.",
    "cross_cutting_debt_t1_p2": "2. Confinamiento Térmico Pasivo y Exposición a Partículas Industriales: La ausencia de cerramientos de pasillo frío/caliente y la exposición directa a condiciones de polvo fabril provocan recirculación de aire caliente y aceleran la degradación de placas base en salas de proceso.",
    "cross_cutting_debt_t1_p3": "3. Procedimientos de Mantenimiento Manuales y Control de Acceso Físico no Integrado: La autorización de intervenciones de contratistas en salas técnicas descansa en libros de registro físico y llaves mecánicas, careciendo de trazabilidad electrónica y autenticación biométrica centralizada.",

    # Tower 2: Compute
    "cross_cutting_debt_t2_p1": "1. Saturación Crítica de Memoria RAM y Dimensionamiento Asimétrico de Clústeres: La concentración de máquinas virtuales sobre clústeres hiperconvergentes ha llevado la memoria al límite de reserva (95%), eliminando el margen de seguridad necesario para absorber la caída de un host sin degradar el servicio.",
    "cross_cutting_debt_t2_p2": "2. Inexistencia de Desacoplamiento Ligero y Proliferación de Máquinas Virtuales Zombi: La totalidad de las cargas se despliega sobre sistemas operativos completos (>300 VMs) sin entornos de contenedores, acumulando instancias huérfanas que consumen recursos perpetuamente por falta de políticas de caducidad.",
    "cross_cutting_debt_t2_p3": "3. Aprovisionamiento Artesanal y Carencia de Infraestructura como Código (IaC): El dimensionamiento y despliegue de nuevos entornos se realiza manualmente mediante tickets y consolas de virtualización, introduciendo dispersión de configuraciones y retrasos en la entrega de proyectos.",

    # Tower 3: Networks
    "cross_cutting_debt_t3_p1": "1. Enlaces WAN Críticos Monoproveedor y Puntos Únicos de Fallo en Sedes Remotas: La conectividad de fábricas y canteras descansa en enlaces únicos de telecomunicaciones sin rutas activas alternativas, provocando aislamiento operativo y parada de despacho ante cualquier corte de fibra.",
    "cross_cutting_debt_t3_p2": "2. Topologías de Red Planas y Segmentación Insuficiente entre Perímetros IT y OT: La coexistencia de tráfico corporativo y señales industriales sobre redes locales poco segregadas permite que incidentes de red o tráfico masivo impacten en controladores de planta.",
    "cross_cutting_debt_t3_p3": "3. Puntos Ciegos de Cobertura Wi-Fi Industrial y Electrónica no Gestionada en Campas: La falta de cobertura inalámbrica robusta en campas logísticas y el despliegue de switches auxiliares no gestionados complican la telemetría de carretillas y terminales de carga.",

    # Tower 4: Storage
    "cross_cutting_debt_t4_p1": "1. Ausencia de Copias Inmutables y Bóvedas Aisladas (Air-Gap) contra Ransomware: La arquitectura de almacenamiento confía en replicación síncrona ordinaria entre cabinas, permitiendo que un ataque con cifrado malicioso se propague instantáneamente al repositorio secundario.",
    "cross_cutting_debt_t4_p2": "2. Dimensionamiento Restrictivo de Discos y Mitigación Manual de Crecimiento de Logs: La política de aprovisionar márgenes mínimos de disco (<1GB libre) para forzar alertas tempranas traslada una carga operativa continua al equipo de sistemas para liberar espacio de forma reactiva.",
    "cross_cutting_debt_t4_p3": "3. Silos de Almacenamiento Dispersos en Sedes Locales y Dependencia de Especialista Único: La coexistencia de cabinas corporativas centrales con soluciones de almacenamiento aisladas en plantas genera dispersión de políticas y dependencia extrema de un recurso clave para su administración.",

    # Tower 5: Resilience
    "cross_cutting_debt_t5_p1": "1. Desalineación entre Métricas RTO/RPO Técnicas y Tolerancia Operativa de Planta: La falta de SLAs y métricas de recuperación pactadas con el negocio provoca que la criticidad se mida de forma empírica por la cola de camiones en fábrica (2-3 horas) en lugar de compromisos técnicos garantizados.",
    "cross_cutting_debt_t5_p2": "2. Proximidad Física entre Centros de Datos (500m) y Dominio de Fallo Eléctrico Común: Al situarse ambos CPDs en el mismo recinto industrial y compartir la acometida general de fábrica, cualquier contingencia ambiental o corte severo de suministro compromete ambas salas simultáneamente.",
    "cross_cutting_debt_t5_p3": "3. Planes de Contingencia (DRP) Teóricos sin Pruebas Periódicas de Conmutación: La ausencia de simulacros periódicos de failover entre centros de datos genera incertidumbre operativa sobre la capacidad real de los sistemas para levantar el servicio tras una caída catastrófica.",

    # Tower 6: Security
    "cross_cutting_debt_t6_p1": "1. Uso Generalizado de Cuentas Compartidas de Máximo Privilegio (Root/Admin) sin Bóveda PAM: La administración ordinaria mediante credenciales genéricas sin registro de sesiones anula la trazabilidad forense de cambios y multiplica el riesgo de compromiso de infraestructura.",
    "cross_cutting_debt_t6_p2": "2. Retraso Acumulado en Ciclos de Parcheo de Hipervisores por Temor a Interrupción del Servicio: Servidores productivos con cientos de días de actividad continua sin reiniciar acumulan vulnerabilidades graves no remediadas para evitar paradas en aplicaciones legacy críticas.",
    "cross_cutting_debt_t6_p3": "3. Falta de Visibilidad y Correlación Centralizada de Eventos de Seguridad entre IT y OT: La monitorización en silos y la ausencia de correlación en un SIEM unificado impiden detectar a tiempo intrusiones o movimientos laterales que crucen el perímetro industrial.",

    # Tower 7: ITSM
    "cross_cutting_debt_t7_p1": "1. Base de Datos de Configuración (CMDB) Fragmentada y Carencia de Mapa Dinámico de Servicios: La documentación técnica dispersa y la falta de dependencias vivas entre servidores y aplicaciones provocan que los cambios en infraestructura generen impactos no previstos en negocio.",
    "cross_cutting_debt_t7_p2": "2. Gestión Reactiva de Incidencias e Inexistencia de Procesos Formales de Gestión de Problemas: La resolución repetitiva de alarmas idénticas (como llenados de disco o reinicios de servicios) consume el esfuerzo del equipo sin abordar las causas raíz que las originan.",
    "cross_cutting_debt_t7_p3": "3. Atención Fragmentada y Canales Informales de Soporte Técnico en Fábricas: La dispersión territorial favorece que las peticiones se gestionen mediante llamadas directas o correos sin ticket, dificultando medir la carga real de soporte y los tiempos de resolución.",

    # Tower 8: FinOps
    "cross_cutting_debt_t8_p1": "1. Opacidad en la Asignación y Reparto de Costes de Infraestructura por Planta y Negocio: La falta de etiquetado y modelos FinOps de showback/chargeback impide a los responsables de fábrica y aplicaciones conocer y optimizar el coste real de los recursos tecnológicos que consumen.",
    "cross_cutting_debt_t8_p2": "2. Presión Fiduciaria por Licenciamiento Monolítico que Condiciona las Decisiones de Arquitectura: Los costes de licencias de bases de datos por procesador físico fuerzan a restringir recursos de hardware, supeditando el dimensionamiento técnico a la penalización contractual de software.",
    "cross_cutting_debt_t8_p3": "3. Dispersión en Compras Tecnológicas Locales y Descoordinación con la Cartera Corporativa: La adquisición puntual de equipamiento o servicios por parte de delegaciones sin homologación previa dificulta consolidar acuerdos marco y duplica costes de mantenimiento.",

    # Tower 9: Workplace
    "cross_cutting_debt_t9_p1": "1. Heterogeneidad en el Parque de Equipos y Procesos Manuales de Despliegue de Puestos: La convivencia de diferentes gamas de portátiles y la preparación individualizada de equipos por técnicos consumen tiempo valioso y generan incidencias recurrentes de configuración.",
    "cross_cutting_debt_t9_p2": "2. Desincronización en Políticas de Parcheo y Actualización de Aplicaciones de Usuario: El retraso en la distribución de parches del sistema operativo y suites ofimáticas deja terminales desactualizados, elevando la superficie de exposición ante amenazas de phishing.",
    "cross_cutting_debt_t9_p3": "3. Brecha Tecnológica y Fricción en Puestos Compartidos y Quioscos de Fábrica: Los puestos de control y terminales en plantas fabriles carecen de la estandarización y agilidad de acceso de los puestos de oficina, ralentizando la operativa de los trabajadores de turno.",

    # Tower 10: Plant Systems
    "cross_cutting_debt_t10_p1": "1. Fragilidad Operativa de Periféricos en Básculas y Puntos de Pesaje que Provoca Colas Físicas: La sensibilidad de impresoras de albaranes, visores y células de carga ante averías locales detiene la expedición de camiones, trasladando el fallo de TI a un atasco físico en planta.",
    "cross_cutting_debt_t10_p2": "2. Dependencia Crítica de Código Transaccional Legacy sin Pruebas Automatizadas de Cambio: Las modificaciones sobre aplicaciones core de expedición y facturación se realizan sobre código propietario histórico, arriesgando errores funcionales que impactan en la salida de producto.",
    "cross_cutting_debt_t10_p3": "3. Vulnerabilidad de Despacho Local ante Cortes de Enlace Central o Procesamiento Batch Nocturno: La emisión de albaranes y registro de pesaje dependen de la sincronización central, ralentizándose la expedición durante horas punta si los procesos nocturnos se prolongan."
}

patterns_en = {
    # Tower 1: Facilities
    "cross_cutting_debt_t1_p1": "1. BMS Operational Isolation and Lack of Dynamic Power Telemetry: Building management systems (BMS) operate in isolation from IT monitoring, preventing real-time correlation between per-rack power draw fluctuations and server compute stress.",
    "cross_cutting_debt_t1_p2": "2. Passive Thermal Management and Exposure to Industrial Airborne Particulates: The absence of cold/hot aisle containment and direct exposure to plant dust cause heat recirculation and accelerate motherboard degradation in server rooms.",
    "cross_cutting_debt_t1_p3": "3. Manual Maintenance Procedures and Fragmented Physical Access Controls: Contractor access authorization to technical rooms relies on paper logbooks and mechanical keys, lacking electronic audit trails and centralized biometric authentication.",

    # Tower 2: Compute
    "cross_cutting_debt_t2_p1": "1. Critical RAM Exhaustion and Asymmetric Cluster Sizing: Virtual machine density on hyperconverged clusters has pushed memory to reserve thresholds (95%), eliminating the safety buffer required to absorb host failure without service degradation.",
    "cross_cutting_debt_t2_p2": "2. Absence of Lightweight Packaging and Zombie Virtual Machine Sprawl: 100% of workloads run on full guest operating systems (>300 VMs) with zero containerization, accumulating orphan instances that perpetually consume resources without lifecycle TTLs.",
    "cross_cutting_debt_t2_p3": "3. Manual Provisioning and Absence of Infrastructure-as-Code (IaC) Pipelines: Sizing and deploying new environments is performed manually via tickets and hypervisor consoles, introducing configuration drift and project delivery delays.",

    # Tower 3: Networks
    "cross_cutting_debt_t3_p1": "1. Single-Carrier WAN Links and Points of Failure Across Remote Sites: Connectivity to plants and quarries relies on single carrier circuits with no active secondary paths, causing complete operational isolation during fiber cuts.",
    "cross_cutting_debt_t3_p2": "2. Flat Network Topologies and Insufficient IT/OT Perimeter Micro-Segmentation: Enterprise and industrial control traffic share unsegmented local networks, allowing corporate traffic spikes or malware to traverse into plant PLCs.",
    "cross_cutting_debt_t3_p3": "3. Industrial Wi-Fi Coverage Blind Spots and Unmanaged Switching in Logistics Yards: Lack of robust wireless coverage across loading yards and unmanaged auxiliary edge switches disrupt forklift telemetry and mobile warehouse barcode scanners.",

    # Tower 4: Storage
    "cross_cutting_debt_t4_p1": "1. Absence of Immutable and Air-Gapped Backup Vaults Against Ransomware: Storage relies on standard synchronous array replication, allowing ransomware encryption to replicate immediately across datacenters and compromise secondary mirrors.",
    "cross_cutting_debt_t4_p2": "2. Restrictive VM Disk Sizing and Reactive Manual Log Management: The policy of provisioning minimal local storage (<1GB free) to force early log alerts creates continuous manual toil for system administrators to reactively free up space.",
    "cross_cutting_debt_t4_p3": "3. Fragmented Local Storage Silos and Extreme Dependency on Solo Specialists: Coexistence of primary arrays with ad-hoc storage in regional facilities creates policy divergence and single-person dependency for administration.",

    # Tower 5: Resilience
    "cross_cutting_debt_t5_p1": "1. Misalignment Between Technical RTO/RPO Metrics and Plant Operating Tolerances: The absence of business-negotiated SLAs means recovery expectations are informally governed by physical truck queue tolerance (2-3 hours) rather than tested systems.",
    "cross_cutting_debt_t5_p2": "2. Close Physical Proximity Between Datacenters (500m) and Correlated Power Outage Domains: Locating both primary and secondary datacenters on the same factory grounds exposes both facilities to identical plant-wide power cuts and environmental incidents.",
    "cross_cutting_debt_t5_p3": "3. Theoretical Disaster Recovery Plans (DRP) Lacking Regular Failover Drills: The absence of scheduled unannounced failover simulations leaves significant operational uncertainty regarding the real ability to recover systems after site disasters.",

    # Tower 6: Security
    "cross_cutting_debt_t6_p1": "1. Widespread Use of Shared Privileged Root/Admin Accounts Without PAM Vaulting: Routine administration using shared root/admin credentials without session recording destroys forensic auditability and multiplies infrastructure breach impact.",
    "cross_cutting_debt_t6_p2": "2. Accumulated Hypervisor Patching Debt Due to Service Interruption Fear: Production servers running for hundreds of days without reboots accumulate unpatched critical CVEs to avoid taking down legacy business dependencies.",
    "cross_cutting_debt_t6_p3": "3. Fragmented Security Telemetry and Lack of Centralized IT/OT Threat Correlation: Siloed monitoring and absent SIEM/EDR log aggregation delay detection of lateral threat traversal across corporate and industrial plant networks.",

    # Tower 7: ITSM
    "cross_cutting_debt_t7_p1": "1. Incomplete CMDB and Absence of Real-Time Dynamic Dependency Mapping: Disconnected documentation and missing CI relationship mapping lead to unintended production outages during scheduled infrastructure changes.",
    "cross_cutting_debt_t7_p2": "2. Reactive Incident Handling and Lack of Formal Problem Management: Repetitive troubleshooting of recurring alarms (such as disk space exhaustion and service restarts) absorbs technical staff without addressing root causes.",
    "cross_cutting_debt_t7_p3": "3. Fragmented Support Intake and Informal Communication Channels Across Plants: Regional dispersion encourages users to request support via informal phone calls or direct emails, obscuring actual IT support demand and resolution SLAs.",

    # Tower 8: FinOps
    "cross_cutting_debt_t8_p1": "1. Opacity in Unit Infrastructure Cost Allocation Across Plants and Business Units: Lack of tagging and FinOps showback models prevents application owners and factory managers from understanding the true cost of consumed IT capacity.",
    "cross_cutting_debt_t8_p2": "2. Fiduciary Lock-in from Core-Based Database Licensing Dictating Technical Architecture: High per-core database licensing fees constrain hardware sizing, subordinating technical architecture to contractual software penalties.",
    "cross_cutting_debt_t8_p3": "3. Uncoordinated Local IT Purchasing and Vendor Contract Fragmentation: Independent software and hardware procurement by business units prevents enterprise agreement consolidation and inflates maintenance costs.",

    # Tower 9: Workplace
    "cross_cutting_debt_t9_p1": "1. Laptop Fleet Heterogeneity and Manual Provisioning Processes: The coexistence of unstandardized laptop models and manual workstation staging consumes technician hours and creates recurrent driver/configuration incidents.",
    "cross_cutting_debt_t9_p2": "2. Patching Delays on User Workstations and Endpoint Applications: Delayed operating system and third-party software updates across user workstations leave endpoints vulnerable to phishing and malware exploits.",
    "cross_cutting_debt_t9_p3": "3. Technological Disparity and Friction Across Plant Kiosks and Mobile Shift Workers: Factory-floor terminals and weighbridge desks lack the streamlined login experience of corporate office PCs, slowing down plant shift workers.",

    # Tower 10: Plant Systems
    "cross_cutting_debt_t10_p1": "1. Operational Fragility of Weighbridge Peripherals Triggering Physical Truck Queues: Sensitivity of dispatch ticket printers, weight indicators, and barrier gates to local hardware faults halts truck shipping lines, creating physical plant gridlock.",
    "cross_cutting_debt_t10_p2": "2. Critical Dependency on Legacy Monolithic Transactional Code Lacking Automated Tests: Operational changes to core dispatch and billing engines are executed on historical proprietary code, risking functional defects that stop shipping.",
    "cross_cutting_debt_t10_p3": "3. Dispatch Vulnerability to Central WAN Disconnects and Nighttime Batch Overruns: Local weighbridge ticketing depends on central database synchronization, causing morning dispatch delays if nighttime batch jobs extend into daytime operating windows."
}

# Update Spanish
if "es" in locales:
    locales["es"]["ch3_intro_by_tower"] = ch3_intro_by_tower_es
    locales["es"]["ch3_scorecard_by_tower"] = ch3_scorecard_by_tower_es
    locales["es"].update(patterns_es)

# Update English
if "en" in locales:
    locales["en"]["ch3_intro_by_tower"] = ch3_intro_by_tower_en
    locales["en"]["ch3_scorecard_by_tower"] = ch3_scorecard_by_tower_en
    locales["en"].update(patterns_en)

with open(loc_path, "w", encoding="utf-8") as f:
    json.dump(locales, f, indent=2, ensure_ascii=False)

print(f"Successfully injected bespoke Section 3.1 catalogs (Intros, Scorecards, 30 Transversal Patterns) into {loc_path}!")
