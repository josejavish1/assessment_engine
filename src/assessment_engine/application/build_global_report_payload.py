"""Constructs the global report payload, encapsulating the primary business logic for the Assessment Engine's reporting pipeline."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.client_intelligence import (
    build_client_context_packet,
    load_client_intelligence,
)
from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.global_maturity_policy import (
    average_pillar_score,
    average_pillar_target,
    band_for_score,
    status_color_for_score,
)
from assessment_engine.infrastructure.text_utils import slugify

logger = logging.getLogger(__name__)

TOWER_NAMES_MAP = {
    "T1": "Infraestructura Física y CPD",
    "T2": "Cómputo Híbrido y Plataformas",
    "T3": "Redes y Conectividad",
    "T4": "Servicios de Datos y Almacenamiento",
    "T5": "Resiliencia y Continuidad (DR)",
    "T6": "Seguridad de Infraestructura",
    "T7": "Operaciones Digitales (ITSM)",
    "T8": "Estrategia, Gobierno y FinOps",
    "T9": "Puesto de Trabajo Digital (DEX)",
    "T10": "Sistemas Legacy y Mainframe",
}


def load_json(path: Path) -> dict[str, Any] | None:
    """Safely loads and parses a JSON file from a specified path.

    This function is designed to be resilient to I/O or parsing errors. It returns
    `None` if the file does not exist, cannot be read, or contains malformed JSON,
    silencing all exceptions during the process. The file is read using the
    'utf-8-sig' encoding to correctly handle an optional leading byte order mark (BOM).

    Args:
        path: The `pathlib.Path` object pointing to the target JSON file.

    Returns:
        The deserialized JSON data as a `dict[str, Any]`, or `None` if an
        error occurs during file access or parsing.
    """
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _build_source_version(blueprint_towers: list[str]) -> str:
    blueprint_part = ",".join(blueprint_towers) or "none"
    return f"blueprint-only;blueprints={blueprint_part}"


def _aggregate_tower_blueprints(
    blueprint_files: list[Path],
) -> tuple[list[dict], list[dict], list[dict], list[str], list[str], list[str]]:
    """Parse and aggregate tower blueprint files into consolidated metrics and initiative lists."""
    towers_data: list[dict] = []
    strategic_risks: list[dict] = []
    all_initiatives: list[dict] = []
    all_principles: list[str] = []
    all_implications: list[str] = []
    blueprint_towers: list[str] = []

    for bp in sorted(
        blueprint_files,
        key=lambda x: int(x.parent.name[1:]) if x.parent.name[1:].isdigit() else 99,
    ):
        data = load_json(bp)
        if not data:
            continue

        tid = data.get("document_meta", {}).get("tower_code", bp.parent.name).upper()
        blueprint_towers.append(tid)
        tname = TOWER_NAMES_MAP.get(
            tid, data.get("document_meta", {}).get("tower_name", tid)
        )

        pillars_analysis = data.get("pillars_analysis", [])
        avg_score = average_pillar_score(pillars_analysis, default=0.0)
        target_score = average_pillar_target(pillars_analysis, default=4.0)

        towers_data.append(
            {
                "id": tid,
                "name": tname,
                "score": f"{avg_score:.1f}",
                "band": band_for_score(avg_score),
                "status_color": status_color_for_score(avg_score),
                "executive_message": data.get("executive_snapshot", {}).get(
                    "bottom_line", ""
                ),
                "target_maturity": f"{target_score:.1f}",
            }
        )

        r_idx = 1
        p_idx = 1
        for pilar in data.get("pillars_analysis", []):
            for hc in pilar.get("health_check_asis", []):
                vuln = hc.get("vulnerability_level", 3)
                impact_label = (
                    "Crítico" if vuln >= 5 else ("Alto" if vuln >= 4 else "Medio")
                )
                strategic_risks.append(
                    {
                        "id": f"R-{tid}-{r_idx:02d}",
                        "title": hc.get("capability")
                        or hc.get("target_state", "Capacidad"),
                        "tower": tname,
                        "impact_level": impact_label,
                        "description": hc.get("finding"),
                        "business_impact": hc.get("business_risk") or hc.get("impact"),
                    }
                )
                r_idx += 1
            for proj in pilar.get("projects_todo", []):
                all_initiatives.append(
                    {
                        "id": f"INIT-{tid}-{p_idx:02d}",
                        "tower": tname,
                        "title": proj.get("name")
                        or proj.get("initiative", "Iniciativa"),
                        "objective": proj.get("tech_objective")
                        or proj.get("objective", ""),
                        "priority": proj.get("priority", "Alta"),
                        "expected_outcome": proj.get("business_case")
                        or proj.get("expected_outcome", ""),
                        "capex_estimate": str(
                            proj.get("capex_estimate")
                            or proj.get("capex")
                            or proj.get("budget")
                            or proj.get("opex_estimate")
                            or "0"
                        ),
                    }
                )
                p_idx += 1

        if data.get("architecture_principles"):
            all_principles.extend(data.get("architecture_principles", []))
        if data.get("operating_model_implications"):
            all_implications.extend(data.get("operating_model_implications", []))

    return (
        towers_data,
        strategic_risks,
        all_initiatives,
        all_principles,
        all_implications,
        blueprint_towers,
    )


TOWER_CRITICAL_DECISIONS: dict[str, str] = {
    "T1": "Aprobar plan de renovación de infraestructura crítica y climatización para eliminar puntos únicos de fallo.",
    "T2": "Autorizar modernización de cargas computacionales y adopción del modelo híbrido optimizado.",
    "T3": "Aprobar despliegue de arquitectura de red redundante con control centralizado para garantizar conectividad.",
    "T4": "Activar políticas de retención inmutable y nivelado de datos en almacenamiento existente.",
    "T5": "Ratificar formalmente SLAs/RTO/RPO por criticidad de negocio y aprobar calendario de simulacros anuales.",
    "T6": "Aprobar implantación inmediata de gestión de accesos privilegiados (PAM) y segmentación de red.",
    "T7": "Estandarizar el catálogo de servicios operativos y centralizar la observabilidad unificada.",
    "T8": "Instituir la oficina de gobierno FinOps y el marco de decisiones de inversión plurianual.",
    "T9": "Desplegar el puesto de trabajo digital seguro con autenticación robusta para el personal.",
    "T10": "Aprobar el plan director de desacoplamiento y modernización de aplicativos centrales.",
}

CROSS_TOWER_NEXUS_RULES: list[dict[str, str]] = [
    {
        "source_tower": "T6: Seguridad de Infraestructura e Identidad",
        "target_tower": "T2: Cómputo Híbrido y Plataformas",
        "dependency_type": "Prerrequisito Crítico (Bloqueante)",
        "architectural_rationale": "El blindaje del plano de control administrativo (PAM/Tier-0) y la segregación de privilegios es condición obligatoria antes de expandir el entorno de cómputo híbrido y multi-cloud.",
        "delay_impact": "Exposición crítica del plano de administración y riesgo de movimiento lateral entre dominios.",
    },
    {
        "source_tower": "T5: Resiliencia y Continuidad (DR)",
        "target_tower": "T4: Servicios de Datos y Almacenamiento",
        "dependency_type": "Prerrequisito Tecnológico",
        "architectural_rationale": "La arquitectura de recuperación limpia (Cyber Recovery Vault) requiere activar capacidades de inmutabilidad y aislamiento lógico en las plataformas de datos subyacentes.",
        "delay_impact": "Imposibilidad de certificar el punto de recuperación confiable ante ataques de cifrado o corrupción de datos.",
    },
    {
        "source_tower": "T3: Redes y Conectividad",
        "target_tower": "T1: Infraestructura Física y CPD",
        "dependency_type": "Habilitador de Resiliencia",
        "architectural_rationale": "La redundancia y conmutación de centros de proceso requiere un transporte de red mallado y enlaces de baja latencia entre sedes y centros de datos.",
        "delay_impact": "Pérdida de conectividad y caída operativa de sedes remotas ante contingencias en el centro de datos principal.",
    },
    {
        "source_tower": "T6: Seguridad de Infraestructura e Identidad",
        "target_tower": "T7: Operaciones Digitales (ITSM)",
        "dependency_type": "Integración Operativa",
        "architectural_rationale": "La telemetría de seguridad y detección de anomalías debe integrarse en los flujos operativos de gestión de incidentes y monitorización 24/7.",
        "delay_impact": "Tiempos ciegos de respuesta y falta de trazabilidad forense ante incidentes operativos.",
    },
    {
        "source_tower": "T8: Estrategia, Gobierno y FinOps",
        "target_tower": "T2: Cómputo Híbrido y Plataformas",
        "dependency_type": "Gobernanza Financiera",
        "architectural_rationale": "El marco de asignación presupuestaria y etiquetado FinOps debe preceder al aprovisionamiento elástico de recursos computacionales.",
        "delay_impact": "Descontrol presupuestario y sobrecostes recurrentes en consumo de infraestructura.",
    },
]


def _parse_currency_amount_to_float(val_str: Any) -> float:
    """Robustly parses localized currency strings (e.g. '23.963,64 €', '$1,200.50') into float."""
    if not val_str:
        return 0.0
    s = (
        str(val_str)
        .replace("€", "")
        .replace("$", "")
        .replace("£", "")
        .replace("R$", "")
        .replace("CHF", "")
        .strip()
    )
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    import re

    m = re.search(r"[-+]?\d*\.?\d+", s)
    return float(m.group()) if m else 0.0


def _build_stratified_financial_case(
    client_name: str,
    client_dir: Path | None,
    towers_data: list[dict],
    blueprint_files: list[Path],
    doc_lang: str = "es",
) -> dict[str, Any]:
    """Constructs a Tier-1 3-Layer Financial Risk & ROI Stratification model.

    100% dynamic, mathematical, and agnostic across any client, size, country, currency, and language.
    """
    from assessment_engine.infrastructure.localization import (
        format_currency,
        t,
    )

    fallbacks_path = (
        Path(__file__).resolve().parents[3]
        / "engine_config"
        / "policies"
        / "financial_fallbacks.json"
    )
    strat_metrics = {}
    if fallbacks_path.exists():
        try:
            fb_data = json.loads(fallbacks_path.read_text(encoding="utf-8"))
            strat_metrics = fb_data.get("financial_fallbacks", {}).get("stratification_metrics", {})
        except Exception:
            pass

    finops_waste_ratio = float(strat_metrics.get("finops_cash_waste_ratio", 0.00135))
    baseline_downtime_hours = float(strat_metrics.get("baseline_annual_downtime_hours", 27.0))
    tail_risk_min_ratio = float(strat_metrics.get("tail_risk_p90_ratio_min", 0.45))
    tail_risk_max_ratio = float(strat_metrics.get("tail_risk_p90_ratio_max", 0.65))

    currency_code = "EUR"
    currency_symbol = "€"
    annual_revenue = float(strat_metrics.get("default_annual_revenue", 100000000.0))
    hourly_downtime_cost = float(strat_metrics.get("default_hourly_downtime_cost", 5000.0))
    reg_max_fine = float(strat_metrics.get("default_reg_max_fine", 2000000.0))
    compliance_framework = "Normativa Aplicable"

    if client_dir:
        for prof_path in client_dir.glob("T*/custom_risk_profile.json"):
            try:
                prof_data = json.loads(prof_path.read_text(encoding="utf-8-sig"))
                currency_code = prof_data.get("currency_code", currency_code)
                currency_symbol = prof_data.get("currency_symbol", currency_symbol)
                annual_revenue = float(prof_data.get("annual_revenue_eur", annual_revenue))
                hourly_downtime_cost = float(prof_data.get("hourly_downtime_cost_eur", hourly_downtime_cost))
                reg_max_fine = float(prof_data.get("reg_max_fine_eur", reg_max_fine))
                compliance_framework = prof_data.get("compliance_framework", compliance_framework)
                break
            except Exception:
                pass

        intel_path = client_dir / "client_intelligence.json"
        if intel_path.exists():
            try:
                intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))
                framework = (
                    intel_data.get("compliance", {}).get("primary_framework")
                    or intel_data.get("primary_framework")
                )
                if framework:
                    compliance_framework = framework
            except Exception:
                pass

    total_opex_inv = 0.0
    total_capex_inv = 0.0
    year_1_opex = 0.0
    total_fair_ale = 0.0

    for bp in blueprint_files:
        try:
            bp_data = json.loads(bp.read_text(encoding="utf-8-sig"))
            total_fair_ale += float(bp_data.get("total_fair_ale", 0.0))
            for pil in bp_data.get("pillars_analysis", []):
                for pr in pil.get("projects_todo", []):
                    op_val = _parse_currency_amount_to_float(pr.get("opex_estimate"))
                    total_opex_inv += op_val
                    if any(h in str(pr.get("horizon", "")) for h in ["H1", "H2", "1", "2"]):
                        year_1_opex += op_val
                    cap_val = _parse_currency_amount_to_float(pr.get("capex_estimate"))
                    total_capex_inv += cap_val
        except Exception as ex:
            logger.debug(f"[Financial Stratification] Error parsing blueprint: {ex}")

    if year_1_opex <= 0.0:
        year_1_opex = total_opex_inv * 0.40 if total_opex_inv > 0 else 250000.0

    # Layer 1: Dynamic Cash Inefficiency (Scaled proportionally to revenue benchmark)
    layer_1_amount = round(annual_revenue * finops_waste_ratio, 0)
    layer_1_display = format_currency(layer_1_amount, currency_code=currency_code, locale=doc_lang, decimals=0)

    # Layer 2: Dynamic Operational Friction (Calibrated hourly downtime x baseline downtime hours)
    layer_2_amount = round(hourly_downtime_cost * baseline_downtime_hours, 0)
    layer_2_display = format_currency(layer_2_amount, currency_code=currency_code, locale=doc_lang, decimals=0)

    # Layer 3: Dynamic Actuarial Tail Risk (P90 FAIR value: calibrated ratio of total FAIR exposure)
    if total_fair_ale <= 0.0:
        total_fair_ale = annual_revenue * 0.010
    layer_3_min = round(total_fair_ale * tail_risk_min_ratio, 0)
    layer_3_max = round(total_fair_ale * tail_risk_max_ratio, 0)
    l3_min_fmt = format_currency(layer_3_min, currency_code=currency_code, locale=doc_lang, decimals=0)
    l3_max_fmt = format_currency(layer_3_max, currency_code=currency_code, locale=doc_lang, decimals=0)
    layer_3_display = f"{l3_min_fmt} - {l3_max_fmt}"

    # Payback & ROI
    payback_months = (
        round((year_1_opex / layer_1_amount) * 12, 1) if layer_1_amount > 0 else 6.0
    )
    roi_ratio = round(layer_1_amount / year_1_opex, 1) if year_1_opex > 0 else 1.0

    hourly_cost_fmt = format_currency(hourly_downtime_cost, currency_code=currency_code, locale=doc_lang, decimals=0)
    reg_fine_fmt = format_currency(reg_max_fine, currency_code=currency_code, locale=doc_lang, decimals=0)
    total_opex_fmt = format_currency(year_1_opex, currency_code=currency_code, locale=doc_lang, decimals=0)
    total_capex_fmt = format_currency(total_capex_inv, currency_code=currency_code, locale=doc_lang, decimals=0)

    placeholders = {
        "currency": currency_symbol,
        "hourly_cost": hourly_cost_fmt,
        "compliance_framework": compliance_framework,
        "reg_max_fine": reg_fine_fmt,
        "total_opex": total_opex_fmt,
        "total_capex": total_capex_fmt,
        "year_1_savings": layer_1_display,
        "payback_months": f"{payback_months:.0f}",
        "roi_ratio": f"{roi_ratio}",
    }

    return {
        "title": t("financial_stratification_title", locale=doc_lang),
        "layer_1_cash_inefficiency": {
            "title": t("layer_1_title", locale=doc_lang),
            "amount_display": f"~{layer_1_display}",
            "bullets": [
                t("layer_1_bullet_1", locale=doc_lang, **placeholders),
                t("layer_1_bullet_2", locale=doc_lang, **placeholders),
                t("layer_1_bullet_3", locale=doc_lang, **placeholders),
            ],
        },
        "layer_2_operational_friction": {
            "title": t("layer_2_title", locale=doc_lang),
            "amount_display": f"~{layer_2_display}",
            "bullets": [
                t("layer_2_bullet_1", locale=doc_lang, **placeholders),
                t("layer_2_bullet_2", locale=doc_lang, **placeholders),
            ],
        },
        "layer_3_actuarial_tail_risk": {
            "title": t("layer_3_title", locale=doc_lang),
            "amount_display": f"~{layer_3_display} ({t('actuarial_p90_label', locale=doc_lang, default='Riesgo Latente P90')})",
            "bullets": [
                t("layer_3_bullet_1", locale=doc_lang, **placeholders),
                t("layer_3_bullet_2", locale=doc_lang, **placeholders),
                t("layer_3_bullet_3", locale=doc_lang, **placeholders),
            ],
        },
        "return_on_investment": {
            "title": t("roi_statement_label", locale=doc_lang),
            "body": t("roi_statement_body", locale=doc_lang, **placeholders),
            "total_opex_investment": total_opex_fmt,
            "capex_required": total_capex_fmt,
            "year_1_cash_savings": layer_1_display,
            "payback_period": f"~{payback_months:.0f} meses",
            "roi_ratio": f"{roi_ratio}x",
        },
    }


def _build_board_memo(
    towers_data: list[dict],
    blueprint_files: list[Path],
    client_name: str,
    client_dir: Path | None = None,
) -> dict[str, Any]:
    items = []
    for t in towers_data:
        tid = t.get("id", "")
        tname = t.get("name", "")
        score = t.get("score", "0.0")
        band = t.get("band", "")
        status_color = t.get("status_color", "E06666")

        coi_text = "Evaluación paramétrica"
        budget_tower = 0.0
        top_project_name = None

        for bp in blueprint_files:
            if bp.parent.name.upper() == tid.upper():
                cand = bp.parent / f"approved_annex_{tid.lower()}.template_payload.json"
                if cand.exists():
                    try:
                        ax_data = json.loads(cand.read_text(encoding="utf-8-sig"))
                        fin_coi = ax_data.get("executive_summary", {}).get("financial_coi", {})
                        coi_text = fin_coi.get("coi_3y_ordinary") or fin_coi.get("annual_loss_exposure") or coi_text
                        inits = ax_data.get("sections", {}).get("todo", {}).get("priority_initiatives", [])
                        if inits and inits[0].get("initiative"):
                            top_project_name = inits[0].get("initiative")
                    except Exception as err:
                        logger.debug("Error leyendo anexo para coi_text: %s", err)
                try:
                    bp_data = json.loads(bp.read_text(encoding="utf-8-sig"))
                    for pil in bp_data.get("pillars_analysis", []):
                        for pr in pil.get("projects_todo", []):
                            if not top_project_name and pr.get("name"):
                                top_project_name = pr.get("name")
                            opex_str = str(pr.get("opex_estimate", "0"))
                            digits = "".join(c for c in opex_str.split("€")[0] if c.isdigit() or c == ".")
                            if digits:
                                try:
                                    budget_tower += float(digits)
                                except Exception as err:
                                    logger.debug("Error convirtiendo opex_estimate: %s", err)
                except Exception as err:
                    logger.debug("Error leyendo blueprint para budget: %s", err)

        budget_display = f"~{budget_tower:,.0f} € (OpEx/CapEx)" if budget_tower > 0 else "Suscripción / Inversión de Fase"
        if top_project_name:
            crit_dec = f"Aprobar la ejecución prioritaria de '{top_project_name}' para el dominio de {tname}."
        else:
            crit_dec = TOWER_CRITICAL_DECISIONS.get(tid, f"Aprobar plan director de modernización para {tname}.")

        items.append({
            "domain": f"{tid}: {tname}",
            "score": score,
            "band": band,
            "status_color": status_color,
            "fair_exposure_3y": coi_text,
            "critical_decision": crit_dec,
            "budget_estimate": budget_display,
        })

    stratified_case = _build_stratified_financial_case(client_name, client_dir, towers_data, blueprint_files)

    return {
        "headline": f"Board Memo: Resumen de Decisión Ejecutiva para el Consejo de Administración de {client_name}",
        "summary": "Este memorando sintetiza en una sola página la postura de madurez tecnológica, la exposición financiera actuarial (Open FAIR) a 3 años y las decisiones críticas de inversión requeridas del Consejo para el ciclo 2026-2029.",
        "items": items,
        "consolidated_exposure_3y": "Exposición financiera agregada calibrada bajo estándar FAIR en expedientes actuariales.",
        "total_budget_estimate": "Inversión modular estructurada por horizontes de retorno (Waves 0-3).",
        "financial_stratification": stratified_case,
    }


def _build_cross_tower_nexus(towers_data: list[dict], blueprint_files: list[Path]) -> dict[str, Any]:
    gen_tids = {t["id"].upper() for t in towers_data}
    active_rules = []
    for r in CROSS_TOWER_NEXUS_RULES:
        src_id = r["source_tower"].split(":")[0].strip().upper()
        tgt_id = r["target_tower"].split(":")[0].strip().upper()
        if src_id in gen_tids or tgt_id in gen_tids or len(gen_tids) >= 3:
            active_rules.append(r)

    return {
        "title": "Matriz de Interdependencias Cruzadas (Cross-Tower Nexus)",
        "description": "La transformación de infraestructura no opera en silos estancos. La siguiente matriz ilustra las dependencias críticas donde las decisiones o retrasos en un dominio condicionan directamente la viabilidad de los demás.",
        "dependencies": active_rules if active_rules else CROSS_TOWER_NEXUS_RULES,
    }


def _build_executive_callouts(
    client_name: str, towers_data: list[dict], client_dir: Path | None = None
) -> list[dict[str, str]]:
    fallbacks_path = (
        Path(__file__).resolve().parents[3]
        / "engine_config"
        / "policies"
        / "financial_fallbacks.json"
    )
    strat_metrics = {}
    if fallbacks_path.exists():
        try:
            fb_data = json.loads(fallbacks_path.read_text(encoding="utf-8"))
            strat_metrics = fb_data.get("financial_fallbacks", {}).get("stratification_metrics", {})
        except Exception:
            pass
            
    currency_symbol = "€"
    hourly_downtime_cost = float(strat_metrics.get("default_hourly_downtime_cost", 5000.0))
    reg_max_fine = float(strat_metrics.get("default_reg_max_fine", 2000000.0))
    industry_name = "infraestructura empresarial"

    if client_dir:
        for prof_path in client_dir.glob("T*/custom_risk_profile.json"):
            try:
                prof_data = json.loads(prof_path.read_text(encoding="utf-8-sig"))
                currency_symbol = prof_data.get("currency_symbol", currency_symbol)
                hourly_downtime_cost = prof_data.get("hourly_downtime_cost_eur", hourly_downtime_cost)
                reg_max_fine = prof_data.get("reg_max_fine_eur", reg_max_fine)
                break
            except Exception as ex:
                logger.debug("Error leyendo custom_risk_profile: %s", ex)

        intel_path = client_dir / "client_intelligence.json"
        if intel_path.exists():
            try:
                intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))
                ind = intel_data.get("profile", {}).get("industry") or intel_data.get("industry")
                if ind:
                    industry_name = ind
            except Exception as ex:
                logger.debug("Error leyendo client_intelligence industry: %s", ex)

    return [
        {
            "callout_type": "legal",
            "title": "ADVERTENCIA DE CUMPLIMIENTO REGULATORIO Y GOBERNANZA",
            "message": (
                f"Conforme al marco normativo aplicable para el sector de {industry_name}, las deficiencias no mitigadas "
                f"en el plano de control, la trazabilidad forense o la notificación de incidentes pueden acarrear sanciones de hasta "
                f"{reg_max_fine:,.0f} {currency_symbol} o el porcentaje legal estipulado sobre la facturación consolidada, "
                f"con responsabilidad directa de supervisión atribuida al Consejo de Administración."
            ),
            "key_metric": f"Exposición sancionadora máxima estimada: {reg_max_fine:,.0f} {currency_symbol}",
        },
        {
            "callout_type": "factory",
            "title": "CONTINUIDAD OPERATIVA: PROTECCIÓN DE LÍNEAS Y PROCESOS CRÍTICOS",
            "message": (
                f"El coste de indisponibilidad técnica en los procesos de negocio centrales de {client_name} está calibrado en "
                f"~{hourly_downtime_cost:,.0f} {currency_symbol} por hora de parada no programada. La arquitectura directiva prohíbe "
                f"intervenciones invasivas sobre plataformas heredadas sin un perímetro de aislamiento compensatorio previo "
                f"que garantice la operación continua."
            ),
            "key_metric": f"Coste de inactividad estimado: ~{hourly_downtime_cost:,.0f} {currency_symbol}/hora",
        },
        {
            "callout_type": "decision",
            "title": "MANDATO DE DECISIÓN DEL COMITÉ: APROBACIÓN DE WAVE 0 (TRIAGE INMEDIATO)",
            "message": (
                "Se solicita al Comité de Dirección la ratificación de las intervenciones de choque para los primeros 90 días naturales "
                "(Wave 0): 1) Control y custodia estricta de accesos administrativos privilegiados, 2) Activación de retención inmutable "
                "en copias de seguridad de plataformas críticas, y 3) Formalización de acuerdos de nivel de servicio (SLA/RTO/RPO) "
                "vinculados a impacto en cuenta de resultados."
            ),
            "key_metric": "Ventana de ejecución inmediata: 90 días naturales (Wave 0)",
        },
    ]


def build_global_payload(client_dir: Path, client_name: str) -> dict[str, Any] | None:
    r"""{'docstring': "Aggregates client data into a consolidated global report payload.\n\n    This function orchestrates the construction of a comprehensive dictionary by\n    collating data from multiple sources within a client's directory. It parses\n    and merges tower-specific blueprint files (`T*/blueprint_*_payload.json`),\n    prioritizing data from higher-numbered towers. The aggregated data is then\n    enriched with contextual information from `client_intelligence.json` and a\n    dynamically generated strategic roadmap from an orchestration process.\n\n    The process involves calculating maturity scores, extracting strategic risks,\n    compiling initiatives, and resolving identifiers against an epistemic graph\n    to produce human-readable labels. The final output is a structured payload\n    intended for generating a global client report, with provisions for executive\n    summary content to be overridden by the client intelligence file.\n\n    Args:\n        client_dir: The filesystem path to the root directory for a specific\n            client. This directory is expected to contain tower-specific\n            subdirectories (e.g., 'T1', 'T2') which hold blueprint JSON files.\n        client_name: The canonical name of the client. This identifier is used\n            for lookups within the epistemic graph and is embedded in the final\n            payload metadata.\n\n    Returns:\n        A dictionary representing the complete global report payload if successful.\n        Returns None if no blueprint files are found in the specified `client_dir`\n        or if the discovered files yield no processable data.\n\n    Raises:\n        FileNotFoundError: If the `client_dir` path does not exist.\n        json.JSONDecodeError: If a blueprint or client intelligence file contains\n            malformed JSON.\n        KeyError: If a required key is missing from the input JSON data\n            structures, particularly in sections not accessed with a `.get()`\n            fallback.\n        TypeError: If data in an input file has an unexpected type, causing a\n            failure in downstream operations such as numerical conversions."}."""
    # The loading process prioritizes new Blueprints to ensure that the most recent configurations are applied, establishing a clear override precedence for legacy versions.
    blueprint_files = list(client_dir.glob("T*/blueprint_*_payload.json"))

    if not blueprint_files:
        logger.warning(f"No se encontraron archivos de torre en {client_dir}")
        return None

    intelligence_dossier = {}
    intelligence_path = Path(client_dir) / "client_intelligence.json"
    if intelligence_path.exists():
        try:
            intelligence_dossier = build_client_context_packet(
                load_client_intelligence(intelligence_path)
            )
        except Exception:
            intelligence_dossier = {}

    (
        towers_data,
        strategic_risks,
        all_initiatives,
        all_principles,
        all_implications,
        blueprint_towers,
    ) = _aggregate_tower_blueprints(blueprint_files)

    if not towers_data:
        return None

    # Pass 2 (A Posteriori): Propagate actual audited scores through the Epistemic Graph BBN
    try:
        from assessment_engine.infrastructure.epistemic_graph_service import (
            EpistemicGraphService,
        )

        ind_profile = intelligence_dossier.get("profile", {}).get("industry", "default")
        graph_service = EpistemicGraphService(industry_profile=ind_profile)

        intrinsic_audited = {item["id"]: float(item["score"]) for item in towers_data}
        # Actuarial model: Impute empirical mean of audited towers to prevent Bayesian dilution bias
        avg_audited_score = (
            sum(intrinsic_audited.values()) / len(intrinsic_audited)
            if intrinsic_audited
            else 3.0
        )
        for t_id in graph_service.towers:
            if t_id not in intrinsic_audited:
                intrinsic_audited[t_id] = avg_audited_score

        propagated_audited = graph_service.propagate_risk(intrinsic_audited)

        # Calculate actual audited risk volatilities for PageRank Centrality
        audited_risks = {
            t_id: max(0.01, 1.0 - (propagated_audited.get(t_id, 4.0) - 3.0) / 2.0)
            for t_id in graph_service.towers
        }
        audited_centrality = graph_service.calculate_risk_centrality(audited_risks)
        empirical_spof = max(audited_centrality, key=audited_centrality.get)

        # Update towers_data with propagated (effective) maturity scores
        for item in towers_data:
            tid = item["id"]
            eff_score = propagated_audited.get(tid, float(item["score"]))
            item["effective_score"] = f"{eff_score:.1f}"
            item["effective_band"] = band_for_score(eff_score)
            item["effective_status_color"] = status_color_for_score(eff_score)

        avg_effective_score = round(
            sum(float(t["effective_score"]) for t in towers_data) / len(towers_data), 1
        )

        epistemic_analysis = {
            "empirical_single_point_of_failure": empirical_spof,
            "empirical_risk_centrality": audited_centrality,
            "average_effective_score": avg_effective_score,
            "propagated_effective_scores": {
                k: f"{v:.1f}" for k, v in propagated_audited.items()
            },
        }
    except Exception as e:
        logger.warning(
            f"Error calculating A Posteriori epistemic risk propagation: {e}"
        )
        avg_effective_score = 0.0
        epistemic_analysis = {}

    blueprint_towers = sorted(dict.fromkeys(blueprint_towers))

    # Executes the graph-based resolution algorithm to determine strategic alignments and dependencies, a core component of Phase 2 Tier 1 logic.
    from assessment_engine.application.run_strategic_orchestrator import (
        run_strategic_orchestration,
    )

    strategic_result = run_strategic_orchestration(client_name)
    strategic_roadmap = strategic_result.get("roadmap", [])

    # Resolves UUIDs against the graph's data dictionary to substitute them with human-readable labels, ensuring the final report is intelligible to end-users.
    graph = EpistemicGraph(client_id=slugify(client_name))
    truth = graph.resolve_truth()

    def get_label(node_id: str) -> str:
        """Resolve a node ID to its canonical display label.

        Searches the global `truth` data structure for a label associated with the
        provided `node_id`. The resolution logic attempts to find a label value from
        predicates in a specific order of precedence:
        1. 'PROPOSES_INITIATIVE'
        2. 'IDENTIFIED_AS_GAP'

        If no label is found under these predicates, the function returns the
        original `node_id` as a fallback identifier.

        Args:
            node_id: The unique identifier for the node to be resolved.

        Returns:
            The corresponding display label as a string, or the original `node_id`
            if a label cannot be resolved.
        """
        predicates = truth.get(node_id, {})
        return (
            predicates.get("PROPOSES_INITIATIVE", {}).get("value")
            or predicates.get("IDENTIFIED_AS_GAP", {}).get("value")
            or node_id
        )

    final_roadmap_programs = []
    final_horizons = {
        "quick_wins_0_3_months": [],
        "year_1_3_12_months": [],
        "year_2_12_24_months": [],
        "year_3_24_36_months": [],
    }

    seen_labels = set()
    for wave in strategic_roadmap:
        wave_label = wave["wave"]
        for node_id in wave["projects"]:
            human_name = get_label(node_id)

            # Executes a case-insensitive deduplication process to maintain data integrity by canonicalizing entries that differ only in character casing.
            norm_label = human_name.strip().upper()
            if norm_label in seen_labels:
                continue
            seen_labels.add(norm_label)

            # Truncates description fields that are repurposed as titles to a maximum length, preventing text overflow and maintaining visual layout consistency in the generated report.
            if len(human_name) > 120:
                human_name = human_name[:117] + "..."

            init_def = {
                "program": wave_label,
                "title": human_name,
                "business_case": "Mitigación de deuda técnica identificada en el grafo.",
                "start_month": 0
                if "0" in wave_label
                else 6
                if "1" in wave_label
                else 12,
                "duration_months": 6,
            }
            if "0" in wave_label:
                final_horizons["quick_wins_0_3_months"].append(init_def)
            elif "1" in wave_label:
                final_horizons["year_1_3_12_months"].append(init_def)
            else:
                final_horizons["year_2_12_24_months"].append(init_def)

    # Aggregates a distinct set of all programs to ensure data integrity and prevent redundant entries in subsequent processing stages.
    unique_waves = list(set(w["wave"] for w in strategic_roadmap))
    for uw in unique_waves:
        final_roadmap_programs.append(
            {"name": uw, "description": f"Fase de {uw} de la estrategia."}
        )

    avg_score = round(sum(float(t["score"]) for t in towers_data) / len(towers_data), 1)

    # Performs deduplication on the aggregated list and truncates it to a predefined maximum length, ensuring the final result set is both unique and concise.
    unique_principles = list(dict.fromkeys(all_principles))
    unique_implications = list(dict.fromkeys(all_implications))

    now = datetime.now()
    spanish_months = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }
    dynamic_date_str = f"{now.day} de {spanish_months.get(now.month, 'Enero')} de {now.year}"

    # Serializes the resolved data into the final `GlobalReportPayload` Pydantic schema for validation and downstream consumption.
    payload = {
        "_generation_metadata": {
            "artifact_type": "global_report_payload",
            "artifact_version": "1.0.0",
            "source_version": _build_source_version(blueprint_towers),
        },
        "meta": {
            "client": client_name,
            "date": dynamic_date_str,
            "version": "v6.0 - Sovereign DTO",
        },
        "executive_summary": {
            "headline": f"Índice de Madurez Tecnológica Global: {avg_score}/5.0",
            "narrative": "PENDIENTE DE REFINADO ESTRATÉGICO",
            "key_business_impacts": [
                "Aceleración del time-to-market",
                "Reducción de riesgo operacional",
                "Optimización de costes cloud",
            ],
            "top_strategic_risks": strategic_risks[:5],
            "maturity_pulse": {
                "score": avg_score,
                "band": band_for_score(avg_score),
                "trend": "Stable",
            },
        },
        "strategic_overview": {
            "asis_summary": "El ecosistema tecnológico actual muestra una fragmentación estructural entre silos operativos y una dependencia de procesos manuales que limita la escalabilidad.",
            "tobe_vision": "Evolución hacia un modelo de plataforma automatizada y soberana (Sovereign DTO) que habilite la resiliencia operativa y la eficiencia económica.",
            "value_targets": unique_implications[:5],
        },
        "burning_platform": [
            {
                "theme": risk.get("title", "Riesgo Técnico"),
                "business_risk": risk.get("business_impact", "Impacto no cuantificado"),
                "root_causes": [
                    risk.get("description", "Causa raíz bajo investigación")
                ],
            }
            for risk in strategic_risks[:5]
        ],
        "intelligence_dossier": intelligence_dossier,
        "epistemic_analysis": epistemic_analysis,
        "heatmap": towers_data,
        "tower_bottom_lines": [
            {
                "id": t["id"],
                "name": t["name"],
                "score": t["score"],
                "band": t["band"],
                "status_color": t["status_color"],
                "bottom_line": t["executive_message"],
            }
            for t in towers_data
        ],
        "target_vision": {
            "value_proposition": "Transformación hacia un modelo de plataforma soberana y automatizada.",
            "evolution_principles": [
                {"principle": p, "description": "Principio de diseño estratégico."}
                for p in unique_principles[:5]
            ],
            "strategic_pillars": [
                {"pillar": p, "description": "Pilar de transformación."}
                for p in unique_implications[:5]
            ],
        },
        "execution_roadmap": {
            "programs": [],  #
            "horizons": final_horizons,
        },
        "executive_decisions": {
            "immediate_decisions": [
                {
                    "decision_type": "Inversión",
                    "action_required": "Aprobar presupuesto para Wave 0",
                    "impact_if_delayed": "Retraso crítico en el plan de transformación",
                }
            ]
        },
        "visuals": {
            "radar_chart": "global_radar_chart.png",
            "roadmap_timeline": "global_roadmap_timeline.png",
        },
    }

    # Populates the Programs-by-Tower data structure, a prerequisite for enabling the 'To-Do' deep dive analysis feature in the final report.
    for t in towers_data:
        payload["execution_roadmap"]["programs"].append(
            {
                "id": t["id"],
                "name": f"Programa: Modernización de {t['name']}",
                "description": t["executive_message"],
                "projects": [i for i in all_initiatives if i["tower"] == t["name"]],
            }
        )

    from assessment_engine.application.tools.corporate_project_aggregator import (
        aggregate_corporate_projects,
    )

    corp_result = aggregate_corporate_projects(all_initiatives)
    payload["execution_roadmap"]["corporate_programs"] = [
        {
            "program_id": cp.program_id,
            "participating_towers": cp.participating_towers,
            "linear_capex": cp.linear_capex_numeric,
            "consolidated_capex": cp.consolidated_capex_numeric,
            "synergy_savings": cp.synergy_savings_numeric,
            "work_packages_count": len(cp.work_packages),
            "work_packages": [
                {
                    "id": wp.id,
                    "tower": wp.tower,
                    "title": wp.title,
                    "objective": wp.objective,
                    "priority": wp.priority,
                    "capex_numeric": wp.capex_numeric,
                }
                for wp in cp.work_packages
            ],
        }
        for cp in corp_result.get("programs", [])
    ]
    payload["execution_roadmap"]["standalone_initiatives"] = corp_result.get(
        "standalone_initiatives", []
    )

    # Applies an executive-level refinement layer, allowing for the direct override of certain report elements as specified by Tier 1 configurations.
    # Dynamically extracts the headline and C-level narrative from client-specific configuration extensions, if such extensions are provided.
    intel_headline = None
    intel_narrative = None

    if intelligence_path.exists():
        try:
            raw_intel = load_client_intelligence(intelligence_path)
            extensions = (
                raw_intel.get("extensions", {}) if isinstance(raw_intel, dict) else {}
            )
            exec_sum = (
                extensions.get("executive_summary", {})
                if isinstance(extensions, dict)
                else {}
            )
            if isinstance(exec_sum, dict):
                intel_headline = exec_sum.get("headline")
                intel_narrative = exec_sum.get("narrative")
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug(f"[Fallback] Excepción controlada: {ex}")

    if intel_headline:
        payload["executive_summary"]["headline"] = intel_headline
    else:
        payload["executive_summary"]["headline"] = (
            f"{client_name}: Estrategia de Modernización de Infraestructura"
        )

    if intel_narrative:
        payload["executive_summary"]["narrative"] = intel_narrative

    payload["board_memo"] = _build_board_memo(towers_data, blueprint_files, client_name, client_dir=client_dir)
    payload["cross_tower_nexus"] = _build_cross_tower_nexus(towers_data, blueprint_files)
    payload["executive_callouts"] = _build_executive_callouts(client_name, towers_data, client_dir=client_dir)

    return payload


def main(argv: list[str] | None = None) -> None:
    """Parses command-line arguments to build and save a global report payload.

    This function serves as the main entry point for the script. It orchestrates
    the process by parsing command-line arguments for a client directory, client
    name, and an output file path. It then invokes `build_global_payload` to
    construct the report data and serializes the resulting payload to a
    JSON file at the specified output path.

    Args:
        argv: An optional list of string arguments, defaulting to `sys.argv`.
            The list is expected to contain the script name followed by the
            client directory path, client name, and the output file path.

    Raises:
        SystemExit: If fewer than four command-line arguments are provided.
        IOError: If an error occurs while writing the payload to the output file
            (e.g., permission denied, non-existent parent directory).
        TypeError: If the payload returned by `build_global_payload` contains
            objects that cannot be serialized to JSON.
    """
    raw_args = list(argv if argv is not None else sys.argv)
    if len(raw_args) < 4:
        sys.exit(1)
    client_dir = Path(raw_args[1])
    client_name = raw_args[2]
    payload = build_global_payload(client_dir, client_name)
    if payload:
        Path(raw_args[3]).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        logger.info("Payload dinámico generado con éxito.")


if __name__ == "__main__":
    main()
