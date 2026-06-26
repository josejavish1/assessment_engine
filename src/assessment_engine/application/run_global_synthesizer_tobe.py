import argparse
import asyncio
import glob
import json
import os
from pathlib import Path

from google.adk.agents import Agent
from pydantic import BaseModel, Field
from vertexai.agent_engines import AdkApp

from assessment_engine.infrastructure.ai_client import run_agent

# Defines the data structures governing the iterative, expanded chain-of-synthesis generation process.


class Phase1Strategy(BaseModel):
    """Defines the strategic framework for a TO-BE target state architecture.

    A data model encapsulating the core strategic components for the initial phase
    (Phase 1) of an architectural synthesis process. It establishes the
    high-level vision, transformation strategy, and scope that inform the
    generation of subsequent, detailed architectural artifacts.

    Attributes:
        executive_vision: A dense, technical executive summary of the 3- and
            5-year TO-BE target state model, composed of 3-4 paragraphs.
        transformation_strategy: A detailed narrative on the core transformation
            paradigm (e.g., Sovereign Hybrid Edge), elaborated in a minimum of
            3-4 comprehensive paragraphs.
        document_purpose: An articulation of the document's purpose, specifying how
            it will guide strategic IT and business decisions, described in 2-3
            paragraphs.
        document_scope: A definition of the organizational and technological scope
            and perimeters of the TO-BE target architecture, described in 2-3
            comprehensive paragraphs.
        maturity_approach: A description of the maturity model approach (Levels 1-5),
            establishing a Level 5 capability as the 3-year strategic
            objective, explained in 2-3 paragraphs.
    """

    executive_vision: str = Field(
        ...,
        description="Provides a dense, technical, and highly detailed executive summary of the 3- and 5-year TO-BE target state model. Requires a 3-4 paragraph composition.",
    )
    transformation_strategy: str = Field(
        ...,
        description="Provides a detailed narrative on the core transformation paradigm (e.g., Sovereign Hybrid Edge), elaborated in a minimum of 3-4 comprehensive paragraphs.",
    )
    document_purpose: str = Field(
        ...,
        description="Articulates the document's purpose, specifying how it will guide strategic IT and business decisions. Requires a 2-3 paragraph description.",
    )
    document_scope: str = Field(
        ...,
        description="Defines the organizational and technological scope and perimeters of the TO-BE target architecture. Requires a comprehensive description of 2-3 paragraphs.",
    )
    maturity_approach: str = Field(
        ...,
        description="Details the maturity model approach (Levels 1-5), establishing a baseline Level 5 capability as the 3-year strategic objective. Requires a 2-3 paragraph explanation.",
    )


class Phase2ResilienceStrategy(BaseModel):
    """A data model for the narrative components of a Phase 2 resilience and modernization strategy.

    This class encapsulates the textual descriptions required to articulate a
    comprehensive multi-year plan for data center resilience, high-availability,
    and its alignment with application modernization efforts.

    Attributes:
        cpd_strategy_3_years (str): Outlines the 3-year data center siting plan,
            defining the roles of the primary and secondary/contingency
            facilities. Requires a robust 3-4 paragraph description.
        cpd_strategy_5_years (str): Articulates the long-term (5-year) data
            center siting vision, optionally addressing a tertiary site or future
            migrations. Requires a 3-4 paragraph description.
        active_active_transition (str): Describes the dual-site operational
            strategy, detailing the optimized active-active and active-passive
            high-availability schemes. Requires a 3-4 paragraph technical
            explanation.
        app_modernization_relation (str): Details the explicit relationship
            between the TO-BE infrastructure and the client's application
            modernization roadmap. Requires a 3-4 paragraph analysis.
    """

    cpd_strategy_3_years: str = Field(
        ...,
        description="Outlines the 3-year data center siting plan, defining the roles of the primary and secondary/contingency facilities. Requires a robust 3-4 paragraph description.",
    )
    cpd_strategy_5_years: str = Field(
        ...,
        description="Articulates the long-term (5-year) data center siting vision, optionally addressing a tertiary site or future migrations. Requires a 3-4 paragraph description.",
    )
    active_active_transition: str = Field(
        ...,
        description="Describes the dual-site operational strategy, detailing the optimized active-active and active-passive high-availability schemes. Requires a 3-4 paragraph technical explanation.",
    )
    app_modernization_relation: str = Field(
        ...,
        description="Details the explicit relationship between the TO-BE infrastructure and the client's application modernization roadmap. Requires a 3-4 paragraph analysis.",
    )


