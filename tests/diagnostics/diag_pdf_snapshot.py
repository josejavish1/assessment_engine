import asyncio
import logging

from assessment_engine.infrastructure.evidence_governance import EvidenceSnapshotter
from assessment_engine.infrastructure.runtime_paths import ROOT

logging.basicConfig(level=logging.INFO)


async def test_pdf_download():
    test_dir = ROOT / "working" / "test_pdf"
    snapshotter = EvidenceSnapshotter(storage_dir=test_dir)

    url = "https://www.redeia.com/sites/default/files/2024-03/informe-de-sostenibilidad-2023.pdf"
    print(f"🚀 Probando descarga de PDF real: {url}")

    snapshot = await snapshotter.capture_snapshot(url)

    if snapshot and snapshot.get("status") == "verified":
        print(f"✅ EXITO: PDF guardado en {snapshot.get('local_snapshot')}")
        file_path = ROOT / snapshot.get("local_snapshot")
        if file_path.exists():
            print(f"   Tamaño: {file_path.stat().st_size} bytes")
    else:
        print(f"❌ FALLO: {snapshot}")


if __name__ == "__main__":
    asyncio.run(test_pdf_download())
