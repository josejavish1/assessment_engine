import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import VersionedPayload


class HealthCheckAsIs(BaseModel):
    """Represents the current state (AS-IS) assessment of a technical capability.

    A Pydantic model capturing a single finding from a technical health check.
    It details the observed risk, its business impact, and includes quantitative
    risk analysis metrics derived from the Factor Analysis of Information Risk
    (FAIR) methodology. The model also links the finding to its source evidence,
    such as a specific document fragment.

    Attributes:
        node_id (str): A unique identifier for the assessment node, defaulting to
            a UUIDv4.
        target_state (str): The specific technical capability being assessed. Can be
            populated using the alias 'capability'.
        risk_observed (str): An objective analysis of the finding or capability gap
            identified. Can be populated using the alias 'finding'.
        impact (str): The specific, tangible business risk that directly results
            from the identified technical finding. Can be populated using the alias
            'business_risk'.
        fragment_id (Optional[str]): The unique identifier for the source document
            fragment from which evidence was extracted.
        literal_evidence (Optional[str]): A verbatim quote from the source material
            serving as direct evidence for the finding.
        threat_event_frequency (int): The estimated threat event frequency, rated
            on a discrete scale of 1 to 5, as defined by the FAIR model.
        vulnerability_level (int): The estimated asset vulnerability, rated on a
            discrete scale of 1 to 5, as defined by the FAIR model.
        loss_magnitude (int): The estimated financial loss magnitude, rated on a
            discrete scale of 1 to 5, as defined by the FAIR model.
        fair_ale_score (Optional[float]): The calculated Annualized Loss Expectancy
            (ALE), typically expressed in a monetary currency.
    """
    model_config = ConfigDict(populate_by_name=True)

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_state: str = Field(..., alias="capability", description="The specific technical capability being assessed within this architectural pillar.")
    risk_observed: str = Field(..., alias="finding", description="An objective, executive-level analysis of the finding or capability gap identified in the AS-IS assessment.")
    impact: str = Field(..., alias="business_risk", description="The specific, tangible business risk that directly results from the identified technical finding.")
    fragment_id: Optional[str] = Field(None, description="The unique identifier for the source document fragment used as RAG evidence.")
    literal_evidence: Optional[str] = Field(None, description="A verbatim quote extracted from the RAG source material to serve as evidence.")
    
    # Specifies fields for risk quantification using the Factor Analysis of Information Risk (FAIR) model.
    threat_event_frequency: int = Field(..., description="The estimated threat event frequency on a scale of 1 to 5, as defined by the FAIR model.")
    vulnerability_level: int = Field(..., description="The estimated asset vulnerability on a scale of 1 to 5, as defined by the FAIR model.")
    loss_magnitude: int = Field(..., description="The estimated financial loss magnitude on a scale of 1 to 5, as defined by the FAIR model.")
    fair_ale_score: Optional[float] = Field(None, description="The calculated Annualized Loss Expectancy (ALE) in the designated currency.")


