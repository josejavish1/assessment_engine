"""
Módulo build_case_input.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from assessment_engine.scripts.lib.runtime_paths import (
    ROOT,
    resolve_case_dir,
    resolve_client_intelligence_path,
)
from assessment_engine.scripts.lib.text_utils import normalize_tower_name, slugify

RESPONSE_RE = re.compile(r"(T\d+\.P\d+\.K\d+\.PR\d+)\s*:\s*([1-5](?:[.,]\d+)?)")


def read_docx_text(path: Path) -> str:
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"\s+", " ", text).strip()


def read_rtf_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"\\par[d]?|\\line", "\n", raw)
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)
    raw = raw.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", raw).strip()


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx_text(path)
    if suffix == ".rtf":
        return read_rtf_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_matrix_file_name(tower_id: str) -> str | None:
    tower_dir = ROOT / "source_docs" / "towers" / tower_id
    if not tower_dir.exists():
        return None
    candidates = sorted(path.name for path in tower_dir.iterdir() if path.is_file())
    return candidates[0] if candidates else None


def build_question_text(kpi_name: str) -> str:
    return (
        f"Evaluación de madurez para '{kpi_name}'. "
        "La respuesta debe valorarse en escala 1-5."
    )


def parse_responses(responses_text: str, tower_id: str) -> dict[str, float]:
    scores: dict[str, float] = {}
    for question_id, value_text in RESPONSE_RE.findall(responses_text):
        if not question_id.startswith(f"{tower_id}."):
            continue
        scores[question_id] = float(value_text.replace(",", "."))
    return scores


def build_question_lookup(tower_definition: dict) -> dict[str, str]:
    lookup: dict[str, str] = {}

    for question in tower_definition.get("questions", []):
        question_id = question.get("question_id")
        question_text = question.get("question_text")
        if question_id and question_text:
            lookup[question_id] = question_text

    for pillar in tower_definition.get("pillars", []):
        for kpi in pillar.get("kpis", []):
            for question in kpi.get("questions", []):
                question_id = question.get("question_id")
                question_text = question.get("question_text")
                if question_id and question_text and question_id not in lookup:
                    lookup[question_id] = question_text

    return lookup


def build_case_input(args: argparse.Namespace) -> dict:
    tower_definition = load_json(
        ROOT
        / "engine_config"
        / "towers"
        / args.tower
        / f"tower_definition_{args.tower}.json"
    )

    context_path = Path(args.context_file).resolve()
    responses_path = Path(args.responses_file).resolve()
    responses_text = read_text(responses_path)
    parsed_scores = parse_responses(responses_text, args.tower)
    question_lookup = build_question_lookup(tower_definition)

    answers = []
    for pillar in tower_definition.get("pillars", []):
        for kpi in pillar.get("kpis", []):
            question_id = f"{kpi['kpi_id']}.PR1"
            if question_id not in parsed_scores:
                continue
            answers.append(
                {
                    "question_id": question_id,
                    "pillar_id": pillar["pillar_id"],
                    "pillar_name": pillar["pillar_name"],
                    "kpi_id": kpi["kpi_id"],
                    "kpi_name": kpi["kpi_name"],
                    "value": parsed_scores[question_id],
                    "question_text": question_lookup.get(
                        question_id, build_question_text(kpi["kpi_name"])
                    ),
                }
            )

    source_documents = [
        "0. Framework metodológico de Madurez de infraestructura v1.0.docx",
        "1. Taxonomía y gobierno de las Torres Tecnológicas v1.0.docx",
        "12. Template Documento Anexos Alpha v.05.docx",
        context_path.name,
        responses_path.name,
    ]
    matrix_file_name = resolve_matrix_file_name(args.tower)
    if matrix_file_name:
        source_documents.insert(2, matrix_file_name)

    client_slug = slugify(args.client)
    intel_path = resolve_client_intelligence_path(client_slug)
    target_maturity = 4.0
    if intel_path.exists():
        try:
            intel = load_json(intel_path)
            target_maturity = intel.get("target_maturity_matrix", {}).get(
                args.tower, 4.0
            )
        except Exception:
            pass

    return {
        "case_id": f"{client_slug}_{args.tower.lower()}_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}",
        "client": args.client,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "assessment_mode": "Fast Assessment",
        "validation_state": "Exploratoria",
        "tower_id": args.tower,
        "tower_name": normalize_tower_name(tower_definition["tower_name"]),
        "tower_purpose": tower_definition["purpose"],
        "target_maturity_default": target_maturity,
        "source_documents": source_documents,
        "answers": answers,
        "template_sections": [
            "informacion_documento",
            "introduccion_dominio",
            "pilares_de_evaluacion",
            "asis_estado_actual",
            "riesgos_identificados",
            "tobe_estado_objetivo",
            "gap_analysis",
            "todo_plan_de_evolucion",
            "conclusion_dominio",
        ],
        "working_rules": {
            "score_question": tower_definition["working_rules"]["score_question"],
            "score_indicator": tower_definition["working_rules"]["score_indicator"],
            "score_pillar": tower_definition["working_rules"]["score_pillar"],
            "score_tower": tower_definition["working_rules"]["score_tower"],
            "display_rounding": tower_definition["working_rules"]["display_rounding"],
            "reporting_rule": tower_definition["working_rules"]["reporting_rule"],
            "tobe_rule": tower_definition["working_rules"]["tobe_default_rule"],
        },
        "_build_metadata": {
            "context_file": str(context_path),
            "responses_file": str(responses_path),
            "answers_detected": len(answers),
            "context_chars": len(read_text(context_path)),
            "responses_chars": len(responses_text),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    parser.add_argument("--tower", required=True)
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--responses-file", required=True)
    args = parser.parse_args()

    client_slug = slugify(args.client)
    case_dir = resolve_case_dir(client_slug, args.tower)
    case_dir.mkdir(parents=True, exist_ok=True)

    case_input = build_case_input(args)
    output_path = case_dir / "case_input.json"
    output_path.write_text(
        json.dumps(case_input, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"case_input generado en: {output_path}")
    print(f"answers: {len(case_input['answers'])}")


if __name__ == "__main__":
    main()
