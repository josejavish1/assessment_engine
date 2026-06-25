"""Module bootstrap_tower_from_matrix.py.

Contains the primary logic and utilities for the Assessment Engine pipeline.
"""

import argparse
import json
import logging
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from assessment_engine.scripts.lib.runtime_paths import ROOT

logger = logging.getLogger(__name__)

DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
GENERIC_BLOCK_KEYS = [
    "schema_name",
    "schema_version",
    "reusable",
    "maturity_scale",
    "score_bands",
    "validation_states",
    "working_rules",
]


def load_json(path: Path) -> dict:
    """Load a dictionary from a UTF-8 encoded JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def extract_docx_paragraphs(path: Path) -> list[str]:
    """Extract all non-empty text paragraphs from a .docx file.

    This function operates by treating the .docx file as a ZIP archive and
    directly parsing its `word/document.xml` member. It iterates through all
    paragraph (`w:p`) elements, concatenates the text from their constituent
    text run (`w:t`) elements, and normalizes intervening whitespace.

    Args:
        path: A `pathlib.Path` object pointing to the input .docx document.

    Returns:
        A list of strings, where each string is the normalized, non-empty text
        content of a paragraph. The paragraphs are returned in the order they
        appear in the document.

    Raises:
        FileNotFoundError: If the file at the specified path does not exist.
        zipfile.BadZipFile: If the provided file is not a valid ZIP archive
            (e.g., it is corrupted or not a .docx file).
        KeyError: If `word/document.xml` is missing from the archive, indicating
            an invalid or non-standard .docx structure.
        xml.etree.ElementTree.ParseError: If the `word/document.xml` content is
            malformed.
    """
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)

    paragraphs = []
    for paragraph in root.findall(".//w:p", DOCX_NS):
        text = "".join(
            (node.text or "") for node in paragraph.findall(".//w:t", DOCX_NS)
        )
        text = normalize_spaces(text)
        if text:
            paragraphs.append(text)
    return paragraphs


def normalize_spaces(value: str) -> str:
    """Condense all whitespace to single spaces and remove leading/trailing whitespace."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text(value: str) -> str:
    """Normalize a string by collapsing whitespace and applying Unicode NFC normalization."""
    return unicodedata.normalize("NFC", normalize_spaces(value))


def normalize_dash(value: str) -> str:
    """{'docstring': 'Replace various dash-like characters with a standard ASCII hyphen-minus.'}."""
    return str(value or "").replace("–", "-").replace("—", "-").replace("−", "-")


def comparable_text(value: str) -> str:
    r"""{'docstring': 'Normalize a string for case-insensitive, accent-insensitive comparison.\n\n    This function creates a canonical representation of a string by performing\n    the following sequential transformations:\n    1.  Normalizes dash characters within the string.\n    2.  Applies NFKD Unicode normalization to decompose composite characters into\n        base characters and combining marks.\n    3.  Encodes the normalized string to ASCII, discarding any characters that\n        cannot be represented, which effectively strips accents and symbols.\n    4.  Converts the resulting ASCII string to lowercase.\n    5.  Removes all characters that are not lowercase ASCII letters or digits.\n\n    This process yields a simplified token suitable for use as a key in loose,\n    case-insensitive, and accent-insensitive string matching operations.\n\n    Args:\n        value: The string to normalize.\n\n    Returns:\n        The normalized string, containing only lowercase ASCII letters and digits.'}."""
    normalized = unicodedata.normalize("NFKD", normalize_dash(value))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_value.lower())


def extract_tower_name(paragraphs: list[str], tower_id: str) -> str:
    """Extracts a tower name from a list of text paragraphs using a tower ID.

    Scans up to the first 80 paragraphs for a line that matches the
    case-insensitive regular expression pattern: `Torre <ID>[: -] <Name>`.
    The tower ID used in the pattern omits the first character of the `tower_id`
    argument.

    If a match is found, the extracted name undergoes a cleaning process:
    1. Whitespace is normalized to single spaces.
    2. Trailing numerical digits are removed.
    3. Leading or trailing hyphens, colons, and spaces are stripped.
    4. The result is passed through a final text normalization function.

    Args:
        paragraphs: A list of strings representing text paragraphs to search.
        tower_id: The unique identifier for the tower (e.g., "T123").

    Returns:
        The cleaned and normalized tower name string.

    Raises:
        RuntimeError: If a matching tower name cannot be located within the
            first 80 paragraphs.
    """
    pattern = re.compile(
        rf"\bTorre\s+{re.escape(tower_id[1:])}\s*[-:]\s*(.+)", flags=re.IGNORECASE
    )
    for text in paragraphs[:80]:
        match = pattern.search(text)
        if match:
            candidate = normalize_spaces(match.group(1))
            candidate = re.sub(r"\d+$", "", candidate).strip(" -:")
            if candidate:
                return normalize_text(candidate)
    raise RuntimeError(f"No se pudo extraer tower_name para {tower_id}")


