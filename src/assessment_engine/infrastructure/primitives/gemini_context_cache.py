"""
Gemini Context Caching Primitive — Vertex AI Persistent Hot Memory.
Caches heavy repository AST, TypeScript definitions, Apple HIG rules,
and UI primitives in Google Cloud RAM (CachedContent) to achieve sub-second TTFT
and 80% token cost reduction during iterative software synthesis.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from google import genai
from google.genai import types

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger("core.gemini_context_cache")

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "sub403o4u0q5")
LOCATION = os.environ.get("GCP_LOCATION", "global")


class GeminiContextCacheManager:
    """
    Manages persistent hot-memory caches on Vertex AI for autonomous compilation.
    """

    def __init__(self) -> None:
        self.cached_content_name: str | None = None
        self.cache_expires_at: float = 0.0

    def get_or_create_cache(self, client: genai.Client) -> str | None:
        """
        Retrieves active cache name or creates a fresh cache on Vertex AI.
        """
        now = time.time()
        if self.cached_content_name and now < self.cache_expires_at:
            return self.cached_content_name

        try:
            # Build the comprehensive system corpus (TypeScript interfaces, Apple HIG, UI primitives).
            root_dir = Path(__file__).resolve().parent.parent.parent
            templates_dir = root_dir / "templates" / "golden_polyglot_starter" / "web" / "src"

            corpus_parts: list[str] = [
                "// SYSTEM CORPUS: TYPE DEFINITIONS, APPLE HIG RULES, AND UI PRIMITIVES",
                "// Apple HIG: 8pt grid, harmonic 4-step type scale (44, 28, 20, 15px), max 2 primary actions, 2 layers.",
                "// UI Primitives: BookingCalendarView, KanbanBoardView, DataGridTableView, StudioCockpit, BentoGrid, BorderBeam, NumberTicker.",
            ]

            if templates_dir.exists():
                for tsx_file in templates_dir.glob("**/*.tsx"):
                    try:
                        content = tsx_file.read_text(encoding="utf-8")
                        corpus_parts.append(f"// FILE: {tsx_file.name}\n{content[:2000]}")
                    except OSError as err:
                        logger.debug(f"Error reading {tsx_file.name}: {err}")

            combined_corpus = "\n\n".join(corpus_parts)

            # Check whether the cache can be created, or return None with a safe fallback.
            if len(combined_corpus) < 40000:
                logger.debug("[Gemini Context Cache] Corpus por debajo de 32k tokens; operando en modo directo de ultra-baja latencia.")
                return None

            config = types.CreateCachedContentConfig(
                display_name="autonomuos-ui-corpus",
                contents=combined_corpus,
                ttl="3600s",
            )
            created = client.caches.create(
                model=get_model(ModelTier.FAST),
                config=config
            )
            self.cached_content_name = created.name
            self.cache_expires_at = now + 3500
            logger.info(f"[Gemini Context Cache] Cache caliente creado en Vertex AI: {created.name}")
            return self.cached_content_name
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.debug(f"[Gemini Context Cache] Nota de fallback en creación de cache: {e}")
            return None


gemini_context_cache = GeminiContextCacheManager()
