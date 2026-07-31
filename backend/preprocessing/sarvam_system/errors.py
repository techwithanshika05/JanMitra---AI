class DocumentProcessingError(RuntimeError):
    """Base error for document processing failures."""


class InvalidDocumentError(DocumentProcessingError):
    """The uploaded file is not a valid supported PDF."""


class DuplicateDocumentError(DocumentProcessingError):
    def __init__(self, document_id: str):
        super().__init__(f"Document already exists: {document_id}")
        self.document_id = document_id


class ExternalProcessorError(DocumentProcessingError):
    """Sarvam or a fallback processor failed."""
