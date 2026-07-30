"""Executable Sarvam-to-JanMitra document processing pipeline.

This module owns orchestration only.  Sarvam's transport schema remains inside
``sarvam_system`` and the public result is converted to the existing
``preprocessing.document_normalizer`` dataclasses so the current metadata
builder, chunker and RAG ingestion path do not need a second schema.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PyPDF2 import PdfReader, PdfWriter

from ..document_normalizer import (
    DocumentBlock as ExistingDocumentBlock,
    DocumentPage as ExistingDocumentPage,
    NormalizedDocument as ExistingNormalizedDocument,
)
from .artifacts import ArtifactStore, ElementRouter, PageRegionCropper
from .documents import Artifact, DocumentBlock, NormalizedDocument
from .normalizer import SarvamOutputNormalizer
from .sarvam import SarvamJobManager, SarvamResult
from .splitter import AdaptivePdfSplitter, PdfChunk
from .validator import DocumentValidator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineConfig:
    api_key: str
    language: str = "en-IN"
    output_format: str = "md"
    max_pages_per_job: int = 10
    max_chunk_bytes: int = 20_000_000
    poll_interval: int = 5
    timeout: int = 600
    retries: int = 3
    cleanup_temp: bool = True
    artifact_output_dir: Path | None = None


class DocumentPipeline:
    """Run validation -> splitting -> Sarvam -> normalization -> artifacts."""

    def __init__(self, config: PipelineConfig, client: Any | None = None):
        self.config = config
        self.validator = DocumentValidator()
        self.splitter = AdaptivePdfSplitter(
            config.max_pages_per_job,
            config.max_chunk_bytes,
        )
        self.normalizer = SarvamOutputNormalizer()
        self.manager = SarvamJobManager(
            api_key=config.api_key,
            language=config.language,
            output_format=config.output_format,
            poll_interval=config.poll_interval,
            timeout=config.timeout,
            retries=config.retries,
            client=client,
        )

    def process(
        self,
        uploaded_pdf: str | Path,
        page_numbers: Iterable[int] | None = None,
    ) -> ExistingNormalizedDocument:
        validated = self.validator.validate(uploaded_pdf)
        selected = self._validate_selected_pages(page_numbers, validated.page_count)
        work_root = Path(tempfile.mkdtemp(prefix="janmitra_sarvam_"))

        try:
            if selected is None:
                chunks = self.splitter.split(validated.path, work_root / "chunks")
            else:
                chunks = self._selected_page_chunks(
                    validated.path,
                    selected,
                    work_root / "chunks",
                )

            results = self._process_chunks(chunks, work_root / "sarvam")
            internal = self.normalizer.normalize(
                results,
                validated.document_id,
                validated.path.name,
                validated.sha256,
            )
            artifacts = self._create_artifacts(internal, validated.path)
            return self._to_existing_schema(
                internal,
                artifacts,
                selected_pages=selected,
            )
        finally:
            if self.config.cleanup_temp:
                shutil.rmtree(work_root, ignore_errors=True)

    def _process_chunks(
        self,
        chunks: list[PdfChunk],
        output_dir: Path,
    ) -> list[SarvamResult]:
        results: list[SarvamResult] = []
        for chunk in chunks:
            try:
                results.append(self.manager.process(chunk, output_dir))
            except Exception:
                smaller = self.splitter.split_failed_chunk(
                    chunk,
                    output_dir / "retry",
                )
                if len(smaller) == 1 and smaller[0].path == chunk.path:
                    raise
                for retry_chunk in smaller:
                    results.append(self.manager.process(retry_chunk, output_dir))
        return results

    def _create_artifacts(
        self,
        document: NormalizedDocument,
        source_pdf: Path,
    ) -> list[Artifact]:
        if self.config.artifact_output_dir is None:
            return []
        store = ArtifactStore(
            self.config.artifact_output_dir,
            document.document_id,
        )
        router = ElementRouter(store, PageRegionCropper(source_pdf))
        artifacts: list[Artifact] = []
        for page in document.pages:
            for block in page.blocks:
                try:
                    artifact = router.route(block)
                except Exception as exc:
                    # A malformed crop must not discard otherwise useful OCR.
                    block.metadata["artifact_error"] = str(exc)
                    logger.warning(
                        "Artifact generation failed for %s: %s",
                        block.block_id,
                        exc,
                    )
                    continue
                if artifact is not None:
                    if artifact.relative_path:
                        artifact.metadata["absolute_path"] = str(
                            store.safe_path(artifact.relative_path)
                        )
                    preview_path = artifact.metadata.get("preview_path")
                    if preview_path:
                        artifact.metadata["absolute_preview_path"] = str(
                            store.safe_path(str(preview_path))
                        )
                    artifacts.append(artifact)
        return artifacts

    @staticmethod
    def _to_existing_schema(
        document: NormalizedDocument,
        artifacts: list[Artifact],
        selected_pages: list[int] | None,
    ) -> ExistingNormalizedDocument:
        artifact_by_block = {artifact.block_id: artifact for artifact in artifacts}
        created_at = datetime.now(timezone.utc).isoformat()
        pages: list[ExistingDocumentPage] = []

        for page in sorted(document.pages, key=lambda item: item.page_number):
            blocks: list[ExistingDocumentBlock] = []
            for block in sorted(page.blocks, key=lambda item: item.reading_order):
                artifact = artifact_by_block.get(block.block_id)
                image_path = None
                if artifact and artifact.media_type == "image/png":
                    image_path = (
                        artifact.metadata.get("absolute_path")
                        or artifact.relative_path
                    )
                elif artifact:
                    image_path = (
                        artifact.metadata.get("absolute_preview_path")
                        or artifact.metadata.get("preview_path")
                        or None
                    )

                blocks.append(
                    ExistingDocumentBlock(
                        page=page.page_number,
                        layout=block.element_type.value,
                        text=DocumentPipeline._canonical_block_text(block, artifact),
                        confidence=(
                            float(block.confidence)
                            if block.confidence is not None
                            else 1.0
                        ),
                        reading_order=block.reading_order,
                        coordinates=(
                            {
                                "x1": block.bounding_box.x1,
                                "y1": block.bounding_box.y1,
                                "x2": block.bounding_box.x2,
                                "y2": block.bounding_box.y2,
                            }
                            if block.bounding_box
                            else {}
                        ),
                        image_path=image_path,
                    )
                )
            pages.append(
                ExistingDocumentPage(
                    page_number=page.page_number,
                    width=int(page.width or 0),
                    height=int(page.height or 0),
                    created_at=created_at,
                    blocks=blocks,
                )
            )

        artifact_manifest = [
            artifact.model_dump(mode="json")
            for artifact in artifacts
        ]
        metadata = {
            **document.metadata,
            "processor": "sarvam_system",
            "document_id": document.document_id,
            "sha256": document.sha256,
            "artifact_contract": {
                "text": "text/markdown",
                "table": "text/html",
                "chart_graph": "text/html+application/json+optional_image/png",
                "image": "image/png",
                "metadata": "application/json",
            },
            "artifacts": artifact_manifest,
        }
        if selected_pages is not None:
            metadata["processed_pages"] = selected_pages
        return ExistingNormalizedDocument(
            source_file=document.source_file,
            pages=pages,
            metadata=metadata,
        )

    @staticmethod
    def _canonical_block_text(
        block: DocumentBlock,
        artifact: Artifact | None,
    ) -> str:
        # Tables remain HTML as requested; chart HTML/specs stay in the
        # artifact manifest while safe searchable labels remain in block text.
        if artifact and block.element_type.value == "table" and artifact.content:
            return artifact.content
        if artifact and artifact.embedding_text:
            return artifact.embedding_text
        return block.text.strip()

    @staticmethod
    def _validate_selected_pages(
        page_numbers: Iterable[int] | None,
        page_count: int,
    ) -> list[int] | None:
        if page_numbers is None:
            return None
        selected = sorted({int(page) for page in page_numbers})
        invalid = [page for page in selected if page < 1 or page > page_count]
        if invalid:
            raise ValueError(f"Invalid PDF page number(s): {invalid}")
        return selected

    @staticmethod
    def _selected_page_chunks(
        source: Path,
        selected: list[int],
        output_dir: Path,
    ) -> list[PdfChunk]:
        """Create one-page transport chunks so sparse original numbers survive."""
        output_dir.mkdir(parents=True, exist_ok=True)
        reader = PdfReader(str(source))
        chunks: list[PdfChunk] = []
        for index, page_number in enumerate(selected, 1):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_number - 1])
            path = output_dir / f"{source.stem}.selected-p{page_number}.pdf"
            with path.open("wb") as handle:
                writer.write(handle)
            chunks.append(
                PdfChunk(
                    chunk_number=index,
                    start_page=page_number,
                    end_page=page_number,
                    path=path,
                )
            )
        return chunks
