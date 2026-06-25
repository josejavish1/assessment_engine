"""Provides routines and data structures for assembling case inputs for the Assessment Engine pipeline."""

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from assessment_engine.scripts.lib.client_intelligence import (
    build_client_context_packet,
    get_target_maturity,
    load_client_intelligence,
)
from assessment_engine.scripts.lib.runtime_paths import (
    ROOT,
    resolve_case_dir,
    resolve_client_intelligence_path,
)
from assessment_engine.scripts.lib.text_utils import normalize_tower_name, slugify

logger = logging.getLogger(__name__)

RESPONSE_RE = re.compile(r"(T\d+\.P\d+\.K\d+\.PR\d+)\s*:\s*([1-5](?:[.,]\d+)?)")


def read_docx_text(path: Path) -> str:
    """Extract plain text content from a Microsoft Word (.docx) document.

    Parses the raw `word/document.xml` component of a .docx file (a standard
    ZIP archive) to extract its textual content. The function operates by
    stripping all XML tags and normalizing consecutive whitespace characters
    into a single space. This method provides a fast but rudimentary
    extraction that does not preserve document structure, formatting, or
    non-textual elements.

    Args:
        path: The file system path to the .docx document.

    Returns:
        The extracted plain text, stripped of all XML markup and with
        normalized whitespace.

    Raises:
        FileNotFoundError: If the file at `path` does not exist.
        zipfile.BadZipFile: If the file is not a valid ZIP archive or is
            corrupted.
        KeyError: If `word/document.xml` is not found within the archive,
            indicating an invalid DOCX format.
    """
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"\s+", " ", text).strip()


def read_rtf_text(path: Path) -> str:
    r"""Extracts and cleans plain text content from a Rich Text Format (RTF) file.

    This function provides a best-effort, non-compliant extraction of text from
    an RTF document. It operates by reading the file's raw content and applying a
    series of regular expressions to strip common RTF control words (e.g., `\par`,
    `\fonttbl`), hexadecimal character encodings (e.g., `\'e9`), and grouping
    braces. The function is not a full RTF parser and may produce imperfect
    output for complex or non-standard RTF structures. All resulting contiguous
    whitespace is collapsed into a single space.

    Args:
        path (pathlib.Path): The path to the source RTF document.

    Returns:
        str: A string containing the extracted and cleaned plain text.

    Raises:
        FileNotFoundError: If the file at the specified path does not exist.
        IsADirectoryError: If the specified path points to a directory.
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"\\par[d]?|\\line", "\n", raw)
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)
    raw = raw.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", raw).strip()


def read_text(path: Path) -> str:
    """Read text content from a file, dispatching based on file extension.

    Inspects the file suffix to determine the appropriate method for reading its
    content. This function delegates to specialized handlers for `.docx` and `.rtf`
    files. All other file types are treated as plain text and read using UTF-8
    encoding, with any decoding errors ignored.

    Args:
        path (pathlib.Path): The path to the file to be read.

    Returns:
        str: The extracted text content of the file.

    Raises:
        FileNotFoundError: If the file does not exist at the specified path.
        PermissionError: If read permissions are denied for the file.
        IsADirectoryError: If the path points to a directory instead of a file.
    """
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx_text(path)
    if suffix == ".rtf":
        return read_rtf_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path) -> dict:
    """Load a dictionary from a UTF-8 encoded JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_matrix_file_name(tower_id: str) -> str | None:
    """Find the alphabetically first file name within a specific tower directory.

    This function locates the directory for a given tower ID at the path
    `source_docs/towers/<tower_id>`. It then identifies all files within this
    directory, sorts their names alphabetically, and returns the first one.

    Args:
        tower_id (str): The unique identifier for the tower, corresponding to its
            subdirectory name.

    Returns:
        str | None: The file name of the first file found, or None if the
            tower directory does not exist or contains no files.
    """
    tower_dir = ROOT / "source_docs" / "towers" / tower_id
    if not tower_dir.exists():
        return None
    candidates = sorted(path.name for path in tower_dir.iterdir() if path.is_file())
    return candidates[0] if candidates else None


