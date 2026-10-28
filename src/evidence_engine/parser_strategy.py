# src/evidence_engine/parser_strategy.py

from abc import ABC, abstractmethod
from typing import Any, Dict

from .clients.document_ai_client import DocumentAIClient

class ParserStrategy(ABC):
    """Abstract base class for document parsing strategies."""

    @abstractmethod
    def parse(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Parses the content of a file and returns structured data.

        Args:
            file_content: The raw content of the file.
            mime_type: The MIME type of the file.

        Returns:
            A dictionary representing the structured data from the document.
        """
        pass

class LegacyParserStrategy(ParserStrategy):
    """A dummy implementation of the legacy sequential parser."""

    def parse(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Simulates parsing with the old system. For now, it returns a simple
        representation of the document's text.
        """
        # In a real scenario, this would involve complex text extraction logic.
        return {
            "text": file_content.decode('utf-8', errors='ignore'),
            "source": "legacy_parser",
        }

class CloudParserStrategy(ParserStrategy):
    """
    A parsing strategy that uses a cloud-based service (e.g., Google Document AI)
    to extract structured information from a document.
    """

    def __init__(self, client: DocumentAIClient):
        """
        Initializes the strategy with a Document AI client.

        Args:
            client: An instance of DocumentAIClient.
        """
        self._client = client

    def parse(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Processes the document using the Document AI client and translates the
        response into the internal data model.

        Args:
            file_content: The raw content of the file to process.
            mime_type: The MIME type of the file.

        Returns:
            A dictionary representing the structured data from Document AI.
        """
        processed_document = self._client.process_document(file_content, mime_type)
        
        # Here, we would implement the translation from the Document AI 'Document'
        # object to our internal data model. For now, we'll return a simplified
        # representation of the structured data.
        
        # This translation logic could be complex, mapping entities, tables, and
        # form fields to a consistent internal schema.
        
        return {
            "text": processed_document.text,
            "entities": [
                {"type": entity.type_, "value": entity.mention_text}
                for entity in processed_document.entities
            ],
            "source": "cloud_parser",
        }
