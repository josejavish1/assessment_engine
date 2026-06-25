"""Defines the core logic and primary utilities for the Assessment Engine pipeline."""

import argparse
import json
import logging
import re
from pathlib import Path
from zipfile import ZipFile

from assessment_engine.scripts.lib.runtime_paths import ROOT

logger = logging.getLogger(__name__)


def load_json(path: Path) -> dict:
    """Load and parse a UTF-8 encoded JSON file from a specified path."""
    return json.loads(path.read_text(encoding="utf-8"))


def read_docx_text(path: Path) -> str:
    """Extract the raw text content from a Microsoft Word (.docx) file.

    This function operates by treating the .docx file as a standard ZIP archive,
    extracting the `word/document.xml` member, and decoding its content as UTF-8,
    ignoring any decoding errors. All XML tags are subsequently stripped and
    consecutive whitespace characters are collapsed into a single space.

    Args:
        path: The `pathlib.Path` object pointing to the input .docx file.

    Returns:
        A string containing the extracted and normalized text from the document.

    Raises:
        FileNotFoundError: If the file at the specified path does not exist.
        zipfile.BadZipFile: If the file is not a valid ZIP archive.
        KeyError: If `word/document.xml` is not found within the archive,
            indicating an invalid or unsupported .docx format.
    """
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"\s+", " ", text).strip()


def read_rtf_text(path: Path) -> str:
    r"""Performs a basic, lossy conversion of a Rich Text Format (RTF) file to plain text.

    This function implements a non-comprehensive parser to extract text content
    from an RTF file. It operates by sequentially applying regular expression
    substitutions to remove common RTF control words and artifacts. The process
    includes:
    1.  Replacing paragraph (`\par`) and line (`\line`) control words with
        newline characters.
    2.  Stripping hexadecimal character codes (e.g., `\\'e9`).
    3.  Removing other common control words (e.g., `\b`, `\fonttbl`).
    4.  Replacing RTF grouping braces (`{`, `}`) with spaces.
    5.  Collapsing all resulting consecutive whitespace characters into single
        spaces and trimming the result.

    This utility is not a conformant RTF parser and may produce incorrect
    output for complex or non-standard RTF documents. It is intended for
    best-effort text extraction from simple files.

    Args:
        path (pathlib.Path): The path to the RTF file to be processed.

    Returns:
        str: The extracted plain text content, with whitespace normalized.

    Raises:
        FileNotFoundError: If the file at the specified path does not exist.
        IsADirectoryError: If the specified path points to a directory.
        PermissionError: If the file cannot be read due to filesystem permissions.
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"\\par[d]?|\\line", "\n", raw)
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", raw)
    raw = raw.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", raw).strip()


def read_text(path: Path) -> str:
    """Extracts text from a file, dispatching based on file extension.

    Delegates to specialized readers for `.docx` and `.rtf` file types based
    on a case-insensitive extension check. For all other file types, the
    function defaults to reading the file as UTF-8 encoded text, ignoring any
    decoding errors.

    Args:
        path (Path): The pathlib.Path object for the file to be read.

    Returns:
        str: The extracted text content of the file.

    Raises:
        FileNotFoundError: If the file at the specified path does not exist.
    """
    if path.suffix.lower() == ".docx":
        return read_docx_text(path)
    if path.suffix.lower() == ".rtf":
        return read_rtf_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def split_sentences(text: str) -> list[str]:
    r"""{'docstring': 'Segment a string into sentences based on terminal punctuation.\n\n    The function identifies sentence boundaries by periods, exclamation marks, or\n    question marks that are immediately followed by whitespace. The terminal\n    punctuation is retained as part of the sentence.\n\n    Each identified sentence is subsequently normalized by collapsing all internal\n    whitespace sequences into a single space and removing any leading or\n    trailing whitespace.\n\n    Args:\n        text (str): The input string to be segmented.\n\n    Returns:\n        list[str]: A list of normalized sentences. If the input text lacks\n            terminal punctuation, a list containing the single normalized\n            input string is returned. Returns an empty list if the input\n            is empty or contains only whitespace.'}."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [re.sub(r"\s+", " ", part).strip() for part in parts if part.strip()]


def tokenize(text: str) -> set[str]:
    """Extract a unique set of lowercase tokens from a string.

    The input string is converted to lowercase before tokenization. The function
    finds all non-overlapping substrings that consist of one or more allowed
    characters. The allowed character set includes lowercase ASCII letters (a-z),
    digits (0-9), specific Spanish letters (á, é, í, ó, ú, ü, ñ), and the
    symbols &, /, +, and -.

    Args:
        text: The input string to tokenize.

    Returns:
        A set of unique, lowercase tokens extracted from the text.
    """
    return set(re.findall(r"[a-z0-9áéíóúüñ&/+-]+", text.lower()))


