"""
Módulo build_evidence_ledger.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import argparse
import json
import re
from pathlib import Path
from zipfile import ZipFile

from assessment_engine.scripts.lib.runtime_paths import ROOT


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    if path.suffix.lower() == ".docx":
        return read_docx_text(path)
    if path.suffix.lower() == ".rtf":
        return read_rtf_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [re.sub(r"\s+", " ", part).strip() for part in parts if part.strip()]


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9áéíóúüñ&/+-]+", text.lower()))


def pillar_keywords(pillar: dict) -> set[str]:
    keywords = tokenize(pillar["pillar_name"])
    for kpi in pillar.get("kpis", []):
        keywords.update(tokenize(kpi["kpi_name"]))
    return {word for word in keywords if len(word) > 2}


def support_tags_from_score(score: float) -> list[str]:
    if score >= 4:
        return ["asis", "executive_summary"]
    if score >= 3:
        return ["asis", "risk", "executive_summary"]
    return ["gap", "risk", "tobe", "todo", "executive_summary"]


def build_evidence_entries(
    case_input: dict, context_path: Path, responses_path: Path, tower_definition: dict
) -> list[dict]:
    context_text = read_text(context_path)
    context_sentences = split_sentences(context_text)
    answers = case_input.get("answers", [])
    answers_by_kpi = {answer["kpi_id"]: answer for answer in answers}

    evidences = []
    next_id = 1

    for pillar in tower_definition.get("pillars", []):
        keywords = pillar_keywords(pillar)
        matched = []
        for sentence in context_sentences:
            tokens = tokenize(sentence)
            if tokens & keywords:
                matched.append(sentence)
            if len(matched) >= 3:
                break

        if not matched:
            matched = [
                f"El contexto del cliente menciona capacidades y dependencias relevantes para {pillar['pillar_name']}."
            ]

        for sentence in matched:
            related_kpis = [kpi["kpi_id"] for kpi in pillar.get("kpis", [])]
            evidences.append(
                {
                    "evidence_id": f"CTX-{case_input['tower_id']}-{next_id:02d}",
                    "source_type": "context_summary",
                    "source_name": context_path.name,
                    "excerpt": sentence,
                    "pillar_ids": [pillar["pillar_id"]],
                    "kpi_ids": related_kpis,
                    "supports": ["asis", "risk", "executive_summary"],
                    "validation_state": case_input.get(
                        "validation_state", "Exploratoria"
                    ),
                }
            )
            next_id += 1

        for kpi in pillar.get("kpis", []):
            answer = answers_by_kpi.get(kpi["kpi_id"])
            if not answer:
                continue
            score = float(answer["value"])
            evidences.append(
                {
                    "evidence_id": f"QNR-{case_input['tower_id']}-{next_id:02d}",
                    "source_type": "questionnaire_response",
                    "source_name": responses_path.name,
                    "excerpt": (
                        f"{answer['question_id']} = {score:.1f}/5 en '{kpi['kpi_name']}' "
                        f"para el pilar '{pillar['pillar_name']}'."
                    ),
                    "pillar_ids": [pillar["pillar_id"]],
                    "kpi_ids": [kpi["kpi_id"]],
                    "supports": support_tags_from_score(score),
                    "validation_state": case_input.get(
                        "validation_state", "Exploratoria"
                    ),
                }
            )
            next_id += 1

    return evidences


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-input", required=True)
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--responses-file", required=True)
    args = parser.parse_args()

    case_input_path = Path(args.case_input).resolve()
    context_path = Path(args.context_file).resolve()
    responses_path = Path(args.responses_file).resolve()

    case_input = load_json(case_input_path)
    tower_definition = load_json(
        ROOT
        / "engine_config"
        / "towers"
        / case_input["tower_id"]
        / f"tower_definition_{case_input['tower_id']}.json"
    )
    ledger = {
        "case_id": case_input["case_id"],
        "tower_id": case_input["tower_id"],
        "tower_name": case_input["tower_name"],
        "validation_state": case_input.get("validation_state", "Exploratoria"),
        "evidences": build_evidence_entries(
            case_input, context_path, responses_path, tower_definition
        ),
        "_build_metadata": {
            "case_input": str(case_input_path),
            "context_file": str(context_path),
            "responses_file": str(responses_path),
        },
    }

    output_path = case_input_path.with_name("evidence_ledger.json")
    output_path.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"evidence_ledger generado en: {output_path}")
    print(f"evidences: {len(ledger['evidences'])}")


if __name__ == "__main__":
    main()
