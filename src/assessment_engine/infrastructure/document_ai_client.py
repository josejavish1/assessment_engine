"""Client for interacting with Google Cloud Document AI."""

from google.api_core.client_options import ClientOptions
from google.cloud import documentai


class DocumentAIClient:
    """A client for processing documents with Google Cloud Document AI."""

    def __init__(self, project_id: str, location: str, processor_id: str):
        """Initializes the Document AI client.

        Args:
            project_id: The Google Cloud project ID.
            location: The location of the Document AI processor (e.g., 'us').
            processor_id: The ID of the Document AI processor.
        """
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id

        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        self.client = documentai.DocumentProcessorServiceClient(client_options=opts)
        self.processor_name = self.client.processor_path(
            project_id, location, processor_id
        )

    def process_document(
        self, file_content: bytes, mime_type: str
    ) -> documentai.Document:
        """Processes a document using the configured Document AI processor.

        Args:
            file_content: The raw content of the file to process.
            mime_type: The MIME type of the file (e.g., 'application/pdf', 'image/jpeg').

        Returns:
            The processed document object from the Document AI API.
        """
        raw_document = documentai.RawDocument(
            content=file_content, mime_type=mime_type
        )

        request = documentai.ProcessRequest(
            name=self.processor_name, raw_document=raw_document
        )

        result = self.client.process_document(request=request)
        return result.document
