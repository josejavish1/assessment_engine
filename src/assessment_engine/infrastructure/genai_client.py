"""
Unified Google GenAI Client Factory & Agnostic Model Hub for Autonomuos Tier-1.
Supports direct GEMINI_API_KEY as primary auth, falling back to Vertex AI ADC.
Provides capability-based model tiering (AI_*_MODEL) decoupled from provider branding.
"""
from __future__ import annotations


import logging
import os
from enum import Enum

from google import genai

logger = logging.getLogger("assessment_engine.infrastructure.genai_client")

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "sub403o4u0q5")
LOCATION = os.environ.get("GCP_LOCATION", "global")


class ModelTier(str, Enum):
    """Define semantic inference levels for the autonomous factory."""

    REASONING = "reasoning"  # Deep reasoning / Architecture / Dialectics
    FAST = "fast"  # Standard high-speed tasks / Ingestion / Scouting
    LOCAL = "local"  # Micro-tasks / AST extraction (switchable to local model)
    IMAGE = "image"  # Visual generation and editing
    AUDIO = "audio"  # Transcription and acoustic comprehension
    VIDEO = "video"  # Temporal comprehension and video analysis
    EMBEDDING = "embedding"  # Vector representation and CAG memory


# Canonical decoupled resolution table (SSOT):
# Tier: (Primary Agnostic Variable, Optional Legacy Variable, Primary Default, Fallback Default)
_MODEL_SPECS: dict[ModelTier, tuple[str, str, str, str | None]] = {
    ModelTier.REASONING: (
        "AI_REASONING_MODEL",
        "GEMINI_PRO_MODEL",
        "gemini-4-argon",
        "gemini-3.1-pro-preview",
    ),
    ModelTier.FAST: (
        "AI_FAST_MODEL",
        "GEMINI_FLASH_MODEL",
        "gemini-3.8-flash",
        "gemini-2.5-flash",
    ),
    ModelTier.LOCAL: ("AI_LOCAL_MODEL", "LOCAL_LLM_MODEL", "gemini-3.8-flash", None),
    ModelTier.IMAGE: (
        "AI_IMAGE_MODEL",
        "GEMINI_IMAGE_MODEL",
        "imagen-3.0-generate-002",
        None,
    ),
    ModelTier.AUDIO: ("AI_AUDIO_MODEL", "GEMINI_AUDIO_MODEL", "gemini-3.8-flash", None),
    ModelTier.VIDEO: ("AI_VIDEO_MODEL", "GEMINI_VIDEO_MODEL", "gemini-3.8-flash", None),
    ModelTier.EMBEDDING: (
        "AI_EMBEDDING_MODEL",
        "GEMINI_EMBEDDING_MODEL",
        "text-embedding-004",
        None,
    ),
}


def get_model(tier: ModelTier = ModelTier.FAST) -> str:
    """Resolve canonical model identifier for the requested inference tier."""
    spec = _MODEL_SPECS.get(
        tier, ("AI_FAST_MODEL", "GEMINI_FLASH_MODEL", "gemini-flash-latest", None)
    )
    primary_var, legacy_var, default_model, _ = spec
    return os.environ.get(primary_var) or os.environ.get(legacy_var) or default_model


def get_fallback_model(model_name: str | None = None) -> str | None:
    """Returns the configured fallback model if the primary model fails or experiences rate limits."""
    if not model_name:
        return None
    for _, spec in _MODEL_SPECS.items():
        primary_var, legacy_var, default_model, fallback = spec
        active_model = (
            os.environ.get(primary_var) or os.environ.get(legacy_var) or default_model
        )
        if active_model == model_name and fallback and fallback != active_model:
            return fallback
    return None


def create_genai_client(location: str | None = None) -> genai.Client:
    """
    Creates a robust genai.Client.
    Prioritizes GEMINI_API_KEY to prevent ADC expiration errors,
    falling back to Vertex AI ADC when API key is not present.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key, http_options={"timeout": 180000})

    loc = location or LOCATION
    return genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=loc,
        http_options={"timeout": 180000},
    )
