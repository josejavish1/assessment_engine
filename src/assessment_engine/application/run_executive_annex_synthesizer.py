import logging
logger = logging.getLogger(__name__)
import asyncio
import json
import re
import sys
import uuid
from importlib import import_module
from pathlib import Path
from typing import IO, Any, Optional, Protocol, cast

"""
Módulo run_executive_annex_synthesizer.py.
Implementa el flujo Top-Down: Toma el Blueprint y genera el resumen para el Anexo del CTO.
"""

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.application.build_case_input import read_text
from assessment_engine.domain.maturity_band import (
    ANNEX_MATURITY_BANDS,
    resolve_maturity_band,
)
from assessment_engine.domain.schemas.annex_synthesis import (
    AnnexPayload,
    GapRowAnnex,
    InitiativeAnnex,
    RiskItemAnnex,
)
from assessment_engine.domain.schemas.blueprint import BlueprintPayload
from assessment_engine.domain.schemas.common import VersionMetadata
from assessment_engine.infrastructure.ai_client import run_agent
from assessment_engine.infrastructure.client_intelligence import (
    load_client_intelligence_legacy_view,
)
from assessment_engine.infrastructure.config_loader import (
    resolve_model_for_role,
)
from assessment_engine.infrastructure.contract_utils import robust_load_payload
from assessment_engine.infrastructure.runtime_paths import (
    resolve_annex_template_payload_path,
    resolve_blueprint_payload_path,
    resolve_case_input_path,
    resolve_client_dir,
    resolve_client_intelligence_path,
)

ROOT = Path(__file__).resolve().parents[3]
PRIORITY_RANK = {"Alta": 0, "Media": 1, "Baja": 2}


class _YamlModule(Protocol):
    def safe_load(self, stream: IO[str]) -> Any: ...


# The following utility functions are architecturally constrained to be pure; they must not produce side effects and their output must depend solely on their input.
def derive_maturity_band(score: float, locale: str | None = None) -> str:
    return resolve_maturity_band(score, ANNEX_MATURITY_BANDS, locale=locale)["label"]


def infer_initiative_priority(project: Any, pillar_score: float = 3.0) -> str:
    """Derives strategic priority based on risk mitigation, horizon duration, and pillar maturity gap."""
    explicit_priority = getattr(project, "priority", None) or (
        project.get("priority") if isinstance(project, dict) else None
    )
    if explicit_priority and str(explicit_priority).strip().capitalize() in {"Alta", "Media", "Baja"}:
        return str(explicit_priority).strip().capitalize()

    duration = str(getattr(project, "duration", "") or (project.get("duration") if isinstance(project, dict) else "")).lower()
    b_case = str(getattr(project, "business_case", "") or (project.get("business_case") if isinstance(project, dict) else "")).lower()
    is_direct_mitigation = "mitigación directa" in b_case or "vulnerabilidad crítica" in b_case
    is_short_term = any(k in duration for k in ["corto", "horizonte 1", "h1", "inmediato", "mes 1", "mes 2", "mes 3"])

    if pillar_score < 2.2 and (is_direct_mitigation or is_short_term):
        return "Alta"
    if is_direct_mitigation and is_short_term:
        return "Alta"
    if "nis2" in b_case and is_short_term:
        return "Alta"

    is_long_term = any(k in duration for k in ["horizonte 3", "h3", "largo plazo", "mes 18", "mes 24"])
    if pillar_score >= 3.8 or is_long_term:
        return "Baja"

    return "Media"


def truncate_list(items, limit) -> Any:
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
        primary_finding = (
            pillar.health_check_asis[0] if pillar.health_check_asis else None
        )
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
            priority = infer_initiative_priority(project, pillar.score)
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