def extract_purpose(paragraphs: list[str]) -> str:
    r"""{'docstring': 'Extracts the purpose statement of a tower from a list of document paragraphs.\n\n    This function identifies the section header "Definición de la torre" and\n    then scans the subsequent 11 paragraphs to find a sentence that describes\n    the tower\'s scope, identified by the pattern "La torre ... cubre ...".\n\n    Args:\n        paragraphs: A list of strings, where each string is a paragraph\n            from the source document.\n\n    Returns:\n        The normalized text of the paragraph containing the tower\'s purpose.\n\n    Raises:\n        RuntimeError: If the section "Definición de la torre" is not found, or\n            if the purpose statement cannot be located within the 11 paragraphs\n            following the section header.'}."""
    try:
        start = paragraphs.index("Definición de la torre")
    except ValueError as exc:
        raise RuntimeError(
            "No se encontró la sección 'Definición de la torre'"
        ) from exc

    for text in paragraphs[start + 1 : start + 12]:
        normalized = text.lower()
        if normalized.startswith("la torre ") and " cubre " in normalized:
            return normalize_text(text)
    raise RuntimeError("No se pudo extraer purpose desde la sección de definición")


def clean_repeated_phrase(value: str) -> str:
    """Clean specific, hardcoded redundant phrases from a string."""
    text = normalize_text(value)
    patterns = [
        (
            "Seguridad Física y Control de Accesos y Control de Accesos",
            "Seguridad Física y Control de Accesos",
        ),
        (
            "Seguridad Fisica y Control de Accesos y Control de Accesos",
            "Seguridad Fisica y Control de Accesos",
        ),
        (
            "Seguridad Física y Control de Accesos y accesos",
            "Seguridad Física y Control de Accesos",
        ),
        (
            "Seguridad Fisica y Control de Accesos y accesos",
            "Seguridad Fisica y Control de Accesos",
        ),
    ]
    for source, target in patterns:
        text = text.replace(source, target)
    return normalize_text(text)


def build_pillar_name_map(
    paragraphs: list[str], tower_id: str, warnings: list[str]
) -> dict[str, str]:
    """Extracts and maps pillar identifiers to their corresponding names from text paragraphs.

    Parses a list of text paragraphs using a case-insensitive regular expression
    to find lines that match the format:
    `Pilar <number> - <tower_id>.P<number> - <Pillar Name>`.

    Extracted names are cleaned by removing repeated phrases, trailing digits,
    and stripping leading or trailing spaces, hyphens, or colons. If a pillar
    identifier is encountered multiple times with different names, the first one
    is retained and a warning message is appended to the `warnings` list.

    Args:
        paragraphs: A list of strings representing paragraphs to be searched.
        tower_id: The tower identifier used to construct the regex pattern for
            matching pillar IDs (e.g., 'T123').
        warnings: A list to which warning messages are appended. This argument is
            modified in place.

    Returns:
        A dictionary mapping each uppercase pillar ID (e.g., 'T123.P1') to its
        cleaned name.

    Raises:
        RuntimeError: If no pillar definitions are found in the paragraphs.
    """
    pillar_name_map: dict[str, str] = {}
    pattern = re.compile(
        rf"\bPilar\s+(\d+)\s*-\s*({re.escape(tower_id)}\.P\d+)\s*-\s*(.+)$",
        flags=re.IGNORECASE,
    )

    for text in paragraphs:
        match = pattern.search(normalize_dash(text))
        if not match:
            continue
        pillar_id = match.group(2).upper()
        pillar_name = clean_repeated_phrase(match.group(3))
        pillar_name = re.sub(r"\d+$", "", pillar_name).strip(" -:")
        if pillar_id in pillar_name_map and pillar_name_map[pillar_id] != pillar_name:
            warnings.append(
                f"Nombre de pilar conflictivo para {pillar_id}: "
                f"'{pillar_name_map[pillar_id]}' vs '{pillar_name}'. Se conserva el primero."
            )
            continue
        pillar_name_map[pillar_id] = pillar_name

    if not pillar_name_map:
        raise RuntimeError(
            "No se pudieron extraer pilares desde los encabezados del documento"
        )
    return pillar_name_map