class ArchitecturalGravityProfile(BaseModel):
    """A data model representing the constraints and directives that influence a system's architectural design.

    This model serves as a structured profile, quantifying factors that pull a
    solution towards on-premise, cloud-native, or hybrid topologies. It provides a
    formal input for architectural decision-making processes, ensuring the
    resulting system blueprint aligns with specified business requirements,
    technical constraints, and regulatory obligations.

    Attributes:
        on_premise_weight (float): The proportion of workloads designated to remain
            on-premise, expressed as a value between 0.0 and 1.0.
        cloud_native_weight (float): The proportion of workloads suitable for
            public cloud deployment, expressed as a value between 0.0 and 1.0.
        regulatory_strictness (str): The level of regulatory stringency
            constraining data residency and sovereignty. Expected values are 'High',
            'Medium', or 'Low'.
        vendor_lockin_tolerance (str): The tolerance for dependency on a
            specific cloud service provider. Expected values are 'High', 'Medium',
            or 'Low'.
        strategic_directive (str): The designated high-level architectural
            pattern for the solution (e.g., 'Sovereign Hybrid Edge',
            'Cloud-First', 'Aggressive Strangler Fig').
        recommended_target_maturity (float): The target operational maturity
            level for the proposed architecture, derived from system criticality
            and strategic objectives.
    """
    on_premise_weight: float = Field(..., description="The estimated proportion of workloads that must remain on-premise, expressed as a float between 0.0 and 1.0.")
    cloud_native_weight: float = Field(..., description="The estimated proportion of workloads suitable for public cloud deployment, expressed as a float between 0.0 and 1.0.")
    regulatory_strictness: str = Field(..., description="The level of regulatory stringency (High, Medium, or Low) that constrains data sovereignty requirements.")
    vendor_lockin_tolerance: str = Field(..., description="The client's tolerance for vendor lock-in with a specific cloud service provider, rated as High, Medium, or Low.")
    strategic_directive: str = Field(..., description="The final architectural directive for the solution, such as 'Sovereign Hybrid Edge', 'Cloud-First', or 'Aggressive Strangler Fig'.")
    recommended_target_maturity: float = Field(..., description="The recommended target maturity level (e.g., 4.0, 4.2, 4.5), derived from client-specific criticality and strategic objectives.")


class TargetArchitectureToBe(BaseModel):
    r"""{'docstring': 'Models the target state ("To-Be") architecture for a specific domain.\n\nThis class defines the desired future state, encapsulating the long-term\nvision, tactical and strategic goals, required implementation levers\n(technology, process, and operations), expected benefits, and the risks\nassociated with inaction.\n\nAttributes:\n    vision: The long-term "To-Be" architectural vision. Mandates a \'Sovereign\n        Hybrid Edge\' model for critical infrastructure clients with a\n        significant on-premises footprint to prevent public cloud vendor\n        lock-in. This model requires an agnostic abstraction layer (e.g.,\n        Kubernetes) to retain critical workloads on-premises for sovereignty and\n        latency, while using a hyperscaler for elastic extension, unified\n        control, and analytics.\n    vision_3_years: A description of maturity and capability objectives to be\n        achieved within a 3-year tactical horizon.\n    vision_5_years: A description of the 5-year strategic vision.\n    levers_technology: A list of technology stacks, platforms, and solutions\n        required to implement the target state architecture.\n    levers_process: A list of process frameworks (e.g., ITIL, SRE, DevOps)\n        required to support the target state.\n    levers_operation: A list of operational models and artifacts (e.g., on-call\n        schedules, role definitions) required to support the target state.\n    expected_benefits: A list of expected benefits upon successful\n        implementation of the target state architecture.\n    cost_of_inaction_risks: An enumeration of specific risks and key\n        dependencies that materialize if no action is taken, representing the\n        cost of inaction.'}."""
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
        description="A description of the maturity and capability objectives to be achieved within a 3-year tactical horizon, such as reaching Basic Level 5."
    )
    vision_5_years: str = Field(
        default="Visión a 5 años no definida.",
        description="A description of the 5-year aspirational strategic vision, such as Consolidation or AIOps."
    )
    levers_technology: list[str] = Field(
        default_factory=list,
        description="The technology stacks, platforms, and solutions required to implement the TO-BE state architecture."
    )
    levers_process: list[str] = Field(
        default_factory=list,
        description="The process frameworks (e.g., ITIL, SRE, DevOps) required to support the TO-BE state."
    )
    levers_operation: list[str] = Field(
        default_factory=list,
        description="The operational models and artifacts (e.g., on-call schedules, role definitions, NOC procedures, training plans) required to support the TO-BE state."
    )
    expected_benefits: list[str] = Field(
        default_factory=list,
        description="A description of the expected benefits upon successful implementation of the TO-BE target state architecture."
    )
    cost_of_inaction_risks: list[str] = Field(
        default_factory=list,
        description="An enumeration of specific risks and key dependencies if no action is taken, representing the Cost of Inaction for the domain."
    )


