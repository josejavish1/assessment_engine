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


class ArchitecturalGravityProfile(BaseModel):
    """Perfil calculado dinámicamente en la Fase 0 para restringir la arquitectura al contexto real."""
    on_premise_weight: float = Field(..., description="Porcentaje estimado de cargas de trabajo que deben permanecer on-premise (0.0 a 1.0).")
    cloud_native_weight: float = Field(..., description="Porcentaje estimado de cargas de trabajo aptas para cloud público (0.0 a 1.0).")
    regulatory_strictness: str = Field(..., description="Nivel de rigurosidad regulatoria (e.g., Alto/Medio/Bajo) que restringe la soberanía del dato.")
    vendor_lockin_tolerance: str = Field(..., description="Tolerancia del cliente a quedar atado a un proveedor cloud específico (Alta/Media/Baja).")
    strategic_directive: str = Field(..., description="Directriz arquitectónica resultante (e.g., 'Sovereign Hybrid Edge', 'Cloud-First', 'Aggressive Strangler Fig').")


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


class ProjectToDo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    initiative: str = Field(
        ..., 
        alias="name", 
        description="Nombre del proyecto técnico. EXIGENCIA DE INGENIERÍA DURA: Debe requerir implementación técnica hands-on (ej. IaC, Kubernetes, Landing Zones, Automatización). Prohibido proponer Workshops, Comités o reuniones."
    )
    transformation_typology: str = Field(
        ...,
        description="Clasificación o Vector de Inversión al que pertenece este proyecto (e.g., 'Core Modernization', 'Security & Sovereignty', 'Automation Engine')."
    )
    expected_outcome: str = Field(..., alias="business_case", description="Justificación e impacto estratégico en el negocio de realizar este proyecto.")
    objective: str = Field(
        ..., 
        alias="tech_objective", 
        description="Objetivo técnico específico de ingeniería. Prohibidos proyectos blandos de definición o gobernanza consultiva."
    )
    deliverables: list[str] = Field(..., description="Entregables técnicos tangibles y verificables (DoD).")
    sizing: str = Field(..., description="Dimensión estimativa del proyecto (S, M, L, XL).")
    duration: str = Field(..., description="Duración estimada del proyecto (ej. '3 Meses', '6 Meses').")
    program_id: Optional[str] = None


class PillarBlueprintDraft(BaseModel):
    thought_process: str = Field(
        description="Paso de razonamiento libre (Chain of Thought). Expresa aquí tu lógica de análisis arquitectónico paso a paso antes de formatear las propiedades JSON estrictas."
    )
    pilar_id: str
    pilar_name: str
    score: float = 0.0
    target_score: float = 4.0
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