def extract_weights(
    paragraphs: list[str],
    tower_id: str,
    pillar_name_map: dict[str, str],
    warnings: list[str],
) -> dict[str, int]:
    """Extracts pillar percentage weights from document paragraphs using a tiered strategy.

    This function implements a hierarchical, multi-stage process to extract
    integer percentage weights for a set of predefined pillars from a list of text
    paragraphs. The extraction methods are applied in a specific order of
    precedence to robustly handle variations and inconsistencies in source
    document formatting.

    The extraction strategy is as follows:
    1.  **Numbered Pillar Match:** The entire document is scanned for explicit,
        numbered pillar declarations (e.g., "Pilar 1 ... (25%)"). These matches
        are considered the most authoritative and are processed first.
    2.  **Named Pillar Match:** If any pillars remain without weights, the entire
        document is scanned for named weight declarations (e.g.,
        "Pillar Name - 25%").
    3.  **Section-Based Fallback:** For any remaining pillars, the function
        isolates the "Factores de Importancia" section and searches within it for
        lines containing a pillar's name, extracting the first percentage value
        found on that line.

    The input `warnings` list is mutated by appending messages for any pillars
    whose weights could not be determined after all stages.

    Args:
        paragraphs: A list of strings, where each string is a paragraph or line
            from the source document.
        tower_id: The identifier for the parent tower, used as a prefix to
            construct full pillar IDs (e.g., 'T1' for 'T1.P1').
        pillar_name_map: A dictionary mapping canonical pillar IDs to their
            corresponding human-readable names.
        warnings: A list that is mutated in-place by appending string warnings for
            any pillars for which a weight could not be extracted.

    Returns:
        A dictionary mapping pillar IDs to their extracted integer percentage
        weights. Pillars for which no weight could be found are omitted from this
        dictionary.

    Raises:
        RuntimeError: If the "Factores de Importancia" section header cannot be
            located in the input `paragraphs`, as it is required for the
            fallback extraction logic.
    """
    weights: dict[str, int] = {}
    section_start = None
    section_end = None

    for index, text in enumerate(paragraphs):
        if "Factores de Importancia" in text:
            section_start = index
            continue
        if section_start is not None and "Matriz de madurez" in text:
            section_end = index
            break

    if section_start is None:
        raise RuntimeError("No se encontró la sección 'Factores de Importancia'")

    scan = paragraphs[section_start : section_end or len(paragraphs)]

    # Certain source matrices declare the final pillar weight as an explicit, distinct line item.
    # Matching pillar-specific weight declarations by their cardinal number (e.g., "Pilar 2") provides greater robustness compared to fuzzy string matching against pillar names.
    # This numerical matching strategy mitigates naming convention inconsistencies observed across different sections of the source matrix.
    explicit_pattern = re.compile(
        r"Pilar\s+(\d+).*\((\d+)%\)",
        flags=re.IGNORECASE,
    )
    for text in paragraphs:
        normalized = normalize_dash(text)
        match = explicit_pattern.search(normalized)
        if not match:
            continue
        pillar_id = f"{tower_id}.P{int(match.group(1))}"
        if pillar_id in pillar_name_map:
            weights[pillar_id] = int(match.group(2))

    # Certain source matrices embed the final, normalized pillar weights within unstructured text lines.
    # When present, these explicit weight declarations are considered authoritative and will override any calculated or inferred weights.
    # These values represent the final, rounded weight distribution, which is engineered to sum precisely to 100.
    named_weight_pattern = re.compile(r"(.+?)\s[-–—]\s(\d+)%$", flags=re.IGNORECASE)
    for text in paragraphs:
        normalized = normalize_dash(text)
        match = named_weight_pattern.search(normalized)
        if not match:
            continue
        line_name = comparable_text(match.group(1))
        for pillar_id, pillar_name in pillar_name_map.items():
            if comparable_text(pillar_name) == line_name:
                weights[pillar_id] = int(match.group(2))
                break

    for pillar_id, pillar_name in pillar_name_map.items():
        if pillar_id in weights:
            continue
        weight = None
        pillar_key = comparable_text(pillar_name)
        for text in scan:
            normalized = normalize_dash(text)
            text_key = comparable_text(normalized)
            if pillar_key not in text_key:
                continue
            match = re.search(r"(\d+)\s*%", normalized)
            if match:
                weight = int(match.group(1))
                break
            if weight is not None:
                break
        if weight is None:
            warnings.append(f"No se encontró peso para {pillar_id} ({pillar_name})")
            continue
        weights[pillar_id] = weight

    return weights


def extract_kpis(
    paragraphs: list[str], tower_id: str, warnings: list[str]
) -> dict[str, list[dict]]:
    r"""{'docstring': "Extracts and groups Key Performance Indicators (KPIs) from text paragraphs.\n\n    This function parses a list of strings to identify and structure KPI\n    definitions. It supports two primary formats for KPI declarations:\n    1.  A single-line format where the ID and name appear together (e.g.,\n        'TOWER.P1.K1 - KPI Name').\n    2.  A multi-line format where the ID is on one line and the name follows on\n        a subsequent line.\n\n    KPIs are grouped by their pillar ID (e.g., 'TOWER.P1'). The function\n    identifies and ignores duplicate KPI IDs, appending a warning for each\n    occurrence after the first. Other parsing issues are also reported via the\n    `warnings` list.\n\n    Args:\n        paragraphs: A list of text paragraphs to be parsed.\n        tower_id: The root identifier for the tower, used to construct regex\n            patterns for matching KPI IDs (e.g., 'TWR1').\n        warnings: A mutable list to which parsing warning messages are appended.\n            This list is modified in place by the function.\n\n    Returns:\n        A dictionary mapping pillar IDs to a list of extracted KPIs. Each KPI\n        is represented as a dictionary with 'kpi_id' and 'kpi_name' keys.\n\n    Raises:\n        RuntimeError: If no KPIs can be extracted from the provided paragraphs."}."""
    kpis_by_pillar: dict[str, list[dict]] = {}
    seen_kpi_ids: set[str] = set()
    pattern = re.compile(
        rf"\b({re.escape(tower_id)}\.P(\d+)\.K(\d+))\s*-\s*(.+)$", flags=re.IGNORECASE
    )
    id_only_pattern = re.compile(
        rf"^({re.escape(tower_id)}\.P(\d+)\.K(\d+))$", flags=re.IGNORECASE
    )

    for index, text in enumerate(paragraphs):
        normalized = normalize_dash(text)
        match = pattern.search(normalized)
        if match:
            kpi_id = match.group(1).upper()
            pillar_number = match.group(2)
            pillar_id = f"{tower_id}.P{pillar_number}"
            kpi_name = clean_repeated_phrase(match.group(4))
        else:
            id_only_match = id_only_pattern.match(normalized)
            if not id_only_match:
                continue
            kpi_id = id_only_match.group(1).upper()
            pillar_number = id_only_match.group(2)
            pillar_id = f"{tower_id}.P{pillar_number}"
            kpi_name = ""
            for candidate in paragraphs[index + 1 : index + 4]:
                candidate = clean_repeated_phrase(normalize_text(candidate))
                if not candidate:
                    continue
                if re.match(
                    rf"^{re.escape(tower_id)}\.P\d+(\.K\d+)?$",
                    normalize_dash(candidate),
                    flags=re.IGNORECASE,
                ):
                    break
                if re.match(r"^\d+%$", candidate):
                    break
                kpi_name = candidate
                break
            if not kpi_name:
                warnings.append(f"No se pudo extraer kpi_name para {kpi_id}")
                continue

        if kpi_id in seen_kpi_ids:
            warnings.append(
                f"KPI duplicado en documento: {kpi_id}. Se ignora la aparición repetida."
            )
            continue
        seen_kpi_ids.add(kpi_id)
        kpis_by_pillar.setdefault(pillar_id, []).append(
            {"kpi_id": kpi_id, "kpi_name": kpi_name}
        )

    if not kpis_by_pillar:
        raise RuntimeError("No se pudieron extraer KPIs desde la sección de madurez")
    return kpis_by_pillar


