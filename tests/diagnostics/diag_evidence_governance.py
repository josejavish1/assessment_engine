import asyncio
import logging

from assessment_engine.infrastructure.evidence_governance import EvidenceSnapshotter
from assessment_engine.infrastructure.runtime_paths import ROOT

# Configurar logging para ver la salida
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def test_snapshotter():
    print("\n🚀 Iniciando TEST de Gobernanza de Evidencias...")

    # Directorio temporal para el test
    test_dir = ROOT / "working" / "test_governance"
    snapshotter = EvidenceSnapshotter(storage_dir=test_dir)

    # URL real para probar (Sala de prensa de Redeia o AWS)
    test_url = "https://www.redeia.com/es/sala-de-prensa"

    print(f"  -> Probando captura de: {test_url}")
    snapshot = await snapshotter.capture_snapshot(test_url)

    if snapshot and snapshot.get("status") == "verified":
        print("  ✅ TEST EXITOSO")
        print(f"  📍 Snapshot guardado en: {snapshot.get('local_snapshot')}")
        print(f"  🔑 Hash de contenido: {snapshot.get('content_hash')[:16]}...")

        # Verify that the file physically exists
        file_path = ROOT / snapshot.get("local_snapshot")
        if file_path.exists():
            print(
                f"  📄 Verificado: El archivo existe y tiene {file_path.stat().st_size} bytes."
            )
        else:
            print("  ❌ ERROR: El archivo no se encuentra en la ruta indicada.")
    else:
        print(f"  ❌ TEST FALLIDO: {snapshot.get('error', 'Error desconocido')}")


if __name__ == "__main__":
    asyncio.run(test_snapshotter())
