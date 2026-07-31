import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from PyPDF2 import PdfReader

from .errors import DuplicateDocumentError, InvalidDocumentError


class DuplicateRegistry(Protocol):
    def find_by_hash(self, sha256: str) -> str | None: ...


@dataclass(frozen=True)
class ValidatedDocument:
    path: Path
    document_id: str
    sha256: str
    page_count: int


class DocumentValidator:
    def __init__(self, registry: DuplicateRegistry | None = None):
        self.registry = registry

    def validate(self, path: str | Path) -> ValidatedDocument:
        pdf_path = Path(path).resolve()
        if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
            raise InvalidDocumentError("A readable PDF file is required")
        sha256 = self._hash(pdf_path)
        if self.registry:
            existing = self.registry.find_by_hash(sha256)
            if existing:
                raise DuplicateDocumentError(existing)
        try:
            page_count = len(PdfReader(str(pdf_path)).pages)
        except Exception as exc:
            raise InvalidDocumentError(f"Invalid or corrupted PDF: {exc}") from exc
        if page_count < 1:
            raise InvalidDocumentError("PDF contains no pages")
        return ValidatedDocument(
            path=pdf_path,
            document_id=f"doc_{uuid4().hex[:16]}",
            sha256=sha256,
            page_count=page_count,
        )

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