def collect_section_items(
    paragraphs: list[str], section_title: str, next_titles: list[str]
) -> list[str]:
    """Extract and normalize textual items from a delimited document section.

    Identifies a section within a list of paragraphs demarcated by a start title.
    Collection proceeds until a terminating title from a provided list is
    encountered or the end of the paragraph list is reached. Paragraphs that
    consist solely of whitespace are discarded, and the remaining items are
    normalized.

    Args:
        paragraphs: A list of strings, where each string represents a paragraph
            or line from the source document.
        section_title: The exact string of the title that marks the beginning
            of the desired section. Extraction begins from the line immediately
            following this title.
        next_titles: A list of title strings that act as terminators for the
            section. The first occurrence of any of these titles will end the
            extraction.

    Returns:
        A list of normalized strings from the specified section. An empty
        list is returned if `section_title` is not found in `paragraphs`.
    """
    start = None
    end = len(paragraphs)
    for index, text in enumerate(paragraphs):
        if text == section_title:
            start = index + 1
            break
    if start is None:
        return []
    for index in range(start, len(paragraphs)):
        if paragraphs[index] in next_titles:
            end = index
            break
    return [
        normalize_text(item) for item in paragraphs[start:end] if normalize_spaces(item)
    ]


def extract_scope_summary(paragraphs: list[str]) -> list[str]:
    """Extracts and cleans scope summary labels from a list of text paragraphs.

    Identifies a text section delineated by the title "Alcance típico:" and the
    subsequent title "Por qué esta torre es fundamental en el modelo global de
    madurez". Within this section, it processes each line item. For items
    containing a colon, the substring preceding the first colon is extracted as
    a label. These labels are then subjected to a cleaning routine which
    includes standardization and specific term capitalization.

    Args:
        paragraphs: A list of strings, where each string is a paragraph of text.

    Returns:
        A list of cleaned strings representing the scope summary labels.
    """
    items = collect_section_items(
        paragraphs,
        section_title="Alcance típico:",
        next_titles=[
            "Por qué esta torre es fundamental en el modelo global de madurez"
        ],
    )
    out = []
    for item in items:
        if ":" not in item:
            continue
        label = item.split(":", 1)[0]
        out.append(clean_repeated_phrase(label).replace("facilities", "Facilities"))
    return out


def extract_related_towers(paragraphs: list[str], tower_id: str) -> list[str]:
    """Extracts and formats tower identifiers from text paragraphs.

    Parses a list of strings for case-insensitive mentions of tower identifiers
    following the patterns "Torre <number>" or "Torres <numbers>". The function
    handles single numbers, comma-separated lists, and the Spanish conjunction 'y'.
    Each identified number is prefixed with 'T' to form a standardized identifier.
    The source tower's own ID is excluded from the final list to prevent
    self-referencing.

    Args:
        paragraphs: A list of text strings to be scanned for tower mentions.
        tower_id: The identifier of the source tower (e.g., "T1") to exclude
            from the results.

    Returns:
        A list of unique, related tower identifiers found in the text, sorted
        in ascending numerical order (e.g., ["T2", "T11"]).
    """
    related: set[str] = set()
    for text in paragraphs:
        for group in re.findall(r"\bTorres\s+([0-9,\s+y]+)", text, flags=re.IGNORECASE):
            for match in re.findall(r"\d+", group):
                candidate = f"T{match}"
                if candidate != tower_id:
                    related.add(candidate)
        for match in re.findall(r"\bTorre\s+(\d+)\b", text, flags=re.IGNORECASE):
            candidate = f"T{match}"
            if candidate != tower_id:
                related.add(candidate)
    return sorted(related, key=lambda item: int(item[1:]))


