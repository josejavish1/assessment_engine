import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import VersionedPayload


class HealthCheckAsIs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_state: str = Field(..., alias="capability", description="La capacidad técnica específica evaluada en el pilar.")
    risk_observed: str = Field(..., alias="finding", description="Análisis ejecutivo y objetivo del hallazgo o brecha detectada en el AS-IS.")
    impact: str = Field(..., alias="business_risk", description="Riesgo de negocio real derivado directamente de este hallazgo técnico.")
    fragment_id: Optional[str] = Field(None, description="Identificador único del fragmento de evidencia del RAG.")
    literal_evidence: Optional[str] = Field(None, description="Cita de texto literal exacta extraída del RAG como evidencia.")
    
    # --- FAIR Risk Quantification Fields ---
    threat_event_frequency: int = Field(..., description="Estimación FAIR de la frecuencia de la amenaza (1 a 5).")
    vulnerability_level: int = Field(..., description="Estimación FAIR de la vulnerabilidad del activo (1 a 5).")
    loss_magnitude: int = Field(..., description="Estimación FAIR del impacto financiero en caso de pérdida (1 a 5).")
    fair_ale_score: Optional[float] = Field(None, description="Annualized Loss Expectancy calculado matemáticamente.")


class ArchitecturalGravityProfile(BaseModel):
    """Perfil calculado dinámicamente en la Fase 0 para restringir la arquitectura al contexto real."""
    on_premise_weight: float = Field(..., description="Porcentaje estimado de cargas de trabajo que deben permanecer on-premise (0.0 a 1.0).")
    cloud_native_weight: float = Field(..., description="Porcentaje estimado de cargas de trabajo aptas para cloud público (0.0 a 1.0).")
    regulatory_strictness: str = Field(..., description="Nivel de rigurosidad regulatoria (e.g., Alto/Medio/Bajo) que restringe la soberanía del dato.")
    vendor_lockin_tolerance: str = Field(..., description="Tolerancia del cliente a quedar atado a un proveedor cloud específico (Alta/Media/Baja).")
    strategic_directive: str = Field(..., description="Directriz arquitectónica resultante (e.g., 'Sovereign Hybrid Edge', 'Cloud-First', 'Aggressive Strangler Fig').")
    recommended_target_maturity: float = Field(..., description="Nivel de madurez objetivo recomendado (ej. 4.0, 4.2, 4.5) basado en la criticidad y ambición del cliente.")


class TargetArchitectureToBe(BaseModel):
    vision: str = Field(
        ...,
        description=(
            "Visión arquitectónica To-Be a largo plazo para este pilar. "
            "MANDATO DE SOBERANÍA Y ANTI-LOCK-IN: Para clientes de Infraestructura Crítica con huella on-premise mayoritaria, "
            "la arquitectura DEBE ser un modelo 'Sovereign Hybrid Edge'. Se prohíbe proponer una migración "
            "del 100% al Cloud público. Se debe diseñar una capa agnóstica (e.g., Kubernetes/OpenShift/Tanzu) "
            "que mantenga las cargas críticas on-premise por latencia y soberanía, utilizando el Hyperscaler (e.g. AWS) "
            "como extensión elástica, plano de control unificado y habilitador de analítica, sin generar vendor lock-in estructural."
        )
    )
    vision_3_years: str = Field(
        default="Visión a 3 años no definida.",
        description="Descripción del objetivo de madurez y capacidades a alcanzar en el horizonte de 3 años (Nivel 5 básico)."
    )
    vision_5_years: str = Field(
        default="Visión a 5 años no definida.",
        description="Descripción de la visión aspiracional a 5 años (Consolidación, AIOps, etc.)."
    )
    levers_technology: list[str] = Field(
        default_factory=list,
        description="Palancas tecnológicas para alcanzar el TO-BE."
    )
    levers_process: list[str] = Field(
        default_factory=list,
        description="Palancas de procesos (ITIL, SRE, DevOps) para alcanzar el TO-BE."
    )
    levers_operation: list[str] = Field(
        default_factory=list,
        description="Palancas operativas (guardias, roles, NOC, capacitación) para alcanzar el TO-BE."
    )
    expected_benefits: list[str] = Field(
        default_factory=list,
        description="Beneficios esperados de alcanzar el modelo TO-BE."
    )
    cost_of_inaction_risks: list[str] = Field(
        default_factory=list,
        description="Riesgos específicos si no se actúa y dependencias clave (El Cost of Inaction por dominio)."
    )


