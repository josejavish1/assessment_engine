import asyncio
import sys
from pathlib import Path

from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
from assessment_engine.infrastructure.raptor_engine import RaptorEngine
from assessment_engine.infrastructure.text_utils import slugify


async def test_raptor(client_name: str, docx_path: str):
    client_id = slugify(client_name)
    storage_dir = Path(f"working/{client_id}")
    storage_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fragment (Evidence Engine)
    evidence_engine = EvidenceEngine(client_id=client_id, storage_dir=storage_dir)
    print(f"📂 Fragmentando: {docx_path}")
    evidence_engine.ingest_file(Path(docx_path))

    # 2. Build Tree (RAPTOR)
    raptor = RaptorEngine(client_id=client_id, storage_dir=storage_dir)
    await raptor.build_tree(evidence_engine.ledger.fragments)

    # 3. Show Results
    print("\n🔍 MUESTRA DEL ÁRBOL RAPTOR (NIVEL 1 - RESÚMENES DE SECCIÓN):")
    context = raptor.get_context_at_level(1)
    print(context)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/test_raptor.py <client_name> <docx_path>")
    else:
        # Load environment for Vertex AI
        import os

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            str(Path.home() / ".secrets" / "sa-key.json")
        )
        asyncio.run(test_raptor(sys.argv[1], sys.argv[2]))
