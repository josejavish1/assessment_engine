"""
Módulo run_tower_blueprint_engine.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, cast

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from domain.ontology_registry import OntologyRegistry
from domain.prompts.blueprint_prompts import (
    get_blueprint_architect_instruction,
    get_closing_orchestrator_prompt,
    get_critic_prompt,
    get_pilar_architect_prompt,
    get_gravity_profiler_prompt,
    get_bid_manager_prompt,
)
from domain.schemas.blueprint import (
    ArchitecturalGravityProfile,
    BlueprintPayload,
    OrchestratorBlueprintDraft,
    PillarBlueprintDraft,
    ProjectCharterEnrichment,
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

    # --- DYNAMIC CONTEXT PROFILER (TIER 1 GRAVITY RESOLUTION) ---
    print("🔎 [Pre-flight] Calculando el Perfil de Gravedad Arquitectónica del cliente...")
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
    # -------------------------------------------------------------

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
            # SOTA 2026: Preserve the mathematically calculated target_score from the client intelligence dossier
            from infrastructure.client_intelligence import get_target_maturity
            p_result["target_score"] = get_target_maturity(intel_data, tower_id, 4.0)
            
            blueprint_analysis = p_result.get("pillar_analysis", p_result)

            # --- PROGRAMMATIC RAG CHECKER (GAP A: ZERO HALLUCINATION) ---
            # Create a normalized reference corpus from the inputs provided to the LLM
            corpus = (context_str + " " + enhanced_intel_str + " " + json.dumps(pillars_map[p_id]["answers"])).lower()
            import re
            corpus_clean = re.sub(r'\s+', ' ', corpus)

            for finding in blueprint_analysis.get("health_check_asis", []):
                evidence = finding.get("literal_evidence", "")
                if evidence and evidence != "No se proporcionó evidencia literal.":
                    evidence_clean = re.sub(r'\s+', ' ', evidence.lower())
                    # If the exact sequence (or a very close one) isn't in the corpus, flag it
                    if evidence_clean not in corpus_clean:
                        # Fallback: check if at least 70% of the words are in the corpus (to account for minor formatting differences like punctuation)
                        words = evidence_clean.split()
                        matched_words = sum(1 for w in words if w in corpus_clean)
                        if not words or (matched_words / len(words)) < 0.7:
                            finding["literal_evidence"] = "[ALERTA RAG] Cita literal no validada matemáticamente en el documento original."

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

    # --- DETERMINISTIC BYPASS DEFENSIVE RE-MAPPING (MANDATORY QUALITY GATE) ---
    # Asegura que las iniciativas técnicas detalladas SOTA se inyecten ANTES del cierre
    # para que el orquestador genere el roadmap con los nombres reales.
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
                            sota_projects.append({
                                "name": init.get("title", f"Iniciativa Estratégica {idx + 1}"),
                                "transformation_typology": init.get("typology", "Core Modernization"),
                                "business_case": init.get("business_case", ""),
                                "tech_objective": init.get("rationale", "Evolución técnica."),
                                "deliverables": init.get("deliverables", []),
                                "sizing": "L",
                                "duration": init.get("horizon", "Sin calendario detallado"),
                                "program_id": None
                            })
                        p_analysis["projects_todo"] = sota_projects
                    break

    # --- GRAPH-FIRST SYNCHRONIZATION (TIER 1 SOVEREIGN FABRIC) ---
    print(f"🔄 Sincronizando hallazgos de {tower_id} con el Epistemic Graph...")
    sync_findings_to_graph(
        graph=graph,
        entity_resolver=entity_resolver,
        ontology=ontology,
        blueprint_payload=blueprint_payload,
        tower_id=tower_id,
    )

    # --- SOVEREIGN POLICY ENGINE COMPILER (ZERO-DEFECT QUALITY GATE) ---
    # Analiza el Grafo y peina las incoherencias lógicas de forma determinista
    print("🛡️ [Sovereign QA] Ejecutando el Motor de Políticas Arquitectónicas...")
    try:
        from infrastructure.policy_engine import SovereignPolicyEngine
        engine = SovereignPolicyEngine(graph)
        blueprint_payload = engine.compile(blueprint_payload)
    except Exception as policy_err:
        print(f"⚠️ Error ejecutando Sovereign Policy Engine: {policy_err}")

    # Calculate ALE before closing to pass it to the orchestrator
    total_ale = 0.0
    for pilar in blueprint_payload.get("pillars_analysis", []):
        for finding in pilar.get("health_check_asis", []):
            val = finding.get("fair_ale_score")
            total_ale += float(val) if val is not None else 0.0

    # AGENTE DE CIERRE: SNAPSHOT Y ROADMAP
    print("    -> Generando Snapshot Ejecutivo y Roadmap Estratégico...")
    closing_prompt = get_closing_orchestrator_prompt(
        tower_name=tower_name,
        pillars_analysis_json=json.dumps(blueprint_payload["pillars_analysis"]),
        intel_str=intel_str,
        total_ale=total_ale
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
                    import difflib

                    StructuralIntegrityGate.verify_dossier_logic(closing_data)
                    
                    # --- MATHEMATICAL TRIBUNAL (REFLECTION LOOP VALIDATION) ---
                    # Extraer nombres reales de proyectos para validar dependencias y roadmap
                    valid_project_names = [
                        proj["name"]
                        for pilar in blueprint_payload.get("pillars_analysis", [])
                        for proj in pilar.get("projects_todo", [])
                    ]
                    
                    def fuzzy_match(name, choices, cutoff=0.6):
                        matches = difflib.get_close_matches(name, choices, n=1, cutoff=cutoff)
                        return matches[0] if matches else None

                    # Validar y autocorregir dependencias
                    invalid_deps = []
                    for dep in closing_data.get("external_dependencies", []):
                        dep_name = dep.get("depends_on")
                        if dep_name not in valid_project_names and dep_name not in ["Independiente", "Ninguna"]:
                            corrected = fuzzy_match(dep_name, valid_project_names)
                            if corrected:
                                dep["depends_on"] = corrected
                            else:
                                invalid_deps.append(dep_name)
                                
                    if invalid_deps:
                        raise ValueError(f"HAS INVENTADO DEPENDENCIAS. Los siguientes proyectos habilitadores no existen en la lista de proyectos aprobados: {invalid_deps}. Solo puedes usar proyectos reales.")
                        
                    # Validar y autocorregir roadmap
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
                        raise ValueError(f"HAS INVENTADO PROYECTOS EN EL ROADMAP. Los siguientes proyectos no existen en la lista de proyectos aprobados: {invalid_roadmap}.")
                        
                    missing_projects = set(valid_project_names) - mapped_projects
                    if missing_projects:
                        raise ValueError(f"HAS OMITIDO PROYECTOS DEL ROADMAP. Regla inquebrantable rota. Debes incluir TODOS los proyectos. Te has dejado estos: {list(missing_projects)}")

                    # Validar número de principios (Gap 1)
                    principles = closing_data.get("design_principles", [])
                    if len(principles) > 10:
                        raise ValueError(f"Demasiados principios de diseño ({len(principles)}). Condénsalos en un máximo de 5 a 7 principios maestros transversales para toda la torre.")

                    blueprint_payload.update(closing_data)
                    break
            except Exception as e:
                last_error = str(e)
                print(
                    f"    🚨 VIOLACIÓN DIPLOMÁTICA O ERROR: {e}. Reintentando Orquestador (Intento {attempt + 1})..."
                )
        if last_error and closing_data:
            print(
                f"⚠️ Fallo crítico en el Orquestador tras 3 intentos. Aplicando Degradación Elegante (Borrando dependencias inventadas y añadiendo proyectos huérfanos)..."
            )
            # Graceful degradation: Remove invalid dependencies and save what we have
            valid_deps = [d for d in closing_data.get("external_dependencies", []) if d.get("depends_on") in valid_project_names or d.get("depends_on") in ["Independiente", "Ninguna"]]
            closing_data["external_dependencies"] = valid_deps
            
            # Graceful degradation: Add missing projects to the last wave
            import difflib
            def f_match(name, choices, cutoff=0.6):
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

    # --- BID MANAGER AGENT (DEEP CHARTER ENRICHMENT) ---
    print("💼 [Bid Manager] Enriqueciendo proyectos con WBS, TCO, y ROI...")
    try:
        from domain.schemas.blueprint import ProjectCharterEnrichment
        from domain.prompts.blueprint_prompts import get_bid_manager_prompt

        bid_manager_agent = Agent(
            name="bid_manager_architect",
            model=model_name,
            instruction="Eres el Bid Manager de NTT DATA. Devuelve estrictamente el JSON pedido.",
            output_schema=ProjectCharterEnrichment,
        )
        app_bid_manager = AdkApp(agent=bid_manager_agent)

        async def enrich_project(p_analysis_idx, proj_idx, proj):
            # Resolve mitigated risk impact text and FAIR score
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
                mitigated_risk_impact=mitigated_risk_text
            )
            
            enrichment_data = await run_agent(
                app_bid_manager,
                user_id=f"bid_manager_{proj.get('node_id', proj_idx)}",
                message=prompt,
                schema=ProjectCharterEnrichment,
            )
            if enrichment_data:
                # Calculate FinOps deterministically using engine_config/rate_card.json
                rate_card_path = Path("engine_config/rate_card.json")
                if rate_card_path.exists():
                    try:
                        rate_data = json.loads(rate_card_path.read_text(encoding="utf-8-sig"))
                        rates = rate_data.get("tarifas_hora", {})
                        margin = rate_data.get("margenes", {}).get("consultoria", 0.45)
                        
                        total_cost = 0.0
                        for task in enrichment_data.get("wbs_breakdown", []):
                            profile = task.get("required_profile", "experto")
                            hours = task.get("estimated_hours", 0)
                            rate = rates.get(profile, 58) # fallback to experto
                            total_cost += (hours * rate)
                            
                        sell_price = total_cost / (1 - margin)
                        enrichment_data["opex_estimate"] = f"{sell_price:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
                        
                        sizing = proj.get("sizing", "M").upper()
                        if sizing in ["L", "XL"]:
                            enrichment_data["capex_estimate"] = "~150.000,00 € (Estimación paramétrica de licenciamiento Enterprise / Nodos físicos)"
                        else:
                            enrichment_data["capex_estimate"] = "Bajo / Nulo (Suscripciones cloud menores a 20.000€)"
                            
                    except Exception as finops_err:
                        print(f"⚠️ Error calculando FinOps matemático: {finops_err}")
                
                if "commercial_name" in enrichment_data and enrichment_data["commercial_name"]:
                    old_name = proj["name"]
                    new_name = enrichment_data["commercial_name"]
                    proj["name"] = new_name
                    
                    # Update roadmap references
                    for wave in blueprint_payload.get("roadmap", []):
                        wave["projects"] = [new_name if p == old_name else p for p in wave.get("projects", [])]
                        
                    # Update external dependencies references
                    for d in blueprint_payload.get("external_dependencies", []):
                        if d.get("project") == old_name:
                            d["project"] = new_name
                        if d.get("depends_on") == old_name:
                            d["depends_on"] = new_name
                    
                blueprint_payload["pillars_analysis"][p_analysis_idx]["projects_todo"][proj_idx].update(enrichment_data)

        enrichment_tasks = []
        for p_idx, p_analysis in enumerate(blueprint_payload.get("pillars_analysis", [])):
            for proj_idx, proj in enumerate(p_analysis.get("projects_todo", [])):
                enrichment_tasks.append(enrich_project(p_idx, proj_idx, proj))
                
        if enrichment_tasks:
            await asyncio.gather(*enrichment_tasks)
            print("✅ Enriquecimiento de Bid Manager completado.")
    except Exception as bid_err:
        print(f"⚠️ Error en Bid Manager Agent: {bid_err}")

    # --- DEFENSIVE CLIENT NAME SANITIZATION (AIRTIGHT QUALITY GATE) ---
    # Elimina placeholders bracketados de la IA como [Cliente] o [CLIENTE]
    def scrub_client_placeholders(obj, name):
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
    
    # --- COI (Cost of Inaction) MATHEMATICAL AGGREGATION ---
    total_ale = 0.0
    for pilar in blueprint_payload.get("pillars_analysis", []):
        for finding in pilar.get("health_check_asis", []):
            val = finding.get("fair_ale_score")
            total_ale += float(val) if val is not None else 0.0
    
    blueprint_payload["total_fair_ale"] = total_ale

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