def derive_pillar_executive_reading(pillar: Any, idx: int = 0) -> str:
    score = pillar.score
    band = derive_maturity_band(score)
    formatted_score = f"{score:.2f}".replace(".", ",")
    
    findings = pillar.health_check_asis or []
    if not findings:
        return (
            f"**Situación de Capacidades (KPIs):**\n"
            f"La capacidad presenta un nivel de madurez '{band}' ({formatted_score} / 5,00). "
            f"No se han registrado hallazgos ni brechas críticas específicas en el perímetro de evaluación.\n\n"
            f"**Brechas y Consecuencias Operativas:**\n"
            f"La plataforma opera de forma estable, sin identificarse limitaciones de continuidad de negocio o cuellos de botella de infraestructura materiales.\n\n"
            f"**Justificación de la Nota:**\n"
            f"La puntuación refleja un estado consistente de operaciones, recomendado para sostener el catálogo de servicios actual."
        )
    
    # Sort findings by vulnerability_level (descending) or fair_ale_score (descending)
    def get_ale(f):
        return getattr(f, "fair_ale_score", 0.0) or 0.0
    def get_vuln(f):
        return getattr(f, "vulnerability_level", 3) or 3
        
    sorted_findings = sorted(findings, key=lambda x: (get_vuln(x), get_ale(x)), reverse=True)
    
    # Gaps (worst findings: vuln >= 4 or first 2)
    gaps_findings = [f for f in sorted_findings if get_vuln(f) >= 4]
    if not gaps_findings:
        gaps_findings = sorted_findings[:1]
        
    # Stable (vulnerability < 4 or remaining findings)
    stable_findings = [f for f in sorted_findings if f not in gaps_findings]
    
    # Extract capability names
    gaps_caps = [f.target_state for f in gaps_findings if f.target_state]
    stable_caps = [f.target_state for f in stable_findings if f.target_state]
    
    # Deterministic variation index based on index
    v_idx = idx % 3
    
    # 1. Situación de Capacidades
    prose_caps = []
    
    if v_idx == 0:
        prose_caps.append(f"El diagnóstico para el dominio de {pillar.pilar_name} sitúa su nivel de madurez en un rango '{band}' ({formatted_score} / 5,00), evidenciando margen de consolidación.")
    elif v_idx == 1:
        prose_caps.append(f"La evaluación de capacidades en el perímetro de {pillar.pilar_name} refleja un nivel de control '{band}' ({formatted_score} / 5,00).")
    else:
        prose_caps.append(f"Con una puntuación de {formatted_score} sobre 5,00, el pilar {pillar.pilar_name} se clasifica cualitativamente en la banda de '{band}', mostrando un comportamiento heterogéneo.")
    
    if stable_caps:
        caps_str = ", ".join(stable_caps[:3])
        if v_idx == 0:
            prose_caps.append(f"Este resultado se apoya en un desempeño sólido y consistente en capacidades clave como {caps_str}.")
        elif v_idx == 1:
            prose_caps.append(f"En este ámbito, se detectan fortalezas funcionales y prácticas estables en {caps_str}.")
        else:
            prose_caps.append(f"La plataforma demuestra solvencia operativa y control adecuado en {caps_str}.")
    else:
        prose_caps.append("Se identifican necesidades de consolidación generalizada en las capacidades evaluadas.")
        
    if gaps_caps:
        caps_str = ", ".join(gaps_caps[:3])
        if v_idx == 0:
            prose_caps.append(f"No obstante, se identifican brechas de madurez relevantes en {caps_str}.")
        elif v_idx == 1:
            prose_caps.append(f"Sin embargo, existen debilidades y áreas de mejora prioritarias en {caps_str}.")
        else:
            prose_caps.append(f"En contraposición, el entorno presenta desafíos operativos materiales en {caps_str}.")
        
    situacion_text = " ".join(prose_caps)
    
    # 2. Brechas y Consecuencias Operativas
    main_gaps = []
    main_risks = []
    for f in gaps_findings[:2]:
        fd = (f.risk_observed or f.finding or "").strip()
        br = (f.impact or f.business_risk or "").strip()
        if fd:
            fd_sent = fd.split(".")[0] + "."
            main_gaps.append(fd_sent)
        if br:
            br_sent = br.split(".")[0] + "."
            main_risks.append(br_sent)
            
    if not main_gaps:
        main_gaps = ["Se registran carencias en la automatización y predictibilidad de las operaciones de infraestructura."]
    if not main_risks:
        main_risks = ["Esto eleva el riesgo de incidentes operativos y limita la agilidad frente al crecimiento de la demanda."]
        
    gaps_str_joined = " ".join(main_gaps)
    risks_str_joined = " ".join(main_risks)
    
    if v_idx == 0:
        gaps_text = f"La limitación principal reside en que {gaps_str_joined} Esto deriva en un impacto directo de negocio, destacando {risks_str_joined}"
    elif v_idx == 1:
        gaps_text = f"El análisis técnico identifica un cuello de botella relevante en {gaps_str_joined} En consecuencia, esto genera una exposición operativa directa caracterizada por {risks_str_joined}"
    else:
        gaps_text = f"Se constata una carencia material en {gaps_str_joined} lo cual expone a la organización a consecuencias de negocio como {risks_str_joined}"
    
    # 3. Justificación de la Nota
    worst_cap = gaps_caps[0] if gaps_caps else "las capacidades críticas"
    
    if v_idx == 0:
        justificacion_text = (
            f"La calificación final del pilar ({formatted_score}) se encuentra sustentada por el nivel de madurez base, "
            f"pero se ve penalizada de forma directa por las deficiencias críticas detectadas en '{worst_cap}', "
            f"que actúa como el factor limitante para el desarrollo global de esta plataforma."
        )
    elif v_idx == 1:
        justificacion_text = (
            f"La puntuación de {formatted_score} refleja un equilibrio entre las fortalezas de la plataforma y el lastre "
            f"que suponen las brechas en '{worst_cap}', las cuales restan resiliencia y limitan la escalabilidad operativa."
        )
    else:
        justificacion_text = (
            f"El score consolidado del pilar ({formatted_score}) se ve severamente condicionado por la inmadurez de la capacidad "
            f"de '{worst_cap}', la cual penaliza el resultado global y actúa como el principal obstáculo para consolidar un nivel de control estructural robusto en la operación actual."
        )
    
    full_narrative = (
        f"**Situación de Capacidades (KPIs):**\n{situacion_text}\n\n"
        f"**Brechas y Consecuencias Operativas:**\n{gaps_text}\n\n"
        f"**Justificación de la Nota:**\n{justificacion_text}"
    )
    return full_narrative


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
        getattr(blueprint, "design_principles", []),
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
            "executive_reading": derive_pillar_executive_reading(pillar, idx),
        }
        for idx, pillar in enumerate(blueprint.pillars_analysis)
    ]
    if radar_chart_path.exists():
        result_payload.pillar_score_profile.radar_chart = str(
            radar_chart_path.resolve()
        )

    result_payload.executive_summary.global_score = f"{avg_score} / 5.0"
    result_payload.executive_summary.global_band = derive_maturity_band(avg_score)
    if str(avg_target_score) not in str(
        result_payload.executive_summary.target_maturity
    ):
        result_payload.executive_summary.target_maturity = f"{avg_target_score:.1f}"

    # Calculate and inject financial Cost of Inaction (COI) deterministically
    global_fair_ale = blueprint.total_fair_ale or 0.0
    portfolio_p90 = getattr(blueprint, "total_fair_p90", None)
    if not portfolio_p90 and hasattr(blueprint, "model_dump"):
        portfolio_p90 = blueprint.model_dump().get("total_fair_p90")

    if portfolio_p90 and float(portfolio_p90) > 0:
        global_fair_p90 = float(portfolio_p90)
    else:
        p90_raw = 0.0
        for p in blueprint.pillars_analysis:
            for hc in p.health_check_asis:
                p90_raw += hc.fair_p90_score or 0.0
        diversification = 1.0 / (len(blueprint.pillars_analysis) ** 0.35) if blueprint.pillars_analysis else 1.0
        global_fair_p90 = p90_raw * diversification

    coi_extreme_3y = global_fair_p90 + (global_fair_ale * 2)

    formatted_ale = f"{global_fair_ale:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    formatted_3y_ord = f"{(global_fair_ale * 3):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    formatted_3y_ext = f"{coi_extreme_3y:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    from assessment_engine.domain.schemas.annex_synthesis import FinancialCOIProfile
    result_payload.executive_summary.financial_coi = FinancialCOIProfile(
        annual_loss_exposure=f"{formatted_ale} €",
        coi_3y_ordinary=f"{formatted_3y_ord} €",
        coi_3y_extreme=f"{formatted_3y_ext} €"
    )

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
    yaml = cast(_YamlModule, import_module("yaml"))
    filepath = (
        Path(__file__).resolve().parent.parent
        / "domain"
        / "prompts"
        / "registry"
        / filename
    )
    with filepath.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_synthesis_prompt(
    blueprint_data: dict,
    executive_handover: dict[str, Any],
    client_intelligence: dict,
    context_summary: str,
    config: dict,
) -> str:
    tower_name = blueprint_data.get("document_meta", {}).get(
        "tower_name", "la torre evaluada"
    )
    
    # Calculate dynamic temporal values based on current actual system year (timeless engineering)
    import datetime
    from assessment_engine.infrastructure.text_utils import format_date_spanish
    now = datetime.datetime.now()
    current_year = now.year
    
    current_date_str = format_date_spanish().upper()  # Standard uppercase month and year
    active_strategic_range = f"{current_year - 1}-{current_year + 3}"  # e.g., 2026-2030
    future_investment_horizon_range = f"{current_year + 1}-{current_year + 3}/{current_year + 4}" # e.g., 2028-2030/2031
    obsolete_strategic_range = f"{current_year - 6}-{current_year - 2}" # e.g., 2021-2025

    prompt = (
        f"Eres un {config['role']} con expertise en {config['expertise']}.\n"
        f"{config['context_description'].format(tower_name=tower_name)}\n\n"
        f"TAREA PRINCIPAL:\n{config['task']}\n\n"
        f"{config['non_negotiable_facts_header']}\n"
        f"{json.dumps(executive_handover, ensure_ascii=False, indent=2)}\n\n"
        f"{config['client_strategy_header']}\n"
        f"{json.dumps(client_intelligence, ensure_ascii=False, indent=2)}\n\n"
        f"{config['interview_context_header']}\n"
        f"{context_summary or 'No hay contexto adicional disponible.'}\n\n"
        f"{config['source_blueprint_header']}\n"
        f"{json.dumps(blueprint_data, ensure_ascii=False, indent=2)}\n\n"
        f"{config['specific_instructions_header']}\n"
    )
    for idx, instruction in enumerate(config.get("instructions", []), start=1):
        if isinstance(instruction, str):
            instruction = instruction.format(
                current_date_str=current_date_str,
                active_strategic_range=active_strategic_range,
                future_investment_horizon_range=future_investment_horizon_range,
                obsolete_strategic_range=obsolete_strategic_range,
            )
        prompt += f"{idx}. {instruction}\n"

    prompt += f"\n{config['tone_rules_header']}\n"
    for idx, rule in enumerate(config.get("tone_rules", []), start=1):
        if isinstance(rule, str):
            rule = rule.format(
                current_date_str=current_date_str,
                active_strategic_range=active_strategic_range,
                future_investment_horizon_range=future_investment_horizon_range,
                obsolete_strategic_range=obsolete_strategic_range,
            )
        prompt += f"{idx}. {rule}\n"

    prompt += f"\n{config.get('handover', '')}\n"
    prompt += f"{config.get('final_handover_instruction', '')}\n"
    return prompt


#
async def generate_synthesis(
    blueprint: BlueprintPayload,
    client_intelligence: dict,
    context_summary: str,
    config: dict,
    radar_chart_path: Path,
    run_id: str,
) -> Optional[AnnexPayload]:
    """Executes the core synthesis logic by processing input data through the specified AI agent to produce an enriched annex payload. This function is designed to be pure, encapsulating all business logic without external side effects."""
    blueprint_data = blueprint.model_dump(by_alias=True)
    executive_handover = build_executive_handover(blueprint)
    prompt = build_synthesis_prompt(
        blueprint_data=blueprint_data,
        executive_handover=executive_handover,
        client_intelligence=client_intelligence,
        context_summary=context_summary,
        config=config,
    )

    model_name = resolve_model_for_role("section_writer", default_model="gemini-2.5-pro")

    agent = Agent(
        name="executive_synthesizer",
        model=model_name,
        instruction=f"Eres un {config['role']}. Tu misión es: {config['mission']}",
        output_schema=AnnexPayload,
    )
    app = AdkApp(agent=agent)

    result = None
    last_error = ""
    for attempt in range(3):
        try:
            msg = prompt
            if last_error:
                msg += f"\n\n🚨 VIOLACIÓN DE PROTOCOLO EN INTENTO ANTERIOR:\n{last_error}\nCorrige el texto inmediatamente.\n"
            result = await run_agent(
                app,
                user_id=f"synthesizer_{blueprint.document_meta.tower_code}",
                message=msg,
                schema=AnnexPayload,
            )

            if result:
                from assessment_engine.infrastructure.governance import (
                    StructuralIntegrityGate,
                )

                StructuralIntegrityGate.verify_dossier_logic(result)
                break
        except Exception as e:
            last_error = str(e)
            print(
                f"    🚨 VIOLACIÓN DIPLOMÁTICA O ERROR: {e}. Reintentando Anexo (Intento {attempt + 1})..."
            )

    if last_error:
        print(
            f"⚠️ Fallo crítico en el Sintetizador de Anexo tras 3 intentos. Último error: {last_error}"
        )

    if not result:
        return None

    result_payload = AnnexPayload.model_validate(result)
    return enrich_annex_payload(result_payload, blueprint, radar_chart_path, run_id)


#
async def synthesize_annex(client_name: str, tower_id: str):
    """Coordinates the complete synthesis process for the executive annex. This function serves as the primary entry point, handling all I/O operations and orchestrating the data processing pipeline."""
    run_id = f"run_{uuid.uuid4()}"
    print(
        f"🧠 [Top-Down] Sintetizando Anexo Ejecutivo para {tower_id} (Run ID: {run_id})..."
    )

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
    client_intelligence = load_client_intelligence_legacy_view(client_intelligence_path)
    config = load_yaml_config("annex_executive_synthesizer.yaml")
    context_summary = ""
    if case_input_path.exists():
        case_input = json.loads(case_input_path.read_text(encoding="utf-8"))
        context_file = case_input.get("_build_metadata", {}).get(
            "context_file"
        ) or case_input.get("context_file")
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
        content = final_payload.model_dump_json(indent=2, by_alias=True)
        
        # European Spanish localization: Replace 'sistémico/sistémica' with 'estructural'
        content = content.replace("sistémicas", "estructurales")
        content = content.replace("sistémicos", "estructurales")
        content = content.replace("Sistémicas", "Estructurales")
        content = content.replace("Sistémicos", "Estructurales")
        content = content.replace("sistémica", "estructural")
        content = content.replace("sistémico", "estructural")
        content = content.replace("Sistémica", "Estructural")
        content = content.replace("Sistémico", "Estructural")

        # Spelling corrections for 'múltiples'
        content = content.replace("mùltiples", "múltiples")
        content = content.replace("Mùltiples", "Múltiples")
        content = content.replace("móltiples", "múltiples")
        content = content.replace("Móltiples", "Múltiples")
        content = content.replace("multiples", "múltiples")
        content = content.replace("Multiples", "Múltiples")

        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        try:
            tmp_path.write_text(content, encoding="utf-8")
            tmp_path.replace(output_path)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except (OSError, ValueError, KeyError, AttributeError) as ex:

                    logger.debug(f"[Fallback] Excepción controlada: {ex}")
        print(f"✅ Anexo Ejecutivo sintetizado con éxito: {output_path}")
    else:
        print("❌ Error al generar el anexo.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Uso: python -m assessment_engine.application.run_executive_annex_synthesizer <client> <tower>"
        )
        sys.exit(1)
    asyncio.run(synthesize_annex(sys.argv[1], sys.argv[2]))
