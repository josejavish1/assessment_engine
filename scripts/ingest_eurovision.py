
import asyncio
import os
from pathlib import Path
from src.infrastructure.evidence_engine import EvidenceEngine
from src.infrastructure.raptor_engine import RaptorEngine

async def ingest_documents():
    storage_dir = Path("working/eurovision_demo_ultimate")
    client_id = "eurovision_demo_ultimate"
    
    # 1. Fragmentación (Evidence Engine)
    print("Iniciando Evidence Engine...")
    evidence_engine = EvidenceEngine(client_id=client_id, storage_dir=storage_dir)
    
    context_file = storage_dir / "contexto_eurovision_elite.docx"
    responses_file = storage_dir / "preguntas_eurovision_con_notas_v2.txt"
    
    print(f"Ingestando {context_file}...")
    evidence_engine.ingest_file(context_file)
    
    print(f"Ingestando {responses_file}...")
    evidence_engine.ingest_file(responses_file)
    
    print(f"Total fragmentos: {len(evidence_engine.ledger.fragments)}")
    
    # 2. Árbol RAG (Raptor Engine)
    print("Iniciando Raptor Engine (esto puede tardar unos minutos)...")
    raptor = RaptorEngine(client_id=client_id, storage_dir=storage_dir)
    await raptor.build_tree(evidence_engine.ledger.fragments)
    
    print("Ingesta completada. Ficheros de conocimiento generados en", storage_dir)

if __name__ == "__main__":
    asyncio.run(ingest_documents())