def pillar_keywords(pillar: dict) -> set[str]:
    """Extracts a filtered set of keywords from a pillar dictionary.

    Tokenizes the value of the 'pillar_name' key and the 'kpi_name' key from
    each dictionary in the optional 'kpis' list. The resulting tokens are
    aggregated into a single set. This set is then filtered to retain only
    tokens with a length greater than two characters.

    Args:
        pillar: A dictionary representing a pillar object. It must contain a
            'pillar_name' key with a string value. It may optionally contain
            a 'kpis' key with a list of dictionaries, where each dictionary
            must possess a 'kpi_name' key with a string value.

    Returns:
        A set of unique string keywords, each longer than two characters,
        derived from the pillar and associated KPI names.

    Raises:
        KeyError: If 'pillar_name' is missing from the `pillar` dictionary,
            or if 'kpi_name' is missing from any dictionary within the 'kpis'
            list.
    """
    keywords = tokenize(pillar["pillar_name"])
    for kpi in pillar.get("kpis", []):
        keywords.update(tokenize(kpi["kpi_name"]))
    return {word for word in keywords if len(word) > 2}


def support_tags_from_score(score: float) -> list[str]:
    """Map a numerical score to a corresponding list of support tags."""
    if score >= 4:
        return ["asis", "executive_summary"]
    if score >= 3:
        return ["asis", "risk", "executive_summary"]
    return ["gap", "risk", "tobe", "todo", "executive_summary"]


def build_evidence_entries(
    case_input: dict, context_path: Path, responses_path: Path, tower_definition: dict
) -> list[dict]:
    """Generates a list of evidence entries from customer context and questionnaire data.

    This function synthesizes two primary sources of information—an unstructured
    customer context document and structured questionnaire responses—into a unified
    list of evidence entries against a given tower definition.

    For the context document, the function performs sentence-level analysis,
    matching sentences against keywords defined for each pillar. A maximum of
    three matching sentences per pillar are converted into 'context_summary'
    evidence entries. If no matches are found, a default placeholder entry is
    created.

    For the questionnaire data, each answer corresponding to a Key Performance
    Indicator (KPI) is processed into a 'questionnaire_response' evidence entry.
    The numerical score from the answer is used to generate a set of descriptive
    support tags.

    Each generated evidence entry is assigned a unique, sequential ID and contains
    metadata about its source, associated pillars and KPIs, and validation state.

    Args:
        case_input: A dictionary containing case data. Must include 'tower_id'
            (str) and 'answers' (list of dicts). Each answer dict must have
            'kpi_id', 'value', and 'question_id'. Optionally includes
            'validation_state'.
        context_path: The path to the text file containing the unstructured
            customer context.
        responses_path: The path to the questionnaire file, used as the source name
            for questionnaire-derived evidence.
        tower_definition: A dictionary defining the tower structure. It must
            contain a 'pillars' key, which is a list of pillar dictionaries.
            Each pillar dictionary must contain 'pillar_id', 'pillar_name', and a
            list of 'kpis'.

    Returns:
        A list of evidence entries. Each entry is a dictionary with the keys:
        'evidence_id', 'source_type', 'source_name', 'excerpt', 'pillar_ids',
        'kpi_ids', 'supports', and 'validation_state'.

    Raises:
        FileNotFoundError: If the file at `context_path` does not exist.
        KeyError: If required keys (e.g., 'tower_id', 'answers', 'pillars') are
            missing from the input dictionaries.
        ValueError: If an answer's 'value' cannot be converted to a float.
    """
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
    r"""{'docstring': "Generates and writes an evidence ledger file from command-line inputs.\n\nThis function serves as the main entry point for the script. It parses\ncommand-line arguments for the paths to case input, context, and model\nresponses files. It loads these files, dynamically locates and loads a\ncorresponding tower definition based on the 'tower_id' in the case data,\nand aggregates all information to build the ledger.\n\nThe resulting ledger is written to 'evidence_ledger.json' in the same\ndirectory as the case input file.\n\nCommand-line Arguments:\n  --case-input: The required path to the JSON file containing case data.\n  --context-file: The required path to the JSON file containing context.\n  --responses-file: The required path to the JSON file containing model responses.\n\nRaises:\n  FileNotFoundError: If an input file or the derived tower definition\n      file does not exist.\n  json.JSONDecodeError: If an input JSON file contains invalid JSON.\n  KeyError: If the case input data is missing required keys such as\n      'case_id', 'tower_id', or 'tower_name'."}."""
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

    logger.info(f"evidence_ledger generado en: {output_path}")
    logger.info(f"evidences: {len(ledger['evidences'])}")


if __name__ == "__main__":
    main()
