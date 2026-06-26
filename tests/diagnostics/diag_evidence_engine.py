import sys
from pathlib import Path

from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
from assessment_engine.infrastructure.text_utils import slugify


def test_evidence_engine(client_name: str, docx_path: str):
    client_id = slugify(client_name)
    storage_dir = Path(f"working/{client_id}")
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Reset vault for a clean test
    vault_file = storage_dir / "evidence_vault.json"
    if vault_file.exists():
        vault_file.unlink()
        print(f"🗑️ Vault anterior eliminado en {vault_file}")

    engine = EvidenceEngine(client_id=client_id, storage_dir=storage_dir)

    print(f"🚀 Probando Evidence Engine (Modo Jerárquico) para: {client_name}")
    print(f"📂 Procesando: {docx_path}")

    engine.ingest_file(Path(docx_path))

    print("\n✅ Análisis completado.")
    print(f"📊 Fragmentos totales generados: {len(engine.ledger.fragments)}")
    print(f"💾 Guardado en: {engine.ledger_path}")

    # Display a sample of the hierarchy
    print("\n🔍 MUESTRA DE FRAGMENTOS JERÁRQUICOS:")
    sample_count = 0
    for frag in engine.ledger.fragments:
        hierarchy = frag.location_metadata.get("hierarchy", [])
        h_str = " > ".join(hierarchy) if hierarchy else "ROOT"

        if frag.location_metadata.get("type") == "heading":
            print(f"\n[H{frag.location_metadata.get('level')}] {frag.content}")
        else:
            if sample_count < 15:  # No saturar
                print(f"  └─ [{h_str}] {frag.content[:80]}...")
                sample_count += 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/test_evidence_engine.py <client_name> <docx_path>")
    else:
        test_evidence_engine(sys.argv[1], sys.argv[2])
