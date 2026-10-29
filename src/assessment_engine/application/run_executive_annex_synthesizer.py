import logging

logger = logging.getLogger(__name__)
import asyncio
import json
import os
import re
import sys
import uuid
from importlib import import_module
from pathlib import Path
from typing import IO, Any, Optional, Protocol, cast

"""
Module run_executive_annex_synthesizer.py.
Implements Top-Down flow: Ingests Blueprint and synthesizes CTO Executive Annex.
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
from assessment_engine.infrastructure.localization import format_number, t
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
    """Derive maturity band according to architectural specification."""
    return resolve_maturity_band(score, ANNEX_MATURITY_BANDS, locale=locale)["label"]


def infer_initiative_priority(
    project: Any, locale: str | None = None, pillar_score: float = 3.0
) -> str:
    """Derives strategic priority based on risk mitigation, horizon duration, and pillar maturity gap."""
    from assessment_engine.infrastructure.localization import t

    target_locale = locale or "en"
    explicit_priority = getattr(project, "priority", None) or (
        project.get("priority") if isinstance(project, dict) else None
    )
    if explicit_priority:
        raw_p = str(explicit_priority).strip().lower()
        if raw_p in {"alta", "high", "hoch", "haute", "高"}:
            return t("priority_high", locale=target_locale)
        if raw_p in {"baja", "low", "niedrig", "basse", "低"}:
            return t("priority_low", locale=target_locale)
        return t("priority_medium", locale=target_locale)

    duration = str(
        getattr(project, "duration", "")
        or (project.get("duration") if isinstance(project, dict) else "")
    ).lower()
    b_case = str(
        getattr(project, "business_case", "")
        or (project.get("business_case") if isinstance(project, dict) else "")
    ).lower()
    is_direct_mitigation = (
        "direct mitigation" in b_case.lower() or "critical vulnerability" in b_case.lower() or "mitigacion" in b_case.lower()
    )
    from assessment_engine.infrastructure.runtime_paths import ROOT
    import json
    dur_cfg = {}
    p_dur = ROOT / "engine_config/locales_asis_annex.json"
    if p_dur.exists():
        try:
            dur_cfg = json.loads(p_dur.read_text(encoding="utf-8")).get("duration_priority_keywords", {})
        except (OSError, ValueError, KeyError) as ex:
            logger.debug("[Config] Duration priority keywords loading failed: %s", ex)

    short_keys = dur_cfg.get("short_term", ["h1", "month 1", "month 2", "month 3"])
    long_keys = dur_cfg.get("long_term", ["h3", "month 18", "month 24", "long term"])

    is_short_term = any(k in duration for k in short_keys)

    if (
        (pillar_score < 2.2 and (is_direct_mitigation or is_short_term))
        or (is_direct_mitigation and is_short_term)
        or ("nis2" in b_case and is_short_term)
    ):
        return t("priority_high", locale=target_locale)

    is_long_term = any(k in duration for k in long_keys)
    if pillar_score >= 3.8 or is_long_term:
        return t("priority_low", locale=locale)

    return t("priority_medium", locale=locale)


def truncate_list(items, limit) -> Any:
    """Truncate list according to architectural specification."""
    return items[:limit] if isinstance(items, list) else items


def truncate_text(text: str, limit: int = 280) -> str:
    """Truncate text according to architectural specification."""
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
    """Take complete sentences according to architectural specification."""
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
    """Average  according to architectural specification."""
    return round(sum(values) / len(values), 1) if values else default


def unique_list(items: list[str], limit: int | None = None) -> list[str]:
    """Unique list according to architectural specification."""
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
    """Preserves exact canonical project title for strict cross-document consistency."""
    return " ".join(str(name or "").split()).strip()


def build_executive_handover(blueprint: BlueprintPayload) -> dict[str, Any]:
    """Build executive handover according to architectural specification."""
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
    """Lookup dependency display according to architectural specification."""
    matches = [
        dependency.depends_on
        for dependency in external_dependencies
        if str(dependency.project).strip().lower() == initiative_name.strip().lower()
    ]
    if not matches:
        return "No critical external dependencies identified"
    return ", ".join(matches)


def derive_gap_rows(blueprint: BlueprintPayload) -> tuple[list[str], list[GapRowAnnex]]:
    """Derive gap rows according to architectural specification."""
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
                    else f"Current maturity {pillar.score:.1f}/5.0",
                    max_sentences=2,
                    max_chars=420,
                ),
                target_state=take_complete_sentences(
                    pillar.target_architecture_tobe.vision
                    or "Target capability not yet formalized.",
                    max_sentences=2,
                    max_chars=420,
                ),
                key_gap=take_complete_sentences(
                    primary_finding.impact
                    if primary_finding
                    else "Technical and operational gaps persist, constraining tower evolution.",
                    max_sentences=2,
                    max_chars=420,
                ),
            )
        )
    return unique_list(target_capabilities, limit=5), gap_rows[:6]


def derive_risks(
    blueprint: BlueprintPayload, locale: str | None = None
) -> list[RiskItemAnnex]:
    """Derive risks according to architectural specification."""
    from assessment_engine.infrastructure.localization import t

    meta = getattr(blueprint, "document_meta", None)
    target_locale = (
        locale
        or getattr(meta, "language", None)
        or getattr(meta, "doc_lang", None)
        or "en"
    )

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
                else "Define a specific remediation plan for the affected capability."
            )
        )
        prob_str = (
            t("priority_high", locale=target_locale)
            if pillar.score < 2.0
            else t("priority_medium", locale=target_locale)
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
                probability=prob_str,
                mitigation_summary=take_complete_sentences(
                    mitigation_source,
                    max_sentences=2,
                    max_chars=320,
                ),
            )
        )
    return risks[:6]


def derive_priority_initiatives(
    blueprint: BlueprintPayload, locale: str | None = None
) -> list[InitiativeAnnex]:
    """Derive priority initiatives according to architectural specification."""
    meta = getattr(blueprint, "document_meta", None)
    target_locale = (
        locale
        or getattr(meta, "language", None)
        or getattr(meta, "doc_lang", None)
        or "en"
    )
    ranked: list[tuple[int, float, str, InitiativeAnnex]] = []
    for pillar in blueprint.pillars_analysis:
        for project in pillar.projects_todo:
            priority = infer_initiative_priority(project, locale=target_locale, pillar_score=pillar.score)
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
                                project.initiative,
                                blueprint.external_dependencies,
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
    """Derive focus areas according to architectural specification."""
    initiatives = [
        summarize_project_name(project.initiative)
        for pillar in sorted(blueprint.pillars_analysis, key=lambda item: item.score)
        for project in pillar.projects_todo[:1]
    ]
    if initiatives:
        return unique_list(initiatives, limit=3)
    return unique_list(blueprint.executive_snapshot.decisions, limit=3)


def _format_pillar_kpis_narrative(
    pillar_name: str,
    band: str,
    formatted_score: str,
    stable_caps: list[str],
    gaps_caps: list[str],
    v_idx: int,
    locale: str,
) -> str:
    prose = [
        t("asis_pillar_kpis_narrative", locale=locale, pillar_name=pillar_name, band=band, formatted_score=formatted_score)
    ]
    if stable_caps:
        prose.append(
            t("asis_pillar_stable_caps", locale=locale, caps=", ".join(stable_caps[:3]))
        )
    if gaps_caps:
        prose.append(
            t("asis_pillar_gaps_caps", locale=locale, caps=", ".join(gaps_caps[:3]))
        )
    return " ".join(prose)


def _format_pillar_gaps_narrative(gaps_findings: list[Any], locale: str) -> str:
    main_gaps = []
    main_risks = []
    for f in gaps_findings[:2]:
        fd = (
            getattr(f, "risk_observed", None) or getattr(f, "finding", None) or ""
        ).strip()
        br = (
            getattr(f, "impact", None) or getattr(f, "business_risk", None) or ""
        ).strip()
        if fd:
            main_gaps.append(fd.split(".")[0] + ".")
        if br:
            main_risks.append(br.split(".")[0] + ".")

    gaps_str = (
        " ".join(main_gaps)
        or t("asis_pillar_default_gap", locale=locale)
    )
    risks_str = " ".join(main_risks) or t("asis_pillar_default_risk", locale=locale)
    return t("asis_pillar_gaps_narrative", locale=locale, gaps_str=gaps_str, risks_str=risks_str)


def _format_pillar_score_justification(formatted_score: str, worst_cap: str, locale: str) -> str:
    return t("asis_pillar_score_justification", locale=locale, formatted_score=formatted_score, worst_cap=worst_cap)


def derive_pillar_executive_reading(
    pillar: Any, locale: str, idx: int = 0
) -> str:
    """Derive pillar executive reading with modular structure and low cognitive complexity."""
    score = pillar.score
    band = derive_maturity_band(score, locale=locale)
    formatted_score = format_number(score, locale=locale, decimals=2)

    hdr_kpis = t("asis_header_kpis_status", locale=locale)
    hdr_gaps = t("asis_header_gaps_consequences", locale=locale)
    hdr_just = t("asis_header_score_justification", locale=locale)

    findings = pillar.health_check_asis or []
    if not findings:
        empty_kpis = t("asis_pillar_empty_kpis", locale=locale, band=band, formatted_score=formatted_score)
        empty_gaps = t("asis_pillar_empty_gaps", locale=locale)
        empty_just = t("asis_pillar_empty_justification", locale=locale)
        return (
            f"**{hdr_kpis}**\n{empty_kpis}\n\n"
            f"**{hdr_gaps}**\n{empty_gaps}\n\n"
            f"**{hdr_just}**\n{empty_just}"
        )

    def get_ale(f):
        return getattr(f, "fair_ale_score", 0.0) or 0.0

    def get_vuln(f):
        return getattr(f, "vulnerability_level", 3) or 3

    sorted_findings = sorted(
        findings, key=lambda x: (get_vuln(x), get_ale(x)), reverse=True
    )
    gaps_findings = [f for f in sorted_findings if get_vuln(f) >= 4] or sorted_findings[
        :1
    ]
    stable_findings = [f for f in sorted_findings if f not in gaps_findings]

    gaps_caps = [
        f.target_state for f in gaps_findings if getattr(f, "target_state", None)
    ]
    stable_caps = [
        f.target_state for f in stable_findings if getattr(f, "target_state", None)
    ]
    worst_cap = gaps_caps[0] if gaps_caps else "the critical capabilities"

    v_idx = idx % 3
    kpis_text = _format_pillar_kpis_narrative(
        pillar.pilar_name, band, formatted_score, stable_caps, gaps_caps, v_idx, locale=locale
    )
    gaps_text = _format_pillar_gaps_narrative(gaps_findings, locale=locale)
    justification_text = _format_pillar_score_justification(formatted_score, worst_cap, locale=locale)

    return (
        f"**{hdr_kpis}**\n{kpis_text}\n\n"
        f"**{hdr_gaps}**\n{gaps_text}\n\n"
        f"**{hdr_just}**\n{justification_text}"
    )


def _extract_existing_pillar_readings(result_payload: Any) -> dict[str, str]:
    """Extract existing executive readings from pillar score profile if present."""
    readings: dict[str, str] = {}
    if not (
        hasattr(result_payload, "pillar_score_profile")
        and result_payload.pillar_score_profile
    ):
        return readings
    for p in getattr(result_payload.pillar_score_profile, "pillars", []):
        label = (
            p.get("pillar_label")
            if isinstance(p, dict)
            else getattr(p, "pillar_label", None)
        )
        reading = (
            p.get("executive_reading")
            if isinstance(p, dict)
            else getattr(p, "executive_reading", None)
        )
        if label and reading:
            readings[label] = reading
    return readings


def enrich_annex_payload(
    result_payload: AnnexPayload,
    blueprint: BlueprintPayload,
    radar_chart_path: Path,
    run_id: str,
) -> AnnexPayload:
    """Enrich annex payload according to architectural specification."""
    doc_lang = (
        getattr(blueprint.document_meta, "language", None)
        or (
            blueprint.document_meta.get("language")
            if isinstance(blueprint.document_meta, dict)
            else "en"
        )
        or "en"
    )
    scores = [pillar.score for pillar in blueprint.pillars_analysis]
    target_scores = [pillar.target_score for pillar in blueprint.pillars_analysis]
    avg_score = average(scores)
    avg_target_score = average(target_scores, default=4.0)
    target_capabilities, gap_rows = derive_gap_rows(blueprint)
    risks = derive_risks(blueprint, locale=doc_lang)
    initiatives = derive_priority_initiatives(blueprint, locale=doc_lang)
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

    # Preserve rich generative reading from LLM and fall back to deterministic template only if missing
    existing_pillar_readings = _extract_existing_pillar_readings(result_payload)

    result_payload.pillar_score_profile.pillars = [
        {
            "pillar_label": pillar.pilar_name,
            "score_display": str(pillar.score),
            "maturity_band": derive_maturity_band(pillar.score, locale=doc_lang),
            "executive_reading": (
                existing_pillar_readings.get(pillar.pilar_name)
                or derive_pillar_executive_reading(pillar, locale=doc_lang, idx=idx)
            ),
        }
        for idx, pillar in enumerate(blueprint.pillars_analysis)
    ]
    if radar_chart_path.exists():
        result_payload.pillar_score_profile.radar_chart = str(
            radar_chart_path.resolve()
        )

    result_payload.executive_summary.global_score = f"{avg_score} / 5.0"
    result_payload.executive_summary.global_band = derive_maturity_band(
        avg_score, locale=doc_lang
    )
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
        diversification = (
            1.0 / (len(blueprint.pillars_analysis) ** 0.35)
            if blueprint.pillars_analysis
            else 1.0
        )
        global_fair_p90 = p90_raw * diversification

    coi_extreme_3y = global_fair_p90 + (global_fair_ale * 2)

    ale_rounded = round(global_fair_ale, -3)
    ale_p10 = round(global_fair_ale * 0.70, -3)
    ale_p90 = round(global_fair_ale * 1.30, -3)

    from assessment_engine.adapters.generate_asis_markdown_modules import (
        resolve_client_currency_context,
    )
    from assessment_engine.infrastructure.localization import (
        format_currency,
        format_number,
        t,
    )

    str_ale = format_number(ale_rounded, locale=doc_lang, decimals=0)
    str_p10 = format_number(ale_p10, locale=doc_lang, decimals=0)
    str_p90 = format_number(ale_p90, locale=doc_lang, decimals=0)
    
    client_name = getattr(blueprint.document_meta, "client", "generic_client")
    currency_sym, _ = resolve_client_currency_context(client_name)
    if hasattr(blueprint.document_meta, "currency_symbol") and blueprint.document_meta.currency_symbol:
        currency_sym = blueprint.document_meta.currency_symbol
    elif hasattr(blueprint.document_meta, "currency") and blueprint.document_meta.currency:
        currency_sym = blueprint.document_meta.currency
    fmt_ale = f"~{str_ale} {currency_sym}/year (Typical range: {str_p10} {currency_sym} to {str_p90} {currency_sym})"

    cost_3y_ord = format_currency(
        global_fair_ale * 3,
        currency_symbol=currency_sym,
        locale=doc_lang,
        decimals=0,
    )
    cost_3y_ext = format_currency(
        coi_extreme_3y,
        currency_symbol=currency_sym,
        locale=doc_lang,
        decimals=0,
    )
    formatted_3y_ord = t("coi_3y_ord", locale=doc_lang, amount=cost_3y_ord)
    formatted_3y_ext = t("coi_3y_ext", locale=doc_lang, amount=cost_3y_ext)

    from assessment_engine.domain.schemas.annex_synthesis import (
        FinancialCOIProfile,
    )

    result_payload.executive_summary.financial_coi = FinancialCOIProfile(
        annual_loss_exposure=fmt_ale,
        coi_3y_ordinary=formatted_3y_ord,
        coi_3y_extreme=formatted_3y_ext,
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
    """Load yaml config according to architectural specification."""
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
    """Build synthesis prompt according to architectural specification."""
    tower_name = blueprint_data.get("document_meta", {}).get(
        "tower_name", "la torre evaluada"
    )

    # Calculate dynamic temporal values based on current actual system year (timeless engineering)
    import datetime

    from assessment_engine.infrastructure.localization import (
        format_date_localized,
        resolve_target_language_name,
    )

    now = datetime.datetime.now()
    current_year = now.year

    doc_lang = str(
        blueprint_data.get("document_meta", {}).get("language")
        or os.environ.get("ASSESSMENT_DOC_LANG")
        or "en"
    ).lower()
    target_language = resolve_target_language_name(doc_lang)

    current_date_str = (
        format_date_localized(locale=doc_lang).upper()
    )  # Standard uppercase month and year
    active_strategic_range = f"{current_year - 1}-{current_year + 3}"  # e.g., 2026-2030
    future_investment_horizon_range = f"{current_year + 1}-{current_year + 3}/{current_year + 4}"  # e.g., 2028-2030/2031
    obsolete_strategic_range = (
        f"{current_year - 6}-{current_year - 2}"  # e.g., 2021-2025
    )

    format_kwargs = {
        "current_date_str": current_date_str,
        "active_strategic_range": active_strategic_range,
        "future_investment_horizon_range": future_investment_horizon_range,
        "obsolete_strategic_range": obsolete_strategic_range,
        "target_language": target_language,
        "tower_name": tower_name,
    }

    prompt = (
        f"You are a {config.get('role', 'Senior Enterprise Architecture Partner')} with expertise in {config.get('expertise', 'Executive Communication & Strategic Alignment')}.\n"
        f"{config.get('context_description', '').format(**format_kwargs)}\n\n"
        f"TAREA PRINCIPAL:\n{config.get('task', '')}\n\n"
        f"{config.get('non_negotiable_facts_header', 'NON-NEGOTIABLE FACTS FOR THE EXECUTIVE ANNEX:')}\n"
        f"{json.dumps(executive_handover, ensure_ascii=False, indent=2)}\n\n"
        f"{config.get('client_strategy_header', 'CLIENT STRATEGIC CONTEXT:')}\n"
        f"{json.dumps(client_intelligence, ensure_ascii=False, indent=2)}\n\n"
        f"{config.get('interview_context_header', 'INTERVIEW & CASE CONTEXT:')}\n"
        f"{context_summary or 'No hay contexto adicional disponible.'}\n\n"
        f"{config.get('source_blueprint_header', 'DETAILED TOWER BLUEPRINT CONTEXT:')}\n"
        f"{json.dumps(blueprint_data, ensure_ascii=False, indent=2)}\n\n"
        f"{config.get('specific_instructions_header', 'SPECIFIC OPERATIONAL INSTRUCTIONS:')}\n"
    )
    for idx, instruction in enumerate(config.get("instructions", []), start=1):
        if isinstance(instruction, str):
            try:
                instruction = instruction.format(**format_kwargs)
            except KeyError:
                pass
        prompt += f"{idx}. {instruction}\n"

    tone_header = config.get("tone_rules_header")
    tone_rules = config.get("tone_rules", [])
    if tone_header or tone_rules:
        prompt += f"\n{tone_header or 'EXECUTIVE TONE AND STYLE GOVERNANCE:'}\n"
        for idx, rule in enumerate(tone_rules, start=1):
            if isinstance(rule, str):
                try:
                    rule = rule.format(**format_kwargs)
                except KeyError:
                    pass
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
    radar_chart_path: Optional[Path] = None,
    run_id: str = "",
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

    model_name = resolve_model_for_role("section_writer")

    from assessment_engine.infrastructure.localization import (
        resolve_target_language_name,
    )

    doc_lang = getattr(blueprint.document_meta, "language", "en")
    target_lang = resolve_target_language_name(doc_lang)

    agent = Agent(
        name="executive_synthesizer",
        model=model_name,
        instruction=(
            f"You are a {config.get('role', 'Principal Solutions Architect')}. "
            f"Mission: {config.get('mission', 'Synthesize high-impact executive annexes')}.\n\n"
            f"### CRITICAL LANGUAGE MANDATE:\n"
            f"You MUST generate all executive summaries, domain narratives, and strategic findings EXCLUSIVELY in {target_lang}."
        ),
        output_schema=AnnexPayload,
    )
    app = AdkApp(agent=agent)

    result = None
    last_error = ""
    for attempt in range(3):
        try:
            msg = prompt
            if last_error:
                msg += f"\n\n🚨 PROTOCOL VIOLATION IN PREVIOUS ATTEMPT:\n{last_error}\nCorrect the text immediately.\n"
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
                f"    🚨 DIPLOMATIC PROTOCOL VIOLATION: {e}. Retrying Annex Synthesizer (Attempt {attempt + 1})..."
            )

    if last_error:
        print(
            f"⚠️ Critical failure in Annex Synthesizer after 3 attempts. Last error: {last_error}"
        )

    if not result:
        raise RuntimeError(
            f"Critical failure in Annex Synthesizer after 3 attempts. Last error: {last_error}"
        )

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
        print(f"❌ Error: Blueprint not found at {blueprint_path}")
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
        from assessment_engine.infrastructure.text_utils import (
            ExecutiveStyleCompressor,
        )

        if final_payload.executive_summary:
            if final_payload.executive_summary.summary_body:
                final_payload.executive_summary.summary_body = (
                    ExecutiveStyleCompressor.compress_executive_paragraph(
                        final_payload.executive_summary.summary_body,
                        max_words_per_sentence=25,
                    )
                )
            if final_payload.executive_summary.headline:
                final_payload.executive_summary.headline = (
                    ExecutiveStyleCompressor.compress_executive_paragraph(
                        final_payload.executive_summary.headline,
                        max_words_per_sentence=25,
                    )
                )

        content = final_payload.model_dump_json(indent=2, by_alias=True)

        from assessment_engine.infrastructure.localization import (
            apply_vocabulary_substitutions,
        )

        doc_lang = getattr(blueprint.document_meta, "language", "en") or "en"
        content = apply_vocabulary_substitutions(content, locale=doc_lang)

        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        try:
            tmp_path.write_text(content, encoding="utf-8")
            tmp_path.replace(output_path)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except (OSError, ValueError, KeyError, AttributeError) as ex:
                    logger.debug(f"[Fallback] Handled exception: {ex}")
        print(f"✅ Executive Annex synthesized successfully at: {output_path}")
    else:
        print("❌ Error al generar el anexo.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Uso: python -m assessment_engine.application.run_executive_annex_synthesizer <client> <tower>"
        )
        sys.exit(1)
    asyncio.run(synthesize_annex(sys.argv[1], sys.argv[2]))
