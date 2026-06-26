"""Provides core logic for bootstrapping tower configurations from matrix source documents within the Assessment Engine pipeline."""

import argparse
import json
import logging
import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from assessment_engine.infrastructure.runtime_paths import ROOT

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


from typing import Any, cast


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a 'utf-8-sig' encoded JSON file into a dictionary."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def extract_docx_paragraphs(path: Path) -> list[str]:
    r"""{'docstring': "Extracts all non-empty text paragraphs from a DOCX file.\n\nThis function operates by treating the .docx file as a standard ZIP archive\nand directly parsing the 'word/document.xml' member. It identifies paragraph\nelements (`<w:p>`) and concatenates the text from all child text run elements\n(`<w:t>`). The resulting text for each paragraph is then normalized to collapse\nconsecutive whitespace characters. Paragraphs containing no visible text after\nthis process are omitted from the output.\n\nArgs:\n    path (pathlib.Path): The file system path to the input .docx file.\n\nReturns:\n    list[str]: A list of strings, where each string represents the\n        normalized text content of a non-empty paragraph from the document.\n\nRaises:\n    FileNotFoundError: If the file specified by `path` does not exist.\n    zipfile.BadZipFile: If the file is not a valid ZIP archive, which can\n        indicate a corrupted .docx file.\n    KeyError: If the 'word/document.xml' member is not found within the\n        archive, indicating a malformed or non-standard .docx file.\n    xml.etree.ElementTree.ParseError: If the 'word/document.xml' member\n        contains malformed XML."}."""
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
    """Collapse consecutive whitespace into single spaces and strip leading/trailing whitespace."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text(value: str) -> str:
    """Normalize whitespace and Unicode representation of a string."""
    return unicodedata.normalize("NFC", normalize_spaces(value))


def normalize_dash(value: str) -> str:
    """{'docstring': 'Normalize various dash-like characters in a string to a standard hyphen-minus.'}."""
    return str(value or "").replace("–", "-").replace("—", "-").replace("−", "-")


def comparable_text(value: str) -> str:
    """Generates a canonical, alphanumeric representation of a string for comparison.

    This function transforms a string into a simplified form suitable for tasks
    like case-insensitive and diacritic-insensitive matching. The normalization
    pipeline consists of several steps: applying NFKD Unicode normalization to
    decompose composite characters, converting to a lowercase ASCII representation
    by discarding non-ASCII characters, and finally removing all non-alphanumeric
    characters.

    For example, the input "Héllö-Wörld_123!" becomes "helloworld123".

    Args:
        value (str): The input string to be normalized.

    Returns:
        str: A normalized string containing only lowercase ASCII letters and digits.
    """
    normalized = unicodedata.normalize("NFKD", normalize_dash(value))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_value.lower())


def extract_tower_name(paragraphs: list[str], tower_id: str) -> str:
    """Extracts and normalizes a tower name from a list of text paragraphs.

    Scans the initial 80 paragraphs to find a line matching a specific pattern.
    The pattern consists of the case-insensitive word 'Torre', followed by the
    `tower_id` with its first character removed, a colon or hyphen separator,
    and the tower name. For example, for a `tower_id` of 'T123', it searches
    for patterns like 'Torre 123: Substation Alpha'.

    Upon finding a match, the captured name is normalized by removing extraneous
    whitespace, stripping trailing numerical digits, and trimming any
    surrounding hyphens or colons.

    Args:
        paragraphs: A list of string paragraphs from the source document.
        tower_id: The unique identifier for the tower, such as 'T123'. The
            initial character is stripped before matching.

    Returns:
        The extracted and sanitized tower name.

    Raises:
        RuntimeError: If no matching tower name can be located for the given
            `tower_id` within the first 80 paragraphs.
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
    """Extract the tower's purpose statement from a list of text paragraphs.

    This function locates the "Definición de la torre" section header within
    the provided list of paragraphs. It then searches the subsequent 11 paragraphs
    for a sentence that begins with "la torre " and contains the substring
    " cubre " (case-insensitive). The first matching paragraph found is considered
    the purpose statement and is returned after normalization.

    Args:
        paragraphs (list[str]): A list of strings, where each string represents a
            paragraph from the source document.

    Returns:
        str: The normalized text of the purpose statement.

    Raises:
        RuntimeError: If the "Definición de la torre" section header is not
            found, or if a purpose statement matching the expected pattern cannot
            be located within the 11 paragraphs following the header.
    """
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
    """Corrects a specific, duplicated Spanish phrase within a string.

    This function targets and replaces redundant variations of the phrase
    "Seguridad Física y Control de Accesos y Control de Accesos" with the
    corrected form "Seguridad Física y Control de Accesos". It handles
    variations in accentuation (e.g., "Física" vs. "Fisica") and the case of
    the final word. The input string is normalized before replacement, and the
    result is normalized again before being returned.

    Args:
        value: The input string to be processed.

    Returns:
        A cleaned and normalized string with the redundant phrase corrected.
    """
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
    r"""{'docstring': 'Parses text paragraphs to extract a mapping of pillar IDs to names.\n\n    This function scans a list of paragraphs for lines that match a case-\n    insensitive regular expression, typically in the format:\n    \'Pilar <num> - <tower_id>.P<num> - <Pillar Name>\'.\n\n    The extracted pillar name is post-processed to remove common artifacts,\n    such as repeated phrases, trailing digits, and leading/trailing punctuation.\n    If multiple distinct names are found for the same pillar ID, the first one\n    encountered is retained and a warning message is appended to the `warnings`\n    list.\n\n    Args:\n        paragraphs: A list of strings representing text paragraphs to be parsed.\n        tower_id: The expected tower identifier, used to construct the regex\n            pattern for validation.\n        warnings: A list to which warning messages are appended. This argument\n            is mutated by the function to report conflicting pillar names.\n\n    Returns:\n        A dictionary mapping uppercased, full pillar IDs (e.g., "TOWER1.P123")\n        to their corresponding cleaned pillar names.\n\n    Raises:\n        RuntimeError: If no pillar information matching the expected format is\n            found in any of the paragraphs.'}."""
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
    """Extracts integer percentage weights for predefined pillars from a list of text paragraphs.

    This function parses document text to find percentage weights for a given set
    of pillars. It applies a sequence of regular expression-based strategies to
    locate the weights, prioritizing more explicit definitions over general keyword
    searches.

    The parsing strategies are executed in the following order:
    1.  **Explicit Enumeration**: Searches all paragraphs for patterns like
        "Pilar <number> ... (<percentage>%)".
    2.  **Named Weight**: Searches all paragraphs for patterns like
        "<Pillar Name> - <percentage>%" or "<Pillar Name> — <percentage>%"
    3.  **Section Search**: For any remaining pillars, it searches for the pillar's
        name and a percentage value within the "Factores de Importancia" section
        of the document.

    If a weight for any pillar cannot be determined after all strategies have been
    attempted, a descriptive message is appended to the mutable `warnings` list.

    Args:
        paragraphs: A list of strings, where each string is a paragraph from
            the source document.
        tower_id: The identifier for the tower, used as a prefix to construct
            the full pillar ID (e.g., f"{tower_id}.P1").
        pillar_name_map: A dictionary mapping full pillar IDs to their
            corresponding human-readable names.
        warnings: A mutable list to which warning messages are appended for any
            pillars where a weight could not be found.

    Returns:
        A dictionary where keys are full pillar IDs and values are their
        corresponding integer percentage weights.

    Raises:
        RuntimeError: If the "Factores de Importancia" section, which is required
            for the fallback search strategy, cannot be located in the paragraphs.
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

    # Certain tower matrices declare the final weighting factor directly within explicit pillar definition lines, obviating the need for separate calculation.
    # Matching by an explicit pillar number (e.g., 'Pillar 2') provides greater robustness compared to fuzzy string matching against the pillar name.
    # This numerical matching strategy mitigates parsing errors that arise from minor variations in pillar naming conventions across different sections of the source document.
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

    # Certain source matrices embed the final, normalized weight for a component directly within its descriptive text.
    # Prioritize parsing fully articulated weight definitions (e.g., 'Compute Foundation & Virtualization - 22%') when available, as they provide an unambiguous, direct source for weighting factors.
    # Pre-calculated weight values extracted directly from the source document are considered authoritative, as they represent the final, rounded distribution guaranteed to sum to 100%.
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
    """Parses text paragraphs to extract and structure Key Performance Indicators (KPIs).

    This function iterates through a list of text paragraphs to identify KPIs that
    follow a specific format. It handles two primary cases:
    1. The KPI identifier and name are on the same line, separated by a dash
       (e.g., "TOWER.P1.K1 - KPI Name").
    2. The KPI identifier appears on its own line, and its corresponding name
       is found on one of the subsequent three non-empty lines.

    Extracted KPIs are grouped by their pillar identifier (e.g., "TOWER.P1").
    The function maintains a record of seen KPI IDs to prevent duplicates;
    subsequent occurrences of the same KPI ID are ignored and generate a
    warning. Warnings are also generated for KPI IDs that are not followed by a
    valid name.

    Args:
        paragraphs: A list of strings, where each string is a paragraph of text
            to be searched for KPIs.
        tower_id: The case-insensitive root identifier for the tower (e.g., "TOWER")
            used to construct the KPI matching patterns.
        warnings: A list that is populated with warning messages for any parsing
            issues encountered. This argument is modified in-place.

    Returns:
        A dictionary mapping pillar IDs to a list of their associated KPI
        dictionaries. Each KPI dictionary contains 'kpi_id' and 'kpi_name' keys.
        For example:
        {'TOWER.P1': [{'kpi_id': 'TOWER.P1.K1', 'kpi_name': 'Example Name'}]}

    Raises:
        RuntimeError: If no KPIs can be extracted from the provided paragraphs.
    """
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
    """Extract and normalize text items from a delimited section of a document.

    Parses a list of paragraphs to find a section that begins immediately after
    `section_title`. It collects all subsequent paragraphs until it either
    encounters the first paragraph that matches an entry in `next_titles` or
    reaches the end of the paragraph list. Collected paragraphs are normalized,
    and any paragraphs that are empty or consist solely of whitespace are
    discarded from the final output.

    Args:
        paragraphs: A list of strings representing the document's content.
        section_title: The title marking the start of the section to be
            extracted. The title paragraph itself is not included.
        next_titles: A list of titles that signal the end of the section.
            The extraction stops before the paragraph containing the terminating
            title.

    Returns:
        A list of normalized, non-empty strings from the specified section.
        Returns an empty list if the `section_title` is not found or if the
        resulting section contains no contentful paragraphs.
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
    """Extracts and standardizes scope summary labels from document paragraphs.

    Parses a list of document paragraphs to identify a section beginning with
    "Alcance típico:". The function collects all subsequent list items until a
    terminal title, "Por qué esta torre es fundamental en el modelo global de madurez",
    is encountered. For each collected item, the text preceding the first colon
    is isolated as the label. This label is then cleaned of repeated phrases and
    its casing is standardized (e.g., "facilities" becomes "Facilities").

    Args:
        paragraphs (list[str]): A list of strings, where each string is a
            paragraph from the source document.

    Returns:
        list[str]: A list of the extracted, cleaned, and standardized scope
            summary labels.
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
    """Parses Spanish text paragraphs for tower references and returns their normalized IDs.

    This function scans a list of text strings for Spanish-language tower
    mentions using regular expressions. It identifies both singular patterns
    (e.g., "Torre 5") and plural patterns (e.g., "Torres 1, 2 y 3"). All
    discovered tower numbers are normalized into the format 'T<number>'. Any
    extracted tower ID that matches the provided `tower_id` is excluded from the
    final result.

    Args:
        paragraphs: A list of text paragraphs to be searched.
        tower_id: The normalized ID of the primary tower (e.g., 'T1'), which
            will be excluded from the results.

    Returns:
        A list of unique, normalized tower IDs found in the text, sorted
        numerically (e.g., ['T2', 'T5', 'T11']).
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
    """Extracts and formats boundary exclusion notes from a list of paragraphs.

    Searches for the sentinel header "No incluye / se evalúa en otras torres:"
    within the input paragraphs. Upon finding the header, this function processes
    up to the next three subsequent paragraphs to identify exclusion notes.

    The processing of these subsequent paragraphs terminates prematurely if a
    normalized paragraph ends with a colon. Each identified note is normalized,
    potentially split into clauses based on specific delimiters (e.g., ", la "),
    and reconstructed into one or more complete sentences. Each resulting sentence
    is cleaned of repeated phrases and formatted with a terminal period.

    Args:
        paragraphs: A list of strings, where each string represents a paragraph
            of text to be analyzed.

    Returns:
        A list of cleaned and formatted boundary note sentences. Returns an empty
        list if the sentinel header is not found.
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
    """Parses a list of text paragraphs to extract structured question data.

    This function iterates through a list of paragraphs, identifying question
    headers that match a case-insensitive regular expression pattern derived from
    `tower_id` (e.g., 'DC.P1.K2.PR3').

    For each identified question header, it inspects up to three subsequent
    paragraphs to find the corresponding question text. It implements logic to
    skip known non-question content, such as response headers, subsequent
    question IDs, or predefined section titles. The provided `warnings` list
    is populated in-place with messages for issues encountered, such as
    duplicate question IDs or the inability to locate a question's text.
    Each question ID in the returned list is guaranteed to be unique.

    Args:
        paragraphs: A list of strings, where each string is a paragraph or
            line of text from the source document.
        tower_id: The identifier for the tower (e.g., 'DC') used to construct
            the regular expression for locating question codes.
        warnings: A mutable list that is populated in-place with string
            warnings during processing.

    Returns:
        A list of dictionaries, where each dictionary represents an extracted
        question and contains the following keys:
            'question_id' (str): The full unique identifier (e.g., 'DC.P1.K2.PR3').
            'pillar_id' (str): The derived pillar identifier (e.g., 'DC.P1').
            'kpi_id' (str): The derived Key Performance Indicator (KPI)
                identifier (e.g., 'DC.P1.K2').
            'question_text' (str): The extracted and cleaned text of the question.
        Returns an empty list if no matching questions are found.
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
    r"""{'docstring': "Group questions by KPI and attach them in-place to a pillar data structure.\n\n    This function modifies the `pillars` list by adding a 'questions' key\n    to each KPI dictionary. Questions are first grouped by their 'kpi_id'.\n    Each group is then sorted numerically based on the integer component\n    following the '.PR' substring in the 'question_id' before being\n    attached to its corresponding KPI.\n\n    Args:\n        pillars: A list of pillar dictionaries to be modified. Each pillar is\n            expected to contain a 'kpis' key holding a list of KPI\n            dictionaries, and each KPI dictionary must have a 'kpi_id'.\n        questions: A list of question dictionaries. Each question must contain\n            'kpi_id', 'question_id', and 'question_text' keys.\n\n    Returns:\n        None. The `pillars` list is modified in-place.\n\n    Raises:\n        KeyError: If a required key ('kpi_id', 'question_id', 'question_text')\n            is missing from a dictionary in `questions`, or if 'kpi_id' is\n            missing from a KPI dictionary.\n        ValueError: If the numeric component of a 'question_id' (following '.PR')\n            cannot be converted to an integer.\n        IndexError: If a 'question_id' string does not contain the '.PR'\n            separator, preventing sorting key extraction."}."""
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
    """Constructs a tower definition dictionary from a base template and components.

    The function first creates a new dictionary by copying a set of generic
    fields, defined by the global `GENERIC_BLOCK_KEYS`, from the provided
    `base_definition`. It then populates this dictionary with the tower-specific
    attributes passed as arguments.

    Args:
        base_definition: A dictionary template containing generic fields. Must
            contain all keys specified in the `GENERIC_BLOCK_KEYS` global
            constant.
        tower_id: A unique string identifier for the tower.
        tower_name: The human-readable name for the tower.
        purpose: A string describing the tower's objective or purpose.
        scope_summary: A list of strings summarizing the items in scope.
        related_towers: A list of string identifiers for functionally related
            towers.
        boundary_notes: A list of strings providing notes on scope boundaries
            or exclusions.
        pillars: A list of dictionaries, where each defines a pillar.
        questions: A list of dictionaries, where each defines a question.

    Returns:
        A dictionary representing the complete, assembled tower definition.

    Raises:
        KeyError: If `base_definition` is missing any key specified in
            `GENERIC_BLOCK_KEYS`.
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
    """Validate a tower definition dictionary against structural and consistency rules.

    This function performs a series of checks on the provided dictionary to ensure
    its integrity as a tower definition. The specific validations include:
    - Uniqueness of `pillar_id`, `kpi_id`, and `question_id` values.
    - Ensuring the sum of `weight_pct` for all pillars equals 100.
    - Verification that each `kpi_id` is prefixed with its parent `pillar_id`.
    - Confirmation that `pillar_id` and `kpi_id` referenced in questions
      correspond to existing pillars and KPIs.

    Args:
        definition: The tower definition dictionary. It is expected to conform to a
            specific schema:
            - A top-level key "pillars" (list[dict]): Each dict contains:
                - "pillar_id" (str): A unique identifier for the pillar.
                - "weight_pct" (int | str): The pillar's weight as a percentage.
                - "kpis" (list[dict]): Each dict contains:
                    - "kpi_id" (str): A unique identifier for the KPI,
                      prefixed with the parent `pillar_id`.
            - A top-level key "questions" (list[dict]): Each dict contains:
                - "question_id" (str): A unique identifier for the question.
                - "pillar_id" (str): The ID of the pillar this question belongs to.
                - "kpi_id" (str): The ID of the KPI this question belongs to.

    Returns:
        A list of human-readable strings describing validation failures. An
        empty list indicates that the definition is valid.

    Raises:
        KeyError: If a required key (e.g., 'pillar_id', 'kpi_id',
            'question_id') is missing from a dictionary element within the
            definition structure.
        ValueError: If a 'weight_pct' value is present but cannot be
            converted to an integer.
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
    """Constructs a metadata manifest for a tower bootstrapping process.

    This function aggregates metadata about the extraction process into a single
    dictionary. The manifest includes source and output file paths, extraction
    parameters, a summary of the parsed tower structure, and any warnings
    generated during the process.

    Args:
        matrix_file: Path to the source DOCX matrix file from which the
            tower definition was extracted.
        out_dir: The destination directory for the generated tower artifacts.
        tower_definition: A dictionary containing the structured data of the
            tower, including its ID, name, purpose, pillars, and KPIs.
        warnings: A list of string messages detailing non-fatal issues
            encountered during the extraction.
        paragraph_count: The total number of paragraphs analyzed in the source
            document.

    Returns:
        A dictionary representing the bootstrap manifest, containing metadata
        and a summary of the extraction process.

    Raises:
        KeyError: If `tower_definition` or its nested pillar dictionaries are
            missing required keys (e.g., 'tower_id', 'pillars', 'weight_pct').
        ValueError: If a pillar's 'weight_pct' value within the
            `tower_definition` cannot be converted to an integer.
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
    """Parses a structured Word document to generate a JSON tower definition and manifest.

    This function orchestrates the extraction of tower components—such as its name,
    purpose, scope, pillars, KPIs, and scoring questions—from a specially
    formatted `.docx` file. It uses a predefined base tower definition as a
    template, populating it with the parsed data. The process includes several
    validation steps to ensure data integrity, such as verifying that all
    defined pillars have associated weights and KPIs.

    Upon successful parsing and validation, the function writes two JSON files
    to the specified output directory: `tower_definition_{tower_id}.json` and
    `bootstrap_manifest.json`.

    Args:
        tower_id: The unique identifier for the tower (e.g., "T1"). The value is
            normalized to uppercase and stripped of leading/trailing whitespace.
        matrix_file: The path to the source `.docx` Word document containing the
            tower specification matrix.
        out_dir: The directory where the output JSON files will be saved. This
            directory is created if it does not exist.

    Returns:
        A tuple containing the generated tower definition dictionary, the bootstrap
        manifest dictionary, and a list of non-critical warnings encountered
        during parsing.

    Raises:
        FileNotFoundError: If the `matrix_file` or the base T5 JSON definition
            template file cannot be found.
        RuntimeError: If validation of the extracted data fails. This includes cases
            where pillars are missing weights or KPIs, KPIs are associated with
            non-existent pillars, or the final tower definition object does not
            conform to the required data schema.
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
    """Parses command-line arguments and executes the tower bootstrapping process.

    This function serves as the main entry point for the command-line script.
    It defines and parses the required `--tower`, `--matrix-file`, and `--out-dir`
    arguments. After processing the inputs, it invokes the `bootstrap_tower`
    function to perform the core generation logic. Upon completion, it logs
    summary statistics to standard output, including the paths to the generated
    artifacts, the total number of pillars and KPIs, and the count of any
    warnings.

    Raises:
        FileNotFoundError: If the path provided via the --matrix-file argument
            does not exist.
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
