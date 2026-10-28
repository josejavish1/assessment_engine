import logging
logger = logging.getLogger(__name__)
import csv
import json
import sys
from pathlib import Path

from assessment_engine.infrastructure.localization import format_number


def clean_client_name(client_name: str) -> str:
    """Cleans a raw client name (which might be a slug or directory name) for reporting.

    Removes version tags (e.g. _v3, _v2, -v4), replaces underscores/hyphens with spaces,
    strips trailing whitespace, and ensures Proper Noun Title Case capitalization.
    """
    if not client_name:
        return "Cliente"
    import re
    # Remove version endings like _v3, _V2, -v4, etc.
    cleaned = re.sub(r'[_-][vV]\d+\b', '', client_name)
    # Replace underscores/hyphens with spaces
    cleaned = cleaned.replace('_', ' ').replace('-', ' ')
    cleaned = cleaned.strip()
    
    # Elite Capitalization: Ensure it is a Proper Noun (Title Case)
    # If the cleaned string is all lowercase, convert it to Title Case (e.g., 'cliente' -> 'Cliente')
    # If it has uppercase, preserve the client's custom branding (e.g., 'CLIENTE' stays 'CLIENTE')
    if cleaned.islower():
        return cleaned.title()
    return cleaned


def derive_pillar_justification(p: dict, idx: int, doc_lang: str) -> str:
    from assessment_engine.domain.maturity_band import (
        ANNEX_MATURITY_BANDS,
        resolve_maturity_band,
    )
    from assessment_engine.infrastructure.localization import format_number

    p_score = float(p.get("score", 3.0))
    band = resolve_maturity_band(
        p_score, ANNEX_MATURITY_BANDS, locale=doc_lang
    )["label"]
    formatted_score = format_number(p_score, locale=doc_lang, decimals=2)
    p_name = p.get("pilar_name", "Pilar")

    findings = p.get("health_check_asis", [])
    if not findings:
        if doc_lang == "es":
            return (
                f"• **Situación de Capacidades (KPIs):**\n"
                f"• La capacidad presenta un nivel de madurez '{band}' ({formatted_score} / 5,00). "
                f"No se han registrado hallazgos ni brechas críticas específicas en el perímetro de evaluación.\n"
                f"• **Brechas y Consecuencias Operativas:**\n"
                f"• La plataforma opera de forma estable, sin identificarse limitaciones de continuidad de negocio o cuellos de botella de infraestructura materiales.\n"
                f"• **Justificación de la Nota ({formatted_score}):**\n"
                f"• La puntuación refleja un estado consistente de operaciones, recomendado para sostener el catálogo de servicios actual."
            )
        else:
            return (
                f"• **Capabilities Posture (KPIs):**\n"
                f"• The capability presents a maturity level of '{band}' ({formatted_score} / 5.00). "
                f"No specific critical findings or gaps have been registered in the evaluation perimeter.\n"
                f"• **Gaps and Operational Consequences:**\n"
                f"• The platform operates stably, with no material business continuity limitations or infrastructure bottlenecks identified.\n"
                f"• **Justification of the Score ({formatted_score}):**\n"
                f"• The score reflects a consistent state of operations, recommended to support the current service catalog."
            )

    # Sort findings by vulnerability_level (descending) or fair_ale_score (descending)
    def get_ale(f):
        try:
            return float(f.get("fair_ale_score", 0.0) or 0.0)
        except Exception:
            return 0.0
    def get_vuln(f):
        try:
            return int(f.get("vulnerability_level", 3) or 3)
        except Exception:
            return 3
            
    sorted_findings = sorted(findings, key=lambda x: (get_vuln(x), get_ale(x)), reverse=True)
    
    # Gaps (worst findings: vuln >= 4 or first 2)
    gaps_findings = [f for f in sorted_findings if get_vuln(f) >= 4]
    if not gaps_findings:
        gaps_findings = sorted_findings[:1]
        
    # Stable (vulnerability < 4 or remaining findings)
    stable_findings = [f for f in sorted_findings if f not in gaps_findings]
    
    # Extract capability names (translate/sanitize them to Spanish if needed!)
    def clean_cap_name(cap_name):
        if not cap_name:
            return ""
        if doc_lang == "es":
            c_lower = cap_name.lower()
            if "lifecycle" in c_lower or "patch" in c_lower:
                return "Gestión de Ciclo de Vida Automatizada (Parcheado y Actualizaciones)"
            if "governance" in c_lower or "configur" in c_lower:
                return "Gobernanza y Estandarización de la Configuración"
            if "availability" in c_lower or "high availability" in c_lower:
                return "Validación Continua de la Alta Disponibilidad"
            if "observability" in c_lower or "monitoring" in c_lower:
                return "Observabilidad Centralizada y Telemetría"
            if "provision" in c_lower or "self-service" in c_lower:
                return "Autoservicio de Provisión y Automatización de Despliegue"
            if "identity" in c_lower or "access" in c_lower:
                return "Seguridad de Identidad y Gobierno de Accesos"
            if "backup" in c_lower or "recovery" in c_lower:
                return "Respaldo Automatizado y Recuperación ante Desastres"
            if "hybrid cloud" in c_lower or "cloud" in c_lower:
                return "Gobernanza de Nube Híbrida y Consistencia Operativa"
        return cap_name

    gaps_caps = [clean_cap_name(f.get("target_state", f.get("capability", ""))) for f in gaps_findings if f.get("target_state", f.get("capability"))]
    stable_caps = [clean_cap_name(f.get("target_state", f.get("capability", ""))) for f in stable_findings if f.get("target_state", f.get("capability"))]
    
    gaps_caps = [c for c in gaps_caps if c]
    stable_caps = [c for c in stable_caps if c]

    # Deterministic variation index based on index
    v_idx = idx % 3
    
    # 2. Brechas y Consecuencias Operativas
    main_gaps = []
    main_risks = []
    for f in gaps_findings[:2]:
        fd = (f.get("risk_observed", f.get("finding", "")) or "").strip()
        br = (f.get("impact", f.get("business_risk", "")) or "").strip()
        if fd:
            if doc_lang == "es" and ("the" in fd.lower() or "is" in fd.lower() or "reflects" in fd.lower()):
                if "lifecycle" in fd.lower() or "patch" in fd.lower():
                    fd = "los procesos para la gestión del ciclo de vida del cómputo (parcheado, actualizaciones) están estructurados pero su ejecución es predominantemente manual"
                elif "configur" in fd.lower() or "standar" in fd.lower():
                    fd = "se observa una base de estandarización funcional en la configuración de la virtualización, pero el mantenimiento de la consistencia se apoya en procesos con un alto componente manual"
                elif "availability" in fd.lower() or "high availability" in fd.lower():
                    fd = "la consistencia y verificación de esquemas de alta disponibilidad se apoyan en pruebas operativas no automatizadas ni continuas"
                else:
                    fd = "carencias de automatización de procedimientos y soporte manual predominante en el ciclo de vida"
            else:
                # Lowercase the first letter of fd if it was parsed as a separate sentence
                if fd and fd[0].isupper() and not fd.startswith("NIS2") and not fd.startswith("ENS"):
                    fd = fd[0].lower() + fd[1:]
            fd_sent = fd.rstrip(".")
            main_gaps.append(fd_sent)
            
        if br:
            if doc_lang == "es" and ("increase" in br.lower() or "higher" in br.lower() or "risk" in br.lower() or "result" in br.lower()):
                if "security" in br.lower() or "vulnerab" in br.lower():
                    br = "un incremento de la superficie de ataque y del tiempo de exposición a vulnerabilidades críticas"
                elif "cost" in br.lower() or "tco" in br.lower():
                    br = "un incremento del coste total de propiedad (TCO) por la complejidad de gestionar múltiples tecnologías"
                else:
                    br = "un aumento de los tiempos de resolución de incidentes (MTTR) y sobrecarga en el equipo de ingeniería"
            else:
                if br and br[0].isupper() and not br.startswith("NIS2") and not br.startswith("ENS"):
                    br = br[0].lower() + br[1:]
            br_sent = br.rstrip(".")
            main_risks.append(br_sent)
            
    if not main_gaps:
        main_gaps = ["se registran carencias en la automatización y predictibilidad de las operaciones de infraestructura" if doc_lang == "es" else "gaps are registered in the automation and predictability of infrastructure operations"]
    if not main_risks:
        main_risks = ["un elevado riesgo de incidentes operativos y una limitada agilidad frente al crecimiento de la demanda" if doc_lang == "es" else "increased risk of operational incidents and limited agility in the face of demand growth"]
        
    gaps_str_joined = " y ".join(main_gaps) if doc_lang == "es" else " and ".join(main_gaps)
    risks_str_joined = " y ".join(main_risks) if doc_lang == "es" else " and ".join(main_risks)
    
    worst_cap = gaps_caps[0] if gaps_caps else ("las capacidades críticas" if doc_lang == "es" else "critical capabilities")

    p_score = float(p.get("score", 3.0))

    if p_score >= 4.20:
        # HIGH MATURITY CASE: No gaps, focus on Excellence and Optimization
        if doc_lang == "es":
            label_1 = "Liderazgo Tecnológico y Estabilidad"
            label_2 = "Oportunidades de Optimización Continua"
            label_3 = "Calibración Analítica de Excelencia"
            
            p1_text = f"La plataforma demuestra un liderazgo tecnológico sobresaliente en este dominio, sustentado por procesos optimizados y mejores prácticas en capacidades clave como {', '.join(stable_caps[:3])}." if stable_caps else "Las capacidades evaluadas reflejan una madurez operativa excelente y consistente en todo el perímetro."
            p2_text = "No se han detectado brechas de madurez ni vulnerabilidades críticas. Las oportunidades se centran exclusivamente en el mantenimiento proactivo y la innovación tecnológica continua."
            p3_text = f"La calificación excelente refleja un comportamiento maduro y homogéneo, posicionando a este pilar como un habilitador estratégico de resiliencia y escalabilidad."
        else:
            label_1 = "Technological Leadership and Stability"
            label_2 = "Continuous Optimization Opportunities"
            label_3 = "Analytical Excellence Calibration"
            
            p1_text = f"The platform demonstrates outstanding technological leadership in this domain, supported by optimized processes and best practices in key capabilities like {', '.join(stable_caps[:3])}." if stable_caps else "The evaluated capabilities reflect excellent and consistent operational maturity across the perimeter."
            p2_text = "No maturity gaps or critical vulnerabilities have been detected. Opportunities focus exclusively on proactive maintenance and continuous technological innovation."
            p3_text = f"The excellent score reflects a mature and homogeneous posture, positioning this pillar as a strategic enabler of resilience and scalability."

    elif p_score >= 2.60:
        # BALANCED CASE (MEDIUM-HIGH): Both strengths and gaps exist
        if doc_lang == "es":
            label_1 = "Fortalezas Operativas y Estabilidad"
            label_2 = "Brechas de Control y Vulnerabilidades"
            label_3 = "Calibración Analítica del Diagnóstico"
            
            if v_idx == 0:
                p1_text = f"La plataforma demuestra solvencia operativa y un desempeño sólido en capacidades clave como {', '.join(stable_caps[:3])}, lo que proporciona una base de control funcional y estabilidad en los dominios más maduros de la torre." if stable_caps else "Se identifican oportunidades de consolidación generalizadas en las capacidades de este pilar."
                p2_text = f"En contraposición, se identifican brechas de madurez relevantes en {', '.join(gaps_caps[:3])}. El análisis técnico revela que {gaps_str_joined}. Esta limitación expone de forma directa al negocio a consecuencias operativas caracterizadas por {risks_str_joined}."
                p3_text = f"La calificación final del pilar se encuentra sustentada por las capacidades de soporte estables, pero se ve penalizada de forma directa por las deficiencias críticas detectadas en '{worst_cap}', que actúa como el factor de riesgo principal que limita la resiliencia estructural y la robustez actual de la plataforma."
            elif v_idx == 1:
                p1_text = f"El diagnóstico técnico identifica fortalezas funcionales y prácticas estables en {', '.join(stable_caps[:3])}, sirviendo como pilar operativo para el sostenimiento de los servicios actuales." if stable_caps else "Se requiere un esfuerzo de estandarización estructural en todo el perímetro de capacidades de este pilar."
                p2_text = f"Sin embargo, existen áreas de mejora prioritarias en {', '.join(gaps_caps[:3])}. El análisis de control revela que {gaps_str_joined}. En consecuencia, esto genera una exposición operativa directa caracterizada por {risks_str_joined}."
                p3_text = f"La puntuación refleja un equilibrio entre las fortalezas de la plataforma y el lastre que suponen las brechas en '{worst_cap}', las cuales restan resiliencia y limitan la escalabilidad operativa global."
            else:
                p1_text = f"Se constata un nivel de control adecuado y procesos consistentes en capacidades como {', '.join(stable_caps[:3])}, aportando resiliencia a la operación diaria de la infraestructura." if stable_caps else "Las capacidades actuales muestran un comportamiento elemental con necesidad de redefinición de procesos."
                p2_text = f"En contraposición, el entorno presenta desafíos operativos materiales en {', '.join(gaps_caps[:3])}. Se constata que {gaps_str_joined}, lo cual expone a la organización a consecuencias de negocio como {risks_str_joined}."
                p3_text = f"El score consolidado del pilar se ve severamente condicionado por la inmadurez de la capacidad de '{worst_cap}', la cual actúa como el principal obstáculo para consolidar una postura de seguridad y fiabilidad adecuada en la operación actual."
        else:
            label_1 = "Operational Strengths and Stability"
            label_2 = "Control Gaps and Vulnerabilities"
            label_3 = "Analytical Diagnostic Calibration"
            
            if v_idx == 0:
                p1_text = f"The platform demonstrates operational solvency and solid performance in key capabilities like {', '.join(stable_caps[:3])}, providing a functional control baseline and stability in the mature domains of the tower." if stable_caps else "Generalized consolidation needs are identified in the capabilities of this pillar."
                p2_text = f"In contrast, relevant maturity gaps are identified in {', '.join(gaps_caps[:3])}. Specifically, {gaps_str_joined}. This structural limitation directly exposes the business to operational consequences characterized by {risks_str_joined}."
                p3_text = f"The final pillar score is supported by the baseline capabilities, but is directly penalized by the critical deficiencies detected in '{worst_cap}', which acts as the limiting factor for the global evolution of this domain."
            elif v_idx == 1:
                p1_text = f"The technical diagnosis identifies functional strengths and stable practices in {', '.join(stable_caps[:3])}, serving as an operational foundation to sustain current services." if stable_caps else "Structural standardization efforts are required across the entire scope of this pillar."
                p2_text = f"Nonetheless, there are key weaknesses and priority areas for improvement in {', '.join(gaps_caps[:3])}. The analysis reveals that {gaps_str_joined}. Consequently, this generates direct operational exposure characterized by {risks_str_joined}."
                p3_text = f"The score reflects a balance between the strengths of the platform and the burden of the gaps in '{worst_cap}', which reduce resilience and limit global operational scalability."
            else:
                p1_text = f"An adequate control level and consistent processes are noted in capabilities such as {', '.join(stable_caps[:3])}, adding resilience to daily infrastructure operations." if stable_caps else "Current capabilities show basic behavior with a clear need for process redefinition."
                p2_text = f"In contrast, the environment presents material operational challenges in {', '.join(gaps_caps[:3])}. A material gap is noted in {gaps_str_joined}, which exposes the organization to business consequences such as {risks_str_joined}."
                p3_text = f"The consolidated pillar score is severely conditioned by the immaturity of the '{worst_cap}' capability, which acts as the main obstacle to reach the target control state."

    else:
        # CRITICAL/LOW MATURITY CASE (Score < 2.60): No real strengths, focus on State of Deficiency and Remediation Path
        if doc_lang == "es":
            label_1 = "Diagnóstico de Deficiencias y Estado Crítico"
            label_2 = "Exposición al Riesgo e Impacto Operativo"
            label_3 = "Calibración Analítica de Penalización"
            
            p1_text = f"El diagnóstico revela un estado de inmadurez estructural crítico y generalizado, caracterizado por la ausencia de estandarización y control formal en capacidades esenciales como {', '.join(gaps_caps[:3])}." if gaps_caps else "El dominio muestra una postura operativa elemental o no documentada, requiriendo una intervención prioritaria."
            p2_text = f"El análisis técnico revela que {gaps_str_joined}. La carencia de automatizaciones avanzadas y la alta dependencia de procesos manuales exponen de forma inmediata a la organización a {risks_str_joined}."
            p3_text = f"La puntuación crítica asignada se encuentra severamente lastrada por la debilidad estructural detectada en '{worst_cap}', que representa el cuello de botella principal de la torre y anula la efectividad de cualquier control adyacente."
        else:
            label_1 = "Deficiency Diagnosis and Critical State"
            label_2 = "Risk Exposure and Operational Impact"
            label_3 = "Analytical Penalty Calibration"
            
            p1_text = f"The diagnosis reveals a critical and widespread structural immaturity, characterized by the absence of standardization and formal control in essential capabilities such as {', '.join(gaps_caps[:3])}." if gaps_caps else "The domain shows a basic or undocumented operational posture, requiring priority intervention."
            p2_text = f"Technical analysis reveals that {gaps_str_joined}. The lack of advanced automation and high dependence on manual processes directly exposes the organization to {risks_str_joined}."
            p3_text = f"The assigned critical score is severely burdened by the systemic weakness detected in '{worst_cap}', which represents the main bottleneck of the tower and negates the effectiveness of any adjacent control."

    if doc_lang == "es":
        return (
            f"**{label_1}:** {p1_text}\n"
            f"**{label_2}:** {p2_text}\n"
            f"**{label_3}:** {p3_text}"
        )
    else:
        return (
            f"**{label_1}:** {p1_text}\n"
            f"**{label_2}:** {p2_text}\n"
            f"**{label_3}:** {p3_text}"
        )


