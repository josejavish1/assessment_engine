"""
Módulo run_executive_annex_synthesizer.py.
Implementa el flujo Top-Down: Toma el Blueprint y genera el resumen para el Anexo del CTO.
"""
import asyncio
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

import yaml
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.schemas.annex_synthesis import (
    AnnexPayload,
    GapRowAnnex,
    InitiativeAnnex,
    RiskItemAnnex,
)
from assessment_engine.schemas.blueprint import BlueprintPayload
from assessment_engine.schemas.common import VersionMetadata
from assessment_engine.scripts.build_case_input import read_text
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.scripts.lib.config_loader import (
    resolve_model_profile_for_role,
)
from assessment_engine.scripts.lib.contract_utils import robust_load_payload
from assessment_engine.scripts.lib.runtime_paths import (
    resolve_annex_template_payload_path,
    resolve_blueprint_payload_path,
    resolve_case_input_path,
    resolve_client_dir,
    resolve_client_intelligence_path,
)

ROOT = Path(__file__).resolve().parents[3]
PRIORITY_RANK = {"Alta": 0, "Media": 1, "Baja": 2}

# Helper functions (side-effect free)
def derive_maturity_band(score: float) -> str:
    if score >= 4.5:
        return "Optimizado"
    if score >= 3.5:
        return "Gestionado"
    if score >= 2.5:
        return "Definido"
    if score >= 1.5:
        return "Repetible"
    return "Inicial"

def infer_priority_from_size(sizing: str) -> str:
    text = str(sizing or "").strip().lower()
    if text in {"xs", "s"}:
        return "Alta"
    if text in {"m", "media", "medium"}:
        return "Media"
    if text in {"l", "xl", "large"}:
        return "Baja"
    return "Media"

def truncate_list(items, limit):
    return items[:limit] if isinstance(items, list) else items


