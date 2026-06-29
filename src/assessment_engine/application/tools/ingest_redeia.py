import asyncio
from pathlib import Path

from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
from assessment_engine.infrastructure.raptor_engine import RaptorEngine


async def ingest_documents():
    import os

    client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "redeia_v3")
    storage_dir = Path("working") / client_id / "redeia"

    # Asegurar que el directorio de almacenamiento existe
    storage_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fragmentation (Evidence Engine)
    print("Iniciando Evidence Engine...")
    evidence_engine = EvidenceEngine(client_id=client_id, storage_dir=storage_dir)

    context_file = storage_dir / "context_redeia.docx"
    responses_file = storage_dir / "preguntas_redeia_con_notas.txt"

    print(f"Ingestando {context_file}...")
    evidence_engine.ingest_file(context_file)

    print(f"Ingestando {responses_file}...")
    evidence_engine.ingest_file(responses_file)

    print(f"Total fragmentos: {len(evidence_engine.ledger.fragments)}")

    # 2. RAG Tree (Raptor Engine)
    print("Iniciando Raptor Engine (esto puede tardar unos minutos)...")
    raptor = RaptorEngine(client_id=client_id, storage_dir=storage_dir)
    await raptor.build_tree(evidence_engine.ledger.fragments)

    print("Ingesta completada. Ficheros de conocimiento generados en", storage_dir)


if __name__ == "__main__":
    asyncio.run(ingest_documents())