def sanitize_semantic_prose(text: str, doc_lang: str = "es") -> str:
    """Rephrases technical prose to remove speculative language and align it with formal compliance terminology. This function applies two primary sets of transformations: 1. It replaces speculative or conditional phrases (e.g., "posiblemente", "potencialmente") with more declarative, assertive equivalents based on a predefined mapping. 2. It inspects the text for compliance-related keywords (e.g., "automatización", "runbooks", "compliance"). If found, it may replace the entire input string with a standardized statement that frames the subject within target-state regulatory frameworks such as ENS and NIS2. This transformation is language-dependent. If keywords are present but no specific replacement rule matches, a suffix is appended to indicate planned automation. The function is designed to standardize descriptions in formal reports, ensuring consistent, assertive, and compliance-oriented language. Args: text: The source prose to sanitize. doc_lang: The language identifier (e.g., "es", "en") used to select the appropriate set of transformation rules. Defaults to "es". Returns: The sanitized string, which may be a significant modification or a complete replacement of the original input."""
    if not text:
        return text

    t = str(text).strip()
    lang = str(doc_lang).lower()

    # Rule -1: Centralized dynamic translation/cleaning of non-idiomatic terms (Spain compliance)
    if lang == "es":
        t = t.replace("Riesgo de deriva de configuración (Configuration Drift)", "Desalineación y Desviación de Configuraciones")
        t = t.replace("Riesgo de deriva de configuración", "Desalineación y Desviación de Configuraciones")
        t = t.replace("deriva de configuración", "desalineación y desviación de configuraciones")
        t = t.replace("deriva de la configuración", "desalineación y desviación de configuraciones")
        t = t.replace("monitoreo", "monitorización")
        t = t.replace("Monitoreo", "Monitorización")

        # Centralized spelling sanitization for LLM output typos on 'múltiples'
        t = t.replace("mùltiples", "múltiples")
        t = t.replace("Mùltiples", "Múltiples")
        t = t.replace("móltiples", "múltiples")
        t = t.replace("Móltiples", "Múltiples")
        t = t.replace("multiples", "múltiples")
        t = t.replace("Multiples", "Múltiples")

    # Rule 0: Translate core platform descriptions from English to high-quality Spanish if lang is "es"
    if lang == "es":
        # Check if the text contains key English platform overview terms
        if "platform operations" in t.lower() or "siloed architecture" in t.lower() or "standardized yet siloed" in t.lower():
            t = t.replace(
                "The current platform operations model at the client's organization reflects a standardized yet siloed architecture, a common outcome of the organic evolution of a large-scale, critical infrastructure.",
                "El modelo operativo actual de la plataforma de la organización del cliente refleja una arquitectura estandarizada pero altamente fragmentada en silos, un resultado habitual del crecimiento orgánico de infraestructuras críticas a gran escala."
            )
            t = t.replace(
                "The observability capability is founded on powerful, domain-specific tools: Dynatrace is leveraged for Application Performance Monitoring (APM), while Splunk serves as the primary solution for log aggregation and analysis. Despite the strengths of these individual platforms, they operate in discrete technological verticals without a unified correlation layer.",
                "La capacidad de observabilidad se fundamenta en herramientas robustas y especializadas por dominio: se explota Dynatrace para la monitorización de rendimiento de aplicaciones (APM), mientras que Splunk actúa como la solución principal para la agregación y análisis de registros de eventos (logs). A pesar de la solvencia individual de estas plataformas, las mismas operan en verticales tecnológicas discretas sin una capa unificada de correlación cruzada."
            )
            t = t.replace(
                "This fragmentation inhibits end-to-end service visibility, rendering root cause analysis dependent on specialized expertise and manual cross-team collaboration, which introduces delays.",
                "Esta fragmentación restringe la visibilidad extremo a extremo de los servicios, haciendo que el análisis de causa raíz dependa de la experiencia especializada de silos técnicos y de la colaboración manual entre distintos equipos, lo cual introduce demoras operativas inevitables."
            )
            t = t.replace(
                "The monitoring topology mirrors the client's 80/20 hybrid infrastructure. A distinct set of agents and collectors service the on-premise workloads hosted on VMware and Oracle VM, while a separate configuration addresses the AWS cloud environment.",
                "La topología de monitorización refleja con precisión la infraestructura híbrida con un reparto estimado del 80/20 del cliente. Un conjunto específico de agentes y colectores da servicio a las cargas de trabajo locales (on-premise) alojadas en entornos virtuales de VMware y Oracle VM, mientras que una configuración completamente segregada atiende al entorno de nube pública en AWS."
            )
            t = t.replace(
                "The absence of an agnostic telemetry standard like OpenTelemetry perpetuates this tool-dependency and complicates the creation of a consolidated service health view. This separation presents a strategic challenge to achieving a single pane of glass for operations.",
                "La ausencia de un estándar agnóstico de telemetría como OpenTelemetry perpetúa la dependencia directa de herramientas propietarias y dificulta la consolidación de un cuadro de mando único de salud del servicio. Esta segregación técnica representa un desafío estratégico para lograr una consola única operacional (Single Pane of Glass)."
            )
            t = t.replace(
                "Reliability management is currently governed by traditional Service Level Agreements (SLAs), focusing on the availability of individual infrastructure components such as VM uptime or database availability.",
                "La gestión de la fiabilidad y resiliencia está gobernada actualmente por Acuerdos de Nivel de Servicio (SLA) tradicionales, enfocados en la disponibilidad aislada de componentes de infraestructura (v.g. tiempo de actividad de máquinas virtuales o disponibilidad de bases de datos)."
            )
            t = t.replace(
                "This approach, while providing a baseline, is an incomplete measure of actual user experience or the health of transversal business services. The operational model is consequently reactive, a fact underscored by instances where business units report service degradation before it is detected by operations teams. This 'firefighting' posture consumes valuable engineering capacity, limiting the focus on proactive improvement and strategic innovation, which poses a significant risk to the organization's digital transformation ambitions.",
                "Este enfoque basado en SLAs tradicionales, aunque ofrece un baseline de control, resulta en una métrica incompleta para medir la experiencia real del usuario final o la salud de los servicios de negocio transversales. En consecuencia, el modelo operativo es predominantemente reactivo, evidenciado por situaciones donde las unidades de negocio detectan y reportan degradaciones de servicio antes de que sean identificadas por los equipos de operaciones de TI. Esta postura reactiva ('firefighting') consume una gran parte de la capacidad del equipo de ingeniería, desviando el foco de la mejora continua y de la innovación proactiva, lo cual compromete el cumplimiento de los objetivos de transformación digital del cliente."
            )

        # Check if the text contains key English container and observability terms and translate them
        container_obs_translations = {
            "There is a complete absence of a standardized catalog of base services for a container ecosystem. Foundational capabilities are deployed via manual, ad-hoc procedures, which creates operational friction and limits developer agility.":
                "Existe una ausencia absoluta de un catálogo estandarizado de servicios base para el ecosistema de contenedores. Las capacidades fundacionales se despliegan mediante procedimientos manuales y ad-hoc, lo que genera fricción operativa y limita la agilidad de los desarrolladores.",
            "There is a complete absence of a standardized catalog of base services for a container ecosystem.":
                "Existe una ausencia absoluta de un catálogo estandarizado de servicios base para el ecosistema de contenedores.",
            "A complete lack of automated processes and tooling for Kubernetes cluster lifecycle management is evident. Capabilities for provisioning, patching, and scaling clusters depend on manual scripts and specialist knowledge, which introduces risks and scale bottlenecks.":
                "Es evidente la falta absoluta de procesos automatizados y herramientas para la gestión del ciclo de vida de los clústeres de Kubernetes. Las capacidades para la provisión, parcheado y escalado de clústeres dependen de scripts manuales y conocimientos especializados, lo que introduce riesgos y cuellos de botella de escala.",
            "A complete lack of automated processes and tooling for Kubernetes cluster lifecycle management is evident.":
                "Es evidente la falta absoluta de procesos automatizados y herramientas para la gestión del ciclo de vida de los clústeres de Kubernetes.",
            "A 'Zero Trust' security model for the container ecosystem is non-existent. There is no systematic application of container security practices, such as vulnerability scanning of images, network policies, or runtime security monitoring, which leaves the platform exposed to threats.":
                "No existe un modelo de seguridad 'Zero Trust' para el ecosistema de contenedores. No hay una aplicación sistemática de prácticas de seguridad de contenedores, tales como el escaneo de vulnerabilidades de imágenes, políticas de red o monitorización de seguridad en tiempo de ejecución, lo que deja la plataforma expuesta a amenazas.",
            "A 'Zero Trust' security model for the container ecosystem is non-existent.":
                "No existe un modelo de seguridad 'Zero Trust' para el ecosistema de contenedores.",
            "There is no systematic application of container security practices, such as vulnerability scanning of images, network policies, or runtime security monitoring, which leaves the platform exposed to threats.":
                "No hay una aplicación sistemática de prácticas de seguridad de contenedores, tales como el escaneo de vulnerabilidades de imágenes, políticas de red o monitorización de seguridad en tiempo de ejecución, lo que deja la plataforma expuesta a amenazas.",
            "There is a total lack of a formal operating model for managing a container platform. The current model is based on reactive operations and manual troubleshooting, without clear roles, SLAs, or SRE practices to support the platform at scale.":
                "Existe una falta total de un modelo operativo formal para gestionar una plataforma de contenedores. El modelo actual se basa en operaciones reactivas y resolución de problemas manual, sin roles claros, SLAs o prácticas de SRE para dar soporte a la plataforma a escala.",
            "There is a total lack of a formal operating model for managing a container platform.":
                "Existe una falta total de un modelo operativo formal para gestionar una plataforma de contenedores.",
            "The platform's observability model is fragmented due to siloed monitoring tools and the absence of a common telemetry standard. This separation limits end-to-end service visibility, rendering root cause analysis dependent on specialized expertise and manual cross-team collaboration, which introduces delays.":
                "El modelo de observabilidad de la plataforma está fragmentado debido a herramientas de monitorización aisladas en silos y la ausencia de un estándar de telemetría común. Esta separación limita la visibilidad de extremo a extremo del servicio, haciendo que el análisis de causa raíz dependa de la experiencia especializada y de la colaboración manual entre equipos, lo cual introduce retrasos.",
            "The platform's observability model is fragmented due to siloed monitoring tools and the absence of a common telemetry standard.":
                "El modelo de observabilidad de la plataforma está fragmentado debido a herramientas de monitorización aisladas en silos y la ausencia de un estándar de telemetría común.",
            "This separation limits end-to-end service visibility, rendering root cause analysis dependent on specialized expertise and manual cross-team collaboration, which introduces delays.":
                "Esta separación limita la visibilidad de extremo a extremo del servicio, haciendo que el análisis de causa raíz dependa de la experiencia especializada y de la colaboración manual entre equipos, lo cual introduce retrasos.",
            "Reliability is managed via infrastructure-centric SLAs rather than customer-focused Service Level Objectives (SLOs). This approach is an incomplete measure of actual user experience or the health of transversal business services, rendering operations reactive and limiting focus on proactive improvement.":
                "La fiabilidad se gestiona a través de SLAs centrados en la infraestructura en lugar de Objetivos de Nivel de Servicio (SLO) centrados en el cliente. Este enfoque resulta en una medida incompleta de la experiencia real del usuario o de la salud de los servicios de negocio transversales, lo que hace que las operaciones sean reactivas y limiten el foco en la mejora proactiva.",
            "Reliability is managed via infrastructure-centric SLAs rather than customer-focused Service Level Objectives (SLOs).":
                "La fiabilidad se gestiona a través de SLAs centrados en la infraestructura en lugar de Objetivos de Nivel de Servicio (SLO) centrados en el cliente.",
            "This approach is an incomplete measure of actual user experience or the health of transversal business services, rendering operations reactive and limiting focus on proactive improvement.":
                "Este enfoque resulta en una medida incompleta de la experiencia real del usuario o de la salud de los servicios de negocio transversales, lo que hace que las operaciones sean reactivas y limiten el foco en la mejora proactiva.",
            "Lack of standardized services results in slow time-to-market and increased onboarding friction for developers.":
                "La falta de servicios estandarizados ralentiza el time-to-market e incrementa la fricción de incorporación para los desarrolladores.",
            "Manual lifecycle operations increase the risk of configuration drift, security vulnerabilities, and operational outages.":
                "Las operaciones manuales del ciclo de vida aumentan el riesgo de deriva de configuración, vulnerabilidades de seguridad e interrupciones operativas.",
            "Absence of container security controls leaves the platform highly vulnerable to container breakout and unauthorized access.":
                "La ausencia de controles de seguridad en contenedores deja la plataforma altamente vulnerable a escapes de contenedor y accesos no autorizados.",
            "Reactive operations without formal SRE practices lead to high MTTR, frequent outages, and low service reliability.":
                "Las operaciones reactivas sin prácticas formales de SRE conducen a un MTTR alto, interrupciones frecuentes y baja fiabilidad del servicio.",
            "Siloed monitoring increases MTTR and limits visibility into end-to-end transaction flows, delaying root cause analysis.":
                "La monitorización en silos aumenta el MTTR y limita la visibilidad en los flujos de transacciones de extremo a extremo, retrasando el análisis de causa raíz.",
            "Infrastructure-focused SLAs fail to protect user-facing service availability, leading to undetected service degradation.":
                "Los SLAs enfocados en infraestructura no logran proteger la disponibilidad del servicio de cara al usuario, lo que provoca una degradación del servicio no detectada."
        }
        for old, new in container_obs_translations.items():
            if old in t:
                t = t.replace(old, new)

    # RULE 1: Replace speculative or conditional language with declarative phrasing.
    speculative_patterns = {
        "posiblemente con componentes Mainframe": "integrando servidores corporativos y entornos de misión crítica de rango medio (Unix/AIX, AS/400 y plataformas legacy)",
        "posiblemente con componentes mainframe": "integrando servidores corporativos y entornos de misión crítica de rango medio (Unix/AIX, AS/400 y plataformas legacy)",
        "posiblemente con": "integrando",
        "posiblemente": "de manera probada",
        "potencialmente": "de forma estructurada",
        "tal vez": "con total seguridad",
    }
    for old, new in speculative_patterns.items():
        if old in t:
            t = t.replace(old, new)

    # RULE 3: Language compliance (Spain) - Replace non-idiomatic 'sistémico/sistémica' with 'estructural' and 'monitoreo' with 'monitorización'
    if lang == "es":
        # Plural forms (longer) must be replaced BEFORE singular forms (shorter) to prevent substring corruptions
        t = t.replace("sistémicas", "estructurales")
        t = t.replace("sistémicos", "estructurales")
        t = t.replace("Sistémicas", "Estructurales")
        t = t.replace("Sistémicos", "Estructurales")
        t = t.replace("sistémica", "estructural")
        t = t.replace("sistémico", "estructural")
        t = t.replace("Sistémica", "Estructural")
        t = t.replace("Sistémico", "Estructural")
        
        # Spain compliance: remove 'monitoreo' entirely in favor of 'monitorización'
        t = t.replace("monitoreos", "monitorizaciones")
        t = t.replace("Monitoreos", "Monitorizaciones")
        t = t.replace("monitoreo", "monitorización")
        t = t.replace("Monitoreo", "Monitorización")

    # RULE 2: Re-aligns terminology describing current strengths to match future-state compliance frameworks (e.g., NIS2/ENS).
    compliance_keywords = [
        "demostrar",
        "industrialización",
        "automatización",
        "automatizado",
        "continuo y auditable",
        "continuous and auditable",
    ]
    has_target_vocab = any(kw in t.lower() for kw in compliance_keywords)

    if has_target_vocab and len(t) < 300:
        if lang == "es":
            if "cumplimiento" in t.lower() or "normativo" in t.lower():
                t = "Sólida postura de partida y alineamiento inicial para facilitar la conformidad continua con marcos normativos (ENS, NIS2) en el estado objetivo."
            elif "runbooks" in t.lower():
                t = "Base técnica establecida para la futura codificación y automatización de procedimientos operativos (Runbooks-as-Code) de forma estructurada."
            else:
                t = (
                    t
                    + " (planeado para consolidarse de forma automatizada en el estado objetivo)."
                )
        else:
            if "compliance" in t.lower() or "regulatory" in t.lower():
                t = "Solid baseline posture and initial alignment to facilitate continuous compliance with regulatory frameworks (ENS, NIS2) in the target state."
            else:
                t = t + " (planned to be fully automated in the target state)."

    return t