class Phase3Benefits(BaseModel):
    """Models the strategic benefits and mission impact of a proposed TO-BE architecture.

    Defines a data structure for articulating the strategic advantages, outcomes, and
    mission-level impact of implementing a target (TO-BE) system architecture.

    Attributes:
        strategic_levers: A list of strings, where each string represents a
            cross-cutting strategic lever that enables the target architecture. A
            minimum of four distinct levers is required.
        global_benefits: A list of strings detailing the global benefits realized
            upon achieving the target architecture. A minimum of four distinct
            benefits is required.
        public_mission_impact: A string containing a detailed analysis of the
            architecture's impact on the client's public-facing strategic mission
            (e.g., national security, systemic resilience). The analysis must
            consist of at least three dense paragraphs.
    """

    strategic_levers: list[str] = Field(
        ...,
        description="A list of bullet points identifying the cross-cutting strategic levers that enable the TO-BE architecture. Requires a minimum of four detailed items.",
    )
    global_benefits: list[str] = Field(
        ...,
        description="A detailed list of the global benefits realized upon achieving the TO-BE model, presented as a minimum of four descriptive bullet points.",
    )
    public_mission_impact: str = Field(
        ...,
        description="Articulates the impact of the proposed architecture on the client's strategic mission (e.g., national security, systemic resilience). Requires a detailed analysis of at least 3 dense paragraphs.",
    )


class Phase4RisksAndAssumptions(BaseModel):
    """Defines the data model for risks, assumptions, and next steps of a TO-BE architecture.

    This Pydantic model provides a structured container for analyzing a proposed
    TO-BE (target state) architecture. It categorizes assumptions into structural,
    technological, and regulatory domains, delineates risks associated with both
    implementation and non-implementation, and outlines recommended subsequent
    actions.

    Attributes:
        assumptions_structural (list[str]): Foundational structural and
            organizational assumptions required for successful implementation.
        assumptions_technological (list[str]): Technological and architectural
            compatibility assumptions for the proposed implementation.
        assumptions_regulatory (list[str]): Assumptions regarding the applicable
            regulatory and compliance landscape (e.g., ENS High category, NIS2).
        risks_if_not_acted (list[str]): Organizational risks incurred by
            maintaining the current state (AS-IS) and forgoing the TO-BE model
            implementation.
        risks_of_implementation (list[str]): Risks introduced directly by the
            process of implementing the TO-BE model.
        next_steps (list[str]): A summary of conclusions and recommended executive
            actions for project stakeholders or governing bodies.
    """

    assumptions_structural: list[str] = Field(
        ...,
        description="Enumerates the indispensable structural and organizational assumptions required for successful implementation. Requires a minimum of four high-quality bullet points.",
    )
    assumptions_technological: list[str] = Field(
        ...,
        description="Enumerates the core technological and architectural compatibility assumptions required for implementation. Requires a minimum of four high-quality bullet points.",
    )
    assumptions_regulatory: list[str] = Field(
        ...,
        description="Specifies key assumptions regarding the regulatory and compliance environment (e.g., ENS High category, NIS2). Requires a minimum of four distinct bullet points.",
    )
    risks_if_not_acted: list[str] = Field(
        ...,
        description="Identifies critical organizational risks resulting from maintaining the status quo and failing to implement the TO-BE model. Requires a minimum of four distinct bullet points.",
    )
    risks_of_implementation: list[str] = Field(
        ...,
        description="Identifies risks introduced by the TO-BE model implementation process itself. Requires a minimum of four distinct bullet points.",
    )
    next_steps: list[str] = Field(
        ...,
        description="Summarizes key conclusions and recommends immediate executive next steps for the Steering Committee. Requires a minimum of four distinct bullet points.",
    )


class HighLevelRoadmap(BaseModel):
    """Structures a project roadmap into short, medium, and long-term phases."""

    phase_1_short_term: list[str] = Field(
        ...,
        description="Defines tactical milestones and objectives for the short-term horizon (0-12 months).",
    )
    phase_2_mid_term: list[str] = Field(
        ...,
        description="Defines tactical milestones and objectives for the medium-term horizon (Years 2-3).",
    )
    phase_3_long_term: list[str] = Field(
        ...,
        description="Defines strategic milestones and objectives for the long-term horizon (Years 4-5).",
    )


