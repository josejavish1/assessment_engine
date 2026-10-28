# tests/integration/evidence_engine/test_evidence_engine.py

import unittest
from unittest.mock import MagicMock, patch

from src.evidence_engine.main import EvidenceEngine
from src.evidence_engine.parser_strategy import (
    LegacyParserStrategy,
    CloudParserStrategy,
)

class TestEvidenceEngine(unittest.TestCase):
    """Integration tests for the EvidenceEngine."""

    def test_uses_legacy_parser_when_feature_flag_is_false(self):
        """
        Verify that the engine uses the LegacyParserStrategy when the
        feature flag is disabled.
        """
        config = {
            "feature_flags": {"evidence_engine_use_cloud_parser": False}
        }
        engine = EvidenceEngine(config)

        self.assertIsInstance(engine._parser_strategy, LegacyParserStrategy)

        # Test the parsing flow
        result = engine.parse_document(b"test", "text/plain")
        self.assertEqual(result["source"], "legacy_parser")

    @patch("src.evidence_engine.main.DocumentAIClient")
    def test_uses_cloud_parser_when_feature_flag_is_true(self, mock_doc_ai_client):
        """
        Verify that the engine uses the CloudParserStrategy when the
        feature flag is enabled, and that the DocumentAIClient is called.
        """
        # Mock the DocumentAIClient to avoid actual API calls
        mock_client_instance = MagicMock()
        mock_doc_ai_client.return_value = mock_client_instance
        
        # Mock the response from the client's process_document method
        mock_processed_doc = MagicMock()
        mock_processed_doc.text = "Processed text from cloud"
        mock_processed_doc.entities = []
        mock_client_instance.process_document.return_value = mock_processed_doc

        config = {
            "feature_flags": {"evidence_engine_use_cloud_parser": True},
            "document_ai": {
                "project_id": "test-project",
                "location": "test-location",
                "processor_id": "test-processor",
            },
        }
        engine = EvidenceEngine(config)

        self.assertIsInstance(engine._parser_strategy, CloudParserStrategy)

        # Test the parsing flow
        result = engine.parse_document(b"test content", "application/pdf")

        # Verify that the client was initialized and called correctly
        mock_doc_ai_client.assert_called_once_with(
            project_id="test-project",
            location="test-location",
            processor_id="test-processor",
        )
        mock_client_instance.process_document.assert_called_once_with(
            b"test content", "application/pdf"
        )

        # Verify the result is from the cloud parser
        self.assertEqual(result["source"], "cloud_parser")
        self.assertEqual(result["text"], "Processed text from cloud")

if __name__ == "__main__":
    unittest.main()
