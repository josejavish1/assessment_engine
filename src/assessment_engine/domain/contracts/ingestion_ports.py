"""Ingestion and Normalization Domain Ports (RFC 082).

Defines the Abstract Base Classes (Ports) for raw transcript ingestion,
empirical data parsing, phonetic entity resolution, and epistemic ledger synthesis.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from assessment_engine.domain.schemas.epistemic_ledger import (
    EpistemicFragment,
    EpistemicLedger,
    NormalizedUtterance,
    RawUtterance,
)


class ITranscriptParserPort(ABC):
    """Port for parsing unstructured raw interview transcripts into ordered utterances."""

    @abstractmethod
    def parse_transcript(self, file_path: Path) -> List[RawUtterance]:
        """Extracts structured, sequential utterances from a raw transcript file (.docx, .vtt, .txt).

        Args:
            file_path: Filesystem path to the transcript artifact.

        Returns:
            A list of sequentially indexed RawUtterance instances.
        """
        ...


class IEmpiricalDataParserPort(ABC):
    """Port for parsing structured empirical data (questionnaires, telemetry dumps)."""

    @abstractmethod
    def parse_empirical_file(self, file_path: Path) -> List[EpistemicFragment]:
        """Parses structured data (.xlsx, .csv, .txt) into atomic epistemic fragments with cell/row coordinates.

        Args:
            file_path: Filesystem path to the empirical telemetry or survey artifact.

        Returns:
            A list of EpistemicFragment instances with exact provenance metadata.
        """
        ...


class IPhoneticResolverPort(ABC):
    """Port for resolving Speech-to-Text acoustic corruptions into canonical enterprise entities."""

    @abstractmethod
    def normalize_utterance(
        self,
        utterance: RawUtterance,
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> NormalizedUtterance:
        """Resolves STT artifacts in a single utterance using dynamic phonetic/semantic models.

        Args:
            utterance: Raw utterance with potential speech-to-text corruptions.
            runtime_context: Optional tenant metadata (known systems, locations, partners).

        Returns:
            NormalizedUtterance with clean text and audit trail of resolved entities.
        """
        ...

    @abstractmethod
    def normalize_batch(
        self,
        utterances: List[RawUtterance],
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> List[NormalizedUtterance]:
        """Normalizes a stream of utterances in batches for maximum throughput."""
        ...


class IEpistemicSynthesizerPort(ABC):
    """Port for decomposing statements into atomic facts and reconciling multi-modal ground truth."""

    @abstractmethod
    def synthesize_ledger(
        self,
        client_id: str,
        normalized_utterances: List[NormalizedUtterance],
        empirical_fragments: List[EpistemicFragment],
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> EpistemicLedger:
        """Merges interview assertions and empirical test responses into the reconciled EpistemicLedger.

        Args:
            client_id: Unique client identifier.
            normalized_utterances: Cleaned conversational dialogue turns.
            empirical_fragments: Structured questionnaire or telemetry facts.
            runtime_context: Optional tenant contextual configurations.

        Returns:
            An immutable, cryptographic EpistemicLedger establishing verified Ground Truth.
        """
        ...
