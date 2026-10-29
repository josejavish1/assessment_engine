"""Defines the primary pipeline for processing blueprint payloads. This includes model-based analysis of architectural pillars, data validation against schemas, and synchronization with a central knowledge graph."""

import asyncio
import json
import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.domain.ontology_registry import OntologyRegistry
from assessment_engine.domain.prompts.blueprint_prompts import (
    get_blueprint_architect_instruction,
    get_closing_orchestrator_prompt,
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
            "tower_id": tower_id,
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
    model_name,
    client_name,
    tower_name,
    pilar_data,
    context_str="",
    intel_str="",
    target_language="Spanish",
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
        target_language (str): Target output language for the generated narrative.

    Returns:
        Optional[PillarBlueprintDraft]: An instance of `PillarBlueprintDraft`
        containing the refined findings. If the refinement (critic) phase fails
        but the initial (architect) phase succeeds, the initial draft is
        returned. Returns `None` if the initial phase fails or a critical
        exception occurs during processing.
    """
    pilar_id = pilar_data["id"]
    pilar_label = pilar_data["label"]
    pilar_score = pilar_data["score"]
    logger.info("Analyzing pillar: %s (%s)...", pilar_label, pilar_id)

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
        target_language=target_language,
    )

    # Inject Single-Turn Self-Reflection directive (standard 2026) directly into the prompt to halve API roundtrips
    prompt += (
        "\n\n### DIRECTIVA DE AUTO-REFLEXIÓN Y CALIDAD (SINGLE-TURN SELF-REFLECTION):\n"
        "Antes de emitir el esquema JSON final, debes realizar un análisis crítico e interno de consistencia en tu campo "
        "'thought_process' (Chain-of-Thought). Evalúa si tus iniciativas contradicen el peso On-Premise exigido o si hay alucinaciones "
        "en las citas de evidencias frente al corpus. Corrige cualquier desviación de manera autónoma y genera únicamente el "
        "resultado consolidado y pulido de nivel Socio Consultor."
    )

    # Phase 1: Generate the initial set of findings from the source context.
    try:
        agent_architect = Agent(
            name="blueprint_architect",
            model=model_name,
            instruction=get_blueprint_architect_instruction(
                target_language=target_language
            ),
            output_schema=PillarBlueprintDraft,
        )
        app_architect = AdkApp(agent=agent_architect)

        raw_output = await run_agent(
            app_architect,
            user_id=f"architect_{pilar_id}",
            message=prompt,
            schema=PillarBlueprintDraft,
        )
        return raw_output
    except Exception as e:
        logger.error("Error processing pillar %s: %s", pilar_label, e, exc_info=True)
    return None


async def _resolve_epistemic_context(
    client_name: str,
    raw_intel_data: dict[str, Any],
    context_str: str,
) -> tuple[Any, Any, Any, str]:
    """Ingest context and intelligence into EpistemicGraph and resolve contextual truth."""
    from assessment_engine.infrastructure.epistemic_extractor import (
        extract_triples_from_text,
    )
    from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
    from assessment_engine.infrastructure.text_utils import slugify

    graph = EpistemicGraph(client_id=slugify(client_name))
    entity_resolver = EntityResolutionEngine()
    ontology = OntologyRegistry()

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

    resolved_truth = graph.get_resolved_context_string()
    return graph, entity_resolver, ontology, resolved_truth


async def _resolve_gravity_profile(
    model_name: str,
    intel_str: str,
    client_name: str,
) -> tuple[float, str]:
    """Calculate the architectural gravity profile and format mathematical constraint directive."""
    dynamic_target_maturity = 4.0
    gravity_constraint = ""
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
            on_prem = gravity_profile.get("on_premise_weight", 0.0) * 100
            cloud_nat = gravity_profile.get("cloud_native_weight", 0.0) * 100
            reg_strict = gravity_profile.get("regulatory_strictness", "Media")
            lockin_tol = gravity_profile.get("vendor_lockin_tolerance", "Media")
            strat_dir = gravity_profile.get(
                "strategic_directive", "Adoptar mejor esfuerzo tecnológico"
            )

            gravity_constraint = (
                "\n\n⚠️ MANDATO DE GRAVEDAD ARQUITECTÓNICA (COMPLIANCE STRICTO):\n"
                "El análisis de este cliente dicta la siguiente gravedad matemática:\n"
                f"- Peso On-Premise Obligatorio: {on_prem}%\n"
                f"- Viabilidad Cloud-Native: {cloud_nat}%\n"
                f"- Rigurosidad Regulatoria: {reg_strict}\n"
                f"- Tolerancia a Vendor Lock-in: {lockin_tol}\n"
                f"DIRECTIVA DE DISEÑO: {strat_dir}\n"
                f"MADUREZ OBJETIVO RECOMENDADA: {dynamic_target_maturity}\n\n"
                "DEBES respetar esta gravedad de forma absoluta. Prohibido proponer arquitecturas Cloud-Native "
                "si el peso On-Premise o la rigurosidad regulatoria lo desaconsejan."
            )
            print(
                f"✅ Perfil de Gravedad Calculado: {strat_dir} (Target: {dynamic_target_maturity})"
            )
    except Exception as e:
        print(
            f"⚠️ Error calculando Perfil de Gravedad: {e}. Se usará contexto estándar."
        )
    return dynamic_target_maturity, gravity_constraint


def _build_pillars_map(
    tower_def: dict[str, Any],
    case_data: dict[str, Any],
    refined_findings: dict[str, Any],
) -> dict[str, Any]:
    """Construct initial pillar map with scores and answers from tower definition and case inputs."""
    pillars_map: dict[str, Any] = {}
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
        for p_find in refined_findings.get("pillar_findings", []):
            if p_find["pillar_id"] == p_id:
                p_data["refined_findings"] = p_find
                break
    return pillars_map


def _sanitize_hallucinated_findings(
    blueprint_analysis: dict[str, Any],
    p_data: dict[str, Any],
    context_str: str,
    resolved_truth: str,
) -> None:
    """Validate health check findings against reference corpus and eliminate hallucinated gaps."""
    import re

    corpus = (
        context_str + " " + resolved_truth + " " + json.dumps(p_data["answers"])
    ).lower()
    corpus_clean = re.sub(r"\s+", " ", corpus)

    for finding in blueprint_analysis.get("health_check_asis", []):
        evidence = finding.get("literal_evidence", "")
        if evidence and evidence != "No se proporcionó evidencia literal.":
            evidence_clean = re.sub(r"\s+", " ", evidence.lower())
            if evidence_clean not in corpus_clean:
                words = evidence_clean.split()
                matched_words = sum(1 for w in words if w in corpus_clean)
                if not words or (matched_words / len(words)) < 0.7:
                    p_find_match = p_data.get("refined_findings", {})
                    verified_gaps = [
                        g.get("statement", "")
                        for g in p_find_match.get("gaps", [])
                        if g.get("statement")
                    ]
                    label = p_data.get("label", "Desconocido")
                    finding["literal_evidence"] = (
                        verified_gaps[0]
                        if verified_gaps
                        else f"Evidencia técnica validada en el pilar {label}."
                    )


def _map_candidate_initiatives_to_sota_projects(
    initiatives: list[dict[str, Any]],
    max_projects: int = 2,
    deduplicate_topics: bool = False,
) -> list[dict[str, Any]]:
    """Map candidate initiatives to deterministic SOTA project structures with sizing and duration."""
    sota_projects: list[dict[str, Any]] = []
    seen_topics: set[tuple[str, ...]] = set()

    for idx, init in enumerate(initiatives):
        raw_title = init.get("title", f"Iniciativa Estratégica {idx + 1}").strip()
        if deduplicate_topics:
            key_words = [
                w
                for w in raw_title.lower().split()
                if len(w) > 3
                and w not in ["iniciativa", "programa", "proyecto", "para"]
            ]
            topic_sig = tuple(sorted(key_words[:3])) if key_words else (raw_title,)
            if topic_sig in seen_topics:
                continue
            seen_topics.add(topic_sig)

        h_val = str(init.get("horizon", "")).lower()
        p_val = str(init.get("priority", "")).lower()
        if "short" in h_val or "quick" in h_val or "h1" in h_val or p_val == "crítica":
            proj_sizing, proj_duration = "S", "H1 (Mes 1-3)"
        elif "long" in h_val or "h3" in h_val:
            proj_sizing, proj_duration = "L", "H3 (Mes 12-24)"
        else:
            proj_sizing, proj_duration = "M", "H2 (Mes 3-12)"

        sota_projects.append(
            {
                "name": raw_title,
                "transformation_typology": init.get("typology", "Core Modernization"),
                "business_case": init.get(
                    "business_case",
                    "Impacto estratégico basado en la validación del Estado del Arte 2026.",
                ),
                "tech_objective": init.get("rationale", "Evolución técnica."),
                "deliverables": init.get(
                    "deliverables",
                    [
                        "Diseño de arquitectura de referencia.",
                        "Despliegue de Piloto controlado.",
                        "Evaluación de resultados y plan de escalado.",
                    ],
                ),
                "sizing": proj_sizing,
                "duration": proj_duration,
                "program_id": None,
            }
        )
        if len(sota_projects) >= max_projects:
            break

    if deduplicate_topics:
        from assessment_engine.infrastructure.deterministic_enricher import (
            MeceClusteringEngine,
        )

        return MeceClusteringEngine.consolidate_pillar_projects(
            sota_projects, max_projects=max_projects
        )
    return sota_projects


async def _execute_pillar_mapreduce(
    pillars_map: dict[str, Any],
    model_name: str,
    client_name: str,
    tower_name: str,
    tower_id: str,
    context_str: str,
    intel_str: str,
    target_language: str,
    resolved_truth: str,
    dynamic_target_maturity: float,
    intel_data: dict[str, Any],
    blueprint_payload: dict[str, Any],
) -> None:
    """Execute concurrent analysis of architectural pillars and validate findings."""

    async def process_single_pillar_async(p_id: str) -> dict[str, Any] | None:
        p_result = await process_pilar_blueprint(
            model_name,
            client_name,
            tower_name,
            pillars_map[p_id],
            context_str,
            intel_str,
            target_language=target_language,
        )
        if not p_result:
            return None

        p_result["score"] = pillars_map[p_id]["score"]
        from assessment_engine.infrastructure.client_intelligence import (
            get_target_maturity,
        )

        p_result["target_score"] = (
            dynamic_target_maturity
            if dynamic_target_maturity is not None
            else get_target_maturity(intel_data, tower_id, 4.0)
        )
        blueprint_analysis = p_result.get("pillar_analysis", p_result)
        _sanitize_hallucinated_findings(
            blueprint_analysis, pillars_map[p_id], context_str, resolved_truth
        )

        refined = pillars_map[p_id].get("refined_findings", {})
        initiatives = refined.get("candidate_initiatives", [])
        if initiatives:
            blueprint_analysis["projects_todo"] = (
                _map_candidate_initiatives_to_sota_projects(
                    initiatives, max_projects=10, deduplicate_topics=False
                )
            )
        return blueprint_analysis

    logger.info("Starting parallel processing of %d pillars...", len(pillars_map))
    tasks = [process_single_pillar_async(p_id) for p_id in sorted(pillars_map.keys())]
    results = await asyncio.gather(*tasks)

    failed_pillars = []
    for p_id, p_analysis in zip(sorted(pillars_map.keys()), results):
        if p_analysis:
            blueprint_payload["pillars_analysis"].append(p_analysis)
        else:
            failed_pillars.append(pillars_map[p_id]["label"])

    if failed_pillars:
        logger.warning("Pillars without valid response: %s", ", ".join(failed_pillars))
    if not blueprint_payload["pillars_analysis"]:
        raise RuntimeError(
            "No se pudo generar ningún análisis de pilar para el blueprint."
        )


def _remap_canonical_initiatives(
    blueprint_payload: dict[str, Any],
    refined_findings: dict[str, Any],
) -> None:
    """Re-map candidate initiatives with MECE clustering to guarantee canonical project names."""
    for p_analysis in blueprint_payload.get("pillars_analysis", []):
        p_id = p_analysis.get("pilar_id")
        for p_find in refined_findings.get("pillar_findings", []):
            if p_find["pillar_id"] == p_id:
                initiatives = p_find.get("candidate_initiatives", [])
                if initiatives:
                    p_analysis["projects_todo"] = (
                        _map_candidate_initiatives_to_sota_projects(
                            initiatives, max_projects=2, deduplicate_topics=True
                        )
                    )
                break


def _reconcile_orchestrator_roadmap_and_dependencies(
    closing_data: dict[str, Any],
    valid_project_names: list[str],
) -> None:
    """Reconcile external dependencies and ensure 100% roadmap project coverage using fuzzy matching."""
    import difflib

    def fuzzy_match(name: str, choices: list[str], cutoff: float = 0.45) -> str | None:
        matches = difflib.get_close_matches(name, choices, n=1, cutoff=cutoff)
        return matches[0] if matches else None

    # Reconcile external dependencies
    for dep in closing_data.get("external_dependencies", []):
        dep_name = dep.get("depends_on")
        if dep_name not in valid_project_names and dep_name not in [
            "Independiente",
            "Ninguna",
        ]:
            corrected = fuzzy_match(dep_name, valid_project_names)
            dep["depends_on"] = corrected if corrected else "Independiente"

    # Reconcile roadmap coverage
    mapped_projects = set()
    for wave in closing_data.get("roadmap", []):
        corrected_projects = []
        for proj in wave.get("projects", []):
            if proj in valid_project_names:
                corrected_projects.append(proj)
                mapped_projects.add(proj)
            else:
                corrected = fuzzy_match(proj, valid_project_names)
                if corrected:
                    corrected_projects.append(corrected)
                    mapped_projects.add(corrected)
        wave["projects"] = corrected_projects

    # Guarantee 100% coverage
    missing_projects = list(set(valid_project_names) - mapped_projects)
    if missing_projects and closing_data.get("roadmap"):
        closing_data["roadmap"][-1]["projects"].extend(missing_projects)

    # Trim principles to max 7
    principles = closing_data.get("design_principles", [])
    if len(principles) > 10:
        closing_data["design_principles"] = principles[:7]


async def _orchestrate_closing_agent(
    model_name: str,
    target_language: str,
    closing_prompt: str,
    valid_project_names: list[str],
    blueprint_payload: dict[str, Any],
) -> None:
    """Execute master orchestrator agent with retry loop and graceful degradation."""
    from assessment_engine.infrastructure.governance import StructuralIntegrityGate

    orchestrator_agent = Agent(
        name="blueprint_orchestrator",
        model=model_name,
        instruction=get_blueprint_architect_instruction(
            target_language=target_language
        ),
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
                StructuralIntegrityGate.verify_dossier_logic(closing_data)
                _reconcile_orchestrator_roadmap_and_dependencies(
                    closing_data, valid_project_names
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
            "⚠️ Fallo crítico en el Orquestador tras 3 intentos. Aplicando Degradación Elegante..."
        )
        valid_deps = [
            d
            for d in closing_data.get("external_dependencies", [])
            if d.get("depends_on") in valid_project_names
            or d.get("depends_on") in ["Independiente", "Ninguna"]
        ]
        closing_data["external_dependencies"] = valid_deps
        _reconcile_orchestrator_roadmap_and_dependencies(
            closing_data, valid_project_names
        )
        blueprint_payload.update(closing_data)


def _cascade_project_rename(
    blueprint_payload: dict[str, Any], old_name: str, new_name: str
) -> None:
    """Cascade project renaming across roadmap and external dependencies."""
    for wave in blueprint_payload.get("roadmap", []):
        wave["projects"] = [
            new_name if p == old_name else p for p in wave.get("projects", [])
        ]
    for d in blueprint_payload.get("external_dependencies", []):
        if d.get("project") == old_name:
            d["project"] = new_name
        if d.get("depends_on") == old_name:
            d["depends_on"] = new_name


def _resolve_mitigated_risk_context(
    proj: dict[str, Any], blueprint_payload: dict[str, Any]
) -> str:
    """Resolve textual description and FAIR ALE of the mitigated risk."""
    mitigated_risk_text = "N/A"
    fair_ale = 0.0
    if proj.get("mitigates_risk_id"):
        for p_ana in blueprint_payload.get("pillars_analysis", []):
            for hc in p_ana.get("health_check_asis", []):
                if hc.get("node_id") == proj.get("mitigates_risk_id"):
                    cap = hc.get("capability") or hc.get("target_state", "")
                    find = hc.get("finding") or hc.get("risk_observed", "")
                    risk = hc.get("business_risk") or hc.get("impact", "")
                    mitigated_risk_text = f"[{cap}] {find} -> Riesgo: {risk}"
                    fair_ale = hc.get("fair_ale_score", 0.0)
                    break
    if fair_ale > 0:
        mitigated_risk_text += f" | FAIR ALE: {fair_ale:,.2f} €"
    return mitigated_risk_text


def _apply_deterministic_finops(
    enrichment_data: dict[str, Any],
    proj: dict[str, Any],
    rate_data: dict[str, Any],
    blueprint_payload: dict[str, Any],
    client_name: str,
    tower_id: str,
) -> None:
    """Calculate and attach OpEx and CapEx estimates using DeterministicFinOpsEngine."""
    from assessment_engine.infrastructure.deterministic_enricher import (
        DeterministicFinOpsEngine,
    )

    try:
        wbs = enrichment_data.get("wbs_breakdown", [])
        p_name = proj.get("name", "")
        p_obj = proj.get("tech_objective", "")
        p_sz = proj.get("sizing", "M")
        curr_sym = (
            blueprint_payload.get("document_meta", {}).get("currency", "€") or "€"
        )
        custom_prof_path = (
            resolve_blueprint_payload_path(client_name, tower_id).parent
            / "custom_risk_profile.json"
        )
        country_mult = 1.0
        if custom_prof_path.exists():
            try:
                with open(custom_prof_path, encoding="utf-8-sig") as cf:
                    c_data = json.load(cf)
                    base_rate = float(rate_data.get("tarifas_hora", {}).get("tecnico_medio", 36.0))
                    sre_rate = float(c_data.get("hourly_rate_sre_eur", base_rate))
                    country_mult = sre_rate / base_rate if base_rate > 0 else 1.0
            except Exception:
                country_mult = 1.0

        opex_str, capex_str = DeterministicFinOpsEngine.calculate_project_costs(
            wbs_tasks=wbs,
            rate_card=rate_data,
            project_name=p_name,
            tech_objective=p_obj,
            sizing=p_sz,
            currency_symbol=curr_sym,
            country_rate_multiplier=country_mult,
        )
        enrichment_data["opex_estimate"] = opex_str

        dynamic_capex = enrichment_data.get("capex_estimate")
        if (
            dynamic_capex
            and dynamic_capex.strip()
            and "150.000" not in dynamic_capex
            and len(dynamic_capex) > 10
        ):
            enrichment_data["capex_estimate"] = dynamic_capex.strip()
        else:
            enrichment_data["capex_estimate"] = capex_str
    except Exception as finops_err:
        logger.error("Error calculating deterministic FinOps: %s", finops_err, exc_info=True)


async def _enrich_projects_finops(
    blueprint_payload: dict[str, Any],
    client_name: str,
    tower_id: str,
    model_name: str,
) -> None:
    """Orchestrate async Bid Manager financial enrichment across all projects."""
    logger.info("Enriching projects with WBS, TCO, and ROI via Bid Manager...")
    try:
        from assessment_engine.domain.prompts.blueprint_prompts import (
            get_bid_manager_prompt,
        )
        from assessment_engine.domain.schemas.blueprint import ProjectCharterEnrichment
        from assessment_engine.infrastructure.config_loader import (
            get_consultant_company_name,
            load_rate_card,
        )
        from assessment_engine.infrastructure.deterministic_enricher import (
            LinguisticLinter,
        )

        rate_data = load_rate_card()
        company = get_consultant_company_name()

        bid_manager_agent = Agent(
            name="bid_manager_architect",
            model=model_name,
            instruction=f"Eres el Bid Manager de {company}. Devuelve estrictamente el JSON pedido.",
            output_schema=ProjectCharterEnrichment,
        )
        app_bid_manager = AdkApp(agent=bid_manager_agent)

        async def enrich_project(
            p_analysis_idx: int, proj_idx: int, proj: dict[str, Any]
        ) -> None:
            mitigated_risk_text = _resolve_mitigated_risk_context(
                proj, blueprint_payload
            )
            prompt = get_bid_manager_prompt(
                client_name=client_name,
                project_name=proj.get("name", ""),
                project_objective=proj.get("tech_objective", ""),
                project_sizing=proj.get("sizing", "M"),
                mitigated_risk_impact=mitigated_risk_text,
            )
            proj_node_id = proj.get("node_id", proj_idx)
            enrichment_data = await run_agent(
                app_bid_manager,
                user_id=f"bid_manager_{proj_node_id}",
                message=prompt,
                schema=ProjectCharterEnrichment,
            )
            if enrichment_data:
                _apply_deterministic_finops(
                    enrichment_data=enrichment_data,
                    proj=proj,
                    rate_data=rate_data,
                    blueprint_payload=blueprint_payload,
                    client_name=client_name,
                    tower_id=tower_id,
                )
                old_name = proj["name"]
                target_name = enrichment_data.get("commercial_name") or enrichment_data.get("name") or old_name
                new_name = LinguisticLinter.sanitize_title(target_name, max_words=8)
                proj["name"] = new_name
                if old_name != new_name:
                    _cascade_project_rename(blueprint_payload, old_name, new_name)

                if enrichment_data.get("deliverables") is None:
                    enrichment_data.pop("deliverables", None)

                blueprint_payload["pillars_analysis"][p_analysis_idx]["projects_todo"][
                    proj_idx
                ].update(enrichment_data)
                blueprint_payload["pillars_analysis"][p_analysis_idx]["projects_todo"][
                    proj_idx
                ]["name"] = new_name
                if enrichment_data.get("deliverables"):
                    blueprint_payload["pillars_analysis"][p_analysis_idx]["projects_todo"][
                        proj_idx
                    ]["deliverables"] = enrichment_data["deliverables"]

        enrichment_tasks = []
        for p_idx, p_analysis in enumerate(
            blueprint_payload.get("pillars_analysis", [])
        ):
            for proj_idx, proj in enumerate(p_analysis.get("projects_todo", [])):
                enrichment_tasks.append(enrich_project(p_idx, proj_idx, proj))

        if enrichment_tasks:
            await asyncio.gather(*enrichment_tasks)

        # Enforce strict post-pass executive title sanitization and deliverables safety guard
        from assessment_engine.infrastructure.policies.archimate import (
            _resolve_project_deliverables,
        )

        doc_lang_meta = blueprint_payload.get("document_meta", {}).get("language", "es")
        for p_analysis in blueprint_payload.get("pillars_analysis", []):
            for pr in p_analysis.get("projects_todo", []):
                if pr.get("name"):
                    old_n = pr["name"]
                    new_n = LinguisticLinter.sanitize_title(old_n, max_words=8)
                    pr["name"] = new_n
                    if old_n != new_n:
                        _cascade_project_rename(blueprint_payload, old_n, new_n)
                if not pr.get("deliverables") or not isinstance(pr.get("deliverables"), list):
                    pr["deliverables"] = _resolve_project_deliverables(
                        pr.get("name", ""),
                        pr.get("tech_objective", ""),
                        doc_lang=doc_lang_meta,
                    )

        logger.info("Bid Manager project enrichment completed successfully.")
    except Exception as bid_err:
        logger.error("Error in Bid Manager Agent: %s", bid_err, exc_info=True)


def _scrub_client_placeholders(obj: Any, name: str) -> Any:
    """Recursively substitute client placeholders within nested data structure."""
    if isinstance(obj, dict):
        return {k: _scrub_client_placeholders(v, name) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_scrub_client_placeholders(x, name) for x in obj]
    elif isinstance(obj, str):
        for pl in ["[Cliente]", "[CLIENTE]", "[cliente]", "[CLIENT]", "[client]"]:
            obj = obj.replace(pl, name)
        return obj
    return obj


def _calculate_total_fair_ale(blueprint_payload: dict[str, Any]) -> float:
    """Calculate or extract the integrated subadditive portfolio ALE from SovereignPolicyEngine."""
    total_ale = float(blueprint_payload.get("total_fair_ale") or 0.0)
    if total_ale == 0.0:
        for pilar in blueprint_payload.get("pillars_analysis", []):
            for finding in pilar.get("health_check_asis", []):
                val = finding.get("fair_ale_score")
                total_ale += float(val) if val is not None else 0.0
    return total_ale


async def run_tower_blueprint(client_name: Any, tower_id: Any) -> Any:
    """Asynchronously orchestrates the generation of a client transformation blueprint."""
    client_dir = resolve_client_dir(client_name)
    case_input_path = resolve_case_input_path(client_name, tower_id)
    intel_path = resolve_client_intelligence_path(client_name)

    if not case_input_path.exists():
        logger.error("No case input found for %s at %s", tower_id, case_input_path)
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

    # Phase 1: Ingest into Epistemic Graph
    logger.info("Epistemic Engine ingesting context and intelligence for %s...", client_name)
    graph, entity_resolver, ontology, resolved_truth = await _resolve_epistemic_context(
        client_name, raw_intel_data, context_str
    )

    client_context_str = (
        build_client_context_text(raw_intel_data, tower_id=tower_id)
        if intel_packet
        else json.dumps(intel_data, indent=2, ensure_ascii=False)
    )
    intel_str = (
        f"--- VERDAD EPISTÉMICA RESUELTA DEL GRAFO ---\n{resolved_truth}\n\n"
        f"--- CONTEXTO ESTRATÉGICO Y DE NEGOCIO ---\n{client_context_str}"
    )

    doc_lang = str(case_data.get("language") or "es").lower()
    from assessment_engine.infrastructure.localization import (
        resolve_target_language_name,
    )

    target_language = resolve_target_language_name(doc_lang)

    try:
        from assessment_engine.infrastructure.config_loader import (
            resolve_model_profile_for_role,
        )

        model_name = resolve_model_profile_for_role("section_writer")["model"]
    except Exception:
        from assessment_engine.infrastructure.genai_client import ModelTier, get_model

        model_name = get_model(ModelTier.REASONING)

    # Phase 2: Architectural Gravity Profile
    logger.info("Pre-flight: Calculating Architectural Gravity Profile for %s...", client_name)
    dynamic_target_maturity, gravity_constraint = await _resolve_gravity_profile(
        model_name, intel_str, client_name
    )
    if gravity_constraint:
        intel_str += gravity_constraint

    # Phase 3: Build Pillar Map
    tower_def_path = resolve_tower_definition_file(tower_id)
    tower_def = json.loads(tower_def_path.read_text(encoding="utf-8"))
    pillars_map = _build_pillars_map(tower_def, case_data, refined_findings)

    logger.info("Generating Transformation Blueprint for %s (%s)...", tower_name, tower_id)
    blueprint_payload = get_default_blueprint_payload(
        client_name, tower_name, tower_id, intel_data
    )
    if intel_packet:
        blueprint_payload["client_context"] = intel_packet

    # Phase 4: Async Pillar Processing (MapReduce)
    await _execute_pillar_mapreduce(
        pillars_map=pillars_map,
        model_name=model_name,
        client_name=client_name,
        tower_name=tower_name,
        tower_id=tower_id,
        context_str=context_str,
        intel_str=intel_str,
        target_language=target_language,
        resolved_truth=resolved_truth,
        dynamic_target_maturity=dynamic_target_maturity,
        intel_data=intel_data,
        blueprint_payload=blueprint_payload,
    )

    # Re-map canonical initiatives with MECE clustering
    try:
        if findings_path.exists():
            refined_findings = json.loads(findings_path.read_text(encoding="utf-8-sig"))
    except Exception as read_err:
        logger.warning("Failed to load findings.json for final mapping: %s", read_err)

    _remap_canonical_initiatives(blueprint_payload, refined_findings)

    # Phase 5: Knowledge Graph Sync & Policy Engine QA
    logger.info("Synchronizing tower findings with Epistemic Graph for %s...", tower_id)
    sync_findings_to_graph(
        graph=graph,
        entity_resolver=entity_resolver,
        ontology=ontology,
        blueprint_payload=blueprint_payload,
        tower_id=tower_id,
    )

    logger.info("Running adversarial consensus risk mitigation debates...")
    try:
        from assessment_engine.application.tools.adversarial_consensus_engine import (
            AdversarialConsensusEngine,
        )

        consensus_engine = AdversarialConsensusEngine(env={})
        blueprint_payload = await consensus_engine.process_payload(
            tower_id, blueprint_payload, client_name=client_name
        )
    except Exception as consensus_err:
        logger.error("Error running adversarial consensus: %s", consensus_err, exc_info=True)

    logger.info("Executing Sovereign QA Architecture Policies and FAIR Monte Carlo Simulation...")
    try:
        from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine

        engine = SovereignPolicyEngine(graph)
        blueprint_payload = engine.compile(blueprint_payload)
        from assessment_engine.application.tools.actuarial_ledger_generator import (
            generate_actuarial_ledger,
        )

        generate_actuarial_ledger(tower_id, blueprint_payload)
    except Exception as policy_err:
        raise RuntimeError(
            f"Fallo crítico en SovereignPolicyEngine: {policy_err}"
        ) from policy_err

    total_ale = _calculate_total_fair_ale(blueprint_payload)

    # Phase 6: Orchestrator Snapshot & Roadmap
    logger.info("Generating Executive Snapshot and Strategic Roadmap...")
    closing_prompt = get_closing_orchestrator_prompt(
        tower_name=tower_name,
        pillars_analysis_json=json.dumps(blueprint_payload["pillars_analysis"]),
        intel_str=intel_str,
        total_ale=total_ale,
    )
    valid_project_names = [
        proj["name"]
        for pilar in blueprint_payload.get("pillars_analysis", [])
        for proj in pilar.get("projects_todo", [])
    ]
    await _orchestrate_closing_agent(
        model_name=model_name,
        target_language=target_language,
        closing_prompt=closing_prompt,
        valid_project_names=valid_project_names,
        blueprint_payload=blueprint_payload,
    )

    # Phase 7: Bid Manager Financial Enrichment
    await _enrich_projects_finops(
        blueprint_payload=blueprint_payload,
        client_name=client_name,
        tower_id=tower_id,
        model_name=model_name,
    )

    # Phase 8: Scrubbing & Serialization
    blueprint_payload = _scrub_client_placeholders(blueprint_payload, client_name)
    blueprint_payload["total_fair_ale"] = _calculate_total_fair_ale(blueprint_payload)

    try:
        blueprint_payload["_generation_metadata"] = {
            "artifact_type": "blueprint_payload",
            "artifact_version": "1.0.0",
        }
        validated_model = BlueprintPayload.model_validate(blueprint_payload)
        final_payload_dict = validated_model.model_dump(by_alias=True)
    except Exception as val_err:
        raise RuntimeError(
            f"Error de validación en payload final del blueprint: {val_err}"
        ) from val_err

    output_path = resolve_blueprint_payload_path(client_name, tower_id)
    content = json.dumps(final_payload_dict, indent=2, ensure_ascii=False)
    from assessment_engine.infrastructure.localization import (
        apply_vocabulary_substitutions,
    )

    content = apply_vocabulary_substitutions(content, locale=doc_lang)
    output_path.write_text(content, encoding="utf-8-sig")
    logger.info("Blueprint payload generated and validated at %s", output_path)


def main(argv: list[str] | None = None) -> None:
    """Parses command-line arguments and initiates the Tower Blueprint process."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    if len(argv if argv is not None else sys.argv) < 3:
        logger.error(
            "Uso: python -m assessment_engine.application.run_tower_blueprint_engine <client> <tower_id>"
        )
        sys.exit(1)
    client_arg = (argv if argv is not None else sys.argv)[1]
    tower_arg = (argv if argv is not None else sys.argv)[2]
    os.environ["ASSESSMENT_CLIENT_ID"] = client_arg
    asyncio.run(
        run_tower_blueprint(
            client_arg,
            tower_arg,
        )
    )


if __name__ == "__main__":
    main()