class WorkBreakdownStructureTask(BaseModel):
    """Represents a single task within a Work Breakdown Structure (WBS)."""
    task_name: str = Field(..., description="The unique name of the work package, task, or phase (e.g., 'Phase 1: HLD', 'Phase 2: LLD & Build').")
    required_profile: str = Field(..., description="The role profile identifier for the resource (e.g., 'account_manager', 'architect', 'subject_matter_expert', 'project_manager', 'mid_level_technician', 'junior_technician').")
    estimated_hours: int = Field(..., description="The estimated total effort for the task, measured in person-hours.")


class ProjectToDo(BaseModel):
    """Defines a schema for a technical project charter.

    This Pydantic model provides a structured definition for an engineering
    project, covering aspects from high-level strategic alignment to detailed
    execution planning. The schema distinguishes between fields intended for
    initial definition and those that are deterministically calculated
    post-instantiation for financial operations (FinOps) and traceability.

    Attributes:
        node_id (str): A unique identifier for the project node, defaulting to a
            new UUID version 4.
        initiative (str): The formal name of the technical project. Aliased as
            'name'.
        transformation_typology (str): The investment classification or strategic
            vector for the project (e.g., 'Core Modernization').
        expected_outcome (str): The business justification and strategic impact
            of the project. Aliased as 'business_case'.
        objective (str): A specific, technical engineering objective for the
            project. Aliased as 'tech_objective'.
        project_description (Optional[str]): An executive summary of the project
            in non-technical business language.
        smart_objectives (Optional[str]): A set of quantifiable SMART
            (Specific, Measurable, Achievable, Relevant, Time-bound) objectives.
        in_scope (Optional[list[str]]): A strict definition of all in-scope
            items and deliverables.
        out_of_scope (Optional[list[str]]): An explicit list of all out-of-scope
            items to prevent scope creep.
        deliverables (list[str]): A list of concrete technical deliverables
            defining the project's Definition of Done (DoD).
        governance_roles (Optional[list[str]]): A list of key stakeholder
            profiles and a basic RACI matrix.
        critical_risks (Optional[list[str]]): A list of identified technical and
            operational risks with corresponding mitigation strategies.
        sizing (str): The estimated project size, categorized as S, M, L, or XL.
        duration (str): The estimated project duration and time horizon (e.g.,
            'Phase 1: 0-6 Months').
        program_id (Optional[str]): An optional identifier for a parent program
            to which this project belongs.
        wbs_breakdown (Optional[list[WorkBreakdownStructureTask]]): The computed
            Work Breakdown Structure (WBS) for the project. This field is
            typically populated post-generation.
        capex_estimate (Optional[str]): The estimated Capital Expenditure (CAPEX).
            This field is typically populated post-generation.
        opex_estimate (Optional[str]): The estimated Operational Expenditure
            (OPEX), including contingency. This field is typically populated
            post-generation.
        roi_justification (Optional[str]): The Return on Investment (ROI)
            justification with detailed calculations. This field is typically
            populated post-generation.
        mitigates_risk_id (Optional[str]): The unique identifier of an assessment
            finding that this project is designed to resolve.
    """
    model_config = ConfigDict(populate_by_name=True)

    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    initiative: str = Field(
        ..., 
        alias="name", 
        description="The formal name of the technical project, which must be a direct engineering initiative requiring technical implementation."
    )
    transformation_typology: str = Field(
        ...,
        description="The investment classification or strategic vector for the project, such as 'Core Modernization' or 'Security & Sovereignty'."
    )
    expected_outcome: str = Field(..., alias="business_case", description="The justification for the project, detailing its strategic business impact.")
    objective: str = Field(
        ..., 
        alias="tech_objective", 
        description="A specific, technical engineering objective. Prohibits non-technical projects focused on definition or consultative governance."
    )
    
    # Specifies the fields comprising the Board-Ready Project Charter.
    project_description: Optional[str] = Field(None, description="An executive summary of the project, articulated in non-technical business language for a CIO-level audience.")
    smart_objectives: Optional[str] = Field(None, description="A set of quantifiable SMART (Specific, Measurable, Achievable, Relevant, Time-bound) objectives.")
    in_scope: Optional[list[str]] = Field(None, description="A strict definition of all in-scope items and deliverables for the project.")
    out_of_scope: Optional[list[str]] = Field(None, description="A definition of project boundaries, explicitly listing all out-of-scope items to prevent scope creep.")
    deliverables: list[str] = Field(..., description="A list of concrete technical deliverables that constitute the Definition of Done (DoD).")
    governance_roles: Optional[list[str]] = Field(None, description="A list of key stakeholder profiles and a basic RACI (Responsible, Accountable, Consulted, Informed) matrix.")
    critical_risks: Optional[list[str]] = Field(None, description="A list of identified technical and operational execution risks, with corresponding mitigation strategies for each.")
    
    sizing: str = Field(..., description="The estimated project size, categorized as S, M, L, or XL.")
    duration: str = Field(..., description="The estimated project duration and time horizon, such as 'Phase 1: 0-6 Months'.")
    program_id: Optional[str] = None
    
    # Defines FinOps and traceability fields. These values are deterministically calculated post-generation and are excluded from LLM population.
    wbs_breakdown: Optional[list[WorkBreakdownStructureTask]] = Field(None, description="The computed Work Breakdown Structure (WBS) for the project.")
    capex_estimate: Optional[str] = Field(None, description="The estimated Capital Expenditure (CAPEX) in the designated currency.")
    opex_estimate: Optional[str] = Field(None, description="The estimated Operational Expenditure (OPEX), inclusive of a contingency margin, in the designated currency.")
    roi_justification: Optional[str] = Field(None, description="The Return on Investment (ROI) justification, including detailed calculations for both hard and soft savings.")
    mitigates_risk_id: Optional[str] = Field(None, description="The unique identifier of the AS-IS assessment finding that this project is designed to resolve.")


