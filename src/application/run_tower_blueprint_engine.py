"""
Módulo run_tower_blueprint_engine.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import asyncio
import json
import sys
from typing import Any

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from domain.ontology_registry import OntologyRegistry
from domain.prompts.blueprint_prompts import (
    get_blueprint_architect_instruction,
    get_closing_orchestrator_prompt,
    get_critic_prompt,
    get_pilar_architect_prompt,
)
from domain.schemas.blueprint import (
    BlueprintPayload,
    OrchestratorBlueprintDraft,
    PillarBlueprintDraft,
)
from infrastructure.ai_client import run_agent
from infrastructure.client_intelligence import (
    build_client_context_packet,
    build_client_context_text,
    client_intelligence_to_legacy,
    get_target_maturity,
    load_client_intelligence,
)
from infrastructure.entity_resolution import EntityResolutionEngine
from infrastructure.epistemic_graph import EpistemicGraph
from infrastructure.runtime_paths import (
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
    """
    Tier-1 Graph-First Sync.
    Injects findings and initiatives from a blueprint payload into the Sovereign Graph.
    """
    _ = blueprint_payload.get("document_meta", {}).get("client_name", "generic")
    for pillar in blueprint_payload.get("pillars_analysis", []):
        pillar_id = pillar.get("pilar_id", "UNKNOWN")
        _ = pillar.get("pilar_name", "UNKNOWN")

        # 1. Inject Pillar context
        graph.inject_triple(
            subject=pillar_id,
            predicate="BELONGS_TO_TOWER",
            object_val=tower_id,
            source="TOWER_PIPELINE",
            confidence=1.0,
        )

        # 2. Inject Health Checks (Risks)
        for hc in pillar.get("health_check_asis", []):
            finding_text = hc.get("finding", "")
            risk_id = entity_resolver.get_semantic_id(finding_text, context="RISK")
            hc["node_id"] = risk_id  # Sync back to payload for the "view"

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

        # 3. Inject Projects (Initiatives)
        for proj in pillar.get("projects_todo", []):
            proj_name = proj.get("name", "")
            proj_id = entity_resolver.get_semantic_id(proj_name, context="INITIATIVE")
            proj["node_id"] = proj_id  # Sync back

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

    # 4. Inject External Dependencies from Orchestrator
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
    """Provee una estructura base completa que cumple con el contrato de BlueprintPayload."""
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
    """Procesa un pilar individual con el Squad de Arquitecto + Crítico."""
    print(f"    -> Analizando Pilar: {pilar_data['label']}...")

    pilar_id = pilar_data["id"]
    pilar_label = pilar_data["label"]
    pilar_score = pilar_data["score"]

    # Enriquecer context_str con los hallazgos refinados (SOTA + Fragmentos)
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

    # 1. Agente Escritor
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

        # 2. Agente Crítico (Refinado)
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

    # --- EPISTEMIC GRAPH RESOLUTION ---
    print("🧠 [Epistemic Engine] Ingestando contexto e inteligencia...")
    from infrastructure.epistemic_extractor import extract_triples_from_text
    from infrastructure.epistemic_graph import EpistemicGraph
    from infrastructure.text_utils import slugify

    graph = EpistemicGraph(client_id=slugify(client_name))
    entity_resolver = EntityResolutionEngine()
    ontology = OntologyRegistry()

    # 1. Extraer del OSINT (Baja Confianza)
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

    # 2. Extraer del Contexto Interno (Alta Confianza)
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

    # 3. Resolver la Verdad Absoluta
    resolved_truth = graph.get_resolved_context_string()

    # Inyectar al flujo
    intel_str_tangential = json.dumps(intel_data, indent=2, ensure_ascii=False)
    intel_str = f"--- VERDAD EPISTÉMICA RESUELTA ---\n{resolved_truth}\n\n--- DATOS OSINT CRUDOS (TANGENCIALES) ---\n{intel_str_tangential}"
    # ----------------------------------

    # Preparar contexto masivo
    intel_str = (
        build_client_context_text(raw_intel_data, tower_id=tower_id)
        if intel_packet
        else json.dumps(intel_data, indent=2, ensure_ascii=False)
    )

    try:
        from infrastructure.config_loader import (
            resolve_model_profile_for_role,
        )

        model_name = resolve_model_profile_for_role("section_writer")["model"]
    except Exception:
        model_name = "gemini-2.5-pro"

    # Agrupar respuestas por pilar
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
        # INYECTAR LA VERDAD REFINADA (SOTA) EN EL PILAR
        for p_find in refined_findings.get("pillar_findings", []):
            if p_find["pillar_id"] == p_id:
                p_data["refined_findings"] = p_find
                break

    print(f"🏗️ Generando Blueprint de Transformación para {tower_name}...")

    # Inicialización Normalizada (Contrato Estricto)
    blueprint_payload = get_default_blueprint_payload(
        client_name, tower_name, tower_id, intel_data
    )
    if intel_packet:
        blueprint_payload["client_context"] = intel_packet
    failed_pillars = []

    # PROCESAR PILARES EN SERIE PARA MÁXIMA CALIDAD
    for p_id in sorted(pillars_map.keys()):
        # Añadimos el SOTA y el refined finding al intel_str para que el Cerebro 2 lo respete
        # Limpiamos el hack del prompt
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
            p_result["target_score"] = get_target_maturity(intel_data, tower_id, 4.0)
            blueprint_analysis = p_result.get("pillar_analysis", p_result)

            # --- DETERMINISTIC DATA BYPASS (TIER 1 ELITE ARCHITECTURE) ---
            refined = pillars_map[p_id].get("refined_findings", {})
            initiatives = refined.get("candidate_initiatives", [])
            if initiatives:
                if "projects_todo" not in blueprint_analysis:
                    blueprint_analysis["projects_todo"] = []
                # Limpiamos las alucinaciones del LLM y forzamos el SOTA real
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
            # -------------------------------------------------------------

            blueprint_payload["pillars_analysis"].append(blueprint_analysis)
        else:
            failed_pillars.append(pillars_map[p_id]["label"])

    if failed_pillars:
        print("⚠️ Pilares sin respuesta válida: " + ", ".join(failed_pillars))

    if not blueprint_payload["pillars_analysis"]:
        raise RuntimeError(
            "No se pudo generar ningún análisis de pilar para el blueprint."
        )

    # AGENTE DE CIERRE: SNAPSHOT Y ROADMAP
    print("    -> Generando Snapshot Ejecutivo y Roadmap Estratégico...")
    closing_prompt = get_closing_orchestrator_prompt(
        tower_name=tower_name,
        pillars_analysis_json=json.dumps(blueprint_payload["pillars_analysis"]),
        intel_str=intel_str,
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
                    from infrastructure.governance import StructuralIntegrityGate

                    StructuralIntegrityGate.verify_dossier_logic(closing_data)
                    blueprint_payload.update(closing_data)
                    break
            except Exception as e:
                last_error = str(e)
                print(
                    f"    🚨 VIOLACIÓN DIPLOMÁTICA O ERROR: {e}. Reintentando Orquestador (Intento {attempt + 1})..."
                )
        if last_error:
            print(
                f"⚠️ Fallo crítico en el Orquestador tras 3 intentos. Último error: {last_error}"
            )
    except Exception as e:
        raise RuntimeError(f"Error en agente de cierre blueprint: {e}") from e

    # --- GRAPH-FIRST SYNCHRONIZATION (TIER 1 SOVEREIGN FABRIC) ---
    print(f"🔄 Sincronizando hallazgos de {tower_id} con el Epistemic Graph...")
    sync_findings_to_graph(
        graph=graph,
        entity_resolver=entity_resolver,
        ontology=ontology,
        blueprint_payload=blueprint_payload,
        tower_id=tower_id,
    )

    # Validación Final del Contrato con Pydantic
    try:
        blueprint_payload["_generation_metadata"] = {
            "artifact_type": "blueprint_payload",
            "artifact_version": "1.0.0",
        }
        # Forzamos validación para asegurar que el JSON resultante sea íntegro
        validated_model = BlueprintPayload.model_validate(blueprint_payload)
        final_payload_dict = validated_model.model_dump(by_alias=True)
    except Exception as val_err:
        raise RuntimeError(
            f"Error de validación en payload final del blueprint: {val_err}"
        ) from val_err

    # GUARDAR PAYLOAD
    output_path = resolve_blueprint_payload_path(client_name, tower_id)
    output_path.write_text(
        json.dumps(final_payload_dict, indent=2, ensure_ascii=False),
        encoding="utf-8-sig",
    )
    print(f"✅ Payload del Blueprint generado y validado: {output_path}")


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) < 3:
        print(
            "Uso: python -m application.run_tower_blueprint_engine <client> <tower_id>"
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
