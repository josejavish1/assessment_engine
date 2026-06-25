"""Provides core business logic and utility functions for the Assessment Engine pipeline."""

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
    """Load and parse a JSON file from the given path."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv=None) -> None:
    """Validates a section's generated JSON output against a predefined set of rules.

    Acts as the main entry point for a command-line validation script. The script
    takes a single argument, the section name (e.g., 'asis', 'risks'), and reads
    a corresponding JSON file named 'approved_{section}.generated.json'. It then
    checks specified text fields within the JSON object for the presence of
    case-insensitive forbidden substrings.

    The outcome, 'VALIDATION_STATUS=PASS' or 'VALIDATION_STATUS=FAIL', is
    printed to standard output. In case of failure, detailed error messages are
    also printed before the process terminates with a non-zero exit code.

    Args:
        argv: An optional list of command-line arguments. If None, `sys.argv`
            is used. The list is expected to contain the script name at index 0
            and the target section name at index 1.

    Returns:
        None: The function communicates its result by printing to standard output
            and exiting the process; it does not return any value.

    Raises:
        SystemExit: Raised if command-line arguments are invalid (not exactly one
            section argument provided), if the section name is not supported, or
            if the validation fails due to a forbidden phrase being detected.
        FileNotFoundError: Raised if the 'approved_{section}.generated.json' file
            corresponding to the specified section does not exist.
    """
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