class WorkBreakdownStructureTask(BaseModel):
    task_name: str = Field(..., description="Nombre de la tarea o fase (Ej. Fase 1: HLD, Fase 2: LLD & Build).")
    required_profile: str = Field(..., description="Perfil (gerente_cuenta, arquitecto, experto, project_manager, tecnico_medio, tecnico_junior).")
    estimated_hours: int = Field(..., description="Horas estimadas de esfuerzo.")


class ProjectToDo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    initiative: str = Field(
        ..., 
        alias="name", 
        description="Nombre del proyecto técnico. EXIGENCIA DE INGENIERÍA DURA: Debe requerir implementación técnica hands-on."
    )
    transformation_typology: str = Field(
        ...,
        description="Clasificación o Vector de Inversión (e.g., 'Core Modernization', 'Security & Sovereignty')."
    )
    expected_outcome: str = Field(..., alias="business_case", description="Justificación e impacto estratégico en el negocio de realizar este proyecto.")
    objective: str = Field(
        ..., 
        alias="tech_objective", 
        description="Objetivo técnico específico de ingeniería. Prohibidos proyectos blandos de definición o gobernanza consultiva."
    )
    
    # --- Board-Ready Project Charter Fields ---
    project_description: Optional[str] = Field(None, description="Descripción ejecutiva del proyecto en lenguaje llano para el CIO.")
    smart_objectives: Optional[str] = Field(None, description="Objetivos SMART cuantificables (Ej. Reducir latencia 40% en Q4).")
    in_scope: Optional[list[str]] = Field(None, description="Alcance estricto incluido en el proyecto (In-Scope).")
    out_of_scope: Optional[list[str]] = Field(None, description="Límites del proyecto: Qué NO está incluido (Out-of-Scope) para evitar scope creep.")
    deliverables: list[str] = Field(..., description="Entregables técnicos duros (DoD - Definition of Done).")
    governance_roles: Optional[list[str]] = Field(None, description="Perfiles clave y matriz RACI básica (Ej. Sponsor: CIO, Lead: Cloud Architect).")
    critical_risks: Optional[list[str]] = Field(None, description="Riesgos técnicos/operativos de ejecución y su estrategia de mitigación.")
    
    sizing: str = Field(..., description="Dimensión estimativa del proyecto (S, M, L, XL).")
    duration: str = Field(..., description="Duración y horizonte estimado (ej. 'Fase 1: 0-6 Meses').")
    program_id: Optional[str] = None
    
    # --- FinOps & Traceability Fields (Calculated deterministically, not by the architect LLM) ---
    wbs_breakdown: Optional[list[WorkBreakdownStructureTask]] = Field(None, description="Desglose WBS calculado.")
    capex_estimate: Optional[str] = Field(None, description="Estimación matemática del CAPEX.")
    opex_estimate: Optional[str] = Field(None, description="Estimación matemática del OPEX con margen.")
    roi_justification: Optional[str] = Field(None, description="Justificación de ROI y Hard/Soft Savings.")
    mitigates_risk_id: Optional[str] = Field(None, description="ID del HealthCheckAsIs que resuelve.")


class ProjectCharterEnrichment(BaseModel):
    commercial_name: Optional[str] = Field(None, description="Nombre comercial SOTA del proyecto, refinado y de alto impacto para C-Levels.")
    project_description: str = Field(..., description="Descripción ejecutiva del proyecto en lenguaje llano para el CIO.")
    smart_objectives: str = Field(..., description="Objetivos SMART cuantificables (Ej. Reducir latencia 40% en Q4).")
    in_scope: list[str] = Field(..., description="Alcance estricto incluido en el proyecto (In-Scope).")
    out_of_scope: list[str] = Field(..., description="Límites del proyecto: Qué NO está incluido (Out-of-Scope) para evitar scope creep.")
    governance_roles: list[str] = Field(..., description="Perfiles clave y matriz RACI básica.")
    critical_risks: list[str] = Field(..., description="Riesgos técnicos/operativos de ejecución y su estrategia de mitigación.")
    wbs_breakdown: list[WorkBreakdownStructureTask] = Field(..., description="Desglose WBS calculado.")
    roi_justification: str = Field(..., description="Justificación de ROI y Hard/Soft Savings.")


