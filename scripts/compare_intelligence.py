import json
from pathlib import Path


def compare_intel():
    old_path = Path("working/redeia2/client_intelligence.json")
    new_path = Path("working/redeia/client_intelligence.json")

    if not old_path.exists():
        print(f"Error: {old_path} no existe")
        return
    if not new_path.exists():
        print(f"Error: {new_path} no existe")
        return

    with open(old_path, "r", encoding="utf-8-sig") as f:
        old_data = json.load(f)
    with open(new_path, "r", encoding="utf-8-sig") as f:
        new_data = json.load(f)

    print("=====================================================================")
    print("🔍 COMPARATIVA DE COSECHA DE INTELIGENCIA (client_intelligence.json)")
    print("=====================================================================\n")

    # 1. Metadatos Básicos
    print("📋 METADATOS BÁSICOS:")
    print(f"   - Viejo Client Name: {old_data.get('client_name')}")
    print(f"   - Nuevo Client Name: {new_data.get('client_name')}")
    print(
        f"   - Viejo Sector (Industry): {old_data.get('profile', {}).get('industry')}"
    )
    print(
        f"   - Nuevo Sector (Industry): {new_data.get('profile', {}).get('industry')}"
    )
    print()

    # 2. Análisis del Target de Madurez (Tower Overrides)
    print("🎯 COMPARATIVA DE TARGETS DE MADUREZ POR TORRE:")
    old_overrides = old_data.get("tower_overrides", {})
    new_overrides = new_data.get("tower_overrides", {})

    all_towers = sorted(
        list(set(list(old_overrides.keys()) + list(new_overrides.keys()))),
        key=lambda x: int(x[1:]) if x[1:].isdigit() else x,
    )

    print(
        f"   {'Torre':<6} | {'Target Viejo':<13} | {'Target Nuevo':<13} | {'Cambio en Target / Justificación'}"
    )
    print(f"   {'-' * 6} + {'-' * 13} + {'-' * 13} + {'-' * 45}")
    for tower in all_towers:
        old_val = old_overrides.get(tower, {}).get("target_maturity", "N/A")
        new_val = new_overrides.get(tower, {}).get("target_maturity", "N/A")

        # Get dynamic value from new structure
        if isinstance(old_val, dict):
            old_val = old_val.get("target_maturity", "N/A")
        if isinstance(new_val, dict):
            new_val = new_val.get("target_maturity", "N/A")

        old_just = old_overrides.get(tower, {}).get("justification", "N/A")[:45]
        new_just = new_overrides.get(tower, {}).get("justification", "N/A")[:45]

        # Cleanup carriage returns
        old_just = old_just.replace("\n", " ").replace("\r", " ")
        new_just = new_just.replace("\n", " ").replace("\r", " ")

        print(
            f"   {tower:<6} | {str(old_val):<13} | {str(new_val):<13} | {new_just}..."
        )
    print()

    # 3. Comparar el Footprint y Contexto Tecnológico (Narrativa)
    old_summary = (
        old_data.get("technology_context", {})
        .get("footprint_summary", {})
        .get("summary", "N/A")
    )
    new_summary = (
        new_data.get("technology_context", {})
        .get("footprint_summary", {})
        .get("summary", "N/A")
    )

    print("🌐 COMPARATIVA DE NARRATIVA TECNOLÓGICA (FOOTPRINT SUMMARY):")
    print("\n--- Viejo (working/redeia2) ---")
    print(old_summary[:600] + "...")
    print("\n--- Nuevo (working/redeia) ---")
    print(new_summary[:600] + "...")
    print()

    # 4. Chequeo de Contaminación Cruzada
    contamination_words = ["ebu", "eurovision", "dubag", "uefa", "nba", "broadcasting"]
    old_contaminations = []
    new_contaminations = []

    old_str = json.dumps(old_data).lower()
    new_str = json.dumps(new_data).lower()

    for word in contamination_words:
        if word in old_str:
            old_contaminations.append(word)
        if word in new_str:
            new_contaminations.append(word)

    print("🛡️ DETECCIÓN DE CONTAMINACIÓN EN LA INTELIGENCIA:")
    print(
        f"   - Encontrada en Viejo: {old_contaminations if old_contaminations else '¡Ninguna!'}"
    )
    print(
        f"   - Encontrada en Nuevo: {new_contaminations if new_contaminations else '¡Ninguna!'}"
    )
    print("\n" + "=" * 69 + "\n")


if __name__ == "__main__":
    compare_intel()