def sanitize_and_unify_metrics(text: str, exact_score: float, exact_band: str, total_fair_ale: float, doc_lang: str, total_p90: float = 0.0, total_max: float = 0.0) -> str:
    import re
    import os
    if not text:
        return text

    # Set default values
    currency = "€" if doc_lang == "es" else "$"
    rate_mult = 1.0

    # Load dynamic exchange rate and currency symbol from custom calibration if exists (FAIR-MAM)
    client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
    custom_profile_path = Path(f"working/{client_id}/custom_risk_profile.json")
    for t_code in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]:
        temp_path = Path(f"working/{client_id}/{t_code}/custom_risk_profile.json")
        if temp_path.exists():
            custom_profile_path = temp_path
            break

    custom_calibration = {}
    if custom_profile_path.exists():
        try:
            with open(custom_profile_path, "r", encoding="utf-8-sig") as cf:
                custom_calibration = json.load(cf)
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")

    currency = custom_calibration.get("currency_symbol", currency)
    rate_mult = float(custom_calibration.get("exchange_rate", rate_mult))

    from assessment_engine.infrastructure.config_loader import resolve_localized_vocabulary
    vocab = resolve_localized_vocabulary(doc_lang)

    # Scale computed metrics by exchange rate in origin for presentation clarity
    total_fair_ale = total_fair_ale * rate_mult
    total_p90 = total_p90 * rate_mult
    total_max = total_max * rate_mult

    # 1. Format of TRUE ALE (with 2 decimals as requested)
    from assessment_engine.infrastructure.localization import format_number

    formatted_ale = format_number(total_fair_ale, locale=doc_lang, decimals=2)
    true_ale_str = f"{formatted_ale} {currency}"

    formatted_p90 = format_number(total_p90, locale=doc_lang, decimals=0)
    formatted_max = format_number(total_max, locale=doc_lang, decimals=0)
    formatted_score = format_number(exact_score, locale=doc_lang, decimals=2)
    
    # Clean up any mention of currency values (like 35.560.000, 32,120,000, 2.580.552,94, etc.)
    # Robust money_pattern preventing partial matches and ensuring full match of floats/thousands sep
    money_pattern = r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?\s*[€$]"
    text = re.sub(money_pattern, true_ale_str, text)
    
    # Also look for phrases like "35,56 millones de euros" or "32,12 millones" and replace them
    millones_pattern = r"\b\d+[,.]\d+\s*(?:millones|millones de euros)\b"
    if "millon" in text.lower() or "millón" in text.lower():
        text = re.sub(millones_pattern, f"{formatted_ale} {currency}", text)
        
    # 3. Clean up any mention of global score/band
    score_pattern = r"\b\d+[,.]\d+\s*sobre\s*5(?:[.,]0+)?\b"
    text = re.sub(score_pattern, f"{formatted_score} sobre 5,00", text)
    
    # Match band patterns inside quotes or parentheses and align with the true band
    band_pattern = r"Nivel\s*\d+\s*\([^)]+\)"
    true_band_str = f"Nivel {exact_score:.1f}".replace(".", ",") + f" ({exact_band})"
    text = re.sub(band_pattern, true_band_str, text)
    
    # 4. Enhance terminology (Gap C: AIOps)
    text = text.replace("herramientas de análisis predictivo", "plataformas de AIOps y remediación autónoma")
    text = text.replace("análisis predictivo", "AIOps y remediación autónoma")
    
    # 5. Abstract Executive Summary (Gap D: Vendor agnostic)
    # Target specific sentence generated by LLM to abstract it
    target_sentence = "distribuido en un 80% on-premise ( VMware y Oracle VM) y un 20% en un entorno híbrido y multi-cloud (desplegado mayoritariamente en AWS con integraciones secundarias y de identidad en Microsoft Azure y Google Cloud)"
    replacement_sentence = "distribuido en un modelo bimodal (80% cargas tradicionales de misión crítica y 20% en ecosistemas multi-nube pública)"
    text = text.replace(target_sentence, replacement_sentence)
    
    # General vendor cleanup just in case
    text = text.replace("( VMware y Oracle VM)", "")
    text = text.replace("en AWS con integraciones secundarias y de identidad en Microsoft Azure y Google Cloud", "en ecosistemas cloud")
    text = text.replace("La brecha más crítica reside en la inexistencia de una plataforma de contenedores", "La brecha de modernización más crítica reside en la inexistencia de una plataforma de contenedores")
    
    # 6. Inject Cost of Delay (Gap A)
    if "Expectativa de Pérdida Anualizada (ALE)" in text and "inacción" in text.lower():
        if "demora en la monetización" not in text:
            text += f" Más allá del Coste de Inacción operativo ({formatted_ale} {currency} de ALE), la deuda técnica actual impone un alto **impacto por demora en la monetización de proyectos**, postergando la consecución de las iniciativas estratégicas clave."

    # 7. Pedagogical & diplomatic rewrite of executive summary maturity and ALE paragraph (first-time reader alignment)
    if "madurez" in text.lower() and ("ale" in text.lower() or "fair" in text.lower() or "exposición" in text.lower()):
        # Localize fallbacks based on document language to prevent language mixture
        if doc_lang == "es":
            fallback_inicial = "procesos iniciales ad-hoc e informales"
            fallback_repetible = "procesos básicos pero tácticos e inconsistentes"
            fallback_definido = "procesos establecidos localmente pero sin integración global"
            fallback_gestionado = "procesos medidos cuantitativamente y bajo control"
            fallback_optimizado = "procesos optimizados y en mejora continua"
        else:
            fallback_inicial = "initial and ad-hoc processes"
            fallback_repetible = "basic but inconsistent tactical processes"
            fallback_definido = "localized processes lacking global integration"
            fallback_gestionado = "quantitatively measured and controlled processes"
            fallback_optimizado = "optimized and continuously improved processes"

        # Select precise qualitative description from dynamic localized configuration (5 bands)
        if exact_band == "Inicial":
            band_qualitative_desc = vocab.get("desc_band_inicial", fallback_inicial)
        elif exact_band == "Repetible":
            band_qualitative_desc = vocab.get("desc_band_repetible", fallback_repetible)
        elif exact_band == "Definido":
            band_qualitative_desc = vocab.get("desc_band_definido", fallback_definido)
        elif exact_band == "Gestionado":
            band_qualitative_desc = vocab.get("desc_band_gestionado", fallback_gestionado)
        elif exact_band == "Optimizado":
            band_qualitative_desc = vocab.get("desc_band_optimizado", fallback_optimizado)
        else:
            band_qualitative_desc = vocab.get("desc_band_definido", fallback_definido)

        if doc_lang == "es":
            new_maturity_p = (
                f"La torre presenta un perfil de madurez cuantitativo de **{formatted_score} sobre 5,00** (Nivel **'{exact_band}'**), "
                f"{band_qualitative_desc}. Bajo el estándar cuantitativo FAIR, "
                f"esta falta de cohesión operativa se traduce en una fuga de capital medida en una **Expectativa de Pérdida Anualizada (ALE) de {true_ale_str}**, "
                f"la cual define el coste de inactividad rutinario y silencioso de tolerar el statu quo. No obstante, en un escenario anual de crisis "
                f"severa o estrés acumulado en el percentil 90 (P90), la exposición de la plataforma escalaría de forma abrupta hasta los "
                f"**{formatted_p90} {currency}**, con una pérdida máxima estimada de hasta **{formatted_max} {currency}** ante eventos extremos de indisponibilidad concurrentes."
            )
        else:
            new_maturity_p = (
                f"The tower presents a quantitative maturity rating of **{formatted_score} out of 5.00** (Band **'{exact_band}'**), "
                f"{band_qualitative_desc}. Under the FAIR quantitative standard, "
                f"this operational gap translates into capital drainage measured by an **Annual Loss Exposure (ALE) of {true_ale_str}**, "
                f"defining the routine, silent drag of tolerating the statu quo. However, in an annual scenario of severe crisis "
                f"or accumulated stress at the 90th percentile (P90), the platform's exposure would escalate abruptly up to "
                f"**{formatted_p90} {currency}**, with an estimated maximum loss of up to **{formatted_max} {currency}** in case of concurrent extreme outages."
            )
        
        # Flexible regex replacements using subn to prevent the double-replacement bug
        text, count = re.subn(
            r"(?:La torre presenta|El perfil de madurez|El análisis de madurez|La evaluación de madurez).*?(?:Expectativa|Exposición|Pérdida|ALE).*?[\d,.]+\s*[€$].*?\.",
            new_maturity_p,
            text,
            flags=re.IGNORECASE | re.DOTALL
        )
        if count == 0:
            text = re.sub(
                r"(?:La torre presenta|El perfil de madurez|El análisis de madurez|La evaluación de madurez).*?(?:Expectativa|Exposición|Pérdida|ALE).*?[\d,.]+\s*[€$].*?\.",
                new_maturity_p,
                text,
                flags=re.IGNORECASE | re.DOTALL
            )

    # 8. Language compliance (Spain): Replace non-idiomatic "sistémico/sistémica" with "estructural/estructurales"
    if doc_lang == "es":
        # Plural forms (longer) must be replaced BEFORE singular forms (shorter) to prevent substring corruptions
        text = text.replace("sistémicas", "estructurales")
        text = text.replace("sistémicos", "estructurales")
        text = text.replace("Sistémicas", "Estructurales")
        text = text.replace("Sistémicos", "Estructurales")
        text = text.replace("sistémica", "estructural")
        text = text.replace("sistémico", "estructural")
        text = text.replace("Sistémica", "Estructural")
        text = text.replace("Sistémico", "Estructural")
        
        # Spain compliance: remove 'monitoreo' entirely in favor of 'monitorización'
        text = text.replace("monitoreos", "monitorizaciones")
        text = text.replace("Monitoreos", "Monitorizaciones")
        text = text.replace("monitoreo", "monitorización")
        text = text.replace("Monitoreo", "Monitorización")
        
    return text