def extract_boundary_notes(paragraphs: list[str]) -> list[str]:
    """Extracts and normalizes exclusionary boundary notes from a list of paragraphs.

    This function identifies a specific sentinel phrase, "No incluye / se evalúa en otras
    torres:", within a list of text paragraphs. Upon locating the sentinel, it
    inspects the subsequent one to three paragraphs to parse individual exclusion
    notes. The parsing logic is designed to handle multiple notes condensed into a
    single paragraph, using ", la " as a delimiter. Each extracted note component
    is reconstructed into a grammatically complete sentence (e.g., prepending
    "La " to subsequent parts) and standardized. The extraction process
    terminates prematurely if a paragraph within the search window ends with a
    colon (":").

    Args:
        paragraphs (list[str]): A list of strings, where each string represents a
            paragraph of text.

    Returns:
        list[str]: A list of processed exclusion notes, each formatted as a
            complete sentence. Returns an empty list if the sentinel phrase is not
            found or if no valid notes follow it.
    """
    notes = []
    for index, text in enumerate(paragraphs):
        if text == "No incluye / se evalúa en otras torres:":
            for candidate in paragraphs[index + 1 : index + 4]:
                normalized = normalize_text(candidate)
                if normalized.endswith(":"):
                    break
                parts = [
                    part.strip(" .;")
                    for part in normalized.split(", la ")
                    if part.strip()
                ]
                if len(parts) == 1:
                    parts = [normalized]
                for offset, part in enumerate(parts):
                    rebuilt = part if offset == 0 else f"La {part}"
                    rebuilt = clean_repeated_phrase(rebuilt.strip(" .;")) + "."
                    notes.append(rebuilt)
            break
    return notes


def extract_questions(
    paragraphs: list[str], tower_id: str, warnings: list[str]
) -> list[dict]:
    """Parses a list of document paragraphs to extract structured question data.

    Iterates through a list of text paragraphs to identify question markers
    that follow a specific hierarchical format (e.g., 'TOWER_ID.P#.K#.PR#').
    For each identified marker, the function attempts to locate the corresponding
    question text within the subsequent three paragraphs. The text extraction
    process applies normalization and filtering rules to exclude irrelevant
    content, such as section headers or response prompts. Parent identifiers
    ('pillar_id', 'kpi_id') are derived from the full question ID.

    Extraction failures, such as missing question text or duplicate question IDs,
    are logged as string messages and appended to the provided `warnings` list.

    Args:
        paragraphs: A list of strings, where each string is a paragraph of text
            from the source document.
        tower_id: The root identifier string used to construct the regular
            expression for matching question markers.
        warnings: A list instance that is mutated in-place by appending string
            messages for any issues encountered during parsing.

    Returns:
        A list of dictionaries, each representing an extracted question. Each
        dictionary contains the following keys: 'question_id' (str),
        'pillar_id' (str), 'kpi_id' (str), and 'question_text' (str).
        Returns an empty list if no questions are found.
    """
    questions = []
    seen = set()
    pattern = re.compile(
        rf"^({re.escape(tower_id)}\.P(\d+)\.K(\d+)\.PR(\d+))$", flags=re.IGNORECASE
    )

    for index, text in enumerate(paragraphs):
        match = pattern.match(normalize_dash(text))
        if not match:
            continue
        question_id = match.group(1).upper()
        pillar_id = f"{tower_id}.P{match.group(2)}"
        kpi_id = f"{tower_id}.P{match.group(2)}.K{match.group(3)}"
        question_text = ""
        for candidate in paragraphs[index + 1 : index + 4]:
            candidate = normalize_text(candidate)
            if not candidate:
                continue
            if candidate.startswith("Respuesta "):
                continue
            if re.match(rf"^{re.escape(tower_id)}\.P\d+\.K\d+\.PR\d+$", candidate):
                break
            if candidate == clean_repeated_phrase(candidate) and candidate in {
                clean_repeated_phrase("Energía y Continuidad Eléctrica"),
                clean_repeated_phrase(
                    "Climatización, Refrigeración y Control Ambiental"
                ),
                clean_repeated_phrase("Seguridad Física y Control de Accesos"),
                clean_repeated_phrase(
                    "Protección Contra Incendios y Seguridad Ambiental"
                ),
                clean_repeated_phrase(
                    "Operación de Facilities, Monitorización y Mantenimiento"
                ),
            }:
                continue
            question_text = clean_repeated_phrase(candidate)
            break
        if not question_text:
            warnings.append(f"No se pudo extraer question_text para {question_id}")
            continue
        if question_id in seen:
            warnings.append(f"Pregunta duplicada en documento: {question_id}")
            continue
        seen.add(question_id)
        questions.append(
            {
                "question_id": question_id,
                "pillar_id": pillar_id,
                "kpi_id": kpi_id,
                "question_text": question_text,
            }
        )
    return questions