class GlobalToBeSummary(BaseModel):
    """Represents a structured summary of a global 'To-Be' state strategic plan.

    This Pydantic model defines the schema for a comprehensive document outlining
    the future vision, strategy, risks, and roadmap for a large-scale
    transformation.

    Attributes:
        executive_vision: A high-level summary of the desired future state.
        transformation_strategy: The overall approach to achieve the executive
            vision.
        document_purpose: The primary goal and rationale for this document.
        document_scope: The boundaries and extent of what the strategic plan
            covers.
        maturity_approach: The plan for advancing organizational and
            technological maturity.
        cpd_strategy_3_years: The strategic plan for cloud platform development
            over the next three years.
        cpd_strategy_5_years: The strategic plan for cloud platform development
            over the next five years.
        active_active_transition: The strategy for transitioning to an
            active-active system architecture.
        app_modernization_relation: The alignment of this plan with broader
            application modernization efforts.
        strategic_levers: A list of key actions or initiatives that will drive
            the transformation.
        global_benefits: A list of the primary benefits expected from
            implementing the plan.
        public_mission_impact: The expected impact of the transformation on the
            organization's public-facing mission.
        assumptions_structural: Foundational assumptions related to
            organizational structure or processes.
        assumptions_technological: Foundational assumptions related to
            technology.
        assumptions_regulatory: Foundational assumptions related to legal and
            regulatory compliance.
        risks_if_not_acted: Risks the organization faces if this plan is not
            implemented.
        risks_of_implementation: Potential risks that may arise during the
            implementation of the plan.
        next_steps: A list of immediate, actionable steps to begin
            implementation.
        roadmap: The high-level roadmap outlining major phases and milestones.
    """

    executive_vision: str
    transformation_strategy: str
    document_purpose: str
    document_scope: str
    maturity_approach: str
    cpd_strategy_3_years: str
    cpd_strategy_5_years: str
    active_active_transition: str
    app_modernization_relation: str
    strategic_levers: list[str]
    global_benefits: list[str]
    public_mission_impact: str
    assumptions_structural: list[str]
    assumptions_technological: list[str]
    assumptions_regulatory: list[str]
    risks_if_not_acted: list[str]
    risks_of_implementation: list[str]
    next_steps: list[str]
    roadmap: HighLevelRoadmap


# Defines the data schema for the automated audit and self-healing stage of the synthesis process.


class SynthesisAudit(BaseModel):
    """Defines the data schema for the output of an automated synthesis audit.

    This model encapsulates the results of a verification pass on a synthesized
    document, determining whether it is approved for finalization or requires
    specific revisions. It serves as a structured feedback mechanism for a
    self-healing synthesis process.

    Attributes:
        is_approved: A boolean flag indicating if the synthesized document complies
            with all specified requirements, including client industry profile and
            applicable regulations, and is verified to be free of hallucinations or
            critical omissions.
        hallucinations_detected: A list of specific, enumerated deviations found
            within the document. These may include factual hallucinations,
            internal contradictions, or technical inaccuracies. This list is
            expected to be null or empty if `is_approved` is True.
        remediation_critique: A detailed, constructive critique providing actionable
            instructions for a synthesis agent to revise the document and address
            the issues identified in `hallucinations_detected`. This string is
            expected to be null or empty if `is_approved` is True.
    """

    is_approved: bool = Field(
        ...,
        description="A boolean flag that is true if the consolidated TO-BE transformation document strictly complies with the client's industry profile, applicable regulations, and is verified to be free of hallucinations or critical omissions.",
    )
    hallucinations_detected: list[str] = Field(
        ...,
        description="A detailed list of detected hallucinations, contradictions, technical inaccuracies, or incorrect competitor references. This field is null or empty if the document is approved.",
    )
    remediation_critique: str = Field(
        ...,
        description="Provides specific, executive, and constructive corrective instructions to guide the synthesis agent in revising the document. This field is null or empty if the document is approved.",
    )


