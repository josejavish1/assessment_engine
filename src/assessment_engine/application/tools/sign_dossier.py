import json
import os
import sys
from pathlib import Path

# Prepend the project's source directory to the system path to ensure that module imports are resolved relative to the project root.
sys.path.insert(0, os.path.abspath("src"))

from assessment_engine.infrastructure.client_intelligence import sign_dossier


def main():
    """Re-signs a dossier JSON file from the command line, optionally updating the client name.

    This function is the main entry point for a command-line script that processes
    and re-signs a dossier. It operates directly on a file specified via command-
    line arguments.

    The script performs the following actions:
    1.  Parses command-line arguments for a file path and an optional new
        client name.
    2.  Reads and decodes the JSON content from the specified file, assuming
        'utf-8-sig' encoding.
    3.  If a new client name is provided, it updates the `client_name` key in the
        decoded data structure.
    4.  Invokes `sign_dossier` to apply a new signature to the data.
    5.  Serializes the signed data back to JSON (with 2-space indentation) and
        overwrites the original file, preserving the 'utf-8-sig' encoding.

    The script exits with a non-zero status code if the path argument is
    missing or if the specified file does not exist.

    Usage:
        python -m assessment_engine.application.tools.sign_dossier <path_to_json> [new_client_name]

    Raises:
        json.JSONDecodeError: If the input file does not contain valid JSON.
        IOError: If the file cannot be read from or written to.
    """
    if len(sys.argv) < 2:
        print(
            "Uso: python -m assessment_engine.application.tools.sign_dossier <path_to_json> [new_client_name]"
        )
        sys.exit(1)

    path = Path(sys.argv[1])
    new_name = sys.argv[2] if len(sys.argv) > 2 else None

    if not path.exists():
        print(f"Error: {path} no existe.")
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8-sig"))

    if new_name:
        data["client_name"] = new_name
        print(f"Forzando nombre de cliente a: {new_name}")

    #
    signed_data = sign_dossier(data)

    path.write_text(
        json.dumps(signed_data, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Dossier RE-FIRMADO con éxito: {path}")


if __name__ == "__main__":
    main()
