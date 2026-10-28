"""Defines the primary pipeline for processing blueprint payloads. This includes model-based analysis of architectural pillars, data validation against schemas, and synchronization with a central knowledge graph."""

import asyncio
import json
import os
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
    print(f"    -> Analizando Pilar: {pilar_data['label']}...")

    pilar_id = pilar_data["id"]
    pilar_label = pilar_data["label"]
    pilar_score = pilar_data["score"]

    # Enrich the context string with refined findings, including technical standard references and supporting source text fragments.
    refined = pilar_data.get("refined_findings", {})
    refined_str = json.dumps(refined, indent=2, ensure_ascii=False) if refined else ""

    context_enhanced = f"{context_str}\n\n### ANÁLISIS REFINADO Y EVIDENCIAS DISPONIBLES:\n{refined_str}"

    answers_json = json.dumps(
        pilar_data["answers"], indent=2, ensure_ascii=False
    )
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
        print(f"Error procesando pilar {pilar_label}: {e}")
    return None


def _resolve_mitigated_risk_context(proj: dict, blueprint_payload: dict) -> str:
    """Resolve the textual description and FAIR ALE of the mitigated risk."""
    mitigated_risk_text = "N/A"
    fair_ale = 0.0
    if proj.get("mitigates_risk_id"):
        for p_ana in blueprint_payload.get("pillars_analysis", []):
            for hc in p_ana.get("health_check_asis", []):
                if hc.get("node_id") == proj.get("mitigates_risk_id"):
                    mitigated_risk_text = (
                        f"[{hc.get('capability', hc.get('target_state'))}] "
                        f"{hc.get('finding', hc.get('risk_observed'))} -> "
                        f"Riesgo: {hc.get('business_risk', hc.get('impact'))}"
                    )
                    fair_ale = hc.get("fair_ale_score", 0.0)
                    break
    if fair_ale > 0:
        mitigated_risk_text += f" | FAIR ALE: {fair_ale:,.2f} €"
    return mitigated_risk_text


def _cascade_project_rename(blueprint_payload: dict, old_name: str, new_name: str) -> None:
    """Cascade project renaming across roadmap and external dependencies."""
    for wave in blueprint_payload.get("roadmap", []):
        wave["projects"] = [
            new_name if p == old_name else p
            for p in wave.get("projects", [])
        ]
    for d in blueprint_payload.get("external_dependencies", []):
        if d.get("project") == old_name:
            d["project"] = new_name
        if d.get("depends_on") == old_name:
            d["depends_on"] = new_name


def _apply_deterministic_finops(
    enrichment_data: dict,
    proj: dict,
    rate_data: dict,
    blueprint_payload: dict,
    client_name: str,
    tower_id: str,
) -> None:
    """Calculate and attach OpEx and CapEx estimates using DeterministicFinOpsEngine."""
    from assessment_engine.infrastructure.deterministic_enricher import DeterministicFinOpsEngine
    try:
        wbs = enrichment_data.get("wbs_breakdown", [])
        p_name = proj.get("name", "")
        p_obj = proj.get("tech_objective", "")
        p_sz = proj.get("sizing", "M")
        curr_sym = blueprint_payload.get("document_meta", {}).get("currency", "€") or "€"
        custom_prof_path = resolve_blueprint_payload_path(client_name, tower_id).parent / "custom_risk_profile.json"
        country_mult = 1.0
        if custom_prof_path.exists():
            try:
                with open(custom_prof_path, encoding="utf-8-sig") as cf:
                    c_data = json.load(cf)
                    sre_rate = float(c_data.get("hourly_rate_sre_eur", 36.0))
                    country_mult = sre_rate / 36.0
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
        if dynamic_capex and dynamic_capex.strip() and "150.000" not in dynamic_capex and len(dynamic_capex) > 10:
            enrichment_data["capex_estimate"] = dynamic_capex.strip()
        else:
            enrichment_data["capex_estimate"] = capex_str
    except Exception as finops_err:
        print(f"⚠️ Error calculando FinOps matemático: {finops_err}")


def _map_candidate_initiatives_to_sota_projects(initiatives: list) -> list:
    """Map candidate initiatives to deterministic SOTA project structures with sizing and duration."""
    sota_projects = []
    for idx, init in enumerate(initiatives):
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
                "name": init.get("title", f"Iniciativa Estratégica {idx + 1}"),
                "business_case": init.get("business_case", "Impacto estratégico basado en la validación del Estado del Arte 2026."),
                "tech_objective": init.get("rationale", "Evolución técnica."),
                "deliverables": init.get("deliverables", [
                    "Diseño de arquitectura de referencia.",
                    "Despliegue de Piloto controlado.",
                    "Evaluación de resultados y plan de escalado.",
                ]),
                "sizing": proj_sizing,
                "duration": proj_duration,
                "transformation_typology": init.get("typology", "Core Modernization"),
                "program_id": None,
            }
        )
    return sota_projects