def attach_questions_to_pillars(pillars: list[dict], questions: list[dict]) -> None:
    r"""{'docstring': 'Attach sorted questions to KPIs within a nested pillar data structure.\n\n    This function modifies the `pillars` list in-place by associating questions\n    with their corresponding Key Performance Indicators (KPIs). It first indexes the\n    provided `questions` by their `kpi_id` for efficient lookup. It then\n    iterates through each pillar and its KPIs, attaching a new "questions" key\n    to each KPI dictionary. The value for this key is a list of question\n    objects, sorted numerically based on the integer found after the ".PR"\n    delimiter in the `question_id` string.\n\n    Args:\n        pillars: A list of pillar dictionaries to be modified. Each dictionary\n            is expected to contain a "kpis" key mapping to a list of KPI\n            dictionaries, each of which must have a "kpi_id" key.\n        questions: A list of question dictionaries. Each dictionary must contain\n            "kpi_id", "question_id", and "question_text" keys. The\n            `question_id` is expected to have a format like \'PREFIX.PR123\'.\n\n    Raises:\n        KeyError: If a dictionary within `questions` lacks a required key\n            ("kpi_id", "question_id", "question_text") or if a KPI\n            dictionary within `pillars` lacks the "kpi_id" key.\n        ValueError: If the portion of a `question_id` string following the\n            ".PR" delimiter cannot be converted to an integer.\n        IndexError: If a `question_id` string does not contain the ".PR"\n            delimiter, causing the sort-key extraction to fail.'}."""
    questions_by_kpi: dict[str, list[dict]] = {}
    for question in questions:
        questions_by_kpi.setdefault(question["kpi_id"], []).append(
            {
                "question_id": question["question_id"],
                "question_text": question["question_text"],
            }
        )

    for pillar in pillars:
        for kpi in pillar.get("kpis", []):
            kpi["questions"] = sorted(
                questions_by_kpi.get(kpi["kpi_id"], []),
                key=lambda item: int(item["question_id"].split(".PR")[1]),
            )


def build_tower_definition(
    base_definition: dict,
    tower_id: str,
    tower_name: str,
    purpose: str,
    scope_summary: list[str],
    related_towers: list[str],
    boundary_notes: list[str],
    pillars: list[dict],
    questions: list[dict],
) -> dict:
    """Construct a tower definition dictionary from its constituent parts.

    Initializes a new definition by copying generic key-value pairs from a
    base template, then populates it with specific attributes for the tower
    such as its ID, name, purpose, scope, and structural components like
    pillars and questions.

    Args:
        base_definition: The base template dictionary containing generic values.
        tower_id: The unique identifier for the tower.
        tower_name: The human-readable name of the tower.
        purpose: A string describing the objective of the tower.
        scope_summary: A list of strings summarizing what is in scope for the tower.
        related_towers: A list of identifiers for other related towers.
        boundary_notes: A list of strings clarifying what is out of scope.
        pillars: A list of dictionaries, where each dictionary defines a pillar
            of the tower.
        questions: A list of dictionaries, where each dictionary defines a question
            related to the tower's assessment.

    Returns:
        A dictionary representing the complete definition of the tower.

    Raises:
        KeyError: If `base_definition` is missing a key expected by the
            `GENERIC_BLOCK_KEYS` constant.
    """
    definition = {key: base_definition[key] for key in GENERIC_BLOCK_KEYS}
    definition["tower_id"] = tower_id
    definition["tower_name"] = tower_name
    definition["purpose"] = purpose
    definition["scope_summary"] = scope_summary
    definition["related_towers"] = related_towers
    definition["boundary_notes"] = boundary_notes
    definition["pillars"] = pillars
    definition["questions"] = questions
    return definition


def validate_tower_definition(definition: dict) -> list[str]:
    """Validate the structure and referential integrity of a tower definition.

    Executes a comprehensive set of validation checks on the provided tower
    definition dictionary. These checks include:
      - Uniqueness of `pillar_id`, `kpi_id`, and `question_id` values.
      - Correct naming convention for KPIs (i.e., `pillar_id.kpi_name`).
      - Referential integrity, ensuring questions link to existing pillars and KPIs.
      - Verification that the sum of all pillar `weight_pct` values equals 100.

    Args:
        definition: The dictionary representing the tower structure. It is expected
            to contain 'pillars' and 'questions' keys. The 'pillars' value should
            be a list of pillar dictionaries, each potentially containing a list
            of KPI dictionaries.

    Returns:
        A list of strings, where each string is a human-readable error message.
        An empty list signifies a valid definition.

    Raises:
        KeyError: If a required key (e.g., `pillar_id`, `kpi_id`) is missing
            from a dictionary element within the structure.
        ValueError: If a pillar's `weight_pct` value cannot be converted to an
            integer.
    """
    errors = []
    pillars = definition.get("pillars", [])
    pillar_ids = [pillar["pillar_id"] for pillar in pillars]
    if len(pillar_ids) != len(set(pillar_ids)):
        errors.append("Hay pillar_id duplicados.")

    total_weight = sum(int(pillar.get("weight_pct", 0)) for pillar in pillars)
    if total_weight != 100:
        errors.append(f"La suma de weight_pct es {total_weight}, no 100.")

    known_pillars = set(pillar_ids)
    kpi_ids: list[str] = []
    for pillar in pillars:
        for kpi in pillar.get("kpis", []):
            kpi_ids.append(kpi["kpi_id"])
            expected_prefix = f"{pillar['pillar_id']}."
            if not kpi["kpi_id"].startswith(expected_prefix):
                errors.append(
                    f"{kpi['kpi_id']} no pertenece al pilar {pillar['pillar_id']}."
                )
        if pillar["pillar_id"] not in known_pillars:
            errors.append(f"Pilar inexistente referenciado: {pillar['pillar_id']}.")

    if len(kpi_ids) != len(set(kpi_ids)):
        errors.append("Hay kpi_id duplicados.")

    question_ids = [
        question["question_id"] for question in definition.get("questions", [])
    ]
    if len(question_ids) != len(set(question_ids)):
        errors.append("Hay question_id duplicados.")

    known_kpis = set(kpi_ids)
    for question in definition.get("questions", []):
        if question["pillar_id"] not in known_pillars:
            errors.append(
                f"{question['question_id']} referencia un pillar_id inexistente."
            )
        if question["kpi_id"] not in known_kpis:
            errors.append(
                f"{question['question_id']} referencia un kpi_id inexistente."
            )

    return errors


