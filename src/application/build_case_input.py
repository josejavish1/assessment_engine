"""Encapsulates the central processing logic and helper functions for the Assessment Engine's data processing pipeline."""

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from infrastructure.client_intelligence import (
    build_client_context_packet,
    get_target_maturity,
    load_client_intelligence,
)
from infrastructure.runtime_paths import (
    ROOT,
    resolve_case_dir,
    resolve_client_intelligence_path,
)
from infrastructure.text_utils import normalize_tower_name, slugify

logger = logging.getLogger(__name__)

RESPONSE_RE = re.compile(r"(T\d+\.P\d+\.K\d+)\.?\s*PR(\d+)\s*:\s*([1-5](?:[.,]\d+)?)")


def read_docx_text(path: Path) -> str:
    """Extract raw text content from a DOCX file.

    This function processes the .docx file as a standard ZIP archive by reading
    the primary document content from the 'word/document.xml' member. All XML
    tags are subsequently removed and sequences of whitespace are collapsed
    to produce a plain text representation.

    Args:
        path (pathlib.Path): The file system path to the input .docx file.

    Returns:
        str: The extracted text content, where XML tags are removed and any
            sequence of whitespace characters is collapsed into a single space.

    Raises:
        FileNotFoundError: If the file at `path` does not exist.
        zipfile.BadZipFile: If the file at `path` is not a valid ZIP archive.
        KeyError: If 'word/document.xml' is not found within the DOCX archive.
    """
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"\s+", " ", text).strip()


def read_rtf_text(path: Path) -> str:
    r"""Extracts plain text from an RTF file using regular expression substitutions.

    Performs a best-effort, non-parsing extraction of text from a Rich Text
    Format (RTF) document. The function applies a series of regular expressions
    to strip common RTF control words (e.g., \\par, \\fonttbl), hexadecimal
    character codes, and grouping braces. It then normalizes whitespace to
    produce a simplified text representation.

    Note:
        This method is not a comprehensive RTF parser and may yield imperfect
        results for documents with complex formatting or embedded objects.

    Args:
        path (pathlib.Path): The file system path to the RTF document.

    Returns:
        str: The extracted plain text content from the file, with normalized
            whitespace.

    Raises:
        FileNotFoundError: If the file specified by `path` does not exist.
        IsADirectoryError: If `path` points to a directory.
        OSError: If an I/O error occurs during file reading.
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"\\par[d]?|\\line", "\n", raw)
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)
    raw = raw.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", raw).strip()


def read_text(path: Path) -> str:
    """Extracts text content from a file by dispatching based on its extension.

    The function inspects the file's suffix to select an appropriate parsing
    strategy. It provides specialized readers for `.docx` and `.rtf` files.
    For unrecognized extensions, it falls back to a standard text read using
    UTF-8 encoding, with decoding errors ignored.

    Args:
        path: The path object representing the file to be read.

    Returns:
        A string containing the extracted text from the file.

    Raises:
        FileNotFoundError: If the file specified by `path` does not exist.
        Exception: Propagates format-specific exceptions from underlying
            readers for malformed or unreadable files (e.g., `.docx`, `.rtf`).
    """
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx_text(path)
    if suffix == ".rtf":
        return read_rtf_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


from typing import Any, cast


def load_json(path: Path) -> dict[str, Any]:
    """Read and parse a UTF-8-SIG encoded JSON file from the specified path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def resolve_matrix_file_name(tower_id: str) -> str | None:
    """Resolves the matrix file name from a tower's source directory.

    Constructs a path to `ROOT/source_docs/towers/<tower_id>`, lists all files
    within this directory, sorts their names lexicographically, and returns the
    first name from the resulting list. This procedure relies on the convention
    that the first file, when sorted alphabetically, is the intended matrix file.

    Args:
        tower_id (str): The unique identifier for the tower.

    Returns:
        str | None: The file name of the matrix file, or None if the target
            directory does not exist or contains no files.

    Raises:
        NotADirectoryError: If the resolved path for the tower directory exists
            but points to a file.
    """
    tower_dir = ROOT / "source_docs" / "towers" / tower_id
    if not tower_dir.exists():
        return None
    candidates = sorted(path.name for path in tower_dir.iterdir() if path.is_file())
    return candidates[0] if candidates else None


def build_question_text(kpi_name: str) -> str:
    """Generate a Spanish maturity assessment question for a given KPI."""
    return (
        f"Evaluación de madurez para '{kpi_name}'. "
        "La respuesta debe valorarse en escala 1-5."
    )


