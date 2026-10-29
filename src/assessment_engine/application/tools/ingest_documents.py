from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
from assessment_engine.infrastructure.raptor_engine import RaptorEngine


async def run_ingestion(
    client_id: str,
    context_file: Path | None = None,
    responses_file: Path | None = None,
    storage_dir: Path | None = None,
) -> None:
    """Universal parameterized ingestion pipeline for enterprise client documents."""
    resolved_storage = storage_dir or (Path("working") / client_id)
    resolved_storage.mkdir(parents=True, exist_ok=True)

    print(f"📦 [Ingest] Inicializando Evidence Engine para cliente '{client_id}'...")
    evidence_engine = EvidenceEngine(client_id=client_id, storage_dir=resolved_storage)

    if context_file and context_file.is_file():
        print(f"📄 [Ingest] Ingestando contexto: {context_file}...")
        evidence_engine.ingest_file(context_file)
    elif context_file:
        print(f"⚠️ [Ingest] Archivo de contexto no encontrado: {context_file}")

    if responses_file and responses_file.is_file():
        print(f"📝 [Ingest] Ingestando respuestas: {responses_file}...")
        evidence_engine.ingest_file(responses_file)
    elif responses_file:
        print(f"⚠️ [Ingest] Archivo de respuestas no encontrado: {responses_file}")

    fragments_count = len(evidence_engine.ledger.fragments)
    print(f"✅ [Ingest] Total chunks extracted: {fragments_count}")

    if fragments_count > 0:
        print("🌲 [Ingest] Initializing Raptor Engine for hierarchical indexing...")
        raptor = RaptorEngine(client_id=client_id, storage_dir=resolved_storage)
        await raptor.build_tree(evidence_engine.ledger.fragments)
        print(f"🚀 [Ingest] Ingestion completed successfully at {resolved_storage}")
    else:
        print("⚠️ [Ingest] Zero chunks extracted. Skipping Raptor tree construction.")


def main() -> None:
    """CLI entrypoint for document ingestion and hierarchical knowledge graph indexing."""
    parser = argparse.ArgumentParser(
        description="Universal CLI for Document Ingestion and Raptor Indexing."
    )
    parser.add_argument(
        "--client",
        type=str,
        default=os.environ.get("ASSESSMENT_CLIENT_ID", "default"),
        help="Client identifier (e.g., redeia_v3, ivirma).",
    )
    parser.add_argument(
        "--context-file",
        type=Path,
        default=None,
        help="Path to the client context document (DOCX or TXT).",
    )
    parser.add_argument(
        "--responses-file",
        type=Path,
        default=None,
        help="Path to the interview responses file.",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default=None,
        help="Target storage directory for knowledge ledgers.",
    )

    args = parser.parse_args()
    asyncio.run(
        run_ingestion(
            client_id=args.client,
            context_file=args.context_file,
            responses_file=args.responses_file,
            storage_dir=args.storage_dir,
        )
    )


if __name__ == "__main__":
    main()