def truncate_text(text: str, limit: int = 280) -> str:
    normalized = " ".join(str(text or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def take_complete_sentences(
    text: str,
    *,
    max_sentences: int = 2,
    max_chars: int = 360,
) -> str:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return ""

    protected = normalized
    for source, target in (
        ("p. ej.", "p<DOT> ej<DOT>"),
        ("p.ej.", "p<DOT>ej<DOT>"),
        ("ej.", "ej<DOT>"),
        ("etc.", "etc<DOT>"),
        ("vs.", "vs<DOT>"),
        ("Sr.", "Sr<DOT>"),
        ("Sra.", "Sra<DOT>"),
        ("Dr.", "Dr<DOT>"),
    ):
        protected = protected.replace(source, target)

    parts = re.split(r"(?<=[.!?])\s+", protected)
    output: list[str] = []
    for part in parts:
        part = " ".join(part.split()).replace("<DOT>", ".")
        if not part:
            continue
        candidate = " ".join(output + [part]).strip()
        if len(candidate) > max_chars and output:
            break
        output.append(part)
        if len(output) >= max_sentences:
            break

    result = " ".join(output).strip()
    if not result:
        clipped = normalized[: max_chars + 1]
        if len(clipped) < len(normalized) and " " in clipped:
            clipped = clipped.rsplit(" ", 1)[0]
        result = clipped.rstrip(" ,;:")

    if result and result[-1] not in ".!?":
        result += "."
    return result


def average(values: list[float], default: float = 0.0) -> float:
    return round(sum(values) / len(values), 1) if values else default


def unique_list(items: list[str], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        normalized = " ".join(str(item or "").split())
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
        if limit is not None and len(output) >= limit:
            break
    return output


def summarize_project_name(name: str) -> str:
    text = " ".join(str(name or "").split())
    if ":" in text:
        _, remainder = text.split(":", 1)
        if remainder.strip():
            return remainder.strip()
    return text


def build_executive_handover(blueprint: BlueprintPayload) -> dict[str, Any]:
    scores = [pillar.score for pillar in blueprint.pillars_analysis]
    target_scores = [pillar.target_score for pillar in blueprint.pillars_analysis]
    project_names = [
        summarize_project_name(project.initiative)
        for pillar in blueprint.pillars_analysis
        for project in pillar.projects_todo
    ]
    return {
        "tower_code": blueprint.document_meta.tower_code,
        "tower_name": blueprint.document_meta.tower_name,
        "global_score": average(scores),
        "global_band": derive_maturity_band(average(scores)),
        "target_score": average(target_scores, default=4.0),
        "bottom_line": blueprint.executive_snapshot.bottom_line,
        "cost_of_inaction": blueprint.executive_snapshot.cost_of_inaction,
        "business_impact": blueprint.executive_snapshot.business_impact,
        "structural_risks": truncate_list(
            blueprint.executive_snapshot.structural_risks, 5
        ),
        "decisions": truncate_list(blueprint.executive_snapshot.decisions, 4),
        "top_initiatives": unique_list(project_names, limit=6),
        "roadmap_waves": [wave.wave for wave in blueprint.roadmap],
    }


def lookup_dependency_display(
    initiative_name: str,
    external_dependencies: list[Any],
) -> str:
    matches = [
        dependency.depends_on
        for dependency in external_dependencies
        if str(dependency.project).strip().lower() == initiative_name.strip().lower()
    ]
    if not matches:
        return "Sin dependencias externas críticas identificadas"
    return ", ".join(matches)


def derive_gap_rows(blueprint: BlueprintPayload) -> tuple[list[str], list[GapRowAnnex]]:
    target_capabilities: list[str] = []
    gap_rows: list[GapRowAnnex] = []
    for pillar in sorted(blueprint.pillars_analysis, key=lambda item: item.score):
        primary_finding = pillar.health_check_asis[0] if pillar.health_check_asis else None
        if pillar.target_architecture_tobe.vision:
            target_capabilities.append(
                f"{pillar.pilar_name}: {take_complete_sentences(pillar.target_architecture_tobe.vision, max_sentences=2, max_chars=420)}"
            )
        gap_rows.append(
            GapRowAnnex(
                pillar=pillar.pilar_name,
                as_is_summary=take_complete_sentences(
                    primary_finding.risk_observed
                    if primary_finding
                    else f"Madurez actual {pillar.score:.1f}/5.0",
                    max_sentences=2,
                    max_chars=420,
                ),
                target_state=take_complete_sentences(
                    pillar.target_architecture_tobe.vision
                    or "Capacidad objetivo todavía no formalizada.",
                    max_sentences=2,
                    max_chars=420,
                ),
                key_gap=take_complete_sentences(
                    primary_finding.impact
                    if primary_finding
                    else "Persisten brechas técnicas y operativas que limitan la evolución de la torre.",
                    max_sentences=2,
                    max_chars=420,
                ),
            )
        )
    return unique_list(target_capabilities, limit=5), gap_rows[:6]


def derive_risks(blueprint: BlueprintPayload) -> list[RiskItemAnnex]:
    risks: list[RiskItemAnnex] = []
    for pillar in sorted(blueprint.pillars_analysis, key=lambda item: item.score):
        if not pillar.health_check_asis:
            continue
        finding = pillar.health_check_asis[0]
        mitigation_source = (
            summarize_project_name(pillar.projects_todo[0].initiative)
            if pillar.projects_todo
            else (
                pillar.target_architecture_tobe.design_principles[0]
                if pillar.target_architecture_tobe.design_principles
                else "Definir un plan de remediación específico para la capacidad afectada."
            )
        )
        risks.append(
            RiskItemAnnex(
                risk=take_complete_sentences(
                    f"{pillar.pilar_name}: {finding.target_state}",
                    max_sentences=1,
                    max_chars=220,
                ),
                impact=take_complete_sentences(
                    finding.impact,
                    max_sentences=2,
                    max_chars=420,
                ),
                probability="Alta" if pillar.score < 2.0 else "Media",
                mitigation_summary=take_complete_sentences(
                    mitigation_source,
                    max_sentences=2,
                    max_chars=320,
                ),
            )
        )
    return risks[:6]


def derive_priority_initiatives(blueprint: BlueprintPayload) -> list[InitiativeAnnex]:
    ranked: list[tuple[int, float, str, InitiativeAnnex]] = []
    for pillar in blueprint.pillars_analysis:
        for project in pillar.projects_todo:
            priority = infer_priority_from_size(project.sizing)
            ranked.append(
                (
                    PRIORITY_RANK.get(priority, 1),
                    pillar.score,
                    project.initiative,
                    InitiativeAnnex(
                        sequence=0,
                        initiative=summarize_project_name(project.initiative),
                        objective=take_complete_sentences(
                            project.objective,
                            max_sentences=2,
                            max_chars=420,
                        ),
                        priority=priority,
                        expected_outcome=take_complete_sentences(
                            project.expected_outcome,
                            max_sentences=2,
                            max_chars=420,
                        ),
                        dependencies_display=take_complete_sentences(
                            lookup_dependency_display(
                                project.initiative, blueprint.external_dependencies
                            ),
                            max_sentences=2,
                            max_chars=280,
                        ),
                    ),
                )
            )

    ranked.sort(key=lambda item: (item[0], item[1], item[2]))
    initiatives: list[InitiativeAnnex] = []
    for sequence, (_, _, _, item) in enumerate(ranked[:6], start=1):
        initiatives.append(item.model_copy(update={"sequence": sequence}))
    return initiatives


def derive_focus_areas(blueprint: BlueprintPayload) -> list[str]:
    initiatives = [
        summarize_project_name(project.initiative)
        for pillar in sorted(blueprint.pillars_analysis, key=lambda item: item.score)
        for project in pillar.projects_todo[:1]
    ]
    if initiatives:
        return unique_list(initiatives, limit=3)
    return unique_list(blueprint.executive_snapshot.decisions, limit=3)


def derive_pillar_executive_reading(pillar: Any) -> str:
    primary_finding = pillar.health_check_asis[0] if pillar.health_check_asis else None
    if primary_finding:
        return take_complete_sentences(primary_finding.impact)
    if pillar.target_architecture_tobe.vision:
        return take_complete_sentences(pillar.target_architecture_tobe.vision)
    return take_complete_sentences(
        "La capacidad requiere priorización ejecutiva para cerrar la brecha de madurez observada.",
    )


def enrich_annex_payload(
    result_payload: AnnexPayload,
    blueprint: BlueprintPayload,
    radar_chart_path: Path,
    run_id: str,
) -> AnnexPayload:
    scores = [pillar.score for pillar in blueprint.pillars_analysis]
    target_scores = [pillar.target_score for pillar in blueprint.pillars_analysis]
    avg_score = average(scores)
    avg_target_score = average(target_scores, default=4.0)
    target_capabilities, gap_rows = derive_gap_rows(blueprint)
    risks = derive_risks(blueprint)
    initiatives = derive_priority_initiatives(blueprint)
    design_principles = unique_list(
        [
            principle
            for pillar in blueprint.pillars_analysis
            for principle in pillar.target_architecture_tobe.design_principles
        ],
        limit=6,
    )

    result_payload.generation_metadata = VersionMetadata(
        artifact_type="annex_payload",
        artifact_version="1.1.0",
        source_version=(
            blueprint.generation_metadata.artifact_version
            if blueprint.generation_metadata
            else "unknown"
        ),
        run_id=run_id,
    )
    meta_dict = blueprint.document_meta.model_dump()
    meta_dict["report_variant"] = "short"
    meta_dict["source_blueprint_artifact_version"] = (
        blueprint.generation_metadata.artifact_version
        if blueprint.generation_metadata
        else "unknown"
    )
    if blueprint.generation_metadata and blueprint.generation_metadata.run_id:
        meta_dict["source_blueprint_run_id"] = blueprint.generation_metadata.run_id
    result_payload.document_meta = meta_dict

    result_payload.pillar_score_profile.pillars = [
        {
            "pillar_label": pillar.pilar_name,
            "score_display": str(pillar.score),
            "maturity_band": derive_maturity_band(pillar.score),
            "executive_reading": derive_pillar_executive_reading(pillar),
        }
        for pillar in blueprint.pillars_analysis
    ]
    if radar_chart_path.exists():
        result_payload.pillar_score_profile.radar_chart = str(radar_chart_path.resolve())

    result_payload.executive_summary.global_score = f"{avg_score} / 5.0"
    result_payload.executive_summary.global_band = derive_maturity_band(avg_score)
    if str(avg_target_score) not in str(result_payload.executive_summary.target_maturity):
        result_payload.executive_summary.target_maturity = f"{avg_target_score:.1f}"

    result_payload.domain_introduction.technological_domain = (
        result_payload.domain_introduction.technological_domain
        or blueprint.document_meta.tower_name
    )
    result_payload.domain_introduction.domain_objective = (
        result_payload.domain_introduction.domain_objective
        or blueprint.executive_snapshot.business_impact
    )
    result_payload.domain_introduction.evaluated_capabilities = [
        pillar.pilar_name for pillar in blueprint.pillars_analysis
    ]

    result_payload.sections.tobe.design_principles = design_principles
    if not result_payload.sections.tobe.vision:
        result_payload.sections.tobe.vision = (
            blueprint.cross_capabilities_analysis.transformation_paradigm
        )
    result_payload.sections.gap.target_capabilities = target_capabilities
    result_payload.sections.gap.gap_rows = gap_rows
    result_payload.sections.todo.priority_initiatives = initiatives
    result_payload.sections.risks.risks = risks
    result_payload.sections.conclusion.priority_focus_areas = derive_focus_areas(
        blueprint
    )
    return result_payload

def load_yaml_config(filename: str) -> dict:
    filepath = Path(__file__).resolve().parent.parent / "prompts" / "registry" / filename
    with filepath.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_synthesis_prompt(
    blueprint_data: dict,
    executive_handover: dict[str, Any],
    client_intelligence: dict,
    context_summary: str,
    config: dict,
) -> str:
    tower_name = (
        blueprint_data.get("document_meta", {}).get("tower_name", "la torre evaluada")
    )
    prompt = (
        f"Eres un {config['role']} con expertise en {config['expertise']}.\n"
        f"{config['context_description'].format(tower_name=tower_name)}\n\n"
        f"TAREA PRINCIPAL:\n{config['task']}\n\n"
        "HECHOS NO NEGOCIABLES PARA EL ANEXO EJECUTIVO:\n"
        f"{json.dumps(executive_handover, ensure_ascii=False, indent=2)}\n\n"
        "CONTEXTO ESTRATÉGICO DEL CLIENTE:\n"
        f"{json.dumps(client_intelligence, ensure_ascii=False, indent=2)}\n\n"
        "CONTEXTO DEL CASO / ENTREVISTA:\n"
        f"{context_summary or 'No hay contexto adicional disponible.'}\n\n"
        "BLUEPRINT TÉCNICO FUENTE:\n"
        f"{json.dumps(blueprint_data, ensure_ascii=False, indent=2)}\n\n"
        "INSTRUCCIONES ESPECÍFICAS:\n"
    )
    for idx, instruction in enumerate(config.get("instructions", []), start=1):
        prompt += f"{idx}. {instruction}\n"

    prompt += "\nREGLAS DE TONO:\n"
    for idx, rule in enumerate(config.get("tone_rules", []), start=1):
        prompt += f"{idx}. {rule}\n"

    prompt += f"\n{config.get('handover', '')}\n"
    prompt += "Devuelve exclusivamente el JSON final del anexo.\n"
    return prompt

# --- Pure Business Logic Function ---
async def generate_synthesis(
    blueprint: BlueprintPayload,
    client_intelligence: dict,
    context_summary: str,
    config: dict,
    radar_chart_path: Path,
    run_id: str
) -> Optional[AnnexPayload]:
    """
    Toma los datos de entrada, ejecuta el agente IA y devuelve el payload del anexo enriquecido.
    """
    blueprint_data = blueprint.model_dump(by_alias=True)
    executive_handover = build_executive_handover(blueprint)
    prompt = build_synthesis_prompt(
        blueprint_data=blueprint_data,
        executive_handover=executive_handover,
        client_intelligence=client_intelligence,
        context_summary=context_summary,
        config=config,
    )
    
    try:
        model_name = resolve_model_profile_for_role("section_writer")["model"]
    except Exception:
        model_name = "gemini-1.5-pro"

    agent = Agent(
        name="executive_synthesizer",
        model=model_name,
        instruction=f"Eres un {config['role']}. Tu misión es: {config['mission']}",
        output_schema=AnnexPayload
    )
    app = AdkApp(agent=agent)
    
    result = await run_agent(
        app,
        user_id=f"synthesizer_{blueprint.document_meta.tower_code}",
        message=prompt, # El prompt se construiría aquí como antes
        schema=AnnexPayload
    )
    
    if not result:
        return None

    result_payload = AnnexPayload.model_validate(result)
    return enrich_annex_payload(result_payload, blueprint, radar_chart_path, run_id)

# --- I/O Orchestrator Function ---
async def synthesize_annex(client_name: str, tower_id: str):
    """
    Orquesta el proceso de síntesis del anexo ejecutivo. Maneja I/O.
    """
    run_id = f"run_{uuid.uuid4()}"
    print(f"🧠 [Top-Down] Sintetizando Anexo Ejecutivo para {tower_id} (Run ID: {run_id})...")
    
    client_dir = resolve_client_dir(client_name)
    tower_dir = client_dir / tower_id
    blueprint_path = resolve_blueprint_payload_path(client_name, tower_id)
    output_path = resolve_annex_template_payload_path(client_name, tower_id)
    client_intelligence_path = resolve_client_intelligence_path(client_name)
    case_input_path = resolve_case_input_path(client_name, tower_id)
    radar_chart_path = tower_dir / "pillar_radar_chart.generated.png"
    
    if not blueprint_path.exists():
        print(f"❌ Error: No se encontró el Blueprint en {blueprint_path}")
        return

    blueprint = robust_load_payload(
        blueprint_path,
        BlueprintPayload,
        "Blueprint",
        mode="strict",
    )
    client_intelligence = json.loads(client_intelligence_path.read_text(encoding="utf-8-sig")) if client_intelligence_path.exists() else {}
    config = load_yaml_config("annex_executive_synthesizer.yaml")
    context_summary = ""
    if case_input_path.exists():
        case_input = json.loads(case_input_path.read_text(encoding="utf-8"))
        context_file = (
            case_input.get("_build_metadata", {}).get("context_file")
            or case_input.get("context_file")
        )
        if context_file and Path(context_file).exists():
            context_summary = read_text(Path(context_file))
    
    final_payload = await generate_synthesis(
        blueprint,
        client_intelligence,
        context_summary,
        config,
        radar_chart_path,
        run_id,
    )
    
    if final_payload:
        output_path.write_text(final_payload.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
        print(f"✅ Anexo Ejecutivo sintetizado con éxito: {output_path}")
    else:
        print("❌ Error al generar el anexo.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m assessment_engine.scripts.run_executive_annex_synthesizer <client> <tower>")
        sys.exit(1)
    asyncio.run(synthesize_annex(sys.argv[1], sys.argv[2]))
