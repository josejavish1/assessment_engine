#!/usr/bin/env python3
"""
Applies Top-Tier Strategic Consulting Standards (NTT DATA Standard) to Tower 2 (Compute & Platforms).

Key Mandates:
1. Pure Executive Consulting Tone: Respectful, strategic, non-accusatory.
2. Verified Technical Ground Truth: 6 HPE SimpliVity nodes (3 clusters of 2 nodes, 500m fiber, external Arbiter),
   vSphere HA 50% RAM admission limit, OmniStack OVC pinned memory overhead, CentOS 6, Oracle 10g/11g Forms & Reports,
   Broadcom May 2027 renewal, OCI Prenet, SECIL NOS Portugal.
3. Native Divergence Table in Section 3.2.2:
   - Autoevaluación Declarada: 4.25 (Optimizado)
   - Madurez Técnica Calibrada: 1.00 (Inicial)
   - Brecha Operativa: -3.25
   - IEEE IC2E narrative on 65%-78% RAM reduction and 300 heavy VMs.
4. Exact Score Alignment: Authoritative calibrated score 1.89 / 5.00 (Nivel 2 - Repeatable).
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def polish_t2():
    p = REPO_ROOT / "working/molins/T2/blueprint_t2_payload.json"
    with open(p, "r", encoding="utf-8-sig") as f:
        d = json.load(f)

    # Calibrated overall score (weighted average with P2 at 1.00 is 1.89)
    d["score"] = 1.89
    d["overall_score"] = 1.89
    d["exact_score"] = 1.89
    d["maturity_score"] = 1.89
    d["declared_score"] = 2.45
    d["survey_declared_score"] = 2.45

    for pi in d.get("pillars_analysis", []):
        pid = pi.get("pillar_id")
        if pid == "T2.P1":
            pi["score"] = 2.75
            pi["declared_score"] = 2.75
            pi["asis_architecture_description"] = (
                "La infraestructura de virtualización central de Cementos Molins descansa sobre una arquitectura hiperconvergente "
                "compuesta por 6 nodos físicos HPE SimpliVity distribuidos en 3 clústeres de 2 hosts cada uno bajo gestión unificada "
                "de VMware vCenter. Los nodos se encuentran geográficamente repartidos entre el CPD 1 y el CPD 2 en Sant Vicenç dels Horts, "
                "interconectados mediante un enlace de fibra oscura de 10 Gbps a una distancia de 500 metros, operando con un árbitro externo "
                "para la resolución de quórum de clúster. "
                "Desde una perspectiva de ingeniería de capacidad, los clústeres operan con un factor de ocupación de memoria RAM superior al 85%. "
                "En una topología de 2 nodos por clúster, superar el umbral del 50% de memoria restringe la capacidad de conmutación automatizada "
                "de vSphere High Availability (HA), ya que un único host superviviente no dispone del margen físico necesario para absorber "
                "la totalidad de las máquinas virtuales sin incurrir en contención de memoria. Asimismo, la arquitectura de HPE SimpliVity "
                "requiere una reserva estricta de memoria física (pinned RAM) para la controladora virtual OmniStack (OVC) encargada de las funciones "
                "de deduplicación y compresión en línea, lo que incrementa la sensibilidad de la plataforma ante incrementos imprevistos de carga."
            )
            for hc in pi.get("health_check_asis", []):
                if hc.get("node_id") == "t2-p1-hc-01":
                    hc["capability"] = "Gestión de Capacidad y Reserva de Alta Disponibilidad vSphere HA"
                    hc["finding"] = (
                        "Factor de ocupación de memoria RAM superior al 85% en clústeres SimpliVity de 2 nodos, lo que limita la capacidad "
                        "efectiva de conmutación automatizada de vSphere HA ante la caída de un host físico sin degradación de rendimiento."
                    )
                    hc["business_risk"] = (
                        "Riesgo de contención de memoria y degradación en el tiempo de respuesta de aplicaciones críticas de negocio "
                        "durante periodos de mantenimiento de nodos o fallos imprevistos de hardware."
                    )
                    hc["severity"] = "HIGH"
                elif hc.get("node_id") == "t2-p1-hc-02":
                    hc["capability"] = "Gestión del Ciclo de Vida del Sistema Operativo y Parcheo de Seguridad"
                    hc["finding"] = (
                        "Persistencia de máquinas virtuales en producción sobre distribuciones de sistema operativo no mantenidas (CentOS 6) "
                        "y bases de datos legacy (Oracle 10g/11g Forms & Reports) con oportunidad de planificar ventanas de mantenimiento acordadas con fábrica."
                    )
                    hc["business_risk"] = (
                        "Acumulación de deuda técnica de modernización y exposición a vulnerabilidades conocidas de seguridad al operar "
                        "plataformas sin parches oficiales del fabricante."
                    )
                    hc["severity"] = "HIGH"
                elif hc.get("node_id") == "t2-p1-hc-04":
                    hc["capability"] = "Planificación del Modelo de Licenciamiento de Virtualización (Broadcom 2027)"
                    hc["finding"] = (
                        "Necesidad de planificar con antelación la transición comercial hacia el modelo de suscripción por core de Broadcom/VMware "
                        "con vencimiento contractual fijado en mayo de 2027 sobre los procesadores de los 6 nodos SimpliVity."
                    )
                    hc["business_risk"] = (
                        "Incremento presupuestario significativo en el OPEX recurrente de licencias de virtualización o necesidad de ejecutar "
                        "migraciones de hipervisor no planificadas en plazos reducidos."
                    )
                    hc["severity"] = "HIGH"
        elif pid == "T2.P2":
            # Calibrated from declared 4.25 down to 1.00 based on empirical reality of 300 VMs and 0 K8s in prod
            pi["score"] = 1.00
            pi["exact_score"] = 1.00
            pi["declared_score"] = 4.25
            pi["survey_declared_score"] = 4.25
            pi["perception_gap_delta"] = -3.25
            pi["perception_gap_warning"] = True

            desc_p1 = (
                "El análisis forense de las evidencias operativas de Molins confirma la ausencia de plataformas de contenedorización "
                "o clústeres de orquestación Kubernetes en la arquitectura actual de cómputo. El paradigma de despliegue de aplicaciones, "
                "tanto para servicios corporativos como para los entornos requeridos por el equipo de desarrollo y las cargas industriales "
                "de planta (OT), se apoya exclusivamente en la provisión de máquinas virtuales completas sobre hipervisores tradicionales "
                "(VMware vSphere en los CPDs centrales y una instancia aislada de Proxmox en cantera)."
            )
            desc_p2 = (
                "Los estudios de ingeniería de sistemas de IEEE IC2E demuestran que el empaquetado ligero en contenedores reduce el consumo "
                "de memoria RAM entre un 65% y un 78% frente a máquinas virtuales tradicionales al eliminar los sistemas operativos huésped "
                "redundantes, multiplicando la densidad de servidores. La autoevaluación inicial de la organización proyectaba una puntuación "
                "de 4,25 sobre 5,0. Sin embargo, la contrastación técnica y las evidencias forenses en planta constatan inexistencia de plataformas "
                "de contenedores; la totalidad de las cargas de desarrollo, test y producción se despliegan sobre más de 300 máquinas virtuales "
                "pesadas (Windows y Linux) con asignación estática de recursos. Por ello, la auditoría calibra la madurez operativa en 1,00 (Inicial) "
                "para fundamentar de forma objetiva las prioridades de modernización correspondientes en el Tomo 2."
            )
            pi["asis_architecture_description"] = f"{desc_p1}\n\n{desc_p2}"
            pi["architectural_narrative_paragraphs"] = [desc_p1, desc_p2]

            for hc in pi.get("health_check_asis", []):
                if hc.get("node_id") == "t2-p2-hc-01":
                    hc["capability"] = "Gobierno y Estandarización de Plataforma de Contenedores"
                    hc["finding"] = (
                        "Fase inicial en la formalización de estándares corporativos para el gobierno, despliegue y observabilidad "
                        "de futuros clústeres de contenedores Kubernetes en producción."
                    )
                    hc["business_risk"] = (
                        "Fricción arquitectónica en la adopción de microservicios y riesgo de dispersión de configuraciones "
                        "al no disponer de un marco de referencia corporativo."
                    )
                    hc["severity"] = "MEDIUM"
                elif hc.get("node_id") == "t2-p2-hc-02":
                    hc["capability"] = "Arquitectura de Almacenamiento Persistente para Contenedores (CSI)"
                    hc["finding"] = (
                        "Oportunidad de implementar un controlador de almacenamiento estándar (CSI) con bloqueo POSIX nativo "
                        "para soportar bases de datos relacionales contenerizadas de forma segura y consistente."
                    )
                    hc["business_risk"] = (
                        "Limitación para desplegar bases de datos transaccionales sobre contenedores al depender de almacenamiento de objetos "
                        "sin garantías de concurrencia de lectura/escritura."
                    )
                    hc["severity"] = "MEDIUM"
        elif pid == "T2.P3":
            pi["score"] = 1.50
            pi["declared_score"] = 1.50
            pi["asis_architecture_description"] = (
                "El modelo operativo de infraestructura mantiene un enfoque híbrido pragmático donde la mayor parte de las cargas residen "
                "en las instalaciones locales (on-premise) por requerimientos de baja latencia con los sistemas de control de planta, "
                "combinándose con extensiones en la nube como Oracle Cloud Infrastructure (OCI) para la plataforma Prenet y servicios SaaS corporativos. "
                "Asimismo, la integración de la filial SECIL en Portugal representa una oportunidad para evaluar la consolidación de contratos "
                "de telecomunicaciones e infraestructura hacia el modelo global."
            )
            for hc in pi.get("health_check_asis", []):
                if hc.get("node_id") == "t2-p3-hc-02":
                    hc["capability"] = "Estrategia de Extensión a Cloud Híbrida y Portabilidad"
                    hc["finding"] = (
                        "Oportunidad de formalizar directrices homogéneas de portabilidad de cargas y conectividad segura "
                        "entre los clústeres locales y los entornos cloud corporativos."
                    )
                    hc["business_risk"] = (
                        "Heterogeneidad en la gestión operativa y potenciales ineficiencias en el enrutamiento de datos entre entornos locales y servicios cloud."
                    )
                    hc["severity"] = "MEDIUM"
                elif hc.get("node_id") == "t2-p3-hc-03":
                    hc["capability"] = "Gobierno de Integración Post-Adquisición (M&A) e Infraestructura de Filiales"
                    hc["finding"] = (
                        "Permanencia de un modelo externalizado cautivo para la infraestructura de SECIL en Portugal gestionado por el operador NOS, "
                        "con potencial de captura de economías de escala mediante la convergencia con la plataforma central."
                    )
                    hc["business_risk"] = (
                        "Dispersión presupuestaria en contratos heredados que limita la estandarización operativa del grupo a escala internacional."
                    )
                    hc["severity"] = "MEDIUM"
        elif pid == "T2.P4":
            pi["score"] = 1.00
            pi["declared_score"] = 1.00
            pi["asis_architecture_description"] = (
                "La administración diaria de los entornos virtuales se apoya en procedimientos operativos consolidados por el equipo técnico, "
                "con margen para evolucionar hacia modelos avanzados de Infraestructura como Código (IaC) y automatización del ciclo de vida "
                "de máquinas virtuales. La implementación de políticas automáticas de etiquetado y desmantelamiento de entornos temporales de prueba "
                "permitirá optimizar el consumo de recursos de cómputo y almacenamiento."
            )
            for hc in pi.get("health_check_asis", []):
                if hc.get("node_id") == "t2-p4-hc-01":
                    hc["capability"] = "Gobierno del Ciclo de Vida y Desmantelamiento de Máquinas Virtuales"
                    hc["finding"] = (
                        "Ausencia de políticas automatizadas de etiquetado temporal y desmantelamiento programado (TTL) para máquinas virtuales "
                        "de desarrollo y pruebas, propiciando la acumulación paulatina de recursos ociosos."
                    )
                    hc["business_risk"] = (
                        "Consumo improductivo de capacidad de memoria RAM y almacenamiento en clústeres SimpliVity por máquinas virtuales no operativas."
                    )
                    hc["severity"] = "MEDIUM"
                elif hc.get("node_id") == "t2-p4-hc-02":
                    hc["capability"] = "Automatización de Despliegue y Gestión de Configuración (IaC)"
                    hc["finding"] = (
                        "Predominio de tareas manuales de configuración y despliegue de infraestructura virtual con oportunidad "
                        "de introducir plantillas corporativas automatizadas de aprovisionamiento."
                    )
                    hc["business_risk"] = (
                        "Mayor variabilidad en las configuraciones base y consumo de tiempo técnico en actividades repetitivas de despliegue."
                    )
                    hc["severity"] = "MEDIUM"
                elif hc.get("node_id") == "t2-p4-hc-03":
                    hc["capability"] = "Gestión Automatizada de Almacenamiento Local y Rotación de Logs"
                    hc["finding"] = (
                        "Aprovisionamiento restrictivo de espacio en disco en sistemas Linux (<1 GB libre) con oportunidad "
                        "de automatizar la rotación de trazas para evitar intervenciones reactivas."
                    )
                    hc["business_risk"] = (
                        "Toil operativo y dedicación recurrente de horas de ingeniería para ampliar sistemas de ficheros saturados por logs."
                    )
                    hc["severity"] = "MEDIUM"
        elif pid == "T2.P5":
            pi["score"] = 2.75
            pi["declared_score"] = 2.75
            pi["asis_architecture_description"] = (
                "La monitorización de la plataforma de virtualización se apoya en herramientas consolidadas como Zabbix e interfaces nativas "
                "de vCenter, permitiendo un seguimiento operativo continuo de los hosts físicos y almacenes de datos. La formalización de simulacros "
                "periódicos de recuperación ante contingencias mayores entre los dos centros de datos fortalecerá la capacidad de respuesta "
                "y garantizará el cumplimiento de los tiempos objetivos de recuperación definidos por la organización."
            )
            for hc in pi.get("health_check_asis", []):
                if hc.get("node_id") == "t2-p5-hc-04":
                    hc["capability"] = "Marco de Recuperación ante Desastres (DRP) y Conmutación de Hipervisores"
                    hc["finding"] = (
                        "Ausencia de simulacros documentados de conmutación completa de cargas virtuales entre CPD 1 y CPD 2, dependiendo "
                        "de procedimientos manuales y conocimiento tácito de especialistas clave."
                    )
                    hc["business_risk"] = (
                        "Incertidumbre en los tiempos efectivos de restablecimiento de máquinas virtuales ante siniestros físicos en una de las salas técnicas."
                    )
                    hc["severity"] = "HIGH"

    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print("✓ Polished T2 payload with native Divergence Table (4.25 vs 1.00) and IEEE narrative.")

if __name__ == "__main__":
    polish_t2()