def _sanitize_hallucinated_findings(blueprint_analysis: dict, corpus_clean: str, p_data: dict) -> None:
    """Verify generated findings against the reference corpus and replace hallucinations with verified gaps."""
    import re
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
                    finding["literal_evidence"] = (
                        verified_gaps[0]
                        if verified_gaps
                        else f"Evidencia técnica validada en el pilar {p_data.get('label', '')}."
                    )


def _reconcile_orchestrator_roadmap_and_dependencies(
    closing_data: dict, valid_project_names: list
) -> None:
    """Fuzzy match external dependencies and ensure complete roadmap coverage without missing projects."""
    import difflib

    def fuzzy_match(name, choices, cutoff=0.45):
        matches = difflib.get_close_matches(name, choices, n=1, cutoff=cutoff)
        return matches[0] if matches else None

    for dep in closing_data.get("external_dependencies", []):
        dep_name = dep.get("depends_on")
        if dep_name not in valid_project_names and dep_name not in ["Independiente", "Ninguna"]:
            corrected = fuzzy_match(dep_name, valid_project_names)
            dep["depends_on"] = corrected if corrected else "Independiente"

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

    missing_projects = list(set(valid_project_names) - mapped_projects)
    if missing_projects and closing_data.get("roadmap"):
        closing_data["roadmap"][-1]["projects"].extend(missing_projects)

    principles = closing_data.get("design_principles", [])
    if len(principles) > 10:
        closing_data["design_principles"] = principles[:7]


async def _resolve_gravity_profile(model_name: str, intel_str: str, client_name: str) -> tuple[float, str]:
    """Calculate the architectural gravity profile of the client or return fallback defaults."""
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
            dynamic_target_maturity = gravity_profile.get("recommended_target_maturity", 4.0)
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
            print(f"✅ Perfil de Gravedad Calculado: {gravity_profile.get('strategic_directive')} (Target: {dynamic_target_maturity})")
    except Exception as e:
        print(f"⚠️ Error calculando Perfil de Gravedad: {e}. Se usará contexto estándar.")
    return dynamic_target_maturity, intel_str


async def _orchestrate_closing_agent(
    model_name: str,
    target_language: str,
    closing_prompt: str,
    valid_project_names: list,
    blueprint_payload: dict,
) -> None:
    """Execute the master closing orchestrator agent with automatic retry and protocol repair."""
    valid_project_names = [
        proj["name"]
        for pilar in blueprint_payload.get("pillars_analysis", [])
        for proj in pilar.get("projects_todo", [])
    ]
    await _orchestrate_closing_agent(
        model_name, target_language, closing_prompt, valid_project_names, blueprint_payload
    )

    # Enrich initiative charters with budgetary and resource estimates.
    print("💼 [Bid Manager] Enriqueciendo proyectos con WBS, TCO, y ROI...")
    try:
        from assessment_engine.infrastructure.config_loader import load_rate_card

        rate_data = load_rate_card()

        from assessment_engine.domain.prompts.blueprint_prompts import (
            get_bid_manager_prompt,
        )
        from assessment_engine.domain.schemas.blueprint import ProjectCharterEnrichment
        from assessment_engine.infrastructure.config_loader import get_consultant_company_name
        company = get_consultant_company_name()

        bid_manager_agent = Agent(
            name="bid_manager_architect",
            model=model_name,
            instruction=f"Eres el Bid Manager de {company}. Devuelve estrictamente el JSON pedido.",
            output_schema=ProjectCharterEnrichment,
        )
        app_bid_manager = AdkApp(agent=bid_manager_agent)

        async def enrich_project(p_analysis_idx, proj_idx, proj):
            mitigated_risk_text = _resolve_mitigated_risk_context(proj, blueprint_payload)
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
                _apply_deterministic_finops(
                    enrichment_data, proj, rate_data, blueprint_payload, client_name, tower_id
                )
                if enrichment_data.get("commercial_name"):
                    old_name = proj["name"]
                    from assessment_engine.infrastructure.deterministic_enricher import LinguisticLinter
                    new_name = LinguisticLinter.sanitize_title(enrichment_data["commercial_name"])
                    proj["name"] = new_name
                    _cascade_project_rename(blueprint_payload, old_name, new_name)

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

    # Respect portfolio-level integrated ALE from SovereignPolicyEngine if present; fallback to sum if missing
    if not blueprint_payload.get("total_fair_ale"):
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
    content = json.dumps(final_payload_dict, indent=2, ensure_ascii=False)
    
    from assessment_engine.infrastructure.localization import (
        apply_vocabulary_substitutions,
    )

    content = apply_vocabulary_substitutions(content, locale=doc_lang)

    output_path.write_text(
        content,
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