class ProjectCharterEnrichment(BaseModel):
    r"""{'docstring': 'A data model for a comprehensive project charter.\n\nThis class defines the schema for a project charter, a formal document that\nprovides stakeholders with a high-level overview of a project, its goals,\nscope, and governance. It serves as a foundational agreement between the\nproject team and key stakeholders.\n\nAttributes:\n    commercial_name: The formal project name, optimized for executive-level\n        communication and impact.\n    project_description: An executive summary of the project, articulated in\n        non-technical business language for a CIO-level audience.\n    smart_objectives: A set of quantifiable SMART (Specific, Measurable,\n        Achievable, Relevant, Time-bound) objectives.\n    in_scope: A strict definition of all in-scope items and deliverables for\n        the project.\n    out_of_scope: A definition of project boundaries, explicitly listing all\n        out-of-scope items to prevent scope creep.\n    governance_roles: A list of key stakeholder profiles and a basic RACI\n        (Responsible, Accountable, Consulted, Informed) matrix.\n    critical_risks: A list of identified technical and operational execution\n        risks, with corresponding mitigation strategies for each.\n    wbs_breakdown: The computed Work Breakdown Structure (WBS) for the project.\n    roi_justification: The Return on Investment (ROI) justification, including\n        detailed calculations for both hard and soft savings.'}."""
    commercial_name: Optional[str] = Field(None, description="The formal project name, optimized for executive-level communication and impact.")
    project_description: str = Field(..., description="An executive summary of the project, articulated in non-technical business language for a CIO-level audience.")
    smart_objectives: str = Field(..., description="A set of quantifiable SMART (Specific, Measurable, Achievable, Relevant, Time-bound) objectives.")
    in_scope: list[str] = Field(..., description="A strict definition of all in-scope items and deliverables for the project.")
    out_of_scope: list[str] = Field(..., description="A definition of project boundaries, explicitly listing all out-of-scope items to prevent scope creep.")
    governance_roles: list[str] = Field(..., description="A list of key stakeholder profiles and a basic RACI (Responsible, Accountable, Consulted, Informed) matrix.")
    critical_risks: list[str] = Field(..., description="A list of identified technical and operational execution risks, with corresponding mitigation strategies for each.")
    wbs_breakdown: list[WorkBreakdownStructureTask] = Field(..., description="The computed Work Breakdown Structure (WBS) for the project.")
    roi_justification: str = Field(..., description="The Return on Investment (ROI) justification, including detailed calculations for both hard and soft savings.")