def build_manifest(
    matrix_file: Path,
    out_dir: Path,
    tower_definition: dict,
    warnings: list[str],
    paragraph_count: int,
) -> dict:
    """Construct a manifest dictionary summarizing the tower bootstrap process.

    The manifest provides a structured record of the bootstrap operation. It
    includes metadata about the source and destination paths, details of the
    extraction method, a statistical summary of the parsed tower components
    (e.g., pillars, KPIs), and a collection of any non-fatal warnings issued
    during execution.

    Args:
        matrix_file: Path to the source DOCX matrix file.
        out_dir: Path to the output directory where generated artifacts are stored.
        tower_definition: A dictionary containing the parsed tower structure,
            including its ID, name, pillars, KPIs, and purpose statement.
        warnings: A list of string warnings generated during the parsing phase.
        paragraph_count: Total number of paragraphs processed from the source
            DOCX document.

    Returns:
        A dictionary representing the generation manifest.

    Raises:
        KeyError: If `tower_definition` lacks required keys, such as 'tower_id',
            'tower_name', 'pillars', or 'purpose'.
        TypeError: If a `weight_pct` value within a pillar entry in
            `tower_definition` cannot be cast to an integer.
    """
    return {
        "artifact_type": "tower_bootstrap_manifest",
        "schema_version": "1.0",
        "tower_id": tower_definition["tower_id"],
        "tower_name": tower_definition["tower_name"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_matrix_file": str(matrix_file.resolve()),
        "output_directory": str(out_dir.resolve()),
        "extraction_method": {
            "mode": "offline_docx_xml_regex",
            "inputs": {
                "paragraph_count": paragraph_count,
            },
            "patterns": {
                "tower_name": r"\bTorre\s+N\s*[-:]\s*(.+)",
                "pillar_header": r"\bPilar\s+(\d+)\s*-\s*(Tn\.P\d+)\s*-\s*(.+)$",
                "kpi_header": r"\b(Tn\.P\d+\.K\d+)\s*-\s*(.+)$",
                "weight_line": r"^<pillar_name>\s*-\s*(\d+)%$",
            },
        },
        "summary": {
            "purpose_length": len(tower_definition["purpose"]),
            "pillar_count": len(tower_definition["pillars"]),
            "kpi_count": sum(
                len(pillar.get("kpis", [])) for pillar in tower_definition["pillars"]
            ),
            "question_count": len(tower_definition.get("questions", [])),
            "weight_sum_pct": sum(
                int(pillar["weight_pct"]) for pillar in tower_definition["pillars"]
            ),
        },
        "warnings": warnings,
    }


def bootstrap_tower(
    tower_id: str,
    matrix_file: Path,
    out_dir: Path,
) -> tuple[dict, dict, list[str]]:
    """Generates a tower definition and manifest from a DOCX specification matrix.

    This function orchestrates the conversion of a human-readable DOCX matrix
    file into a machine-readable JSON tower definition. It loads a base
    definition template, then parses the input DOCX to extract key attributes
    such as purpose, scope, pillars, KPIs, weights, and questions.

    The extracted data undergoes validation for logical consistency, ensuring, for
    example, that all defined pillars have corresponding weights and KPIs. The
    validated components are assembled into the final tower definition structure,
    which is then validated against a formal JSON schema.

    The resulting `tower_definition_{tower_id}.json` and a
    `bootstrap_manifest.json` are written to the specified output directory.

    Args:
        tower_id (str): The unique identifier for the tower. This value is
            normalized to uppercase and stripped of whitespace.
        matrix_file (pathlib.Path): The path to the input DOCX matrix file
            containing the tower's specification.
        out_dir (pathlib.Path): The directory where the generated JSON definition
            and manifest files will be saved. It is created if it does not exist.

    Returns:
        tuple[dict, dict, list[str]]: A tuple containing:
            - The generated tower definition as a dictionary.
            - The bootstrap process manifest as a dictionary.
            - A list of non-critical warning strings from the parsing process.

    Raises:
        FileNotFoundError: If `matrix_file` or the internal base definition
            template file cannot be found.
        RuntimeError: If validation of the extracted data fails due to critical
            inconsistencies (e.g., pillars with missing weights or KPIs), or if
            the final assembled definition does not conform to the required schema.
    """
    tower_id = tower_id.upper().strip()
    matrix_file = matrix_file.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    base_definition = load_json(
        ROOT / "engine_config" / "towers" / "T5" / "tower_definition_T5.json"
    )
    paragraphs = extract_docx_paragraphs(matrix_file)
    warnings: list[str] = []

    tower_name = extract_tower_name(paragraphs, tower_id)
    purpose = extract_purpose(paragraphs)
    scope_summary = extract_scope_summary(paragraphs)
    related_towers = extract_related_towers(paragraphs, tower_id)
    boundary_notes = extract_boundary_notes(paragraphs)
    pillar_name_map = build_pillar_name_map(paragraphs, tower_id, warnings)
    weights = extract_weights(paragraphs, tower_id, pillar_name_map, warnings)
    kpis_by_pillar = extract_kpis(paragraphs, tower_id, warnings)
    questions = extract_questions(paragraphs, tower_id, warnings)

    missing_weight_pillars = sorted(set(pillar_name_map) - set(weights))
    if missing_weight_pillars:
        raise RuntimeError(f"Faltan pesos para: {', '.join(missing_weight_pillars)}")

    missing_kpi_pillars = sorted(set(pillar_name_map) - set(kpis_by_pillar))
    if missing_kpi_pillars:
        raise RuntimeError(f"Faltan KPIs para: {', '.join(missing_kpi_pillars)}")

    extra_kpi_pillars = sorted(set(kpis_by_pillar) - set(pillar_name_map))
    if extra_kpi_pillars:
        raise RuntimeError(
            f"Hay KPIs asociados a pilares no definidos: {', '.join(extra_kpi_pillars)}"
        )

    pillars = []
    for pillar_id in sorted(
        pillar_name_map, key=lambda value: int(value.split(".P")[1])
    ):
        pillars.append(
            {
                "pillar_id": pillar_id,
                "pillar_name": pillar_name_map[pillar_id],
                "weight_pct": weights[pillar_id],
                "kpis": sorted(
                    kpis_by_pillar[pillar_id],
                    key=lambda item: int(item["kpi_id"].split(".K")[1]),
                ),
            }
        )
    attach_questions_to_pillars(pillars, questions)

    tower_definition = build_tower_definition(
        base_definition=base_definition,
        tower_id=tower_id,
        tower_name=tower_name,
        purpose=purpose,
        scope_summary=scope_summary,
        related_towers=related_towers,
        boundary_notes=boundary_notes,
        pillars=pillars,
        questions=questions,
    )
    errors = validate_tower_definition(tower_definition)
    if errors:
        raise RuntimeError("Validación fallida:\n- " + "\n- ".join(errors))

    manifest = build_manifest(
        matrix_file=matrix_file,
        out_dir=out_dir,
        tower_definition=tower_definition,
        warnings=warnings,
        paragraph_count=len(paragraphs),
    )

    tower_definition_path = out_dir / f"tower_definition_{tower_id}.json"
    manifest_path = out_dir / "bootstrap_manifest.json"
    tower_definition_path.write_text(
        json.dumps(tower_definition, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return tower_definition, manifest, warnings


def main() -> None:
    """Executes the tower bootstrapping process using command-line arguments.

    This function serves as the main entry point for the command-line script. It
    parses arguments for a tower identifier, a matrix file path, and an output
    directory. It then calls the `bootstrap_tower` function to generate the
    tower definition and associated manifest. The resulting artifacts are serialized
    to JSON files in the specified output directory. Finally, it logs key
    statistics, such as pillar and KPI counts, and the paths to the output files.

    The script expects the following command-line arguments:
      --tower (str): The identifier for the tower being bootstrapped.
      --matrix-file (str): The path to the source matrix file.
      --out-dir (str): The path to the directory for storing output artifacts.

    Raises:
        FileNotFoundError: If the path provided via `--matrix-file` does not exist.
        KeyError: If the dictionary returned by `bootstrap_tower` lacks the
            'pillars' key, which is required for logging statistics.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--tower", required=True)
    parser.add_argument("--matrix-file", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    tower_id = args.tower.upper().strip()
    matrix_file = Path(args.matrix_file).resolve()
    out_dir = (
        (ROOT / args.out_dir).resolve()
        if not Path(args.out_dir).is_absolute()
        else Path(args.out_dir).resolve()
    )
    tower_definition, _manifest, warnings = bootstrap_tower(
        tower_id, matrix_file, out_dir
    )

    tower_definition_path = out_dir / f"tower_definition_{tower_id}.json"
    manifest_path = out_dir / "bootstrap_manifest.json"

    logger.info(f"tower_definition generado en: {tower_definition_path}")
    logger.info(f"bootstrap_manifest generado en: {manifest_path}")
    logger.info(f"pillar_count: {len(tower_definition['pillars'])}")
    logger.info(
        f"kpi_count: {sum(len(pillar['kpis']) for pillar in tower_definition['pillars'])}"
    )
    logger.info(f"warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
