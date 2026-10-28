"""
Manage memory bank operations and Vertex AI context caching. Decoupled from adk_lean_factory.py via the Strangler Fig pattern. Provides:
- VertexContextCacheManager: Context KV cache in Gemini Vertex AI for cross-session memory.
- query_memory_bank: Lexical, semantic, and axiom graph search over Sovereign Radar.
- contribute_to_memory_bank: Atomic persistence of learned patterns and antipatterns.
- google_web_search: Real-time web search grounding via Vertex AI.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger("assessment_engine.infrastructure.foundry.memory_bank_cag")

# Configure sovereign memory settings and paths.
PROJECT_ID = os.environ.get("VERTEX_PROJECT_ID", "adk-lean-factory-prod")
LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
MEMORY_BANK_DIR = Path(os.environ.get("MEMORY_BANK_DIR", Path.cwd() / "memory_bank"))
SOVEREIGN_RADAR_DB_PATH = Path(
    os.environ.get(
        "SOVEREIGN_RADAR_DB_PATH",
        Path.home() / "Documents" / "Sovereign_System_Radar" / "dist" / "sovereign_system_radar.db"
    )
)


class VertexContextCacheManager:
    """
    Tier-1 Vertex AI Context Caching Manager for Cross-Project Memory Banks.
    Precaches architecture_patterns.json, antipatterns_and_pitfalls.json, and technology_radar.json
    into Gemini's KV cache, reducing input token costs by up to 75% and accelerating inference.
    """
    _cached_resource_name: str | None = None
    _last_cache_time: float = 0.0
    CACHE_TTL_SECONDS: int = 7200  # 2 hours
    DISPLAY_NAME: str = "autonomuos_memory_bank_cag"
    MODEL_NAME: str = get_model(ModelTier.REASONING)

    @classmethod
    def get_memory_bank_corpus(cls) -> str:
        """Assembles the full structured text corpus of the cross-project memory bank."""
        corpus_parts = ["[CROSS-PROJECT MEMORY BANK - CAG CONTEXT]"]
        for fname in ["architecture_patterns.json", "antipatterns_and_pitfalls.json", "technology_radar.json"]:
            fpath = MEMORY_BANK_DIR / fname
            if fpath.exists():
                try:
                    corpus_parts.append(f"\n--- {fname} ---\n" + fpath.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError) as ex:
                    logger.debug(f"Cache corpus read note for {fname}: {ex}")
        return "\n".join(corpus_parts)

    @classmethod
    def _create_vertex_cache(cls, client: genai.Client, corpus: str, now: float) -> str | None:
        try:
            created = client.caches.create(
                model=cls.MODEL_NAME,
                config=types.CreateCachedContentConfig(contents=corpus, display_name=cls.DISPLAY_NAME, ttl=f"{cls.CACHE_TTL_SECONDS}s")
            )
            cls._cached_resource_name = getattr(created, "name", None)
            cls._last_cache_time = now
            logger.info(f"[Context Cache] Successfully created Vertex AI Context Cache: {cls._cached_resource_name}")
            return cls._cached_resource_name
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as cache_ex:
            logger.debug(f"[Context Cache] Standard fallback active: {cache_ex}")
            return None

    @classmethod
    def _find_active_cache(cls, client: genai.Client) -> str | None:
        try:
            for c in client.caches.list():
                if getattr(c, "display_name", None) == cls.DISPLAY_NAME:
                    return getattr(c, "name", None)
        except Exception as list_ex:
            logger.debug(f"Cache list note: {list_ex}")
        return None

    @classmethod
    def get_or_create_cache(cls, client: genai.Client | None = None) -> str | None:
        """Retrieves or initializes a Vertex AI CachedContent resource."""
        now = time.time()
        if cls._cached_resource_name and (now - cls._last_cache_time < cls.CACHE_TTL_SECONDS - 300):
            return cls._cached_resource_name
        corpus = cls.get_memory_bank_corpus()
        if not corpus or len(corpus) < 100: return None
        if client is None:
            try: client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
            except Exception as ex:
                logger.debug(f"Vertex client init note for cache: {ex}")
                return None
        try:
            if hasattr(client, "caches"):
                cached_name = cls._find_active_cache(client)
                if cached_name:
                    cls._cached_resource_name = cached_name
                    cls._last_cache_time = now
                    logger.info(f"[Context Cache] Reusing active memory bank cache: {cls._cached_resource_name}")
                    return cls._cached_resource_name
                return cls._create_vertex_cache(client, corpus, now)
        except Exception as cache_ex:
            logger.debug(f"[Context Cache] Standard fallback active: {cache_ex}")
        return None


def _query_radar_db(query: str, combined: list[dict[str, Any]]) -> None:
    with sqlite3.connect(str(SOVEREIGN_RADAR_DB_PATH)) as rconn:
        rcur = rconn.cursor()
        stopwords = {"how", "to", "a", "an", "the", "in", "on", "for", "with", "by", "at", "from", "build", "create", "implement", "make", "write", "develop", "design", "do", "is", "are", "what", "which", "where", "when", "why", "can", "should", "using", "use", "into", "about", "more", "some", "any", "system", "como", "cómo", "de", "del", "la", "el", "los", "las", "un", "una", "unos", "unas", "en", "para", "por", "con", "sin", "sobre", "entre", "hacia", "desde", "crear", "hacer", "construir", "disenar", "diseñar", "implementar", "desarrollar", "que", "qué", "cual", "cuál", "donde", "dónde", "cuando", "cuándo", "quien", "quién", "es", "son", "este", "esta", "estos", "estas", "sistema", "mas", "más", "pero"}
        candidates = [w for w in re.findall(r"[A-Za-z0-9_áéíóúÁÉÍÓÚñÑ-]+", query.lower()) if w not in stopwords and len(w) >= 3]
        if candidates:
            top_terms = sorted(candidates, key=len, reverse=True)[:2]
            for search_term in top_terms:
                sql = "SELECT nombre, abstraccion_funcional, aplicacion_plataforma FROM axioma WHERE nombre LIKE ? OR abstraccion_funcional LIKE ? LIMIT 2;"
                like_term = f"%{search_term}%"
                rcur.execute(sql, (like_term, like_term))
                for row in rcur.fetchall():
                    combined.append({"source": "sovereign_radar_axiom", "name": str(row[0] or ""), "principle": str(row[1] or "")[:250], "platform_application": str(row[2] or "")[:250]})

def _fetch_sovereign_radar_axioms(query: str) -> list[dict[str, Any]]:
    combined = []
    if SOVEREIGN_RADAR_DB_PATH.exists():
        try:
            _query_radar_db(query, combined)
        except (sqlite3.Error, OSError) as e:
            logger.debug(f"Radar graph query error: {e}")
    return combined

def query_memory_bank(query: str) -> str:
    """Queries cross-project design patterns, antipatterns, and the Sovereign Radar Axiom Knowledge Graph."""
    combined = []
    for fname in ["architecture_patterns.json", "antipatterns_and_pitfalls.json", "technology_radar.json"]:
        fpath = MEMORY_BANK_DIR / fname
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    combined.extend(json.load(f))
            except (OSError, json.JSONDecodeError) as e:
                logger.debug(f"Memory read error on {fname}: {e}")

    combined.extend(_fetch_sovereign_radar_axioms(query))

    if not combined:
        return "No matching patterns found in memory bank."

    query_words = set(query.lower().split())
    matched = [item for item in combined if any(w in json.dumps(item).lower() for w in query_words)]
    results = matched if matched else combined[:3]
    return json.dumps(results, indent=2, ensure_ascii=False)


def contribute_to_memory_bank(category: str, title: str, summary: str) -> str:
    """Stores a learned architectural pattern or resolved antipattern into the permanent cross-project memory bank."""
    MEMORY_BANK_DIR.mkdir(parents=True, exist_ok=True)
    filename = "antipatterns_and_pitfalls.json" if "anti" in category.lower() else "architecture_patterns.json"
    filepath = MEMORY_BANK_DIR / filename

    entries = []
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    entries = loaded
                elif isinstance(loaded, dict):
                    entries = loaded.get("patterns", loaded.get("items", []))
        except (OSError, json.JSONDecodeError):
            entries = []

    entries.append({
        "title": title,
        "summary": summary,
        "timestamp": time.time()
    })

    try:
        temp_filepath = filepath.with_suffix(".tmp")
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        temp_filepath.replace(filepath)
        return f"SUCCESS: Memory bank updated with entry '{title}'."
    except (OSError, json.JSONDecodeError) as e:
        return f"ERROR: Failed to save memory entry: {e}"


async def google_web_search(query: str) -> str:
    """Searches live documentation and libraries using Vertex AI Google Search Grounding asynchronously."""
    try:
        search_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        resp = await search_client.aio.models.generate_content(
            model=get_model(ModelTier.FAST),
            contents=f"Conduct deep technical research on current standards and official documentation for: {query}",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return resp.text or "No relevant search results."
    except (RuntimeError, ValueError, OSError) as e:
        return f"SEARCH_ERROR: {e!s}"