class PillarBlueprintDraft(BaseModel):
    """Represents a draft architectural blueprint for a specific pillar.

    This model captures a comprehensive analysis of an architectural pillar,
    including its current state (AS-IS), a desired future state (TO-BE), and the
    projects required to bridge the gap. It serves as a structured container for
    architectural assessment and planning.

    Attributes:
        thought_process: A free-form, step-by-step articulation of the
            architectural analysis and reasoning (Chain of Thought) that precedes
            the final JSON object construction.
        pilar_id: The unique identifier for the architectural pillar.
        pilar_name: The human-readable name of the architectural pillar.
        score: The current calculated score for the pillar's health or maturity.
        target_score: The desired target score for the pillar's health or maturity.
        asis_architecture_description: A comprehensive technical narrative detailing
            the current state (AS-IS) architecture, inventory, and topology for
            the pillar, preceding the risk enumeration.
        health_check_asis: A list of structured health check results for the
            current AS-IS architecture.
        target_architecture_tobe: A data structure describing the target (TO-BE)
            architecture.
        projects_todo: A list of projects identified to transition from the AS-IS
            to the TO-BE architecture.
    """
    thought_process: str = Field(
        description="A free-form, step-by-step articulation of the architectural analysis and reasoning (Chain of Thought) that precedes the final JSON object construction."
    )
    pilar_id: str
    pilar_name: str
    score: float = 0.0
    target_score: float = 4.0
    asis_architecture_description: str = Field(
        default="Descripción no disponible.",
        description="A comprehensive technical narrative (minimum 3 paragraphs) detailing the current state (AS-IS) architecture, inventory, and topology for the pillar, preceding the risk enumeration."
    )
    health_check_asis: list[HealthCheckAsIs]
    target_architecture_tobe: TargetArchitectureToBe
    projects_todo: list[ProjectToDo]


class ExecutiveSnapshot(BaseModel):
    """Represents a high-level executive summary of a project wave.

    Attributes:
        bottom_line: The key takeaway or summary statement for the wave.
        decisions: A list of the 2-3 most critical project names. Each name must
            be a verbatim copy of a 'name' field from the 'projects_todo' list in
            its corresponding pillar.
        cost_of_inaction: A description of the negative consequences of not
            proceeding with the proposed actions.
        structural_risks: A list of potential structural risks or long-term
            challenges.
        business_impact: An assessment of the overall impact on the business.
        operational_benefits: A list of the expected benefits to operational
            efficiency.
        transformation_complexity: An evaluation of the complexity involved in the
            transformation.
    """
    bottom_line: str
    decisions: list[str] = Field(
        ...,
        description="A list of the 2-3 most critical project names for this wave. Each name must be a verbatim copy of a 'name' field from the 'projects_todo' list in its corresponding pillar."
    )
    cost_of_inaction: str
    structural_risks: list[str]
    business_impact: str
    operational_benefits: list[str]
    transformation_complexity: str


class CrossCapabilitiesAnalysis(BaseModel):
    """Model the analysis of common patterns and debts across capabilities."""
    common_deficiency_patterns: list[str]
    transformation_paradigm: str
    critical_technical_debt: str


