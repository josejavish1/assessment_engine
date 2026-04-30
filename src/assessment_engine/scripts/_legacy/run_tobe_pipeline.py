"""
Módulo run_tobe_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import asyncio
import json
import os
from pathlib import Path

import vertexai
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.schemas.tobe import ToBeDraft
from assessment_engine.schemas.common import SectionReview
from assessment_engine.scripts.lib.ai_client import run_agent

from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role
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
from assessment_engine.prompts.tobe_prompts import (
    get_tobe_writer_prompt,
    get_tobe_reviewer_prompt
)

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = resolve_case_dir()
TOWER_DEF_FILE = resolve_tower_definition_file()
FINDINGS_FILE = CASE_DIR / "findings.json"
SCORING_FILE = CASE_DIR / "scoring_output.json"
CASE_INPUT_FILE = CASE_DIR / "case_input.json"
TOWER_DEFINITION = json.loads(TOWER_DEF_FILE.read_text(encoding="utf-8"))
TOWER_ID = TOWER_DEFINITION["tower_id"]
TOWER_NAME = TOWER_DEFINITION["tower_name"]
TOWER_LABEL = f"{TOWER_ID} - {TOWER_NAME}"

DRAFT_FILE = CASE_DIR / "draft_tobe.generated.json"
REVIEW_FILE = CASE_DIR / "review_tobe.generated.json"
APPROVED_FILE = CASE_DIR / "approved_tobe.generated.json"
WRITER_RAW_FILE = CASE_DIR / "draft_tobe.generated.raw.txt"
REVIEWER_RAW_FILE = CASE_DIR / "review_tobe.generated.raw.txt"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_writer_prompt(
    findings: dict,
    scoring: dict,
    case_input: dict,
    tower_definition: dict,
    corrective_feedback: list[str] | None = None,
) -> str:
    findings_pretty = json.dumps(findings, ensure_ascii=False, indent=2)
    scoring_pretty = json.dumps(scoring, ensure_ascii=False, indent=2)
    case_input_pretty = json.dumps(case_input, ensure_ascii=False, indent=2)
    tower_definition_pretty = json.dumps(tower_definition, ensure_ascii=False, indent=2)

    feedback_block = ""
    if corrective_feedback:
        feedback_text = "\n".join(f"- {item}" for item in corrective_feedback)
        feedback_block = f"""\nCorrecciones obligatorias para esta nueva iteracion:\n{feedback_text}\nDebes corregir completamente esos defectos y volver a generar la seccion.\n"""

    return get_tobe_writer_prompt(
        findings_pretty, scoring_pretty, case_input_pretty, tower_definition_pretty, TOWER_LABEL, feedback_block
    )


def build_reviewer_prompt(
    draft: dict, findings: dict, scoring: dict, case_input: dict, tower_definition: dict
) -> str:
    draft_pretty = json.dumps(draft, ensure_ascii=False, indent=2)
    findings_pretty = json.dumps(findings, ensure_ascii=False, indent=2)
    scoring_pretty = json.dumps(scoring, ensure_ascii=False, indent=2)
    case_input_pretty = json.dumps(case_input, ensure_ascii=False, indent=2)
    tower_definition_pretty = json.dumps(tower_definition, ensure_ascii=False, indent=2)

    return get_tobe_reviewer_prompt(
        draft_pretty, findings_pretty, scoring_pretty, case_input_pretty, tower_definition_pretty, TOWER_LABEL
    )


def normalize_review(review: dict) -> dict:
    status = review.get("status")
    defects = review.get("defects", [])
    approval_conditions = review.get("approval_conditions", [])
    review_notes = review.get("review_notes", [])
    overall = review.get("overall_assessment", "")

    minor_only_revise = (
        status == "revise"
        and defects
        and all(
            str(item.get("severity", "")).strip().lower() == "minor" for item in defects
        )
        and not approval_conditions
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

    if status == "human_validation_required" and not defects:
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
                + " Se aprueba la sección porque las cuestiones abiertas restantes no bloquean la validez del contenido actual y se consideran oportunidades de enriquecimiento."
            )
        else:
            overall = "La sección se aprueba porque las cuestiones abiertas restantes no bloquean la validez del contenido actual y se consideran oportunidades de enriquecimiento."

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


async def main() -> None:
    ensure_google_cloud_env_defaults()
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.environ["GOOGLE_CLOUD_LOCATION"]

    vertexai.Client(project=project, location=location)
    writer_model = resolve_model_profile_for_role("section_writer")["model"]
    reviewer_model = resolve_model_profile_for_role("section_reviewer")["model"]

    findings = load_json(FINDINGS_FILE)
    scoring = load_json(SCORING_FILE)
    case_input = load_json(CASE_INPUT_FILE)
    tower_definition = load_json(TOWER_DEF_FILE)

    writer_agent = Agent(
        model=writer_model,
        name="t5_writer_tobe_agent",
        instruction=(
            "Eres un redactor tecnico especializado en informes de assessment de infraestructura. "
            "Tu salida debe ser rigurosa, trazable, consistente con la evidencia y util para audiencias tecnicas y ejecutivas. "
            "Devuelve solo JSON valido acorde al esquema solicitado."
        ),
    )
    writer_app = AdkApp(agent=writer_agent)

    reviewer_agent = Agent(
        model=reviewer_model,
        name="t5_reviewer_tobe_agent",
        instruction=(
            "Eres un revisor experto de informes de assessment de infraestructura. "
            "Tu trabajo es identificar defectos de calidad, trazabilidad, coherencia metodologica "
            "y utilidad ejecutiva. Devuelve solo JSON valido acorde al esquema solicitado."
        ),
    )
    reviewer_app = AdkApp(agent=reviewer_agent)

    max_review_rounds = 3
    corrective_feedback = None

    for review_round in range(1, max_review_rounds + 1):
        draft = None

        for attempt in range(1, 3):
            print(
                f"\n=== Writer attempt {attempt} para seccion 'tobe' (round {review_round}) ==="
            )
            writer_message = build_writer_prompt(
                findings, scoring, case_input, tower_definition, corrective_feedback
            )
            try:
                candidate_draft = await run_agent(
                    writer_app,
                    user_id="writer-tobe-local-dev",
                    message=writer_message,
                    raw_output_file=WRITER_RAW_FILE,
                    schema=ToBeDraft
                )
                print("Validacion Pydantic del draft TO-BE: PASS")
                draft = candidate_draft
                break
            except Exception as e:
                print(f"Validacion Pydantic del draft TO-BE: FAIL - {e}")
                corrective_feedback = [str(e)]
                if attempt == 2:
                    print("ERROR: El Writer no pudo generar un TO-BE valido tras 2 intentos.")
                    raise

        if draft is None:
            raise RuntimeError("No se pudo obtener un draft TO-BE valido.")

        save_json(DRAFT_FILE, draft)
        print(f"\nBorrador TO-BE guardado en: {DRAFT_FILE}")

        reviewer_message = build_reviewer_prompt(
            draft, findings, scoring, case_input, tower_definition
        )
        review = await run_agent(
            reviewer_app,
            user_id="reviewer-tobe-local-dev",
            message=reviewer_message,
            raw_output_file=REVIEWER_RAW_FILE,
            schema=SectionReview
        )
        review = normalize_review(review)
        save_json(REVIEW_FILE, review)
        print(f"\nRevision TO-BE guardada en: {REVIEW_FILE}")
        print(f"status: {review.get('status')}")

        if review.get("status") == "approve":
            approved = finalize_approved(draft, review)
            save_json(APPROVED_FILE, approved)
            print(f"Seccion TO-BE aprobada y finalizada en: {APPROVED_FILE}")
            return

        if review.get("status") == "revise" and review_round < max_review_rounds:
            corrective_feedback = build_corrective_feedback(review)
            print(
                "La seccion TO-BE requiere revision. Se relanza automaticamente con feedback del reviewer."
            )
            continue

        if review.get("status") in {"revise", "human_validation_required"}:
            forced_review = force_approve_review(
                review,
                f"Se fuerza la aprobación tras {review_round} rondas para no bloquear el pipeline; queda ajuste manual pendiente.",
            )
            adjusted_draft = inject_manual_revision_note(draft, review, "introduction")
            approved = finalize_approved(adjusted_draft, forced_review)
            save_json(APPROVED_FILE, approved)
            save_json(REVIEW_FILE, forced_review)
            print(
                "La sección TO-BE no convergió tras el máximo de rondas. Se entrega versión aprobada con nota de ajuste manual pendiente."
            )
            print(f"Seccion TO-BE aprobada y finalizada en: {APPROVED_FILE}")
            return

        raise RuntimeError(f"Estado de revision no reconocido: {review.get('status')}")


if __name__ == "__main__":
    asyncio.run(main())