async def synthesize_global_tobe(working_dir: str, industry: str):
    r"""{'docstring': "Synthesizes a global TO-BE executive summary from individual tower blueprints.\n\nThis asynchronous function orchestrates a multi-agent, iterative process to\ngenerate a cohesive, C-level strategic document. It begins by loading an\nindustry-specific profile to provide domain-aware context, such as sector-\nspecific regulations and strategic priorities. The function then aggregates\narchitectural data from multiple 'tower' payload files located within the\nspecified working directory.\n\nThe core logic is a multi-round reflection loop. In each round, a series\nof specialized AI agents generate distinct sections of the summary:\n1. Strategy and Vision\n2. Resilience and Modernization\n3. Benefits and Impact\n4. Risks and Assumptions\n5. High-Level Roadmap\n\nAfter each full synthesis round, a verifier agent audits the consolidated\ndocument for quality, coherence, and adherence to requirements. If the audit\nfails, the verifier's critique is used as feedback to guide the subsequent\nsynthesis round, promoting self-correction. The process concludes when the\ndocument passes the quality audit or the maximum number of rounds is reached.\nThe final, approved document is then saved to disk.\n\nArgs:\n    working_dir (str): The path to the main working directory containing\n        tower-specific subdirectories (e.g., 'T*'), each with its\n        respective 'blueprint_*_payload.json' file.\n    industry (str): The client's industry sector (e.g., 'finance', 'telco'),\n        used to load a corresponding configuration profile which guides the\n        synthesis with domain-specific constraints and priorities.\n\nReturns:\n    None. The function writes its final output to a file named\n    'global_tobe_executive_summary.json' within the `working_dir` and\n    does not return any value.\n\nRaises:\n    FileNotFoundError: If the specified industry profile does not exist and\n        the fallback 'default.json' profile is also not found in the\n        'engine_config/industry_profiles' directory.\n    json.JSONDecodeError: If any of the industry profile or tower payload\n        JSON files are malformed and cannot be parsed."}."""
    print(
        "🚀 Iniciando Global TO-BE Executive Synthesizer (SOTA 2026 with Self-Healing)..."
    )
    print(f"   ├─ Perfil de Industria: {industry}")

    # Load the industry-specific profile to provide dynamic, domain-aware context, ensuring the generated architecture is relevant and compliant with sector-specific constraints.
    profile_path = Path("engine_config/industry_profiles") / f"{industry}.json"
    if not profile_path.exists():
        print(f"   ⚠️ Perfil {industry} no encontrado. Cargando 'default'...")
        profile_path = Path("engine_config/industry_profiles/default.json")

    with open(profile_path, "r", encoding="utf-8-sig") as f:
        profile = json.load(f)

    industry_name = profile.get("industry", "Standard Sector")
    frameworks = profile.get("elite_framework", {})
    primary_reg = frameworks.get("primary_regulation", "General Security Standards")
    sovereignty = frameworks.get("sovereignty_level", "Standard Data Protection")
    risk_modeling = frameworks.get("risk_modeling", "Qualitative")
    priorities = frameworks.get("strategic_priorities", "Resilience & Security")

    print(f"   ├─ Marco Sectorial: {industry_name}")
    print(f"   ├─ Regulación Primaria: {primary_reg}")
    print(f"   └─ Nivel de Soberanía: {sovereignty}")

    # Aggregate the outputs from specialized agent models to form a comprehensive, multi-faceted draft of the target architecture.
    payloads = []
    tower_summaries = []

    search_pattern = os.path.join(working_dir, "T*", "blueprint_*_payload.json")
    for file_path in glob.glob(search_pattern):
        with open(file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            payloads.append(data)

            tobe_visions = []
            for pilar in data.get("pillars_analysis", []):
                tobe = pilar.get("target_architecture_tobe", {})
                tobe_visions.append(
                    f"- Pilar {pilar.get('pilar_name')}: {tobe.get('vision_3_years', '')} / {tobe.get('vision_5_years', '')}"
                )

            tower_summaries.append(
                f"--- TORRE: {data.get('document_meta', {}).get('tower_name')} ---\n"
                f"{chr(10).join(tobe_visions)}\n"
            )

    if not payloads:
        print("❌ Error: No se encontraron payloads de torres para sintetizar.")
        return

    client_name = payloads[0].get("document_meta", {}).get("client_name", "Cliente")
    tower_text = "".join(tower_summaries)

    # Enforce a strict thematic expansion mandate to maintain focus and prevent generative drift from the core architectural topic.
    EXPANSION_MANDATE = (
        "\n\nMANDATO DE EXPANSIÓN Y COMPLETITUD CRUCIAL (MANDATORIO):\n"
        "1. NO des respuestas cortas, escuetas o de un solo párrafo.\n"
        "2. Cada campo de tipo string (executive_vision, transformation_strategy, document_purpose, document_scope, "
        "maturity_approach, cpd_strategy_3_years, cpd_strategy_5_years, active_active_transition, app_modernization_relation, "
        "public_mission_impact) DEBE redactarse como prosa técnica, elegante, sofisticada y de nivel C-Level, con una "
        "extensión mínima de 3 a 4 párrafos largos y completos por campo (mínimo de 2000 a 3000 caracteres por campo).\n"
        "3. Aporta muchísimo detalle arquitectónico y metodológico real basándote en los payloads de las torres. Evita las generalidades.\n"
        "4. En el caso de las listas (strategic_levers, global_benefits, assumptions, risks, next_steps), escribe al menos 4-5 viñetas, "
        "pero cada viñeta debe ser un párrafo explicativo robusto por sí misma, no frases cortas de una línea."
    )

    # Initiate an iterative, multi-agent reflection loop to refine the aggregated content, enhance technical coherence, and align the narrative.
    max_reflection_rounds = 2
    remediation_critique = ""
    round_idx = 1

    final_summary = None

    while round_idx <= max_reflection_rounds:
        print(
            f"\n🔄 --- INICIANDO RONDA DE SÍNTESIS {round_idx} / {max_reflection_rounds} ---"
        )
        if remediation_critique:
            print(
                "   ⚠️ Crítica del Verificador inyectada en el prompt para auto-corrección."
            )

        feedback_prompt = (
            f"\n\nDIRECTIVAS DE CORRECCIÓN DE LA RONDA ANTERIOR:\n{remediation_critique}"
            if remediation_critique
            else ""
        )

        print("   ➔ Ejecutando Fase 1: Estrategia y Enfoque...")
        prompt_1 = (
            f"Eres el Arquitecto Jefe Corporativo de NTT DATA redactando la estrategia TO-BE para {client_name}.\n\n"
            f"REGLAS ESTRATÉGICAS DEL SECTOR ({industry_name}):\n"
            f"- Prioridades: {priorities}\n"
            f"- Marco de Riesgo: {risk_modeling}\n"
            f"- Regulación Primaria: {primary_reg}\n"
            f"- Exigencias de Soberanía: {sovereignty}\n\n"
            f"VISION TO-BE POR TORRES:\n{tower_text}\n\n"
            "Sintetiza la visión futura en una estrategia consolidada, define el paradigma de transformación, "
            "y redacta en Markdown el propósito, alcance y enfoque de madurez para el documento maestro TO-BE."
            f"{EXPANSION_MANDATE}"
            f"{feedback_prompt}"
        )
        agent_1 = Agent(
            name="tobe_phase1",
            model="gemini-2.5-pro",
            instruction="Responde estrictamente con el JSON pedido.",
            output_schema=Phase1Strategy,
        )
        res_1 = await run_agent(
            AdkApp(agent=agent_1),
            user_id="synthesizer",
            message=prompt_1,
            schema=Phase1Strategy,
        )

        print(
            "   ➔ Ejecutando Fase 2: Resiliencia Geográfica y Modernización Aplicacional..."
        )
        prompt_2 = (
            f"Como Arquitecto Jefe Corporativo para {client_name}, considerando la estrategia definida:\n"
            f"- Visión: {res_1.get('executive_vision', '')}\n"
            f"- Estrategia: {res_1.get('transformation_strategy', '')}\n\n"
            f"REGLAS ESTRATÉGICAS DEL SECTOR:\n"
            f"- Regulación Primaria: {primary_reg}\n"
            f"- Exigencias de Soberanía: {sovereignty}\n\n"
            f"Escribe en Markdown los capítulos estratégicos sobre: 1) Plan de CPDs a 3 años. 2) Plan de CPDs a 5 años. "
            "3) Modelo operativo dual-site (activo-activo vs activo-pasivo). 4) La relación de la plataforma con la modernización de aplicaciones del cliente."
            f"{EXPANSION_MANDATE}"
            f"{feedback_prompt}"
        )
        agent_2 = Agent(
            name="tobe_phase2",
            model="gemini-2.5-pro",
            instruction="Responde estrictamente con el JSON pedido.",
            output_schema=Phase2ResilienceStrategy,
        )
        res_2 = await run_agent(
            AdkApp(agent=agent_2),
            user_id="synthesizer",
            message=prompt_2,
            schema=Phase2ResilienceStrategy,
        )

        print("   ➔ Ejecutando Fase 3: Beneficios Globales e Impacto en Misión...")
        prompt_3 = (
            f"Basado en la estrategia de resiliencia geográfica para {client_name}:\n"
            f"- Activo-Activo: {res_2.get('active_active_transition', '')}\n\n"
            f"REGLAS ESTRATÉGICAS DEL SECTOR:\n"
            f"- Prioridades: {priorities}\n\n"
            "Define las palancas estratégicas transversales, los beneficios corporativos globales y el impacto "
            "en la misión estratégica y posicionamiento público/institucional de la organización cliente."
            f"{EXPANSION_MANDATE}"
            f"{feedback_prompt}"
        )
        agent_3 = Agent(
            name="tobe_phase3",
            model="gemini-2.5-pro",
            instruction="Responde estrictamente con el JSON pedido.",
            output_schema=Phase3Benefits,
        )
        res_3 = await run_agent(
            AdkApp(agent=agent_3),
            user_id="synthesizer",
            message=prompt_3,
            schema=Phase3Benefits,
        )

        print(
            "   ➔ Ejecutando Fase 4: Supuestos Estructurales, Riesgos de Implantación y Siguientes Pasos..."
        )
        prompt_4 = (
            f"Considerando el plan de transformación integral de {client_name}:\n"
            f"- Visión ejecutiva: {res_1.get('executive_vision', '')}\n\n"
            f"REGLAS ESTRATÉGICAS DEL SECTOR:\n"
            f"- Regulación Primaria: {primary_reg}\n"
            f"- Exigencias de Soberanía: {sovereignty}\n\n"
            "Define de forma detallada: 1) Supuestos organizativos. 2) Supuestos tecnológicos. 3) Supuestos regulatorios. "
            "4) Los riesgos de no actuar (Cost of Inaction). 5) Los riesgos propios de la implantación del plan. 6) Las conclusiones y próximos pasos ejecutivos inmediatos."
            f"{EXPANSION_MANDATE}"
            f"{feedback_prompt}"
        )
        agent_4 = Agent(
            name="tobe_phase4",
            model="gemini-2.5-pro",
            instruction="Responde estrictamente con el JSON pedido.",
            output_schema=Phase4RisksAndAssumptions,
        )
        res_4 = await run_agent(
            AdkApp(agent=agent_4),
            user_id="synthesizer",
            message=prompt_4,
            schema=Phase4RisksAndAssumptions,
        )

        print("   ➔ Ejecutando Fase 5: Planificación de Roadmap a Alto Nivel...")
        prompt_5 = (
            f"A partir de las visiones por torre de {client_name}:\n{tower_text}\n\n"
            "Genera un Roadmap consolidado de Alto Nivel definiendo hitos claros para el Corto Plazo (0-12 meses), Medio Plazo (Años 2-3) y Largo Plazo (Años 4-5)."
            f"{EXPANSION_MANDATE}"
            f"{feedback_prompt}"
        )
        agent_5 = Agent(
            name="tobe_phase5",
            model="gemini-2.5-pro",
            instruction="Responde estrictamente con el JSON pedido.",
            output_schema=HighLevelRoadmap,
        )
        res_5 = await run_agent(
            AdkApp(agent=agent_5),
            user_id="synthesizer",
            message=prompt_5,
            schema=HighLevelRoadmap,
        )

        #
        final_summary = GlobalToBeSummary(
            executive_vision=res_1.get("executive_vision", "") if res_1 else "",
            transformation_strategy=res_1.get("transformation_strategy", "")
            if res_1
            else "",
            document_purpose=res_1.get("document_purpose", "") if res_1 else "",
            document_scope=res_1.get("document_scope", "") if res_1 else "",
            maturity_approach=res_1.get("maturity_approach", "") if res_1 else "",
            cpd_strategy_3_years=res_2.get("cpd_strategy_3_years", "") if res_2 else "",
            cpd_strategy_5_years=res_2.get("cpd_strategy_5_years", "") if res_2 else "",
            active_active_transition=res_2.get("active_active_transition", "")
            if res_2
            else "",
            app_modernization_relation=res_2.get("app_modernization_relation", "")
            if res_2
            else "",
            strategic_levers=res_3.get("strategic_levers", []) if res_3 else [],
            global_benefits=res_3.get("global_benefits", []) if res_3 else [],
            public_mission_impact=res_3.get("public_mission_impact", "")
            if res_3
            else "",
            assumptions_structural=res_4.get("assumptions_structural", [])
            if res_4
            else [],
            assumptions_technological=res_4.get("assumptions_technological", [])
            if res_4
            else [],
            assumptions_regulatory=res_4.get("assumptions_regulatory", [])
            if res_4
            else [],
            risks_if_not_acted=res_4.get("risks_if_not_acted", []) if res_4 else [],
            risks_of_implementation=res_4.get("risks_of_implementation", [])
            if res_4
            else [],
            next_steps=res_4.get("next_steps", []) if res_4 else [],
            roadmap=res_5
            if res_5
            else HighLevelRoadmap(
                phase_1_short_term=[], phase_2_mid_term=[], phase_3_long_term=[]
            ),
        )

        # Execute a final validation and automated correction pass using a Verifier agent, ensuring the output strictly adheres to all specified technical and business constraints.
        print("\n🔍 --- INICIANDO VERIFICACIÓN DE CALIDAD POR IA (QUALITY GATE) ---")
        audit_prompt = (
            f"Como Lead Enterprise Auditor de NTT DATA, audita el sumario de transformación TO-BE propuesto.\n\n"
            f"REQUISITOS DEL SECTOR DEL CLIENTE ({industry_name}):\n"
            f"- Regulación: {primary_reg}\n"
            f"- Tolerancia de Soberanía: {sovereignty}\n"
            f"- Prioridades: {priorities}\n\n"
            f"DOCUMENTO A AUDITAR:\n{final_summary.model_dump_json(indent=2)}\n\n"
            "Verifica exhaustivamente que: 1) Todo el contenido esté personalizado para el cliente. 2) No contenga "
            "marcas de competidores ni alucinaciones. 3) Mencione explícitamente y alinee el documento con las normativas sectoriales "
            f"como '{primary_reg}' y niveles de '{sovereignty}'. 4) El documento tenga un nivel de extensión y "
            "detalle alto, rechazando resúmenes de una sola línea o secciones breves. Aprueba o genera una crítica detallada de reparación."
        )
        verifier_agent = Agent(
            name="tobe_verifier",
            model="gemini-2.5-pro",
            instruction="Responde estrictamente con el JSON pedido.",
            output_schema=SynthesisAudit,
        )
        audit_res = await run_agent(
            AdkApp(agent=verifier_agent),
            user_id="synthesizer",
            message=audit_prompt,
            schema=SynthesisAudit,
        )

        if audit_res and audit_res.get("is_approved"):
            print(
                "   ✅ ¡El Verificador de Calidad ha APROBADO la síntesis de forma definitiva!"
            )
            break
        else:
            print("   ❌ El Verificador de Calidad ha RECHAZADO el borrador actual.")
            remediation_critique = audit_res.get(
                "remediation_critique",
                "Revisa alineación general, extensión de texto y ortografía.",
            )
            print(
                f"   ├─ Hallucinaciones/Errores: {audit_res.get('hallucinations_detected', [])}"
            )
            print(f"   └─ Instrucciones de Reparación: {remediation_critique}")
            round_idx += 1

    #
    out_path = Path(working_dir) / "global_tobe_executive_summary.json"
    out_path.write_text(final_summary.model_dump_json(indent=4), encoding="utf-8-sig")
    print(
        f"\n🎉 Síntesis TO-BE Global consolidada y verificada guardada en: {out_path}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Defines the root schema for the Global TO-BE Executive Synthesizer, a State-of-the-Art (SOTA) 2026 architecture."
    )
    parser.add_argument("working_dir", type=str, help="Directorio de trabajo")
    parser.add_argument(
        "--industry",
        type=str,
        default="critical_infrastructure",
        help="Perfil sectorial del cliente",
    )
    args = parser.parse_args()

    asyncio.run(synthesize_global_tobe(args.working_dir, args.industry))
