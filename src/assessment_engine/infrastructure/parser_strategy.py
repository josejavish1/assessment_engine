"""Strategy pattern for document parsing strategies."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from assessment_engine.infrastructure.document_ai_client import DocumentAIClient


class ParserStrategy(ABC):
    """Abstract base class for document parsing strategies."""

    @abstractmethod
    def parse(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """Parses the content of a file and returns structured data."""
        pass


class LegacyParserStrategy(ParserStrategy):
    """Fallback implementation of the sequential parser."""

    def parse(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        return {
            "text": file_content.decode("utf-8", errors="ignore"),
            "source": "legacy_parser",
        }


class CloudParserStrategy(ParserStrategy):
    """A parsing strategy that uses Google Document AI to extract structured layout and tables."""

    def __init__(self, client: DocumentAIClient):
        self._client = client

    def parse(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        processed_document = self._client.process_document(
            file_content, mime_type
        )
        return {
            "text": getattr(processed_document, "text", ""),
            "entities": [
                {"type": entity.type_, "value": entity.mention_text}
                for entity in getattr(processed_document, "entities", [])
            ],
            "source": "cloud_parser",
        }
