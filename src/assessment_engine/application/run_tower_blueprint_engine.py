"""Defines the primary pipeline for processing blueprint payloads. This includes model-based analysis of architectural pillars, data validation against schemas, and synchronization with a central knowledge graph."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.domain.ontology_registry import OntologyRegistry
from assessment_engine.domain.prompts.blueprint_prompts import (
    get_blueprint_architect_instruction,
    get_closing_orchestrator_prompt,
    get_critic_prompt,
    get_gravity_profiler_prompt,
    get_pilar_architect_prompt,
)
from assessment_engine.domain.schemas.blueprint import (
    ArchitecturalGravityProfile,
    BlueprintPayload,
    OrchestratorBlueprintDraft,
    PillarBlueprintDraft,
)
from assessment_engine.infrastructure.ai_client import run_agent
from assessment_engine.infrastructure.client_intelligence import (
    build_client_context_packet,
    build_client_context_text,
    client_intelligence_to_legacy,
    load_client_intelligence,
)
from assessment_engine.infrastructure.entity_resolution import EntityResolutionEngine
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.runtime_paths import (
    resolve_blueprint_payload_path,
    resolve_case_input_path,
    resolve_client_dir,
    resolve_client_intelligence_path,
    resolve_tower_definition_file,
)


def sync_findings_to_graph(
    graph: EpistemicGraph,
    entity_resolver: EntityResolutionEngine,
    ontology: OntologyRegistry,
    blueprint_payload: dict,
    tower_id: str,
):
    """Populates a knowledge graph with entities and relationships from a structured blueprint payload.

    This function processes a blueprint payload by iterating through its pillars,
    risks (from `health_check_asis`), and initiatives (from `projects_todo`).
    It uses an entity resolver to generate stable semantic identifiers for each
    risk and initiative, which are then injected as nodes and relationships
    (triples) into the provided `EpistemicGraph` instance. Relationships
    created include risks impacting pillars and initiatives addressing pillars.
    External dependencies between initiatives are also parsed and added to the graph.

    Note: This function modifies the `blueprint_payload` dictionary in-place by
    adding a `node_id` key to each risk and initiative dictionary.

    Args:
        graph: The `EpistemicGraph` instance to be populated.
        entity_resolver: The component used to generate stable semantic identifiers
            for entities.
        ontology: The ontology registry for the graph. Note: This parameter is
            present in the signature but not used in the function's logic.
        blueprint_payload: A dictionary containing the structured blueprint data.
            This argument is modified in-place.
        tower_id: The unique identifier for the Tower, used as a source attribute
            for the injected graph triples.

    Returns:
        None.
    """
    _ = blueprint_payload.get("document_meta", {}).get("client_name", "generic")
    for pillar in blueprint_payload.get("pillars_analysis", []):
        pillar_id = pillar.get("pilar_id", "UNKNOWN")
        _ = pillar.get("pilar_name", "UNKNOWN")

        # Inject pillar-specific context to constrain the analysis scope for the model.
        graph.inject_triple(
            subject=pillar_id,
            predicate="BELONGS_TO_TOWER",
            object_val=tower_id,
            source="TOWER_PIPELINE",
            confidence=1.0,
        )

        #
        for hc in pillar.get("health_check_asis", []):
            finding_text = hc.get("finding", "")
            risk_id = entity_resolver.get_semantic_id(finding_text, context="RISK")
            hc["node_id"] = risk_id  #

            graph.inject_triple(
                subject=risk_id,
                predicate="IDENTIFIED_AS_GAP",
                object_val=finding_text,
                source=f"TOWER_{tower_id}",
                confidence=0.8,
                pillar=pillar_id,
            )
            graph.inject_triple(
                subject=risk_id,
                predicate="IMPACTS_PILLAR",
                object_val=pillar_id,
                source=f"TOWER_{tower_id}",
                confidence=1.0,
            )

        #
        for proj in pillar.get("projects_todo", []):
            proj_name = proj.get("name", "")
            proj_id = entity_resolver.get_semantic_id(proj_name, context="INITIATIVE")
            proj["node_id"] = proj_id  #

            graph.inject_triple(
                subject=proj_id,
                predicate="PROPOSES_INITIATIVE",
                object_val=proj_name,
                source=f"TOWER_{tower_id}",
                confidence=0.9,
                pillar=pillar_id,
                business_case=proj.get("business_case", ""),
            )

            graph.inject_triple(
                subject=proj_id,
                predicate="ADDRESSES_PILLAR",
                object_val=pillar_id,
                source=f"TOWER_{tower_id}",
                confidence=1.0,
            )

    #
    for dep in blueprint_payload.get("external_dependencies", []):
        proj_a_name = dep.get("project", "")
        proj_b_name = dep.get("depends_on", "")
        reason = dep.get("reason", "Technical dependency")

        id_a = entity_resolver.get_semantic_id(proj_a_name, context="INITIATIVE")
        id_b = entity_resolver.get_semantic_id(proj_b_name, context="INITIATIVE")

        graph.inject_triple(
            subject=id_a,
            predicate="REQUIRES_PREREQUISITE",
            object_val=id_b,
            source=f"ORCHESTRATOR_{tower_id}",
            confidence=1.0,
            reason=reason,
        )


def get_default_blueprint_payload(
    client_name, tower_name, tower_id, intel_data
) -> dict:
    """Constructs a default, schema-compliant dictionary for a blueprint payload.

    Initializes a baseline payload dictionary using provided metadata and populates
    remaining sections with default or placeholder values. This ensures a
    consistent and valid structure for subsequent processing.

    Args:
        client_name (str): The name of the client associated with the blueprint.
        tower_name (str): The name of the specific technology tower.
        tower_id (str): The unique identifier or code for the technology tower.
        intel_data (dict): A dictionary containing supplementary intelligence
            data. Expected keys include 'financial_tier' and
            'transformation_horizon'.

    Returns:
        dict: A dictionary representing the default blueprint payload, conforming
            to the required schema.
    """
    return {
        "document_meta": {
            "client_name": client_name,
            "tower_name": tower_name,
            "tower_code": tower_id,
            "financial_tier": intel_data.get("financial_tier", "Tier 2"),
            "transformation_horizon": intel_data.get(
                "transformation_horizon", "General"
            ),
        },
        "executive_snapshot": {
            "bottom_line": "Análisis estratégico pendiente de consolidación por el orquestador.",
            "decisions": [],
            "cost_of_inaction": "El retraso en la transformación mantiene los riesgos operativos actuales.",
            "structural_risks": [],
            "business_impact": "Pendiente de determinar impacto detallado.",
            "operational_benefits": [],
            "transformation_complexity": "Media (estimación base)",
        },
        "cross_capabilities_analysis": {
            "common_deficiency_patterns": [],
            "transformation_paradigm": "Evolución por dominios técnicos.",
            "critical_technical_debt": "Deuda técnica identificada en los pilares individuales.",
        },
        "roadmap": [],
        "external_dependencies": [],
        "pillars_analysis": [],
    }


async def process_pilar_blueprint(
    model_name, client_name, tower_name, pilar_data, context_str, intel_str
):
    """Asynchronously processes an architectural pillar using a two-phase generative AI pipeline.

    This function orchestrates a two-phase process to generate architectural
    findings. In the first phase, an "architect" agent produces an initial draft
    based on the provided pillar data, context, and supplementary intelligence.
    In the second phase, a "critic" agent reviews and refines this draft to
    improve technical accuracy and clarity. The context is enhanced with any
    pre-existing refined findings before being passed to the architect agent.

    Args:
        model_name (str): The identifier of the generative model to be used for
            both architect and critic agents.
        client_name (str): The name of the client for whom the blueprint is
            being generated, used in the critic phase.
        tower_name (str): The name of the architectural tower to which the pillar
            belongs.
        pilar_data (dict[str, Any]): A dictionary containing pillar data. Expected
            keys include 'id' (str), 'label' (str), 'score' (float | int),
            'answers' (dict), and an optional 'refined_findings' (dict).
        context_str (str): The primary contextual information for the analysis.
        intel_str (str): Supplementary intelligence or reference material to guide
            the generation.

    Returns:
        Optional[PillarBlueprintDraft]: An instance of `PillarBlueprintDraft`
        containing the refined findings. If the refinement (critic) phase fails
        but the initial (architect) phase succeeds, the initial draft is
        returned. Returns `None` if the initial phase fails or a critical
        exception occurs during processing.
    """
    print(f"    -> Analizando Pilar: {pilar_data['label']}...")

    pilar_id = pilar_data["id"]
    pilar_label = pilar_data["label"]
    pilar_score = pilar_data["score"]

    # Enrich the context string with refined findings, including technical standard references and supporting source text fragments.
    refined = pilar_data.get("refined_findings", {})
    refined_str = json.dumps(refined, indent=2, ensure_ascii=False) if refined else ""

    context_enhanced = f"{context_str}\n\n### ANÁLISIS REFINADO Y EVIDENCIAS DISPONIBLES:\n{refined_str}"

    answers_json = json.dumps(pilar_data["answers"], indent=2, ensure_ascii=False)
    prompt = get_pilar_architect_prompt(
        tower_name=tower_name,
        pilar_label=pilar_label,
        pilar_score=pilar_score,
        context_str=context_enhanced,
        intel_str=intel_str,
        answers_json=answers_json,
        pilar_id=pilar_id,
    )

    # Phase 1: Generate the initial set of findings from the source context.
    try:
        agent_architect = Agent(
            name="blueprint_architect",
            model=model_name,
            instruction=get_blueprint_architect_instruction(),
            output_schema=PillarBlueprintDraft,
        )
        app_architect = AdkApp(agent=agent_architect)

        raw_output = await run_agent(
            app_architect,
            user_id=f"architect_{pilar_id}",
            message=prompt,
            schema=PillarBlueprintDraft,
        )

        # Phase 2: Refine and validate the initial findings.
        if raw_output:
            agent_critic = Agent(
                name="blueprint_critic",
                model=model_name,
                instruction=get_blueprint_architect_instruction(),
                output_schema=PillarBlueprintDraft,
            )
            app_critic = AdkApp(agent=agent_critic)

            raw_output_json = json.dumps(raw_output)
            critic_prompt = get_critic_prompt(
                pilar_label=pilar_label,
                client_name=client_name,
                raw_output_json=raw_output_json,
            )
            final_output = await run_agent(
                app_critic,
                user_id=f"critic_{pilar_id}",
                message=critic_prompt,
                schema=PillarBlueprintDraft,
            )
            return final_output or raw_output
    except Exception as e:
        print(f"Error procesando pilar {pilar_label}: {e}")
    return None


async def run_tower_blueprint(client_name: Any, tower_id: Any) -> Any:
    r"""{'docstring': "Asynchronously orchestrates the generation of a client transformation blueprint.\n\n    This function coordinates a multi-stage pipeline to analyze a client's\n    current state from assessment data and produce a strategic roadmap. The\n    process integrates data ingestion, knowledge graph construction, generative AI\n    analysis with RAG-based validation, policy enforcement, and financial estimation.\n\n    The pipeline stages include:\n    1.  Data Ingestion: Loads client assessment answers, findings, and intelligence.\n    2.  Knowledge Graph Construction: Builds an epistemic graph to resolve and unify\n        context from disparate data sources.\n    3.  Constraint Profiling: Assesses architectural constraints (e.g., on-premise\n        vs. cloud preference) to guide subsequent analysis.\n    4.  Pillar Processing: Sequentially analyzes each architectural pillar using\n        generative models, validating outputs against the source corpus.\n    5.  Policy Enforcement: Applies a rules engine to the generated payload to\n        ensure compliance with architectural and business constraints.\n    6.  Orchestration and Finalization: Generates an executive summary and roadmap,\n        with a validation and retry loop to ensure logical consistency and\n        dependency resolution.\n    7.  Financial Estimation: Enriches proposed initiatives with budgetary\n        estimates derived from a deterministic rate card.\n    8.  Serialization: Validates the final data structure and writes the complete\n        blueprint payload to a JSON file.\n\n    Args:\n        client_name: The identifier for the client, used to resolve input and\n            output data paths.\n        tower_id: The identifier for the assessment tower being processed.\n\n    Returns:\n        None. The function produces its output as a side effect by writing the\n        generated blueprint to a JSON file.\n\n    Raises:\n        FileNotFoundError: If a required input file, such as the tower\n            definition or case data, is not found at its expected path.\n        json.JSONDecodeError: If a required input JSON file is malformed and\n            cannot be parsed.\n        RuntimeError: If pillar analysis fails for all pillars, the final\n            orchestration model fails after multiple retries, or the final\n            generated payload fails structural validation against its schema."}."""
    client_dir = resolve_client_dir(client_name)
    client_dir / tower_id
    case_input_path = resolve_case_input_path(client_name, tower_id)
    intel_path = resolve_client_intelligence_path(client_name)

    if not case_input_path.exists():
        print(f"Error: No se encuentra input para {tower_id}")
        return

    case_data = json.loads(case_input_path.read_text(encoding="utf-8"))
    findings_path = client_dir / tower_id / "findings.json"
    refined_findings = {}
    if findings_path.exists():
        refined_findings = json.loads(findings_path.read_text(encoding="utf-8-sig"))
    raw_intel_data = {}
    intel_data = {}
    intel_packet = {}
    if intel_path.exists():
        raw_intel_data = load_client_intelligence(intel_path)
        intel_data = client_intelligence_to_legacy(raw_intel_data)
        intel_packet = build_client_context_packet(raw_intel_data, tower_id=tower_id)

    tower_name = case_data.get("tower_name")
    context_str = case_data.get("context_summary", "")

    # Resolve logical inconsistencies in the payload knowledge graph.
    print("🧠 [Epistemic Engine] Ingestando contexto e inteligencia...")
    from assessment_engine.infrastructure.epistemic_extractor import (
        extract_triples_from_text,
    )
    from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
    from assessment_engine.infrastructure.text_utils import slugify

    graph = EpistemicGraph(client_id=slugify(client_name))
    entity_resolver = EntityResolutionEngine()
    ontology = OntologyRegistry()

    #
    if raw_intel_data:
        osint_triples = await extract_triples_from_text(
            json.dumps(raw_intel_data, ensure_ascii=False)
        )
        for t in osint_triples:
            graph.inject_triple(
                subject=t.get("subject", client_name),
                predicate=t.get("predicate", "UNKNOWN"),
                object_val=t.get("object_val", "UNKNOWN"),
                source="OSINT",
                confidence=0.4,
            )

    #
    if context_str:
        ctx_triples = await extract_triples_from_text(context_str)
        for t in ctx_triples:
            graph.inject_triple(
                subject=t.get("subject", client_name),
                predicate=t.get("predicate", "UNKNOWN"),
                object_val=t.get("object_val", "UNKNOWN"),
                source="INTERNAL_DOC",
                confidence=1.0,
            )

    # Phase 3: Reconcile signals from all data sources.
    resolved_truth = graph.get_resolved_context_string()

    #
    intel_str_tangential = json.dumps(intel_data, indent=2, ensure_ascii=False)
    intel_str = f"--- VERDAD EPISTÉMICA RESUELTA ---\n{resolved_truth}\n\n--- DATOS OSINT CRUDOS (TANGENCIALES) ---\n{intel_str_tangential}"
    #

    #
    intel_str = (
        build_client_context_text(raw_intel_data, tower_id=tower_id)
        if intel_packet
        else json.dumps(intel_data, indent=2, ensure_ascii=False)
    )

    try:
        from assessment_engine.infrastructure.config_loader import (
            resolve_model_profile_for_role,
        )

        model_name = resolve_model_profile_for_role("section_writer")["model"]
    except Exception:
        model_name = "gemini-2.5-pro"

    # Resolve data dependencies and establish processing priorities.
    print(
        "🔎 [Pre-flight] Calculando el Perfil de Gravedad Arquitectónica del cliente..."
    )
    dynamic_target_maturity = 4.0
    try:
        profiler_agent = Agent(
            name="gravity_profiler",
            model=model_name,
            instruction="Eres un analista experto que genera perfiles JSON matemáticos basados en contexto. Responde siempre con el JSON pedido.",
            output_schema=ArchitecturalGravityProfile,
        )
        app_profiler = AdkApp(agent=profiler_agent)

        gravity_prompt = get_gravity_profiler_prompt(intel_str, client_name)
        gravity_profile = await run_agent(
            app_profiler,
            user_id="gravity_profiler_agent",
            message=gravity_prompt,
            schema=ArchitecturalGravityProfile,
        )

        if gravity_profile:
            dynamic_target_maturity = gravity_profile.get(
                "recommended_target_maturity", 4.0
            )
            gravity_constraint = (
                f"\n\n⚠️ MANDATO DE GRAVEDAD ARQUITECTÓNICA (COMPLIANCE STRICTO):\n"
                f"El análisis de este cliente dicta la siguiente gravedad matemática:\n"
                f"- Peso On-Premise Obligatorio: {gravity_profile.get('on_premise_weight', 0.0) * 100}%\n"
                f"- Viabilidad Cloud-Native: {gravity_profile.get('cloud_native_weight', 0.0) * 100}%\n"
                f"- Rigurosidad Regulatoria: {gravity_profile.get('regulatory_strictness', 'Media')}\n"
                f"- Tolerancia a Vendor Lock-in: {gravity_profile.get('vendor_lockin_tolerance', 'Media')}\n"
                f"DIRECTIVA DE DISEÑO: {gravity_profile.get('strategic_directive', 'Adoptar mejor esfuerzo tecnológico')}\n"
                f"MADUREZ OBJETIVO RECOMENDADA: {dynamic_target_maturity}\n\n"
                f"DEBES respetar esta gravedad de forma absoluta. Prohibido proponer arquitecturas Cloud-Native "
                f"si el peso On-Premise o la rigurosidad regulatoria lo desaconsejan."
            )
            intel_str += gravity_constraint
            print(
                f"✅ Perfil de Gravedad Calculado: {gravity_profile.get('strategic_directive')} (Target: {dynamic_target_maturity})"
            )
    except Exception as e:
        print(
            f"⚠️ Error calculando Perfil de Gravedad: {e}. Se usará contexto estándar."
        )
    #

    #
    pillars_map = {}
    tower_def_path = resolve_tower_definition_file(tower_id)
    tower_def = json.loads(tower_def_path.read_text(encoding="utf-8"))

    for p in tower_def.get("pillars", []):
        pillars_map[p["pillar_id"]] = {
            "id": p["pillar_id"],
            "label": p["pillar_name"],
            "score": 0,
            "answers": [],
        }

    for ans in case_data.get("answers", []):
        p_id = ".".join(ans["kpi_id"].split(".")[:2])
        if p_id in pillars_map:
            pillars_map[p_id]["answers"].append(ans)

    for p_id, p_data in pillars_map.items():
        if p_data["answers"]:
            p_data["score"] = round(
                sum(float(a["value"]) for a in p_data["answers"])
                / len(p_data["answers"]),
                1,
            )
        # Integrate the refined technical standard finding into its corresponding pillar in the main payload.
        for p_find in refined_findings.get("pillar_findings", []):
            if p_find["pillar_id"] == p_id:
                p_data["refined_findings"] = p_find
                break

    print(f"🏗️ Generando Blueprint de Transformación para {tower_name}...")

    #
    blueprint_payload = get_default_blueprint_payload(
        client_name, tower_name, tower_id, intel_data
    )
    if intel_packet:
        blueprint_payload["client_context"] = intel_packet
    failed_pillars = []

    # Pillars are processed serially to prevent resource contention and to ensure the analysis of each pillar remains independent.
    for p_id in sorted(pillars_map.keys()):
        # Append the technical standard reference and the refined finding to the context string for use in subsequent processing stages.
        # Remove temporary string artifacts that were previously required for prompt formatting.
        enhanced_intel_str = intel_str

        p_result = await process_pilar_blueprint(
            model_name,
            client_name,
            tower_name,
            pillars_map[p_id],
            context_str,
            enhanced_intel_str,
        )
        if p_result:
            p_result["score"] = pillars_map[p_id]["score"]
            # The `target_score` from the client intelligence data must be preserved, overriding any model-generated values.
            from assessment_engine.infrastructure.client_intelligence import (
                get_target_maturity,
            )

            p_result["target_score"] = get_target_maturity(intel_data, tower_id, 4.0)

            blueprint_analysis = p_result.get("pillar_analysis", p_result)

            # Verify generated content against the RAG source corpus to mitigate model hallucination.
            # Create a normalized reference corpus from the input context to serve as the ground truth for validating model output.
            corpus = (
                context_str
                + " "
                + enhanced_intel_str
                + " "
                + json.dumps(pillars_map[p_id]["answers"])
            ).lower()
            import re

            corpus_clean = re.sub(r"\s+", " ", corpus)

            for finding in blueprint_analysis.get("health_check_asis", []):
                evidence = finding.get("literal_evidence", "")
                if evidence and evidence != "No se proporcionó evidencia literal.":
                    evidence_clean = re.sub(r"\s+", " ", evidence.lower())
                    # Flag generated text as a potential hallucination if it is not present in the reference corpus.
                    if evidence_clean not in corpus_clean:
                        # Validate that generated findings meet a 70% lexical similarity threshold against the source corpus as a heuristic to detect potential model hallucinations.
                        words = evidence_clean.split()
                        matched_words = sum(1 for w in words if w in corpus_clean)
                        if not words or (matched_words / len(words)) < 0.7:
                            finding["literal_evidence"] = (
                                "[ALERTA RAG] Cita literal no validada matemáticamente en el documento original."
                            )

            # Inject deterministic data from trusted systems directly into the payload, bypassing the generative analysis stages.
            refined = pillars_map[p_id].get("refined_findings", {})
            initiatives = refined.get("candidate_initiatives", [])
            if initiatives:
                if "projects_todo" not in blueprint_analysis:
                    blueprint_analysis["projects_todo"] = []
                # Validate generated findings against the reference corpus and canonical technical data to mitigate model hallucinations.
                sota_projects = []
                for idx, init in enumerate(initiatives):
                    sota_projects.append(
                        {
                            "name": init.get(
                                "title", f"Iniciativa Estratégica {idx + 1}"
                            ),
                            "business_case": "Impacto estratégico basado en la validación del Estado del Arte 2026.",
                            "tech_objective": init.get(
                                "rationale", "Evolución técnica."
                            ),
                            "deliverables": [
                                "Diseño de arquitectura de referencia.",
                                "Despliegue de Piloto controlado.",
                                "Evaluación de resultados y plan de escalado.",
                            ],
                            "sizing": "L",
                            "duration": init.get("horizon", "Mid-term"),
                        }
                    )
                blueprint_analysis["projects_todo"] = sota_projects
            #

            blueprint_payload["pillars_analysis"].append(blueprint_analysis)
        else:
            failed_pillars.append(pillars_map[p_id]["label"])

    if failed_pillars:
        print("⚠️ Pilares sin respuesta válida: " + ", ".join(failed_pillars))

    if not blueprint_payload["pillars_analysis"]:
        raise RuntimeError(
            "No se pudo generar ningún análisis de pilar para el blueprint."
        )

    # Re-map references for deterministic data to ensure payload integrity.
    # Inject pre-defined technical initiatives into the payload before finalization.
    # Ensures the orchestrator uses canonical project identifiers for roadmap generation.
    try:
        if findings_path.exists():
            refined_findings = json.loads(findings_path.read_text(encoding="utf-8-sig"))
    except Exception as read_err:
        print(f"⚠️ Warning loading findings.json for final mapping: {read_err}")

    if "pillars_analysis" in blueprint_payload:
        for p_analysis in blueprint_payload["pillars_analysis"]:
            p_id = p_analysis.get("pilar_id")
            for p_find in refined_findings.get("pillar_findings", []):
                if p_find["pillar_id"] == p_id:
                    initiatives = p_find.get("candidate_initiatives", [])
                    if initiatives:
                        sota_projects = []
                        for idx, init in enumerate(initiatives):
                            sota_projects.append(
                                {
                                    "name": init.get(
                                        "title", f"Iniciativa Estratégica {idx + 1}"
                                    ),
                                    "transformation_typology": init.get(
                                        "typology", "Core Modernization"
                                    ),
                                    "business_case": init.get("business_case", ""),
                                    "tech_objective": init.get(
                                        "rationale", "Evolución técnica."
                                    ),
                                    "deliverables": init.get("deliverables", []),
                                    "sizing": "L",
                                    "duration": init.get(
                                        "horizon", "Sin calendario detallado"
                                    ),
                                    "program_id": None,
                                }
                            )
                        p_analysis["projects_todo"] = sota_projects
                    break

    # Synchronize the processed payload with the master knowledge graph.
    print(f"🔄 Sincronizando hallazgos de {tower_id} con el Epistemic Graph...")
    sync_findings_to_graph(
        graph=graph,
        entity_resolver=entity_resolver,
        ontology=ontology,
        blueprint_payload=blueprint_payload,
        tower_id=tower_id,
    )

    # Apply registered policies to the final payload to enforce architectural and business constraints.
    # Traverse the finding and initiative graph to resolve logical and dependency inconsistencies.
    print("🛡️ [Sovereign QA] Ejecutando el Motor de Políticas Arquitectónicas...")
    try:
        from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine

        engine = SovereignPolicyEngine(graph)
        blueprint_payload = engine.compile(blueprint_payload)
    except Exception as policy_err:
        print(f"⚠️ Error ejecutando Sovereign Policy Engine: {policy_err}")

    # Calculate the Annualized Loss Expectancy (ALE) for each finding, which is a required input for the final orchestration stage.
    total_ale = 0.0
    for pilar in blueprint_payload.get("pillars_analysis", []):
        for finding in pilar.get("health_check_asis", []):
            val = finding.get("fair_ale_score")
            total_ale += float(val) if val is not None else 0.0

    # Generate the final summary and strategic roadmap from all processed findings.
    print("    -> Generando Snapshot Ejecutivo y Roadmap Estratégico...")
    closing_prompt = get_closing_orchestrator_prompt(
        tower_name=tower_name,
        pillars_analysis_json=json.dumps(blueprint_payload["pillars_analysis"]),
        intel_str=intel_str,
        total_ale=total_ale,
    )
    try:
        orchestrator_agent = Agent(
            name="blueprint_orchestrator",
            model=model_name,
            instruction=get_blueprint_architect_instruction(),
            output_schema=OrchestratorBlueprintDraft,
        )
        app_orchestrator = AdkApp(agent=orchestrator_agent)

        last_error = ""
        closing_data = None
        for attempt in range(3):
            try:
                msg = closing_prompt
                if last_error:
                    msg += f"\n\n🚨 VIOLACIÓN DE PROTOCOLO EN INTENTO ANTERIOR:\n{last_error}\nCorrige el texto inmediatamente.\n"
                closing_data = await run_agent(
                    app_orchestrator,
                    user_id="master_orchestrator",
                    message=msg,
                    schema=OrchestratorBlueprintDraft,
                )

                if closing_data:
                    import difflib

                    from assessment_engine.infrastructure.governance import (
                        StructuralIntegrityGate,
                    )

                    StructuralIntegrityGate.verify_dossier_logic(closing_data)

                    # Validate consistency of scoring and financial metrics.
                    #
                    valid_project_names = [
                        proj["name"]
                        for pilar in blueprint_payload.get("pillars_analysis", [])
                        for proj in pilar.get("projects_todo", [])
                    ]

                    def fuzzy_match(name, choices, cutoff=0.6):
                        """Find the single best fuzzy string match from a sequence of choices."""
                        matches = difflib.get_close_matches(
                            name, choices, n=1, cutoff=cutoff
                        )
                        return matches[0] if matches else None

                    #
                    invalid_deps = []
                    for dep in closing_data.get("external_dependencies", []):
                        dep_name = dep.get("depends_on")
                        if dep_name not in valid_project_names and dep_name not in [
                            "Independiente",
                            "Ninguna",
                        ]:
                            corrected = fuzzy_match(dep_name, valid_project_names)
                            if corrected:
                                dep["depends_on"] = corrected
                            else:
                                invalid_deps.append(dep_name)

                    if invalid_deps:
                        raise ValueError(
                            f"HAS INVENTADO DEPENDENCIAS. Los siguientes proyectos habilitadores no existen en la lista de proyectos aprobados: {invalid_deps}. Solo puedes usar proyectos reales."
                        )

                    #
                    invalid_roadmap = []
                    mapped_projects = set()
                    for wave in closing_data.get("roadmap", []):
                        corrected_projects = []
                        for proj in wave.get("projects", []):
                            if proj not in valid_project_names:
                                corrected = fuzzy_match(proj, valid_project_names)
                                if corrected:
                                    corrected_projects.append(corrected)
                                    mapped_projects.add(corrected)
                                else:
                                    invalid_roadmap.append(proj)
                            else:
                                corrected_projects.append(proj)
                                mapped_projects.add(proj)
                        wave["projects"] = corrected_projects

                    if invalid_roadmap:
                        raise ValueError(
                            f"HAS INVENTADO PROYECTOS EN EL ROADMAP. Los siguientes proyectos no existen en la lista de proyectos aprobados: {invalid_roadmap}."
                        )

                    missing_projects = set(valid_project_names) - mapped_projects
                    if missing_projects:
                        raise ValueError(
                            f"HAS OMITIDO PROYECTOS DEL ROADMAP. Regla inquebrantable rota. Debes incluir TODOS los proyectos. Te has dejado estos: {list(missing_projects)}"
                        )

                    # Validate the architectural principle count against the expected number (Ref: Quality Gap 1).
                    principles = closing_data.get("design_principles", [])
                    if len(principles) > 10:
                        raise ValueError(
                            f"Demasiados principios de diseño ({len(principles)}). Condénsalos en un máximo de 5 a 7 principios maestros transversales para toda la torre."
                        )

                    blueprint_payload.update(closing_data)
                    break
            except Exception as e:
                last_error = str(e)
                print(
                    f"    🚨 VIOLACIÓN DIPLOMÁTICA O ERROR: {e}. Reintentando Orquestador (Intento {attempt + 1})..."
                )
        if last_error and closing_data:
            print(
                "⚠️ Fallo crítico en el Orquestador tras 3 intentos. Aplicando Degradación Elegante (Borrando dependencias inventadas y añadiendo proyectos huérfanos)..."
            )
            # Remove invalid project dependencies to maintain the integrity of the dependency graph.
            valid_deps = [
                d
                for d in closing_data.get("external_dependencies", [])
                if d.get("depends_on") in valid_project_names
                or d.get("depends_on") in ["Independiente", "Ninguna"]
            ]
            closing_data["external_dependencies"] = valid_deps

            # Append unmapped projects to the final roadmap wave for manual review to prevent data loss.
            import difflib

            def f_match(name, choices, cutoff=0.6):
                """Return the single best fuzzy match for a string from an iterable of choices."""
                m = difflib.get_close_matches(name, choices, n=1, cutoff=cutoff)
                return m[0] if m else None

            mapped_projs = set()
            for wave in closing_data.get("roadmap", []):
                c_projs = []
                for p in wave.get("projects", []):
                    if p in valid_project_names:
                        c_projs.append(p)
                        mapped_projs.add(p)
                    else:
                        cor = f_match(p, valid_project_names)
                        if cor:
                            c_projs.append(cor)
                            mapped_projs.add(cor)
                wave["projects"] = c_projs

            missing_projects = list(set(valid_project_names) - mapped_projs)
            if missing_projects and closing_data.get("roadmap"):
                closing_data["roadmap"][-1]["projects"].extend(missing_projects)

            blueprint_payload.update(closing_data)
    except Exception as e:
        raise RuntimeError(f"Error en agente de cierre blueprint: {e}") from e

    # Enrich initiative charters with budgetary and resource estimates.
    print("💼 [Bid Manager] Enriqueciendo proyectos con WBS, TCO, y ROI...")
    try:
        from assessment_engine.infrastructure.config_loader import load_rate_card
        rate_data = load_rate_card()

        from assessment_engine.domain.prompts.blueprint_prompts import (
            get_bid_manager_prompt,
        )
        from assessment_engine.domain.schemas.blueprint import ProjectCharterEnrichment

        bid_manager_agent = Agent(
            name="bid_manager_architect",
            model=model_name,
            instruction="Eres el Bid Manager de NTT DATA. Devuelve estrictamente el JSON pedido.",
            output_schema=ProjectCharterEnrichment,
        )
        app_bid_manager = AdkApp(agent=bid_manager_agent)

        async def enrich_project(p_analysis_idx, proj_idx, proj):
            """Asynchronously enriches a project with a generative model and financial data.

            This coroutine augments a given project dictionary. It first resolves the
            textual description and financial impact (FAIR ALE) of any mitigated risk
            by searching the global `blueprint_payload` object. It then invokes a
            generative model to produce a detailed project charter, including a Work
            Breakdown Structure (WBS).

            Financial metrics are calculated based on a `rate_card.json` configuration
            file. The function computes the total cost from the WBS, applies a standard
            margin to determine the OpEx (sell price), and provides a parametric estimate
            for CapEx based on the project's size. All monetary values are formatted
            as strings for presentation.

            If the generative model proposes a new `commercial_name`, the function
            updates the project's name and performs a cascading update across the
            `roadmap` and `external_dependencies` sections of the global
            `blueprint_payload` to ensure referential integrity.

            Note: This function operates via side effects, modifying the global
            `blueprint_payload` dictionary in-place.

            Args:
                p_analysis_idx (int): Index of the parent pillar analysis within the
                    `blueprint_payload["pillars_analysis"]` list.
                proj_idx (int): Index of the project within the pillar analysis's
                    `projects_todo` list.
                proj (Dict[str, Any]): The project dictionary to be enriched.

            Returns:
                None. The function modifies the global `blueprint_payload` object
                in-place.

            Raises:
                KeyError: If essential keys are absent from the `proj` dictionary or
                    the `blueprint_payload` structure.
                IndexError: If `p_analysis_idx` or `proj_idx` are outside the valid
                    bounds of their respective lists.
                json.JSONDecodeError: If the `rate_card.json` file contains malformed
                    JSON.
            """
            #
            mitigated_risk_text = "N/A"
            fair_ale = 0.0
            if proj.get("mitigates_risk_id"):
                for p_ana in blueprint_payload.get("pillars_analysis", []):
                    for hc in p_ana.get("health_check_asis", []):
                        if hc.get("node_id") == proj.get("mitigates_risk_id"):
                            mitigated_risk_text = f"[{hc.get('capability', hc.get('target_state'))}] {hc.get('finding', hc.get('risk_observed'))} -> Riesgo: {hc.get('business_risk', hc.get('impact'))}"
                            fair_ale = hc.get("fair_ale_score", 0.0)
                            break

            if fair_ale > 0:
                mitigated_risk_text += f" | FAIR ALE: {fair_ale:,.2f} €"

            prompt = get_bid_manager_prompt(
                client_name=client_name,
                project_name=proj.get("name", ""),
                project_objective=proj.get("tech_objective", ""),
                project_sizing=proj.get("sizing", "M"),
                mitigated_risk_impact=mitigated_risk_text,
            )

            enrichment_data = await run_agent(
                app_bid_manager,
                user_id=f"bid_manager_{proj.get('node_id', proj_idx)}",
                message=prompt,
                schema=ProjectCharterEnrichment,
            )
            if enrichment_data:
                try:
                    rates = rate_data.get("tarifas_hora", {})
                    margin = rate_data.get("margenes", {}).get("consultoria", 0.45)

                    total_cost = 0.0
                    for task in enrichment_data.get("wbs_breakdown", []):
                        profile = task.get("required_profile", "experto")
                        hours = task.get("estimated_hours", 0)
                        rate = rates.get(
                            profile, 58
                        )  # If the primary model fails, reroute the request to the 'experto' model configuration as a fallback.
                        total_cost += hours * rate

                    sell_price = total_cost / (1 - margin)
                    enrichment_data["opex_estimate"] = (
                        f"{sell_price:,.2f} €".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )

                    sizing = proj.get("sizing", "M").upper()
                    if sizing in ["L", "XL"]:
                        enrichment_data["capex_estimate"] = (
                            "~150.000,00 € (Estimación paramétrica de licenciamiento Enterprise / Nodos físicos)"
                        )
                    else:
                        enrichment_data["capex_estimate"] = (
                            "Bajo / Nulo (Suscripciones cloud menores a 20.000€)"
                        )

                except Exception as finops_err:
                    print(f"⚠️ Error calculando FinOps matemático: {finops_err}")

                if (
                    "commercial_name" in enrichment_data
                    and enrichment_data["commercial_name"]
                ):
                    old_name = proj["name"]
                    new_name = enrichment_data["commercial_name"]
                    proj["name"] = new_name

                    #
                    for wave in blueprint_payload.get("roadmap", []):
                        wave["projects"] = [
                            new_name if p == old_name else p
                            for p in wave.get("projects", [])
                        ]

                    #
                    for d in blueprint_payload.get("external_dependencies", []):
                        if d.get("project") == old_name:
                            d["project"] = new_name
                        if d.get("depends_on") == old_name:
                            d["depends_on"] = new_name

                blueprint_payload["pillars_analysis"][p_analysis_idx]["projects_todo"][
                    proj_idx
                ].update(enrichment_data)

        enrichment_tasks = []
        for p_idx, p_analysis in enumerate(
            blueprint_payload.get("pillars_analysis", [])
        ):
            for proj_idx, proj in enumerate(p_analysis.get("projects_todo", [])):
                enrichment_tasks.append(enrich_project(p_idx, proj_idx, proj))

        if enrichment_tasks:
            await asyncio.gather(*enrichment_tasks)
            print("✅ Enriquecimiento de Bid Manager completado.")
    except Exception as bid_err:
        print(f"⚠️ Error en Bid Manager Agent: {bid_err}")

    # Remove client name placeholders from all generated text before finalization.
    # Remove bracketed, generic placeholders from model-generated text.
    def scrub_client_placeholders(obj, name):
        r"""{'docstring': 'Recursively substitutes client placeholders within a nested data structure.\n\n    Traverses dictionaries and lists, recursively processing their elements. For\n    any string value encountered, this function replaces all occurrences of a\n    predefined set of placeholders with the provided name. The specific\n    placeholders targeted for replacement are `[Cliente]`, `[CLIENTE]`,\n    `[cliente]`, `[CLIENT]`, and `[client]`. Data types other than\n    dictionaries, lists, or strings are returned unmodified.\n\n    Args:\n        obj (dict | list | Any): The data structure to traverse. Can be a\n            dictionary, list, or any other data type.\n        name (str): The string to substitute for the client placeholders.\n\n    Returns:\n        (dict | list | Any): A new data structure with the same type and nesting\n            as `obj`, where all string placeholders have been replaced.'}."""
        if isinstance(obj, dict):
            return {k: scrub_client_placeholders(v, name) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [scrub_client_placeholders(x, name) for x in obj]
        elif isinstance(obj, str):
            for pl in ["[Cliente]", "[CLIENTE]", "[cliente]", "[CLIENT]", "[client]"]:
                obj = obj.replace(pl, name)
            return obj
        return obj

    blueprint_payload = scrub_client_placeholders(blueprint_payload, client_name)

    #
    total_ale = 0.0
    for pilar in blueprint_payload.get("pillars_analysis", []):
        for finding in pilar.get("health_check_asis", []):
            val = finding.get("fair_ale_score")
            total_ale += float(val) if val is not None else 0.0

    blueprint_payload["total_fair_ale"] = total_ale

    #
    try:
        blueprint_payload["_generation_metadata"] = {
            "artifact_type": "blueprint_payload",
            "artifact_version": "1.0.0",
        }
        #
        validated_model = BlueprintPayload.model_validate(blueprint_payload)
        final_payload_dict = validated_model.model_dump(by_alias=True)
    except Exception as val_err:
        raise RuntimeError(
            f"Error de validación en payload final del blueprint: {val_err}"
        ) from val_err

    #
    output_path = resolve_blueprint_payload_path(client_name, tower_id)
    output_path.write_text(
        json.dumps(final_payload_dict, indent=2, ensure_ascii=False),
        encoding="utf-8-sig",
    )
    print(f"✅ Payload del Blueprint generado y validado: {output_path}")


def main(argv: list[str] | None = None) -> None:
    r"""{'docstring': 'Parses command-line arguments and initiates the Tower Blueprint process.\n\nThis function serves as the primary command-line entry point. It requires two\npositional arguments: a client identifier and a tower identifier. These are\nused to invoke the asynchronous `run_tower_blueprint` function. If the\nrequired arguments are not supplied, a usage message is printed to standard\noutput and the program terminates.\n\nArgs:\n    argv: An optional list of string arguments, intended for testing. If None,\n        `sys.argv` is used as the source of command-line arguments.\n\nRaises:\n    SystemExit: If fewer than two arguments (`client` and `tower_id`) are\n        provided on the command line.'}."""
    if len(argv if argv is not None else sys.argv) < 3:
        print(
            "Uso: python -m assessment_engine.application.run_tower_blueprint_engine <client> <tower_id>"
        )
        sys.exit(1)
    asyncio.run(
        run_tower_blueprint(
            (argv if argv is not None else sys.argv)[1],
            (argv if argv is not None else sys.argv)[2],
        )
    )


if __name__ == "__main__":
    main()
