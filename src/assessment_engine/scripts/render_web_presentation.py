"""Render the strategic web dashboard from global and tower payloads."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import jinja2

from assessment_engine.schemas.blueprint import BlueprintPayload
from assessment_engine.schemas.global_report import GlobalReportPayload
from assessment_engine.scripts.lib.global_maturity_policy import average_pillar_target
from assessment_engine.scripts.lib.maturity_band import (
    GLOBAL_MATURITY_BANDS,
    resolve_maturity_band,
)
from assessment_engine.scripts.lib.runtime_paths import (
    resolve_blueprint_payload_candidates,
    resolve_client_dir,
    resolve_global_report_payload_path,
    resolve_web_dashboard_template_path,
)

TEMPLATE_PATH = resolve_web_dashboard_template_path()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _load_global_payload(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    GlobalReportPayload.model_validate(payload)
    return payload


def _load_blueprint_payload(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    BlueprintPayload.model_validate(payload)
    return payload


def _find_blueprint_payload(tower_dir: Path, tower_id: str) -> Path | None:
    for candidate in resolve_blueprint_payload_candidates(
        tower_dir.parent.name, tower_id
    ):
        if candidate.exists():
            return candidate
    return None


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _try_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).split()[0].replace(",", "."))
    except (TypeError, ValueError):
        return None


def _normalize_tower_meta(tower_meta: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(tower_meta)
    if normalized.get("band") not in (None, ""):
        return normalized

    score = _try_float(normalized.get("score"))
    if score is None:
        return normalized

    normalized["band"] = resolve_maturity_band(score, GLOBAL_MATURITY_BANDS)["label"]
    return normalized


def _compute_global_score(global_payload: dict[str, Any]) -> str:
    executive_summary = global_payload.get("executive_summary", {})
    meta = global_payload.get("meta", {})

    for candidate in (
        executive_summary.get("score"),
        meta.get("global_score_display"),
        meta.get("global_score"),
    ):
        if candidate not in (None, ""):
            return str(candidate)

    scores = [
        _safe_float(tower.get("score"), 0.0)
        for tower in global_payload.get("heatmap", [])
        if tower.get("score") not in (None, "")
    ]
    if not scores:
        return "0.0"
    return f"{sum(scores) / len(scores):.1f}"


def _derive_complexity(score: float) -> str:
    if score < 2.2:
        return "Alta"
    if score < 3.2:
        return "Media"
    return "Baja"


def _normalize_complexity(raw_complexity: Any, fallback: str) -> str:
    if not raw_complexity:
        return fallback
    raw_text = str(raw_complexity)
    if "Alta" in raw_text:
        return "Alta"
    if "Media" in raw_text:
        return "Media"
    if "Baja" in raw_text:
        return "Baja"
    return raw_text[:10] or fallback


def _extract_target_maturity(
    blueprint_payload: dict[str, Any],
    tower_meta: dict[str, Any],
) -> str:
    summary = blueprint_payload.get("summary", {})
    if summary.get("target_maturity"):
        return str(summary["target_maturity"])

    target_architecture = blueprint_payload.get("target_architecture_tobe", {})
    target_maturity = target_architecture.get("target_maturity")
    if isinstance(target_maturity, dict):
        score_reference = target_maturity.get("recommended_score_reference")
        if score_reference:
            return str(score_reference)
    if target_maturity not in (None, ""):
        return str(target_maturity)

    pillars = blueprint_payload.get("pillars_analysis", [])
    pillar_target = average_pillar_target(pillars, default=0.0)
    if pillar_target > 0:
        return f"{pillar_target:.1f}"

    return str(tower_meta.get("target_maturity", "4.0"))


def _build_strategy(global_payload: dict[str, Any], client_id: str) -> dict[str, Any]:
    executive_summary = global_payload.get("executive_summary", {})
    target_vision = global_payload.get("target_vision", {})
    execution_roadmap = global_payload.get("execution_roadmap", {})
    heatmap = [
        _normalize_tower_meta(tower_meta)
        for tower_meta in global_payload.get("heatmap", [])
    ]

    return {
        "meta": {"client": client_id.upper(), "version": "v5.1 Strategic Ops"},
        "strategy": {
            "headline": executive_summary.get("headline", ""),
            "narrative": executive_summary.get("narrative", ""),
            "global_score": _compute_global_score(global_payload),
            "burning_platform": global_payload.get("burning_platform", []),
            "principles": target_vision.get("evolution_principles", []),
            "architecture_principles": target_vision.get("architecture_principles", []),
            "operating_model": target_vision.get("operating_model_implications", []),
            "gtm_strategy": global_payload.get("gtm_strategy", {}),
            "stakeholders": global_payload.get("stakeholder_matrix", []),
            "business_impacts": executive_summary.get("key_business_impacts", []),
            "estimated_tam": global_payload.get("meta", {}).get("estimated_tam", "TBD"),
        },
        "roadmap": {
            "programs": execution_roadmap.get("programs", []),
            "horizons": execution_roadmap.get("horizons", {}),
            "proactive_proposals": execution_roadmap.get("proactive_proposals", [])
            or _default_proposals(),
        },
        "heatmap": heatmap,
        "towers": {},
    }


def _default_proposals() -> list[dict[str, Any]]:
    return [
        {
            "initiative_name": "Programa de Choque NIS2 & Ciber-Resiliencia",
            "executive_synthesis": (
                "Plan de remediación acelerada para cerrar las brechas críticas de "
                "seguridad perimetral, desplegar inmutabilidad de backups frente a "
                "ransomware y establecer un marco de gobierno auditable."
            ),
            "context_and_why": {
                "cost_of_inaction": (
                    "Incumplimiento de normativas (NIS2/GDPR) con riesgo de sanciones "
                    "millonarias e incapacidad de recuperar las operaciones ante un ataque."
                )
            },
            "solution_and_what": {
                "target_state": (
                    "Postura defensiva validada, MFA ubicuo, y capacidad demostrable "
                    "de recuperación (Cyber Vault)."
                )
            },
            "investment_and_timeline": {"tcv_range": "3-6 Meses"},
            "deep_dive": {
                "deliverables": [
                    "Arquitectura Zero Trust Perimeter",
                    "Bóveda de Backups Inmutable (Air-gapped)",
                    "Plan Director de Seguridad (PDS) para cumplimiento NIS2",
                ],
                "roi": (
                    "Evita multas regulatorias de hasta el 2% de la facturación "
                    "global y mitiga el lucro cesante por paradas operativas "
                    "superiores a 24h."
                ),
                "prerequisites": (
                    "Aprobación de presupuesto CAPEX extraordinario y disponibilidad "
                    "del equipo de cumplimiento corporativo."
                ),
            },
        },
        {
            "initiative_name": "Estabilización Core Network & SD-WAN",
            "executive_synthesis": (
                "Saneamiento de la arquitectura de red corporativa para eliminar "
                "puntos únicos de fallo (SPOF) y migrar hacia un modelo SD-WAN "
                "que garantice el rendimiento de aplicaciones críticas."
            ),
            "context_and_why": {
                "cost_of_inaction": (
                    "Caídas de servicio impredecibles y lentitud que paraliza la "
                    "operativa del personal y la atención clínica/cliente."
                )
            },
            "solution_and_what": {
                "target_state": (
                    "Red de alta disponibilidad, monitorización proactiva y ancho "
                    "de banda garantizado para SaaS."
                )
            },
            "investment_and_timeline": {"tcv_range": "6-9 Meses"},
            "deep_dive": {
                "deliverables": [
                    "Renovación de electrónica de red core",
                    "Despliegue de SD-WAN en sedes principales",
                    "Plataforma de Monitorización Proactiva (NPM)",
                ],
                "roi": (
                    "Reducción del 80% en los tiempos de caída de sedes. Incremento "
                    "directo en la productividad de los empleados y mejora en la "
                    "experiencia del paciente."
                ),
                "prerequisites": (
                    "Ventanas de mantenimiento aprobadas para cortes controlados "
                    "durante la migración de la electrónica."
                ),
            },
        },
    ]


def _build_tower_nexus(
    tower_meta: dict[str, Any],
    blueprint_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_tower_meta = _normalize_tower_meta(tower_meta)
    score = _safe_float(normalized_tower_meta.get("score"), 2.5)
    default_complexity = _derive_complexity(score)

    tower_nexus: dict[str, Any] = {
        "meta": {
            **normalized_tower_meta,
            "status_color": normalized_tower_meta.get("status_color", "38BDF8"),
        },
        "executive_summary": normalized_tower_meta.get("executive_message", ""),
        "pillars": [],
        "decisions": [],
        "cost_of_inaction": "",
        "target_maturity": str(normalized_tower_meta.get("target_maturity", "4.0")),
        "complexity": default_complexity,
        "structural_risks": [],
        "business_impact": "",
        "operational_benefits": [],
    }

    if not blueprint_payload:
        return tower_nexus

    executive_snapshot = blueprint_payload.get("executive_snapshot", {})
    tower_nexus["complexity"] = _normalize_complexity(
        executive_snapshot.get("transformation_complexity"),
        default_complexity,
    )
    tower_nexus["target_maturity"] = _extract_target_maturity(
        blueprint_payload,
        tower_meta,
    )
    tower_nexus.update(
        {
            "executive_summary": executive_snapshot.get(
                "bottom_line",
                tower_nexus["executive_summary"],
            ),
            "cost_of_inaction": executive_snapshot.get("cost_of_inaction", ""),
            "decisions": executive_snapshot.get("decisions")
            or blueprint_payload.get("executive_decisions", []),
            "structural_risks": executive_snapshot.get("structural_risks", []),
            "business_impact": executive_snapshot.get("business_impact", ""),
            "operational_benefits": executive_snapshot.get("operational_benefits", []),
        }
    )

    for pillar in blueprint_payload.get("pillars_analysis", []):
        tower_nexus["pillars"].append(
            {
                "name": pillar.get("pilar_name"),
                "score": pillar.get("score"),
                "health_check": pillar.get("health_check_asis", []),
                "projects": pillar.get("projects_todo", []),
                "target_vision": pillar.get("target_architecture_tobe", {}).get(
                    "vision", ""
                ),
            }
        )

    return tower_nexus


def _build_nexus_data(client_id: str) -> tuple[dict[str, Any], Path]:
    client_dir = resolve_client_dir(client_id)
    global_payload_path = resolve_global_report_payload_path(client_id)
    if not global_payload_path.exists():
        raise FileNotFoundError(
            f"No se encuentra el payload global: {global_payload_path}"
        )

    global_payload = _load_global_payload(global_payload_path)
    nexus_data = _build_strategy(global_payload, client_id)

    for tower_meta in global_payload.get("heatmap", []):
        tower_id = tower_meta.get("id")
        if not tower_id:
            continue
        tower_dir = client_dir / tower_id
        blueprint_path = _find_blueprint_payload(tower_dir, tower_id)
        blueprint_payload = (
            _load_blueprint_payload(blueprint_path) if blueprint_path else None
        )
        nexus_data["towers"][tower_id] = _build_tower_nexus(
            tower_meta,
            blueprint_payload,
        )

    return nexus_data, client_dir


def _load_template() -> jinja2.Template:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_PATH),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )
    return env.get_template("dashboard.html")


def _render_html(client_id: str, nexus_data: dict[str, Any]) -> str:
    template = _load_template()
    json_data = json.dumps(nexus_data, ensure_ascii=False)
    return template.render(client_id=client_id.upper(), json_data=json_data)


def generate_web_dashboard(client_id: str) -> Path:
    nexus_data, client_dir = _build_nexus_data(client_id)
    presentation_dir = client_dir / "presentation"
    presentation_dir.mkdir(parents=True, exist_ok=True)

    # Copiar los assets estáticos
    import shutil
    for asset in ["styles.css", "main.js"]:
        source_path = TEMPLATE_PATH / asset
        if source_path.exists():
            shutil.copy(source_path, presentation_dir / asset)

    output_path = presentation_dir / "index.html"
    output_path.write_text(_render_html(client_id, nexus_data), encoding="utf-8")

    print(f"✅ Dashboard v5.1 (Strategic & Interactive) generado en: {output_path}")
    return output_path


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv
    client_id = args[1] if len(args) > 1 else "ivirma"
    generate_web_dashboard(client_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