def build_question_text(kpi_name: str) -> str:
    """Construct the standard Spanish-language text for a maturity evaluation question."""
    return (
        f"Evaluación de madurez para '{kpi_name}'. "
        "La respuesta debe valorarse en escala 1-5."
    )


def parse_responses(responses_text: str, tower_id: str) -> dict[str, float]:
    """Parses raw response text to extract numeric scores for a specific tower.

    The function finds all question-value pairs in the text using a regular
    expression. It filters for questions where the ID is prefixed with the
    specified `tower_id` followed by a dot (i.e., `f"{tower_id}."`).
    The corresponding string values are then converted to floating-point
    numbers, normalizing comma-based decimals to dot-based decimals during
    the conversion.

    Args:
        responses_text: The raw string containing all survey responses, with
            each response composed of a question identifier and a value.
        tower_id: The identifier for the tower used to filter responses. Only
            question IDs matching the prefix `f"{tower_id}."` are processed.

    Returns:
        A dictionary mapping the fully qualified question IDs to their
        corresponding numeric scores as floats.

    Raises:
        ValueError: If a response value for a filtered question cannot be
            converted to a float after decimal normalization.
    """
    scores: dict[str, float] = {}
    for question_id, value_text in RESPONSE_RE.findall(responses_text):
        if not question_id.startswith(f"{tower_id}."):
            continue
        scores[question_id] = float(value_text.replace(",", "."))
    return scores


def build_question_lookup(tower_definition: dict) -> dict[str, str]:
    """Constructs a flat lookup map of question IDs to their corresponding text from a tower definition.

    This function traverses a hierarchical tower definition dictionary to extract all
    questions. It processes questions from the top-level 'questions' key first,
    then processes questions nested within 'pillars' and their subsequent 'kpis'.
    Top-level questions have precedence; if a question ID from a nested
    structure is already present in the lookup map, it is ignored.

    Args:
        tower_definition: A dictionary representing the tower's structure. The
            function expects optional 'questions' and 'pillars' keys. The
            expected nested structure is pillars -> kpis -> questions. Each
            question dictionary should contain 'question_id' and 'question_text'.

    Returns:
        A dictionary mapping unique question IDs (str) to their question text (str).
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
    """Constructs a case input dictionary from configuration and user-provided files.

    This function orchestrates the assembly of a complete case input package. It
    loads a tower's structural definition from a predefined configuration path,
    parses user-provided assessment responses and context files, integrates
    optional client intelligence data, and compiles all information into a
    structured dictionary. The resulting dictionary serves as the primary input
    for subsequent processing and report generation stages.

    Args:
        args: An object containing command-line arguments, typically an
            `argparse.Namespace`. It must expose the following attributes:
            - tower (str): The identifier for the technology tower.
            - context_file (str): The path to the context document.
            - responses_file (str): The path to the assessment responses file.
            - client (str): The name of the client for the assessment.

    Returns:
        A dictionary containing the structured case input data. The schema includes
        top-level keys for case metadata (`case_id`, `client`, `date`),
        tower configuration (`tower_id`, `tower_name`, `working_rules`),
        parsed data (`answers`, `context_summary`), source documents, and build
        metadata (`_build_metadata`).

    Raises:
        FileNotFoundError: If the tower definition file, context file, or responses
            file cannot be found at their respective derived or provided paths.
        KeyError: If the loaded tower definition JSON is malformed and missing
            required keys such as 'tower_name', 'purpose', or nested keys
            within 'working_rules'.
    """
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
    """Parses command-line arguments to generate and persist a case input JSON file.

    This script functions as the primary entry point for creating a case-specific
    input file. It processes command-line arguments to identify the client, tower,
    and the paths to context and response data files. A unique directory is created
    based on a slugified client name and tower, into which the generated
    'case_input.json' file is written.

    The script consumes the following command-line arguments:
      --client: The client identifier string.
      --tower: The specific tower or vertical associated with the case.
      --context-file: The path to a JSON file containing context data.
      --responses-file: The path to a JSON file containing response data.

    Raises:
        FileNotFoundError: If the path provided via `--context-file` or
            `--responses-file` does not exist.
        OSError: If the case directory cannot be created due to file system
            permission errors or other system-level issues.
    """
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