def generate_modules(payload_path: str):
    """Generates a structured set of AS-IS assessment report modules from a JSON payload.

    This function processes a primary JSON payload, enriching it with data from
    supplementary files such as approved annexes, client intelligence reports,
    tower definitions, and localization vocabularies. The aggregated data is then
    serialized into a series of Markdown (.md) and CSV (.csv) files that
    constitute a complete technical AS-IS report.

    All output files are written to an `asis_modules` subdirectory, which is
    created within the same directory as the input `payload_path`.

    Args:
        payload_path (str): The file system path to the main JSON payload file.

    Returns:
        None. The function's primary effect is writing files to the file system.

    Raises:
        FileNotFoundError: If the file specified by `payload_path` does not exist.
        json.JSONDecodeError: If the main payload file contains malformed JSON.
        OSError: If an error occurs during directory creation or file I/O, such as
            insufficient write permissions.
    """
    payload_path_obj = Path(payload_path)
    tower_dir = payload_path_obj.parent
    modules_dir = tower_dir / "asis_modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"📂 Iniciando Extracción de Módulos Docs-as-Code en: {modules_dir}")

    # Loads technical payloads from the blueprint configuration, which serves as the primary data source.
    with open(payload_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Load scoring output to get exact score and band deterministically
    scoring_file = tower_dir / "scoring_output.json"
    exact_score = 3.0
    exact_band = "Definido"
    if scoring_file.exists():
        try:
            with open(scoring_file, "r", encoding="utf-8-sig") as sf:
                score_data = json.load(sf)
            exact_score = float(score_data.get("tower_score_exact", score_data.get("score_exact", 3.0)))
            exact_band = score_data.get("maturity_band_from_exact", {}).get("label", score_data.get("current_maturity_band", "Definido"))
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")

    global_fair_ale = data.get("total_fair_ale", 0.0)

    tower_meta = data.get("document_meta", {})
    doc_lang = tower_meta.get("language", "es").lower()

    from assessment_engine.infrastructure.config_loader import (
        resolve_localized_vocabulary,
    )

    vocab = resolve_localized_vocabulary(doc_lang)

    tower_name = tower_meta.get("tower_name", "Desconocida")
    tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
    client_name = clean_client_name(tower_meta.get("client_name", "Cliente"))

    # Load client_intelligence.json for industry_name
    intel_data = {}
    client_intel_file = tower_dir.parent / "client_intelligence.json"
    if client_intel_file.exists():
        try:
            with open(client_intel_file, "r", encoding="utf-8-sig") as cif:
                intel_data = json.load(cif)
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")

    profile_sec = intel_data.get("profile", {}) if isinstance(intel_data, dict) else {}
    raw_industry = profile_sec.get("industry", profile_sec.get("industry_type_es", "Sector Estándar"))
    if doc_lang == "es":
        industry_map_es = {
            "Energy & Critical Infrastructure": "Sectores de Energía e Infraestructura Crítica",
            "Utilities": "Servicios Públicos e Infraestructura Crítica",
            "Finance": "Sector Financiero y Bancario",
            "Retail": "Sector de Distribución y Retail"
        }
        industry_name = industry_map_es.get(raw_industry, raw_industry)
    else:
        industry_name = raw_industry

    pillars = data.get("pillars_analysis", [])
    
    global_fair_p90 = 0.0
    global_fair_max = 0.0
    try:
        for p in pillars:
            for hc in p.get("health_check_asis", []):
                global_fair_p90 += hc.get("fair_p90_score", 0.0) or 0.0
                global_fair_max += hc.get("fair_max_score", 0.0) or 0.0
    except (OSError, ValueError, KeyError, AttributeError) as ex:

        logger.debug(f"[Fallback] Excepción controlada: {ex}")

    snap = data.get("executive_snapshot", {})
    cca = data.get("cross_capabilities_analysis", {})

    # Loads the `approved_annex` data if present, which contains curated and validated findings.
    annex_path = tower_dir / f"approved_annex_{tower_id.lower()}.template_payload.json"
    annex_data = {}
    if annex_path.exists():
        with open(annex_path, "r", encoding="utf-8-sig") as af:
            try:
                annex_data = json.load(af)
            except (OSError, ValueError, KeyError, AttributeError) as ex:

                logger.debug(f"[Fallback] Excepción controlada: {ex}")

    exec_sum = annex_data.get("executive_summary", {})
    score_profile = annex_data.get("pillar_score_profile", {})

    # Dynamically loads the tower definition and integrates KPIs into a narrative paragraph, avoiding bulleted lists to maintain prose flow.
    pillars_list_md = ""
    tower_def_path = (
        Path("engine_config/towers")
        / tower_id
        / f"tower_definition_{tower_id.lower()}.json"
    )
    if not tower_def_path.exists():
        # Provides a fallback for case-insensitive key matching to handle variations in source data.
        tower_def_path = (
            Path("engine_config/towers")
            / tower_id
            / f"tower_definition_{tower_id}.json"
        )

    if tower_def_path.exists():
        with open(tower_def_path, "r", encoding="utf-8-sig") as tdf:
            try:
                t_def = json.load(tdf)
                for p in t_def.get("pillars", []):
                    p_name = p.get("pillar_name", "Pilar")
                    p_weight = p.get("weight_pct", "0")

                    # Extracts Key Performance Indicator (KPI) names for integration into narrative text.
                    kpi_names = []
                    for kpi in p.get("kpis", []):
                        k_name = kpi.get("kpi_name", "KPI").strip()
                        # Normalizes text to lowercase while preserving the case of known acronyms to maintain technical accuracy.
                        if k_name and not k_name.isupper() and len(k_name) > 4:
                            k_name = k_name[0].lower() + k_name[1:]
                        kpi_names.append(k_name)

                    # Formats the KPI list into a grammatically standard series (e.g., 'a, b, and c') for prose integration.
                    if len(kpi_names) > 1:
                        kpi_str = ", ".join(kpi_names[:-1]) + " y " + kpi_names[-1]
                    elif kpi_names:
                        kpi_str = kpi_names[0]
                    else:
                        kpi_str = "las capacidades operativas del pilar"

                    pillars_list_md += f"* **{p_name} (Peso: {p_weight}%)**: Evalúa de manera integral la madurez operativa y los baselines técnicos de la infraestructura, analizando críticamente factores clave como {kpi_str}.\n"
            except Exception as e:
                logger.info(f"⚠️ Error parsing tower definition: {e}")

    if not pillars_list_md:
        # Returns a default empty string on a JSON parsing exception to prevent downstream processing failures.
        for p in pillars:
            p_name = p.get("pilar_name", "Pilar")
            pillars_list_md += f"* **{p_name}**: Evaluación técnica y análisis de brechas operativas en la torre.\n"

    #
    # SECTION MAPPING: Appendix B (Objective, Scope, Methodology) maps to `01_introduccion.md`.
    # The following section is designated for Appendix B to conform to the standard report structure.
    #
    if doc_lang == "es":
        intro_content = f"""# Objetivo, Alcance y Marco Metodológico

## Objetivos y Alcance
Este documento técnico anexo detalla el diagnóstico de la situación actual (AS-IS) de la torre tecnológica de **{tower_name}** para la organización **{client_name}**, desarrollado bajo un marco de evaluación ágil (*Fast Assessment*). El propósito principal de este análisis es proporcionar a la dirección de tecnología una radiografía clara, objetiva y priorizada de las capacidades operativas del perímetro evaluado.

El diagnóstico se enfoca específicamente en lograr tres resultados ejecutivos:
*   **Identificación de brechas de resiliencia:** Localizar ineficiencias de infraestructura y cuellos de botella que comprometan la continuidad de los servicios de producción.
*   **Determinación de obsolescencia técnica:** Evaluar el ciclo de vida de los activos tecnológicos y su alineación con los estándares actuales de soporte, seguridad y costes de mantenimiento.
*   **Priorización racional de inversiones:** Establecer una hoja de ruta de transformación donde cada iniciativa propuesta esté justificada por su capacidad real para mitigar riesgos y mejorar la eficiencia del servicio.

El alcance técnico de esta evaluación comprende el análisis detallado de los siguientes pilares de capacidad del dominio de **{tower_name}**:

{pillars_list_md}
La determinación de la madurez operativa y la postura de riesgo de estos pilares se realiza contrastando las prácticas actuales de **{client_name}** frente a los baselines estándar de la industria del **{industry_name}** y los marcos regulatorios aplicables.

## Marco Metodológico del Diagnóstico
La solidez de este análisis radica en un método de **calibración objetiva cruzada**, diseñado para mitigar sesgos de percepción y asegurar que las recomendaciones correspondan a la realidad operativa de la organización. El proceso se desarrolla en tres fases de análisis secuenciales:

1.  **Ingesta de Datos y Contraste de Evidencias:** Se recopila la información base mediante sesiones técnicas estructuradas y el análisis de la arquitectura física y lógica con los equipos especialistas de **{client_name}**. Esta autoevaluación inicial se contrasta y calibra con evidencias documentales de configuración y operación.
2.  **Análisis de Interdependencias Críticas:** El diagnóstico no evalúa componentes aislados. Se modelan las relaciones de dependencia lógica entre la infraestructura evaluada y el resto de los servicios de la organización, identificando de manera analítica cómo la fragilidad de un componente puede propagar riesgos a toda la cadena de valor de negocio.
3.  **Modelado Cuantitativo de Riesgos:** Para dotar al informe de rigor financiero, los riesgos técnicos identificados se evalúan utilizando el estándar internacional **OpenFAIR (Factor Analysis of Information Risk)**. Este marco traduce la probabilidad de fallos operativos y su impacto técnico en métricas cuantitativas de exposición económica y operativa, permitiendo fundamentar la urgencia de las acciones correctoras con criterios estrictamente de negocio.
"""
    else:
        intro_content = f"""# Objective, Scope, and Methodological Framework

## Objectives and Scope
This technical annex document details the current situation diagnostic (AS-IS) of the **{tower_name}** technology tower for **{client_name}**, developed within a fast-track assessment framework (*Fast Assessment*). The primary purpose of this analysis is to provide the technology leadership with a clear, objective, and prioritized overview of the operational capabilities of the evaluated perimeter.

The diagnostic specifically focuses on achieving three executive outcomes:
*   **Identification of Resilience Gaps:** Locating infrastructure inefficiencies and bottlenecks that compromise the continuity of production services.
*   **Determination of Technical Obsolescence:** Evaluating the lifecycle of technology assets and their alignment with current support, security, and maintenance cost standards.
*   **Rational Investment Prioritization:** Establishing a transformation roadmap where each proposed initiative is justified by its actual capacity to mitigate risks and improve service efficiency.

The technical scope of this evaluation covers the detailed analysis of the following capability pillars within the **{tower_name}** domain:

{pillars_list_md}
The determination of operational maturity and risk posture across these pillars is performed by contrasting **{client_name}**'s current practices against standard industry baselines for the **{industry_name}** sector and applicable regulatory frameworks.

## Methodological Framework of the Diagnostic
The robustness of this analysis is grounded in a **cross-objective calibration** method, designed to mitigate perception biases and ensure that the recommendations align with the organization's operational reality. The process is conducted across three sequential analytical phases:

1.  **Data Ingestion and Evidence Contrast:** Baseline information is gathered through structured technical sessions and the analysis of physical and logical architecture with **{client_name}**'s specialist teams. This initial self-assessment is contrasted and calibrated against physical and operational documentation.
2.  **Critical Interdependency Analysis:** The diagnostic does not evaluate isolated components. Logical dependency relationships are modeled between the evaluated infrastructure and the rest of the organization's services, analytically identifying how the fragility of a single component can propagate risks across the entire business value chain.
3.  **Quantitative Risk Modeling:** To provide the report with financial rigor, the identified technical risks are evaluated using the international **OpenFAIR (Factor Analysis of Information Risk)** standard. This framework translates the probability of operational failures and their technical impact into quantitative metrics of financial and operational exposure, justifying the urgency of corrective actions based on strict business criteria.
"""

    with open(modules_dir / "01_introduccion.md", "w", encoding="utf-8") as f_out:
        f_out.write(intro_content.strip())

    #
    # SECTION MAPPING: Module 2 (Executive Summary) maps to `02_resumen_ejecutivo.md`.
    # Revises section titles to align with formal reporting terminology.
    #
    re_content = []
    re_content.append("# Resumen Ejecutivo\n")

    body_text = exec_sum.get("summary_body", "") if exec_sum else snap.get("bottom_line", "")
    cleaned_paragraphs = []
    if body_text:
        import re
        # Apply bilingually-sanitized and unified metrics on the entire un-split text first to avoid double regex matches
        body_text_sanitized = sanitize_and_unify_metrics(body_text, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
        
        # Split body text on double newlines to process paragraphs separately
        paragraphs = [p.strip() for p in body_text_sanitized.split("\n\n") if p.strip()]
        
        for p in paragraphs:
            # Force separation of the maturity and ALE if merged in the same paragraph
            if "Más importante" in p:
                p = p.replace(". Más importante", ".\n\nMás importante")
                p = p.replace(".  Más importante", ".\n\nMás importante")

            # Split again to process them as distinct paragraphs
            sub_ps = [sp.strip() for sp in p.split("\n\n") if sp.strip()]
            for sp in sub_ps:
                # Remove redundant sentence stating the quantitative score
                sp_clean = re.sub(r"El análisis cuantitativo sitúa.*?\.\s*", "", sp)
                
                # Global semicolon removal (replaced by commas or periods) to suit user preference
                sp_clean = sp_clean.replace(";", ",")

                if sp_clean:
                    cleaned_paragraphs.append(sp_clean)

    if cleaned_paragraphs:
        # Dynamic injection of Critical Technical Debt core concept as a separate paragraph
        tech_debt = cca.get("critical_technical_debt", "") if isinstance(cca, dict) else ""
        if tech_debt:
            tech_debt_clean = sanitize_and_unify_metrics(tech_debt, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
            if tech_debt_clean:
                # Remove semicolons from the tech debt paragraph too
                tech_debt_clean = tech_debt_clean.replace(";", ",")
                cleaned_paragraphs.append(tech_debt_clean)
                
        re_content.append("\n\n".join(cleaned_paragraphs) + "\n")

    # Load dynamic exchange rate and currency symbol from custom calibration if exists (FAIR-MAM)
    currency = "€" if doc_lang == "es" else "$"
    rate_mult = 1.0
    custom_profile_path = tower_dir / "custom_risk_profile.json"
    if custom_profile_path.exists():
        try:
            with open(custom_profile_path, "r", encoding="utf-8-sig") as cf:
                custom_cal = json.load(cf)
                currency = custom_cal.get("currency_symbol", currency)
                rate_mult = float(custom_cal.get("exchange_rate", rate_mult))
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")

    # Collect and sort all health check risks from all pillars to identify the top 3
    all_risks = []
    for pilar in pillars:
        p_name = pilar.get("pilar_name", "General")
        for hc in pilar.get("health_check_asis", []):
            capability = hc.get("target_state", hc.get("capability", "Capacidad"))
            ale_val = float(hc.get("fair_ale_score", 0.0))
            finding = hc.get("finding", hc.get("risk_observed", "No definido"))
            all_risks.append({
                "pilar_name": p_name,
                "capability": capability,
                "ale": ale_val,
                "finding": finding
            })
            
    # Sort risks by ALE descending
    all_risks.sort(key=lambda x: x["ale"], reverse=True)

    # Group risks by strategic mitigation initiative to prevent repetitive mapping of multiple risks to the same project
    mitigation_groups = {}
    for r in all_risks:
        cap = r['capability']
        p_name = r['pilar_name']
        
        if "automatización" in cap.lower() or "foundation" in p_name.lower():
            group_key = "Estandarización hacia Infraestructura como Código (IaC)"
            base_prop = "Transicionar de la gestión manual y fragmentada a un modelo operativo basado en código, consolidando plataformas y asegurando la conformidad continua con directivas de seguridad como **NIS2**."
        elif "kubernetes" in cap.lower() or "container" in p_name.lower() or "contenedor" in cap.lower():
            group_key = "Orquestación Unificada de Contenedores"
            base_prop = "Establecer un modelo operativo corporativo en *Kubernetes* para eliminar silos tecnológicos, gobernar el ciclo de vida y habilitar el despliegue ágil de microservicios en producción."
        elif "slo" in cap.lower() or "operations" in p_name.lower() or "observabilidad" in cap.lower():
            group_key = "Observabilidad y Operaciones SRE"
            base_prop = "Evolucionar de la monitorización reactiva tradicional a la observabilidad avanzada basada en *Objetivos de Nivel de Servicio (SLOs)* para predecir fallos y garantizar los niveles de acuerdo de negocio."
        elif "cloud" in p_name.lower():
            group_key = "Landing Zones y Arquitectura Cloud Híbrida"
            base_prop = "Diseñar e implementar zonas de aterrizaje seguras y estandarizadas para habilitar el consumo ágil y controlado de servicios cloud, mitigando el Shadow IT."
        else:
            # Normalize long/technical pillar names into clean executive initiative names
            clean_pilar_name = p_name
            if "automation" in p_name.lower() or "provisioning" in p_name.lower():
                clean_pilar_name = "Automatización y Autoservicio de Plataformas" if doc_lang == "es" else "Platform Automation and Self-Service"
            elif "hybrid" in p_name.lower() or "compute" in p_name.lower():
                clean_pilar_name = "Modernización de Cómputo Híbrido" if doc_lang == "es" else "Hybrid Compute Modernization"
            
            if doc_lang == "es":
                group_key = f"Optimización y Estandarización de {clean_pilar_name}" if "Automatización" not in clean_pilar_name and "Modernización" not in clean_pilar_name else clean_pilar_name
                base_prop = f"Modernizar de forma estratégica el pilar de {p_name} mediante la remediación de vulnerabilidades de configuración, gobernando de manera estricta el ciclo de vida tecnológico y erradicando silos de operación."
            else:
                group_key = f"Optimization and Standardization of {clean_pilar_name}" if "Platform" not in clean_pilar_name and "Hybrid" not in clean_pilar_name else clean_pilar_name
                base_prop = f"Strategically modernize the {p_name} pillar by remediating configuration vulnerabilities, strictly governing the technology lifecycle, and eradicating operational silos."
            
        if group_key not in mitigation_groups:
            mitigation_groups[group_key] = {"ale_sum": 0.0, "prop": base_prop}
        mitigation_groups[group_key]["ale_sum"] += r["ale"]

    # Sort grouped mitigations by ALE sum descending
    sorted_groups = sorted(mitigation_groups.items(), key=lambda x: x[1]["ale_sum"], reverse=True)

    # 4. Pilares de Mitigación y Habilitación de Valor Estratégico (Streamlined Section 1.2 + 1.3 for 1-page fit)
    re_content.append("## Pilares de Mitigación y Habilitación de Valor Estratégico")
    
    if sorted_groups:
        if doc_lang == "es":
            intro_pilares = (
                f"La calibración de los rangos de Magnitud de Pérdida (LM) para {client_name} se realiza bajo el criterio "
                f"riguroso de operador de {industry_name}. Bajo esta base de calibración, "
                f"la simulación estocástica de riesgos consolida las deficiencias técnicas en tres iniciativas o proyectos "
                f"estratégicos críticos, cuya ejecución inmediata desbloqueará la resiliencia operativa y mitigará la "
                f"exposición financiera acumulada de la organización:\n"
            )
        else:
            intro_pilares = (
                f"The loss magnitude (LM) calibration for {client_name} is performed under the rigorous criteria of a "
                f"{industry_name} operator. Based on this calibrated baseline, the stochastic risk simulation "
                f"consolidates the technical deficiencies into three critical strategic initiatives. Their immediate execution "
                f"will unlock operational resilience and mitigate the annualized financial exposure of the organization:\n"
            )
        re_content.append(intro_pilares)
        
        top_3_sum = 0.0
        for i, (g_key, g_data) in enumerate(sorted_groups[:3], 1):
            g_ale = g_data["ale_sum"]
            top_3_sum += g_ale
            pct = (g_ale / global_fair_ale * 100) if global_fair_ale > 0 else 0.0
            
            # Scale dynamically by the exchange rate in time of presentation (FAIR-MAM)
            scaled_g_ale = g_ale * rate_mult
            formatted_g_ale = format_number(
                scaled_g_ale, locale=doc_lang, decimals=2
            )
            
            value_proposition = f"{g_data['prop']} Esta iniciativa mitiga de forma consolidada **{formatted_g_ale} {currency}** ({pct:.1f}% del ALE total) de exposición financiera latente."
            re_content.append(f"* **{g_key}:** {value_proposition}")
        re_content.append("")

    top_3_pct = (top_3_sum / global_fair_ale * 100) if global_fair_ale > 0 else 0.0

    if doc_lang == "es":
        if top_3_pct >= 80.0:
            mitigation_phrase = "la práctica totalidad de la exposición financiera al riesgo identificada"
        elif top_3_pct >= 65.0:
            mitigation_phrase = "más de las dos terceras partes de la exposición financiera al riesgo identificada"
        elif top_3_pct >= 40.0:
            mitigation_phrase = "aproximadamente la mitad de la exposición financiera al riesgo identificada"
        else:
            mitigation_phrase = "una parte muy relevante de la exposición financiera al riesgo identificada"
            
        c_to_action = (
            f"La adopción inmediata de este plan de transformación mitigará {mitigation_phrase}, "
            f"reduciendo de forma proporcional el coste de inacción operativo, resolviendo la sobrecarga operativa de ingeniería e "
            f"impulsando la conformidad con normativas europeas, lo cual habilitará la agilidad y escalabilidad requerida para soportar las demandas "
            f"estratégicas del negocio en el mediano plazo."
        )
    else:
        if top_3_pct >= 80.0:
            mitigation_phrase = "practically all of the identified financial risk exposure"
        elif top_3_pct >= 65.0:
            mitigation_phrase = "more than two-thirds of the identified financial risk exposure"
        elif top_3_pct >= 40.0:
            mitigation_phrase = "approximately half of the identified financial risk exposure"
        else:
            mitigation_phrase = "a highly significant portion of the identified financial risk exposure"
            
        c_to_action = (
            f"The immediate adoption of this transformation plan will mitigate {mitigation_phrase}, "
            f"proportionally reducing the operational cost of inaction, resolving engineering operational overload, and "
            f"driving compliance with European regulations, which will enable the agility and scalability required to support "
            f"medium-term strategic business demands."
        )

    re_content.append(c_to_action)

    # 5. Escribir archivo de resumen ejecutivo consolidador
    with open(modules_dir / "02_resumen_ejecutivo.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(re_content).strip())

    #
    # SECTION MAPPING: Module 3 (Platform Description) maps to `03_descripcion_plataforma.md`.
    #
    desc_parts = []
    if pillars:
        for p in pillars:
            desc_p = p.get("asis_architecture_description", p.get("asis_description", "")).strip()
            if desc_p and desc_p not in desc_parts:
                desc_parts.append(desc_p)
                
    if desc_parts:
        desc_raw = "\n\n".join(desc_parts)
    else:
        desc_raw = "Descripción técnica de la plataforma no disponible."

    desc_clean = sanitize_semantic_prose(desc_raw, doc_lang)

    desc_content = f"""# Descripción de la Plataforma de Infraestructura Actual

A continuación, se define de manera consolidada y unificada el inventario técnico, arquitectura y estado operativo general del entorno. Esta descripción unifica el contexto tecnológico general para evitar repeticiones innecesarias entre dominios:

{desc_clean}
"""
    with open(
        modules_dir / "03_descripcion_plataforma.md", "w", encoding="utf-8"
    ) as f_out:
        f_out.write(desc_content.strip())

    #
    # SECTION MAPPING: Module 4 (Maturity Matrix) maps to `04_matriz_madurez.csv`.
    #
    csv_mat_path = modules_dir / "04_matriz_madurez.csv"

    with open(csv_mat_path, "w", newline="", encoding="utf-8") as cf_out:
        writer = csv.writer(cf_out, delimiter=";")
        writer.writerow(
            [
                "Pilar / Capacidad Tecnológica Evaluada",
                "Score AS-IS",
                "Análisis de Brechas y Calibración del Diagnóstico",
            ]
        )

        for s_idx, p in enumerate(pillars):
            p_name = p.get("pilar_name", "Pilar")
            
            # We always generate the highly detailed, localized, structured justification dynamically
            justification = derive_pillar_justification(p, s_idx, doc_lang)

            writer.writerow([p_name, f"{p.get('score', 0.0):.2f}", justification])

    #
    # SECTION MAPPING: Module 5 (Cross-Cutting Platform Analysis) maps to `05_transversal.md`.
    #
    # Consolidates technical debt and cross-cutting weaknesses from the blueprint into a single dataset.
    trans_content = []
    trans_content.append("# Análisis Transversal de Capacidades\n")

    if cca:
        trans_content.append("### Deuda Técnica Crítica")
        tech_debt_raw = cca.get("critical_technical_debt", "No definido.")
        tech_debt_clean = sanitize_and_unify_metrics(tech_debt_raw, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
        
        # Intercept and refactor the aggressive/rigid default LLM technical debt text into constructive, C-level bullet points
        if "la heterogeneidad en la capa de virtualización" in tech_debt_clean.lower() or "carga operativa insostenible" in tech_debt_clean.lower():
            tech_debt_clean = (
                "La deuda técnica más relevante identificada en la plataforma se concentra en tres vectores principales de atención:\n\n"
                "* **Fragmentación en la capa de virtualización:** Coexistencia de múltiples plataformas de virtualización e infraestructura física remanente, lo que incrementa el esfuerzo de gestión técnica y la complejidad de la administración unificada de la capacidad computacional.\n"
                "* **Adopción gradual de arquitecturas de contenedores:** Conveniencia de consolidar un plano de control homogéneo y un catálogo de servicios estándar para facilitar la agilidad operativa y agilizar los despliegues de microservicios.\n"
                "* **Estandarización de la automatización:** Prevalencia de aprovisionamiento manual y procesos tradicionales que representan una excelente oportunidad para la adopción progresiva de Infraestructura como Código (IaC), impulsando la consistencia y seguridad en el entorno híbrido."
            )
            
        trans_content.append(tech_debt_clean + "\n")

        trans_content.append("### Patrones Transversales de Ineficiencia y Deuda Estructural")
        def_patterns = cca.get("common_deficiency_patterns", [])
        if isinstance(def_patterns, str):
            def_patterns_clean = sanitize_and_unify_metrics(def_patterns, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
            trans_content.append(def_patterns_clean + "\n")
        else:
            for pat in def_patterns:
                pat_clean = sanitize_and_unify_metrics(pat, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
                trans_content.append(f"* {pat_clean}")
            trans_content.append("")

    with open(modules_dir / "05_transversal.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(trans_content).strip())

    #
    # SECTION MAPPING: Module 6 (Risk Register, FAIR) maps to `06_matriz_riesgos_fair.csv`.
    #
    # Exports data in the three-column format required by the blueprint specification.
    csv_risks_path = modules_dir / "06_matriz_riesgos_fair.csv"
    with open(csv_risks_path, "w", newline="", encoding="utf-8") as cf_out:
        writer = csv.writer(cf_out, delimiter=";")
        writer.writerow(
            [
                "Capacidad Técnica Evaluada",
                "Diagnóstico Técnico y Evidencias de Auditoría (Audit RAG)",
                "Riesgo de Negocio e Impacto Operativo",
                "TEF",
                "LM",
                "ALE",
            ]
        )

        for pilar in pillars:
            p_name = pilar.get("pilar_name", "General")
            for hc in pilar.get("health_check_asis", []):
                #
                finding = hc.get("finding", hc.get("risk_observed", "No descripto."))
                evidence = hc.get("literal_evidence", "No se aportó evidencia literal.")
                biz_risk = hc.get("business_risk", hc.get("impact", "No descripto."))

                #
                finding_full = (
                    f'{finding}\n\nEvidencia Forense Literal (Audit RAG):\n"{evidence}"'
                )

                tef = hc.get("threat_event_frequency", 0.0)
                lm = hc.get("loss_magnitude", 0.0)
                ale = hc.get("fair_ale_score", 0.0)

                writer.writerow(
                    [
                        f"{p_name} - {hc.get('target_state', hc.get('capability', 'Capacidad'))}",
                        finding_full,
                        biz_risk,
                        f"{tef:.1f}",
                        f"{lm:.1f}",
                        f"{ale:.0f}",
                    ]
                )

    #
    # SECTION MAPPING: Module 7 (Conclusions and Gaps) maps to `07_conclusiones.md`.
    #
    conc_content = []
    conc_content.append(
        f"# {vocab.get('conclusions_title', 'Conclusiones, Brechas y Coste de Inacción')}\n"
    )

    conc_content.append(
        f"## {vocab.get('quick_diagnosis_title', 'Fortalezas y Brechas Clave (Diagnóstico Rápido)')}"
    )
    conc_content.append(
        vocab.get(
            "quick_diagnosis_intro",
            "A continuación se presenta el balance comparativo de las fortalezas encontradas frente a las deudas operativas más críticas:",
        )
    )

    # Structures strengths and gaps as discrete lists for rendering into a two-column table.
    strengths_list = []
    
    # Generate empirical AS-IS baseline strengths directly by sorting capabilities by vulnerability level
    empirical_caps = []
    if pillars:
        for p in pillars:
            p_name = p.get("pilar_name", "Dominio")
            for f in p.get("health_check_asis", []):
                vuln = f.get("vulnerability_level", 5)
                cap = f.get("capability", "")
                if cap:
                    empirical_caps.append((vuln, cap, p_name))
        
        # Sort by vulnerability level (lowest first = healthiest)
        empirical_caps.sort(key=lambda x: x[0])
        
        # Take the top 3 distinct capabilities to build the baseline
        seen_caps = set()
        for vuln, cap, p_name in empirical_caps:
            if cap not in seen_caps:
                seen_caps.add(cap)
                if doc_lang == "es":
                    if vuln <= 2:
                        strengths_list.append(f"Capacidad consolidada en '{cap}' ({p_name}), operando con niveles de riesgo controlados y sirviendo como anclaje de estabilidad operativa.")
                    else:
                        strengths_list.append(f"La capacidad de '{cap}' ({p_name}) conforma la línea base operativa funcional de la plataforma, asegurando el soporte continuo a los servicios de negocio actuales.")
                else:
                    if vuln <= 2:
                        strengths_list.append(f"Consolidated capability in '{cap}' ({p_name}), operating with controlled risk levels and serving as an operational stability anchor.")
                    else:
                        strengths_list.append(f"The '{cap}' capability ({p_name}) forms the current operational baseline of the platform, ensuring continuous support for critical business services.")
            if len(strengths_list) >= 3:
                break

    if not strengths_list:
        if doc_lang == "es":
            strengths_list.append("El entorno tecnológico evaluado requiere una modernización y estandarización integral en todos sus frentes operativos.")
        else:
            strengths_list.append("The evaluated technological environment requires comprehensive modernization and standardization across all operational fronts.")

    gaps_list = []
    # We use the structural risks generated by the executive snapshot as they accurately reflect AS-IS gaps
    weaknesses = snap.get("structural_risks", [])
    if isinstance(weaknesses, str):
        gaps_list.append(weaknesses)
    elif isinstance(weaknesses, list):
        gaps_list.extend(weaknesses)
        
    # If the LLM failed to provide structural risks, we fallback to empirical critical findings
    if not gaps_list and pillars:
        for p in pillars:
            findings = p.get("health_check_asis", [])
            for f in findings:
                f_score = float(f.get("exact_score", 5.0))
                finding_desc = f.get("finding", f.get("risk_observed", ""))
                if f_score < 2.60 and finding_desc:
                    gaps_list.append(finding_desc.strip())
                    if len(gaps_list) >= 4:
                        break

    # Serializes data to a specific format required by the downstream document compilation service.
    conc_content.append("--- TABLA COMPARATIVA FORTALEZAS VS BRECHAS ---")
    conc_content.append("FORTALEZAS_CLAVE:")
    for s in strengths_list:
        conc_content.append(f"* {sanitize_semantic_prose(s, doc_lang)}")
    conc_content.append("BRECHAS_CLAVE:")
    for g in gaps_list:
        conc_content.append(f"* {sanitize_semantic_prose(g, doc_lang)}")
    conc_content.append("--- FIN TABLA --- \n")

    # Implements regulatory terminology harmonization as specified by Requirement 2.
    doc_lang = tower_meta.get("language", "es").lower()
    reg_frameworks = tower_meta.get("regulatory_frameworks")
    if not reg_frameworks:
        reg_frameworks = (
            "ENS y NIS2" if doc_lang == "es" else "applicable regulatory frameworks"
        )

    conc_content.append(
        f"## {vocab.get('operational_implications_title', 'Implicaciones Operativas Clave')}"
    )

    # Loads localized implication text from `locales.json` to generate context-specific output.
    bottlenecks_txt = vocab.get(
        "bottlenecks_bullet",
        "**Cuellos de botella estructurales:** El modelo manual de aprovisionamiento de infraestructura limita la velocidad de entrega de las iniciativas estratégicas del negocio.",
    )
    delayed_txt = vocab.get(
        "delayed_faults_bullet",
        "**Detección tardía de incidentes técnicos:** La falta de observabilidad correlacionada eleva el Tiempo Medio de Resolución (MTTR) de fallos críticos.",
    )
    drift_tmpl = vocab.get(
        "config_drift_bullet",
        "**Desalineación y Desviación de Configuraciones:** El mantenimiento manual provoca que los entornos se desvíen continuamente del estado técnico aprobado, dificultando demostrar el cumplimiento normativo en tiempo real de {reg_frameworks}.",
    )

    conc_content.append(f"* {bottlenecks_txt}")
    conc_content.append(f"* {delayed_txt}")
    conc_content.append(f"* {drift_tmpl.format(reg_frameworks=reg_frameworks)}\n")

    conc_content.append(
        f"## {vocab.get('coi_title', 'Coste de Inacción (Do Nothing) y Siguientes Pasos')}"
    )
    msg_bottle = exec_sum.get("message_bottleneck", "")
    if msg_bottle:
        msg_bottle_clean = sanitize_and_unify_metrics(msg_bottle, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
        conc_content.append(msg_bottle_clean + "\n")

    coi = snap.get("cost_of_inaction", [])
    if isinstance(coi, str):
        coi_clean = sanitize_and_unify_metrics(coi, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
        conc_content.append(coi_clean + "\n")
    else:
        for item in coi:
            item_clean = sanitize_and_unify_metrics(item, exact_score, exact_band, global_fair_ale, doc_lang, global_fair_p90, global_fair_max)
            conc_content.append(f"* {item_clean}")

    with open(modules_dir / "07_conclusiones.md", "w", encoding="utf-8") as f_out:
        f_out.write("\n".join(conc_content).strip())

    logger.info(f"🎉 ¡Módulos Docs-as-Code extraídos con éxito en: {modules_dir}!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.info("Uso: python generate_asis_markdown_modules.py <blueprint_payload.json>")
        sys.exit(1)
    generate_modules(sys.argv[1])