class RoadmapWave(BaseModel):
    """Models a single, time-bound wave within a transformation roadmap.

    Each wave is defined by a unique identifier and contains a list of projects
    scheduled for that period.

    Attributes:
        wave (str): The identifier for the transformation wave, which typically
            includes a time frame (e.g., 'Wave 1: 0-6m').
        projects (list[str]): A list of project names assigned to this wave.
            This field is governed by a strict closed-extraction contract and
            must only contain project names that are explicitly and identically
            present in the source `projects_todo` list. Adding project names not
            found in the source is prohibited.
    """
    wave: str = Field(..., description="The identifier for the transformation wave, such as 'Wave 1: 0-6m'.")
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
    """Models an external dependency of one technical project on another.

    This class defines the data structure for tracking a dependency, linking a
    dependent project to its prerequisite and requiring a clear justification for
    the relationship.

    Attributes:
        project: The unique identifier of the project that has the dependency.
        depends_on: The unique identifier of the prerequisite project. Generic
            identifiers (e.g., 'T3-Networks') are disallowed; a specific,
            formal project name is required.
        reason: A human-readable explanation for why the dependency exists.
    """
    project: str = Field(..., description="The unique name of the technical project that possesses this dependency.")
    depends_on: str = Field(..., description="The unique name of the prerequisite project or enabling initiative. Generic identifiers (e.g., 'T3-Networks') are disallowed; a specific, formal project name is required.")
    reason: str


class OrchestratorBlueprintDraft(VersionedPayload):
    """A data model for a draft architectural solution blueprint.

    This model captures the essential components of a proposed architecture, including
    a high-level summary, design principles, capability analysis, implementation
    roadmap, and external dependencies.

    Attributes:
        executive_snapshot (ExecutiveSnapshot): A high-level, executive-facing
            summary of the proposed solution.
        design_principles (list[str]): A set of 3 to 7 cross-cutting architectural
            design principles governing the solution. These principles must align
            with the client's established Architectural Profile.
        cross_capabilities_analysis (CrossCapabilitiesAnalysis): An analysis of the
            interplay and dependencies between different solution capabilities.
        roadmap (list[RoadmapWave]): A sequence of implementation phases, defining
            the staged rollout of the solution.
        external_dependencies (list[ExternalDependency]): A list of dependencies on
            systems, teams, or resources external to the core solution.
    """
    executive_snapshot: ExecutiveSnapshot
    design_principles: list[str] = Field(
        ...,
        description="A set of 3 to 7 cross-cutting architectural design principles governing the solution. These principles must align with the client's established Architectural Profile (e.g., Sovereign Cloud, Cloud-Native)."
    )
    cross_capabilities_analysis: CrossCapabilitiesAnalysis
    roadmap: list[RoadmapWave]
    external_dependencies: list[ExternalDependency]


class BlueprintDocumentMeta(BaseModel):
    """Model the core metadata for a blueprint document."""
    client_name: str
    tower_name: str
    tower_code: str
    financial_tier: str
    transformation_horizon: str


class BlueprintPayload(OrchestratorBlueprintDraft):
    """Represents the comprehensive data payload for a blueprint analysis.

    This Pydantic model extends `OrchestratorBlueprintDraft` to include detailed
    document metadata, a structured analysis for each pillar, and a final
    consolidated risk assessment score, the Annualized Loss Expectancy (ALE).

    Attributes:
        document_meta: An instance of `BlueprintDocumentMeta` containing metadata
            for the source document.
        pillars_analysis: A list of `PillarBlueprintDraft` objects, where each
            object contains the detailed analysis for a specific pillar.
        total_fair_ale: The consolidated Annualized Loss Expectancy (ALE)
            calculated from all pillars, denominated in Euros (EUR). This
            value is `None` if the calculation has not been performed.
    """
    document_meta: BlueprintDocumentMeta
    pillars_analysis: list[PillarBlueprintDraft]
    total_fair_ale: Optional[float] = Field(None, description="The consolidated Annualized Loss Expectancy (ALE), denominated in Euros (EUR).")