class PillarBlueprintDraft(BaseModel):
    thought_process: str = Field(
        description="Paso de razonamiento libre (Chain of Thought). Expresa aquí tu lógica de análisis arquitectónico paso a paso antes de formatear las propiedades JSON estrictas."
    )
    pilar_id: str
    pilar_name: str
    score: float = 0.0
    target_score: float = 4.0
    asis_architecture_description: str = Field(
        default="Descripción no disponible.",
        description="Narrativa técnica profunda y detallada (mínimo 3 párrafos) que describe la arquitectura, inventario y topología ACTUAL (AS-IS) de este pilar, antes de enumerar los riesgos."
    )
    health_check_asis: list[HealthCheckAsIs]
    target_architecture_tobe: TargetArchitectureToBe
    projects_todo: list[ProjectToDo]


class ExecutiveSnapshot(BaseModel):
    bottom_line: str
    decisions: list[str] = Field(
        ...,
        description="Nombres de las 2-3 iniciativas críticas a tomar. Deben ser copia EXACTA de los campos 'name' de projects_todo de los pilares."
    )
    cost_of_inaction: str
    structural_risks: list[str]
    business_impact: str
    operational_benefits: list[str]
    transformation_complexity: str


class CrossCapabilitiesAnalysis(BaseModel):
    common_deficiency_patterns: list[str]
    transformation_paradigm: str
    critical_technical_debt: str


class RoadmapWave(BaseModel):
    wave: str = Field(..., description="Nombre de la ola de transformación (ej. Wave 1: 0-6m).")
    projects: list[str] = Field(
        ...,
        description=(
            "Lista de nombres de proyectos asignados a esta Ola. "
            "CONTRATO DE EXTRACCIÓN CERRADA (MANDATORIO): Debe contener ÚNICAMENTE nombres de proyectos "
            "explicitados de forma idéntica en projects_todo de los pilares analizados. "
            "ESTRICTAMENTE PROHIBIDO inventar o añadir proyectos nuevos al roadmap que no tengan su respectiva ficha de proyecto en projects_todo."
        )
    )


class ExternalDependency(BaseModel):
    project: str = Field(..., description="Nombre EXACTO del proyecto técnico que tiene la dependencia.")
    depends_on: str = Field(..., description="Nombre EXACTO del proyecto o iniciativa PREVIA (Habilitador) de la cual depende. PROHIBIDO poner nombres genéricos de torres (ej. 'T3-Redes'). Debe apuntar a nombres de proyectos específicos.")
    reason: str


class OrchestratorBlueprintDraft(VersionedPayload):
    executive_snapshot: ExecutiveSnapshot
    design_principles: list[str] = Field(
        ...,
        description="Principios de diseño arquitectónico transversales (3 a 7 como máximo) que rigen toda la torre. Deben estar alineados al Perfil Arquitectónico del cliente (ej. Sovereign Cloud, Cloud-Native)."
    )
    cross_capabilities_analysis: CrossCapabilitiesAnalysis
    roadmap: list[RoadmapWave]
    external_dependencies: list[ExternalDependency]


class BlueprintDocumentMeta(BaseModel):
    client_name: str
    tower_name: str
    tower_code: str
    financial_tier: str
    transformation_horizon: str


class BlueprintPayload(OrchestratorBlueprintDraft):
    document_meta: BlueprintDocumentMeta
    pillars_analysis: list[PillarBlueprintDraft]
    total_fair_ale: Optional[float] = Field(None, description="Expectativa de pérdida anualizada (ALE) consolidada en euros.")
