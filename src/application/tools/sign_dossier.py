import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

from infrastructure.client_intelligence import sign_dossier


def main():
    if len(sys.argv) < 2:
        print(
            "Uso: python -m application.tools.sign_dossier <path_to_json> [new_client_name]"
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

    # Re-firmar
    signed_data = sign_dossier(data)

    path.write_text(
        json.dumps(signed_data, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Dossier RE-FIRMADO con éxito: {path}")


if __name__ == "__main__":
    main()
