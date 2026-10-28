"""Unit tests for the Document AI client."""

import unittest
from unittest.mock import MagicMock, patch

from src.evidence_engine.clients.document_ai_client import DocumentAIClient


class TestDocumentAIClient(unittest.TestCase):
    """Test suite for the DocumentAIClient."""

    @patch("src.evidence_engine.clients.document_ai_client.documentai")
    def test_process_document_success(self, mock_docai_module):
        """
        Tests successful document processing.
        """
        # Arrange
        mock_client_instance = MagicMock()
        mock_docai_module.DocumentProcessorServiceClient.return_value = mock_client_instance

        project_id = "test-project"
        location = "us"
        processor_id = "test-processor"
        file_content = b"dummy pdf content"
        mime_type = "application/pdf"

        client = DocumentAIClient(project_id, location, processor_id)

        # Mock the response from the Document AI API
        mock_response = MagicMock()
        mock_response.document.text = "Processed document text."
        mock_client_instance.process_document.return_value = mock_response

        # Act
        document = client.process_document(file_content, mime_type)

        # Assert
        self.assertEqual(document.text, "Processed document text.")
        mock_client_instance.process_document.assert_called_once()

        # Check that ProcessRequest was called with the RawDocument mock
        mock_docai_module.RawDocument.assert_called_once_with(
            content=file_content, mime_type=mime_type
        )
        mock_docai_module.ProcessRequest.assert_called_once_with(
            name=client.processor_name,
            raw_document=mock_docai_module.RawDocument.return_value,
        )


if __name__ == "__main__":
    unittest.main()
