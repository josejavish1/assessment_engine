# src/evidence_engine/main.py

import json
from typing import Any, Dict

from .clients.document_ai_client import DocumentAIClient
from .parser_strategy import (
    ParserStrategy,
    LegacyParserStrategy,
    CloudParserStrategy,
)

class EvidenceEngine:
    """
    The main component for processing documents and extracting evidence.
    It uses a configurable parsing strategy to adapt to different document types
    and structures.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the EvidenceEngine with a given configuration.

        Args:
            config: A dictionary containing the engine's configuration,
                    including feature flags and client settings.
        """
        self._config = config
        self._parser_strategy = self._create_parser_strategy()

    def _create_parser_strategy(self) -> ParserStrategy:
        """
        Creates the appropriate parser strategy based on the feature flag
        in the configuration.
        """
        use_cloud_parser = self._config.get("feature_flags", {}).get(
            "evidence_engine_use_cloud_parser", False
        )

        if use_cloud_parser:
            doc_ai_config = self._config.get("document_ai", {})
            client = DocumentAIClient(
                project_id=doc_ai_config.get("project_id"),
                location=doc_ai_config.get("location"),
                processor_id=doc_ai_config.get("processor_id"),
            )
            return CloudParserStrategy(client)
        else:
            return LegacyParserStrategy()

    def parse_document(
        self, file_content: bytes, mime_type: str
    ) -> Dict[str, Any]:
        """
        Parses a document using the configured strategy.

        Args:
            file_content: The raw content of the file.
            mime_type: The MIME type of the file.

        Returns:
            The structured data extracted from the document.
        """
        return self._parser_strategy.parse(file_content, mime_type)

def load_config(path: str) -> Dict[str, Any]:
    """A simple utility to load a JSON configuration file."""
    with open(path, "r") as f:
        return json.load(f)

# Example usage (for demonstration purposes):
if __name__ == "__main__":
    # Load configuration from a file
    config = load_config("engine_config/runtime_manifest.json")

    # Initialize the engine
    engine = EvidenceEngine(config)

    # Example: Parse a dummy text file
    dummy_content = b"This is a test document."
    result = engine.parse_document(dummy_content, "text/plain")

    print(f"Parsing result (source: {result.get('source')}):")
    print(result)
