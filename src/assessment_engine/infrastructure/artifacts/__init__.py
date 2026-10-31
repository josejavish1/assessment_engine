"""Deterministic Artifact Registry and Path Resolution Module (RFC-023).

Provides canonical POSIX file naming, cryptographic hashing, atomic manifest management,
and late-binding commercial presentation names for all assessment deliverables.
"""

from __future__ import annotations

from assessment_engine.infrastructure.artifacts.domain import (
    ArtifactContext,
    ArtifactFormat,
    ArtifactIntegrityError,
    ArtifactNotFoundError,
    ArtifactVersionRecord,
    DocumentType,
    InvalidArtifactTokenError,
)
from assessment_engine.infrastructure.artifacts.presentation import PresentationFilenameBuilder
from assessment_engine.infrastructure.artifacts.registry import ArtifactRegistry
from assessment_engine.infrastructure.artifacts.resolver import ArtifactPathResolver

__all__ = [
    "ArtifactContext",
    "ArtifactFormat",
    "ArtifactIntegrityError",
    "ArtifactNotFoundError",
    "ArtifactPathResolver",
    "ArtifactRegistry",
    "ArtifactVersionRecord",
    "DocumentType",
    "InvalidArtifactTokenError",
    "PresentationFilenameBuilder",
]
