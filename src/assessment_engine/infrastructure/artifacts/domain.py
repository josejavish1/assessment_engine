"""Domain models and exceptions for Deterministic Artifact Registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DocumentType(str, Enum):
    """Authoritative document categories produced by the assessment engine."""

    EXECUTIVE_REPORT = "exec_report"
    TECHNICAL_ANNEX = "tech_annex"
    TECHNICAL_BLUEPRINT = "tech_blueprint"
    FINANCIAL_MODEL = "fin_model"
    REMEDIATION_PLAN = "remediation_plan"
    RAW_DATASET = "raw_data"
    PRESENTATION_DECK = "pitch_deck"


class ArtifactFormat(str, Enum):
    """Permitted storage and deliverable file formats."""

    DOCX = "docx"
    PDF = "pdf"
    XLSX = "xlsx"
    JSON = "json"
    PPTX = "pptx"
    CSV = "csv"


class ArtifactError(Exception):
    """Base exception for all artifact registry operations."""


class ArtifactNotFoundError(ArtifactError):
    """Raised when an artifact cannot be located in storage or manifest."""


class ArtifactIntegrityError(ArtifactError):
    """Raised when physical file checksum does not match registered manifest hash."""


class InvalidArtifactTokenError(ArtifactError):
    """Raised when an input token fails strict POSIX sanitization."""


@dataclass(frozen=True)
class ArtifactContext:
    """Immutable metadata context defining a unique logical deliverable."""

    tenant_id: str
    assessment_id: str
    period: str
    domain_unit_id: str
    doc_type: DocumentType
    locale: str = "en"
    extension: ArtifactFormat = ArtifactFormat.DOCX


@dataclass(frozen=True)
class ArtifactVersionRecord:
    """Immutable metadata record for a single physical version of an artifact."""

    version: int
    physical_filename: str
    relative_path: str
    sha256_full: str
    size_bytes: int
    generated_at_utc: str
    generator_engine: str
    presentation_metadata: dict[str, Any] = field(default_factory=dict)
