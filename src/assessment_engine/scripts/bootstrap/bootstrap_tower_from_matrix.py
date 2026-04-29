"""
Módulo bootstrap_tower_from_matrix.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from assessment_engine.scripts.lib.runtime_paths import ROOT


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
    return json.loads(path.read_text(encoding="utf-8"))


def extract_docx_paragraphs(path: Path) -> list[str]:
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
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", normalize_spaces(value))


def normalize_dash(value: str) -> str:
    return str(value or "").replace("–", "-").replace("—", "-").replace("−", "-")


def comparable_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", normalize_dash(value))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_value.lower())


def extract_tower_name(paragraphs: list[str], tower_id: str) -> str:
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

    # Some tower matrices express the final factor in explicit pillar lines such as
    # "Pilar 2 - ... (20%)". Matching by pillar number is more robust than fuzzy
    # matching by pillar name because naming varies slightly across sections.
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

    # Some matrices also publish the normalized final weight in plain lines such as
    # "Compute Foundation & Virtualization - 22%". When available, prefer these
    # values because they already reflect the final rounded distribution that sums 100.
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

    print(f"tower_definition generado en: {tower_definition_path}")
    print(f"bootstrap_manifest generado en: {manifest_path}")
    print(f"pillar_count: {len(tower_definition['pillars'])}")
    print(
        f"kpi_count: {sum(len(pillar['kpis']) for pillar in tower_definition['pillars'])}"
    )
    print(f"warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