def parse_responses(responses_text: str, tower_id: str) -> dict[str, float]:
    """Parse a raw response string to extract numerical scores for a specific tower.

    Uses a regular expression to find all question-value pairs in the input
    text. The function filters these pairs, retaining only those whose question
    prefix matches the specified `tower_id`. For each valid pair, it
    constructs a standardized question ID (e.g., 'T1.Q1.PR1') and parses the
    associated numerical score, handling comma-separated decimals.

    Args:
        responses_text: The raw string containing all responses to be parsed.
        tower_id: The identifier for the tower used to filter which questions
            are processed (e.g., 'T1').

    Returns:
        A dictionary mapping question IDs (e.g., 'T1.Q1.PR1') to their
        corresponding numerical scores as floats.

    Raises:
        ValueError: If a matched response value cannot be converted to a float
            after replacing commas with periods.
    """
    scores: dict[str, float] = {}
    for question_prefix, pr_number, value_text in RESPONSE_RE.findall(responses_text):
        question_id = f"{question_prefix}.PR{pr_number}"
        if not question_prefix.startswith(f"{tower_id}."):
            continue
        scores[question_id] = float(value_text.replace(",", "."))
    return scores


def build_question_lookup(tower_definition: dict) -> dict[str, str]:
    """Constructs a flat lookup mapping question IDs to their corresponding text.

    This function traverses a nested dictionary structure, extracting questions from a
    top-level 'questions' list and from deeply nested lists within 'pillars' and
    'kpis'. Top-level questions are given precedence; if a question ID appears
    at the top level, any nested question with the same ID is ignored. The
    function gracefully handles missing keys within the input dictionary.

    Args:
        tower_definition: A dictionary defining a tower structure. It is expected
            to contain an optional 'questions' list and an optional 'pillars'
            list. Each pillar can contain a 'kpis' list, and each KPI can
            contain a 'questions' list. Each question dictionary should have
            'question_id' and 'question_text' keys.

    Returns:
        A dictionary where keys are question IDs (str) and values are the
        corresponding question texts (str).
    """
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
    r"""{'docstring': 'Constructs a case input dictionary from command-line arguments.\n\nThis function orchestrates the aggregation of data required for a complete\nassessment case. It loads a technology tower definition, parses client\nresponses from a text file, reads supplementary context documents, and\nretrieves client-specific intelligence data if available. All retrieved\nand processed information is structured into a single dictionary suitable\nfor use by an assessment generation engine.\n\nArgs:\n    args: An `argparse.Namespace` object containing command-line\n        arguments. Expected attributes include `tower`, `context_file`,\n        `responses_file`, and `client`.\n\nReturns:\n    A dictionary containing the structured case input data, including\n    client information, tower details, parsed answers, source\n    documents, configuration rules, and build metadata.\n\nRaises:\n    FileNotFoundError: If the tower definition, context file, or responses\n        file cannot be found at their respective paths.\n    KeyError: If a required key is missing from the loaded tower definition\n        JSON file.\n    ValueError: If the client responses text file cannot be parsed.'}."""
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
    intel: dict = {}
    target_maturity = 4.0
    if intel_path.exists():
        try:
            intel = load_client_intelligence(intel_path)
            target_maturity = get_target_maturity(intel, args.tower, 4.0)
        except Exception:
            pass

    context_text = read_text(context_path)
    context_summary = context_text[:4000]
    client_context = (
        build_client_context_packet(intel, tower_id=args.tower) if intel else {}
    )

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
        "context_summary": context_summary,
        "client_context": client_context,
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
            "context_chars": len(context_text),
            "responses_chars": len(responses_text),
        },
    }


def main() -> None:
    r"""{'docstring': "Parses command-line arguments to generate and serialize a case input JSON file.\n\nServes as the script's main entry point. This function orchestrates the\ngeneration of a case-specific input file by parsing command-line arguments\nfor a client, tower, and associated data source files. It creates a\nstandardized output directory derived from the client and tower names, then\ndelegates the core data payload construction to the `build_case_input`\nfunction. The resulting data is serialized as a UTF-8 encoded, indented\nJSON file named `case_input.json` within the output directory.\n\nThe primary side effect of this function is the creation of the aforementioned\nfile on the local filesystem.\n\nReturns:\n    None\n\nRaises:\n    SystemExit: If required command-line arguments are missing or invalid, as\n        handled by the `argparse` module.\n    FileNotFoundError: If the files specified by `--context-file` or\n        `--responses-file` do not exist. This exception is expected to\n        propagate from downstream functions that consume these file paths."}."""
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

    logger.info(f"case_input generado en: {output_path}")
    logger.info(f"answers: {len(case_input['answers'])}")


if __name__ == "__main__":
    main()
