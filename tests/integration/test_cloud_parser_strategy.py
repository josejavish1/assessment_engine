import unittest
from unittest.mock import MagicMock, patch

from assessment_engine.infrastructure.evidence_engine import EvidenceEngine
from assessment_engine.infrastructure.parser_strategy import (
    CloudParserStrategy,
    LegacyParserStrategy,
)


class TestCloudParserStrategy(unittest.TestCase):
    """Integration tests for the unified EvidenceEngine parser strategies."""

    def test_uses_legacy_parser_when_feature_flag_is_false(self):
        config = {
            "feature_flags": {"evidence_engine_use_cloud_parser": False}
        }
        engine = EvidenceEngine(config=config)
        self.assertIsInstance(engine._parser_strategy, LegacyParserStrategy)

        result = engine.parse_document(b"test", "text/plain")
        self.assertEqual(result["source"], "legacy_parser")

    @patch("assessment_engine.infrastructure.evidence_engine.DocumentAIClient")
    def test_uses_cloud_parser_when_feature_flag_is_true(
        self, mock_doc_ai_client
    ):
        mock_client_instance = MagicMock()
        mock_doc_ai_client.return_value = mock_client_instance

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
        engine = EvidenceEngine(config=config)
        self.assertIsInstance(engine._parser_strategy, CloudParserStrategy)

        result = engine.parse_document(b"test content", "application/pdf")
        mock_doc_ai_client.assert_called_once_with(
            project_id="test-project",
            location="test-location",
            processor_id="test-processor",
        )
        mock_client_instance.process_document.assert_called_once_with(
            b"test content", "application/pdf"
        )
        self.assertEqual(result["source"], "cloud_parser")
        self.assertEqual(result["text"], "Processed text from cloud")


if __name__ == "__main__":
    unittest.main()
