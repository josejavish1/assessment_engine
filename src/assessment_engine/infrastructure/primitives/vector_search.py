"""
Vector Search & Semantic Embedding Engine — GEMA 80 (Tier-1 SOTA 2026).
Enables local semantic AI search and RAG retrieval directly on SQLite WAL at $0.00 cost.
Zero heavy dependencies: uses native Python math and struct for compact float32 binary embeddings.
"""

from __future__ import annotations

import datetime
import heapq
import json
import logging
import math
import os
import re
import sqlite3
import struct
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.vector_search")
WORKSPACES_DIR = Path(os.environ.get("AUTONOMUOS_WORKSPACES_DIR", str(Path(__file__).resolve().parents[2] / "workspaces")))


def normalize_l2_vector(vec: list[float]) -> list[float]:
    """Compute L2 normalized vector so cosine similarity equals fast dot product."""
    if not vec:
        return []
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return [0.0] * len(vec)
    return [round(x / norm, 6) for x in vec]


def pack_vector_blob(vec: list[float]) -> bytes:
    """Pack float array into compact binary IEEE-754 32-bit float buffer."""
    normalized = normalize_l2_vector(vec)
    return struct.pack(f"{len(normalized)}f", *normalized)


def unpack_vector_blob(blob: bytes) -> list[float]:
    """Unpack binary float buffer back to Python float list."""
    if not blob:
        return []
    count = len(blob) // 4
    return list(struct.unpack(f"{count}f", blob))


def compute_dot_product(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute dot product between two L2 normalized vectors (O(D) time)."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0
    return sum(a * b for a, b in zip(vec_a, vec_b))


class VectorSearchPrimitive(CapabilityPrimitive):
    """Vector storage and cosine similarity retrieval engine over SQLite WAL."""

    def __init__(self, workspaces_dir: Path | None = None) -> None:
        self.workspaces_dir = workspaces_dir or WORKSPACES_DIR

    @property
    def namespace(self) -> str:
        """Return the unique namespace identifier for the capability."""
        return "vector_search"

    def get_capabilities(self) -> dict[str, Any]:
        """Expose capability metadata and operations schema."""
        return {
            "version": "1.0.0",
            "metric": "cosine_similarity",
            "storage_format": "float32_binary_blob",
            "features": ["l2_normalization", "sqlite_wal_persistence", "compact_packing", "multi_collection"],
        }

    def _get_db_connection(self, slug: str) -> sqlite3.Connection:
        """Establish SQLite WAL connection and ensure vector schema exists."""
        clean_slug = re.sub(r"[^\w.-]", "", slug)
        db_path = self.workspaces_dir / clean_slug / "data" / "app.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _vector_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                record_id TEXT NOT NULL,
                text_content TEXT NOT NULL,
                embedding_blob BLOB NOT NULL,
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                UNIQUE(collection, record_id)
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vec_coll ON _vector_embeddings(collection);")
        return conn

    def index_record(
        self,
        slug: str,
        collection: str,
        record_id: str,
        text_content: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Index or upsert a text record with its vector embedding."""
        if not vector:
            raise ValueError("El vector de embedding no puede estar vacío")

        packed_blob = pack_vector_blob(vector)
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_db_connection(slug) as conn:
            conn.execute(
                """
                INSERT INTO _vector_embeddings (collection, record_id, text_content, embedding_blob, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(collection, record_id) DO UPDATE SET
                    text_content = excluded.text_content,
                    embedding_blob = excluded.embedding_blob,
                    metadata_json = excluded.metadata_json,
                    created_at = excluded.created_at;
                """,
                (collection, record_id, text_content, packed_blob, meta_str, now),
            )
            conn.commit()

        return {
            "collection": collection,
            "record_id": record_id,
            "dimension": len(vector),
            "status": "indexed",
        }

    def similarity_search(
        self,
        slug: str,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search for top-K records by cosine similarity against the query vector."""
        if not query_vector:
            return []

        norm_query = normalize_l2_vector(query_vector)
        scored_records: list[dict[str, Any]] = []

        with self._get_db_connection(slug) as conn:
            cursor = conn.execute(
                "SELECT record_id, text_content, embedding_blob, metadata_json FROM _vector_embeddings WHERE collection = ?",
                (collection,),
            )
            rows = cursor.fetchall()

        for row in rows:
            stored_vec = unpack_vector_blob(row["embedding_blob"])
            score = round(compute_dot_product(norm_query, stored_vec), 4)
            if score >= min_score:
                try:
                    meta = json.loads(row["metadata_json"])
                except Exception:
                    meta = {}
                scored_records.append(
                    {
                        "record_id": row["record_id"],
                        "text_content": row["text_content"],
                        "score": score,
                        "metadata": meta,
                    }
                )

        return heapq.nlargest(limit, scored_records, key=lambda r: r["score"])

    def delete_record(self, slug: str, collection: str, record_id: str) -> bool:
        """Delete an indexed record from a collection."""
        with self._get_db_connection(slug) as conn:
            cursor = conn.execute(
                "DELETE FROM _vector_embeddings WHERE collection = ? AND record_id = ?",
                (collection, record_id),
            )
            conn.commit()
            return cursor.rowcount > 0


vector_search_primitive = VectorSearchPrimitive()