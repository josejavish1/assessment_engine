"""
Módulo run_section_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import vertexai
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.prompts.section_prompts import (
    get_section_reviewer_prompt,
    get_section_writer_prompt,
)
from assessment_engine.schemas.asis import AsIsDraft
from assessment_engine.schemas.common import SectionReview
from assessment_engine.schemas.risks import RisksDraft
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.scripts.lib.config_loader import (
    resolve_document_profile,
    resolve_model_profile_for_role,
    resolve_review_rules,
)
from assessment_engine.scripts.lib.editorial_autofix import (
    apply_editorial_autofix,
    should_autofix_editorial,
)
from assessment_engine.scripts.lib.review_resilience import (
    build_corrective_feedback,
    force_approve_review,
    inject_manual_revision_note,
)
from assessment_engine.scripts.lib.runtime_env import ensure_google_cloud_env_defaults
from assessment_engine.scripts.lib.runtime_paths import (
    resolve_case_dir,
    resolve_tower_definition_file,
)

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = resolve_case_dir()
TOWER_DEF_FILE = resolve_tower_definition_file()
FINDINGS_FILE = CASE_DIR / "findings.json"
SCORING_FILE = CASE_DIR / "scoring_output.json"
TOWER_DEFINITION = json.loads(TOWER_DEF_FILE.read_text(encoding="utf-8"))
TOWER_ID = TOWER_DEFINITION["tower_id"]
TOWER_NAME = TOWER_DEFINITION["tower_name"]
TOWER_LABEL = f"{TOWER_ID} - {TOWER_NAME}"

SCHEMA_MAP = {"asis": AsIsDraft, "risks": RisksDraft}

SECTION_CONFIG = {
    "asis": {
        "id": "asis",
        "title": "AS-IS",
        "writer_description": f"redactar SOLO la sección AS-IS de la torre {TOWER_LABEL}.",
        "writer_rules": [
            "Usa exclusivamente la información incluida en INPUT_FINDINGS e INPUT_SCORING.",
            "No inventes capacidades, riesgos ni recomendaciones no soportadas.",
            "Mantén tono profesional, técnico y ejecutivo.",
            "Redacta en castellano.",
            "Devuelve SOLO JSON válido acorde al esquema solicitado.",
            "No uses markdown.",
            "No expliques tu proceso.",
            "No anticipes recomendaciones ni objetivos futuros; limítate al estado actual.",
            "En el desglose de pilares, describe el impacto operativo actual.",
        ],
        "review_description": f"revisar SOLO la sección AS-IS de la torre {TOWER_LABEL}.",
        "review_checks": [
            "Consistencia con los hallazgos.",
            "Consistencia con el scoring.",
            "Calidad profesional del texto.",
            "Ausencia de afirmaciones inventadas.",
            "Calidad y utilidad del desglose por pilares.",
            "Claridad metodológica.",
        ],
    },
    "risks": {
        "id": "risks",
        "title": "Riesgos identificados",
        "writer_description": f"redactar SOLO la sección Riesgos identificados de la torre {TOWER_LABEL}.",
        "writer_rules": [
            "Usa exclusivamente la información incluida en INPUT_FINDINGS e INPUT_SCORING.",
            "No inventes riesgos, causas ni mitigaciones no soportadas.",
            "Mantén tono profesional, técnico y ejecutivo.",
            "Redacta en castellano.",
            "Devuelve SOLO JSON válido acorde al esquema solicitado.",
            "No uses markdown.",
            "No expliques tu proceso.",
            "Los riesgos deben ser consistentes con el estado AS-IS y con la madurez observada.",
            "No conviertas esta sección en un roadmap ni en una lista de capacidades objetivo.",
        ],
        "review_description": f"revisar SOLO la sección Riesgos identificados de la torre {TOWER_LABEL}.",
        "review_checks": [
            "Consistencia con los hallazgos.",
            "Consistencia con el scoring.",
            "Calidad profesional del texto.",
            "Ausencia de riesgos, causas o mitigaciones inventadas.",
            "Calidad y utilidad de la estructura de riesgos (risk_items).",
            "Coherencia metodológica.",
            "Coherencia de los pilares afectados.",
        ],
    },
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_writer_prompt(
    section: str,
    findings: dict,
    scoring: dict,
    document_profile: dict,
    corrective_feedback: list[str] | None = None,
) -> str:
    cfg = SECTION_CONFIG[section]
    findings_pretty = json.dumps(findings, ensure_ascii=False, indent=2)
    scoring_pretty = json.dumps(scoring, ensure_ascii=False, indent=2)

    return get_section_writer_prompt(
        section_cfg=cfg,
        findings_pretty=findings_pretty,
        scoring_pretty=scoring_pretty,
        document_profile=document_profile,
        corrective_feedback=corrective_feedback,
    )


def build_reviewer_prompt(
    section: str,
    draft: dict,
    findings: dict,
    scoring: dict,
    tower_definition: dict,
) -> str:
    cfg = SECTION_CONFIG[section]
    draft_pretty = json.dumps(draft, ensure_ascii=False, indent=2)
    findings_pretty = json.dumps(findings, ensure_ascii=False, indent=2)
    scoring_pretty = json.dumps(scoring, ensure_ascii=False, indent=2)
    tower_definition_pretty = json.dumps(tower_definition, ensure_ascii=False, indent=2)

    return get_section_reviewer_prompt(
        section_cfg=cfg,
        draft_pretty=draft_pretty,
        findings_pretty=findings_pretty,
        scoring_pretty=scoring_pretty,
        tower_definition_pretty=tower_definition_pretty,
    )


def normalize_review(review: dict, review_rules: dict) -> dict:
    status = review.get("status")
    defects = review.get("defects", [])
    approval_conditions = review.get("approval_conditions", [])
    review_notes = review.get("review_notes", [])
    overall = review.get("overall_assessment", "")

    normalize_non_blocking = review_rules.get(
        "normalize_non_blocking_human_validation_to_approve", True
    )

    minor_only_revise = (
        status == "revise"
        and defects
        and all(
            str(item.get("severity", "")).strip().lower() == "minor" for item in defects
        )
        and not approval_conditions
        and normalize_non_blocking
    )

    if minor_only_revise:
        editorial_autofix = should_autofix_editorial(defects)
        review["status"] = "approve"
        review_notes.extend(
            [
                "Defecto menor no bloqueante normalizado automáticamente: "
                + " ".join(
                    part
                    for part in [
                        str(item.get("type", "")).strip(),
                        str(item.get("message", "")).strip(),
                    ]
                    if part
                ).strip()
                for item in defects
            ]
        )
        review["review_notes"] = review_notes
        review["defects"] = []
        review["_auto_fix_editorial"] = editorial_autofix
        defects = []
        status = "approve"

        overall = " ".join(str(overall).split()).strip()
        if overall:
            overall += " Se aprueba la sección porque los defectos detectados son menores y no bloquean la validez del contenido actual."
        else:
            overall = "La sección se aprueba porque los defectos detectados son menores y no bloquean la validez del contenido actual."
        review["overall_assessment"] = overall

    if status == "human_validation_required" and not defects and normalize_non_blocking:
        review["status"] = "approve"

        if approval_conditions:
            moved_notes = [
                f"Pendiente de validacion o enriquecimiento futuro: {item}"
                for item in approval_conditions
            ]
            review_notes.extend(moved_notes)
            review["review_notes"] = review_notes
            review["approval_conditions"] = []

        replacements = [
            "Por esta razón, el borrador requiere validación humana antes de ser aprobado.",
            "Por esta razon, el borrador requiere validacion humana antes de ser aprobado.",
            "requiere validación humana antes de ser aprobado",
            "requiere validacion humana antes de ser aprobado",
        ]
        for old in replacements:
            overall = overall.replace(old, "")

        overall = " ".join(overall.split()).strip()

        if overall:
            overall = (
                overall
                + " Se aprueba la sección porque las cuestiones abiertas restantes no bloquean "
                "la validez del contenido actual y se consideran oportunidades de enriquecimiento."
            )
        else:
            overall = (
                "La sección se aprueba porque las cuestiones abiertas restantes no bloquean "
                "la validez del contenido actual y se consideran oportunidades de enriquecimiento."
            )

        review["overall_assessment"] = overall

    return review


def finalize_approved(draft: dict, review: dict) -> dict:
    approved = json.loads(json.dumps(draft, ensure_ascii=False))
    replacements = 0
    if review.get("_auto_fix_editorial"):
        approved, replacements = apply_editorial_autofix(approved)
    approved["status"] = "approved"
    approved["_approval_metadata"] = {
        "review_status": review.get("status"),
        "overall_assessment": review.get("overall_assessment"),
        "review_notes": review.get("review_notes", []),
        "editorial_autofix_replacements": replacements,
    }
    return approved


def fallback_note_field_for_section(section: str) -> str:
    if section == "asis":
        return "executive_narrative"
    if section == "risks":
        return "introduction"
    return "section_title"


def main(argv: list[str] | None = None) -> None:
    # Soporte para orquestador asíncrono
    args = argv if argv is not None else sys.argv
    if len(args) != 2:
        raise SystemExit("Uso: python scripts/run_section_pipeline.py <asis|risks>")

    section = args[1].strip().lower()
    if section not in SECTION_CONFIG:
        raise SystemExit(f"Seccion no soportada: {section}. Usa: asis o risks")

    asyncio.run(_run_section_logic(section))


async def _run_section_logic(section: str) -> None:
    ensure_google_cloud_env_defaults()
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.environ["GOOGLE_CLOUD_LOCATION"]

    vertexai.Client(project=project, location=location)

    document_profile = resolve_document_profile()
    review_rules = resolve_review_rules()
    writer_model_profile = resolve_model_profile_for_role("section_writer")
    reviewer_model_profile = resolve_model_profile_for_role("section_reviewer")

    findings = load_json(FINDINGS_FILE)
    scoring = load_json(SCORING_FILE)
    tower_definition = load_json(TOWER_DEF_FILE)

    draft_file = CASE_DIR / f"draft_{section}.generated.json"
    review_file = CASE_DIR / f"review_{section}.generated.json"
    approved_file = CASE_DIR / f"approved_{section}.generated.json"
    writer_raw_file = CASE_DIR / f"draft_{section}.generated.raw.txt"
    reviewer_raw_file = CASE_DIR / f"review_{section}.generated.raw.txt"

    logger.info(f"Document profile: {document_profile.get('document_profile_id')}")
    logger.info(f"Writer model: {writer_model_profile.get('model')}")
    logger.info(f"Reviewer model: {reviewer_model_profile.get('model')}")

    writer_agent = Agent(
        model=writer_model_profile["model"],
        name=f"t5_writer_{section}_agent",
        instruction=(
            "Eres un redactor técnico especializado en informes de assessment de infraestructura. "
            "Tu salida debe ser rigurosa, trazable, consistente con la evidencia y útil para audiencias técnicas y ejecutivas. "
            "Devuelve solo JSON válido acorde al esquema solicitado."
        ),
    )
    writer_app = AdkApp(agent=writer_agent)

    max_writer_attempts = int(review_rules.get("max_writer_attempts", 2))
    max_review_rounds = int(review_rules.get("max_review_rounds", 3))

    reviewer_agent = Agent(
        model=reviewer_model_profile["model"],
        name=f"t5_reviewer_{section}_agent",
        instruction=(
            "Eres un revisor experto de informes de assessment de infraestructura. "
            "Tu trabajo es identificar defectos de calidad, trazabilidad, coherencia metodológica "
            "y utilidad ejecutiva. Devuelve solo JSON válido acorde al esquema solicitado."
        ),
    )
    reviewer_app = AdkApp(agent=reviewer_agent)

    corrective_feedback = None
    section_schema = SCHEMA_MAP[section]

    for review_round in range(1, max_review_rounds + 1):
        draft = None

        for attempt in range(1, max_writer_attempts + 1):
            logger.info(
                f"\n=== Writer attempt {attempt} para seccion '{section}' (round {review_round}) ==="
            )
            writer_message = build_writer_prompt(
                section,
                findings,
                scoring,
                document_profile,
                corrective_feedback,
            )
            try:
                candidate_draft = await run_agent(
                    writer_app,
                    user_id=f"writer-{section}-local-dev",
                    message=writer_message,
                    raw_output_file=writer_raw_file,
                    schema=section_schema,
                )
                logger.info(f"Validacion Pydantic del draft {section}: PASS")
                draft = candidate_draft
                break
            except Exception as e:
                logger.error(f"Validacion Pydantic del draft {section}: FAIL - {e}")
                corrective_feedback = [str(e)]
                if attempt == max_writer_attempts:
                    logger.warning(
                        f"WARNING: El Writer no pudo generar una seccion valida para '{section}' tras {max_writer_attempts} intentos. Se continuará con el borrador generado, pero contiene advertencias."
                    )
                    draft = candidate_draft
                    break
                continue

        if draft is None:
            raise RuntimeError("No se pudo obtener un draft valido.")

        save_json(draft_file, draft)
        logger.info(f"\nBorrador guardado en: {draft_file}")

        reviewer_message = build_reviewer_prompt(
            section, draft, findings, scoring, tower_definition
        )
        review = await run_agent(
            reviewer_app,
            user_id=f"reviewer-{section}-local-dev",
            message=reviewer_message,
            raw_output_file=reviewer_raw_file,
            schema=SectionReview,
        )
        review = normalize_review(review, review_rules)
        save_json(review_file, review)
        logger.info(f"\nRevision guardada en: {review_file}")
        logger.info(f"status: {review.get('status')}")

        if review.get("status") == "approve":
            approved = finalize_approved(draft, review)
            save_json(approved_file, approved)
            logger.info(f"Seccion aprobada y finalizada en: {approved_file}")
            return

        if review.get("status") == "revise" and review_round < max_review_rounds:
            corrective_feedback = build_corrective_feedback(review)
            logger.info(
                "La seccion requiere revision. Se relanza automaticamente con feedback del reviewer."
            )
            continue

        if review.get("status") in {"revise", "human_validation_required"}:
            forced_review = force_approve_review(
                review,
                f"Se fuerza la aprobación tras {review_round} rondas para no bloquear el pipeline; queda ajuste manual pendiente.",
            )
            adjusted_draft = inject_manual_revision_note(
                draft,
                review,
                fallback_note_field_for_section(section),
            )
            approved = finalize_approved(adjusted_draft, forced_review)
            save_json(approved_file, approved)
            save_json(review_file, forced_review)
            logger.info(
                "La sección no convergió tras el máximo de rondas. Se entrega versión aprobada con nota de ajuste manual pendiente."
            )
            logger.info(f"Seccion aprobada y finalizada en: {approved_file}")
            return
        raise RuntimeError(f"Estado de revision no reconocido: {review.get('status')}")


if __name__ == "__main__":
    main()
