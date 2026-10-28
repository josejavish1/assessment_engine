import asyncio
import os
from pathlib import Path

from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
from assessment_engine.infrastructure.raptor_engine import RaptorEngine


async def ingest_documents():
    client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "molins")
    storage_dir = Path("working") / client_id / "molins"
    storage_dir.mkdir(parents=True, exist_ok=True)

    source_dir = Path("source_docs") / "molins"

    print("Iniciando Evidence Engine para Molins...")
    evidence_engine = EvidenceEngine(client_id=client_id, storage_dir=storage_dir)

    context_docx = source_dir / "Assessment_Contexto_Molins.docx"
    preguntas_xlsx = (
        source_dir / "Preguntas Fast Assessment Molins contestadas cliente.xlsx"
    )
    respuestas_txt = source_dir / "261014 Respuestas Test Molins.txt"

    for src_file in [context_docx, preguntas_xlsx, respuestas_txt]:
        if src_file.exists():
            print(f"Ingestando {src_file}...")
            count = evidence_engine.ingest_file(src_file)
            print(f"  -> {count} nuevos fragmentos añadidos.")
        else:
            print(f"⚠️ Archivo no encontrado: {src_file}")

    print(f"Total fragmentos en Vault: {len(evidence_engine.ledger.fragments)}")

    # 2. RAG Tree (Raptor Engine)
    print("Iniciando Raptor Engine...")
    raptor = RaptorEngine(client_id=client_id, storage_dir=storage_dir)
    await raptor.build_tree(evidence_engine.ledger.fragments)

    print("Ingesta completada. Ficheros de conocimiento generados en", storage_dir)


if __name__ == "__main__":
    asyncio.run(ingest_documents())
