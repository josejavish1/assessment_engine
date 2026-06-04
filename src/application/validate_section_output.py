"""
Módulo validate_section_output.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "working" / "client" / "T5"

SECTION_RULES = {
    "asis": {
        "forbidden_phrases": [
            "TO-BE",
            "estado objetivo",
            "capacidades objetivo",
            "roadmap",
            "plan de evolucion",
        ],
        "text_fields": ["executive_narrative"],
    },
    "risks": {
        "forbidden_phrases": [
            "roadmap",
            "quick wins",
            "capacidades objetivo por pilar",
            "estado objetivo",
        ],
        "text_fields": ["introduction", "closing_summary"],
    },
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv=None) -> None:
    if len(argv if argv is not None else sys.argv) != 2:
        raise SystemExit("Uso: python scripts/validate_section_output.py <asis|risks>")

    section = (argv if argv is not None else sys.argv)[1].strip().lower()
    if section not in SECTION_RULES:
        raise SystemExit(f"Seccion no soportada: {section}")

    approved_file = CASE_DIR / f"approved_{section}.generated.json"
    if not approved_file.exists():
        raise FileNotFoundError(f"No existe: {approved_file}")

    data = load_json(approved_file)
    rules = SECTION_RULES[section]

    errors = []

    for field in rules["text_fields"]:
        value = data.get(field, "")
        if not isinstance(value, str):
            continue

        lower_value = value.lower()
        for phrase in rules["forbidden_phrases"]:
            if phrase.lower() in lower_value:
                errors.append(
                    f"Campo '{field}' contiene frase prohibida para la seccion '{section}': '{phrase}'"
                )

    if errors:
        print("VALIDATION_STATUS=FAIL")
        for err in errors:
            print(err)
        raise SystemExit(1)

    print("VALIDATION_STATUS=PASS")
    print(f"Seccion '{section}' validada correctamente.")


if __name__ == "__main__":
    main()
