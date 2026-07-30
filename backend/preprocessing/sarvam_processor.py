"""
===============================================================================
Production Ready Sarvam Document Processor
-------------------------------------------------------------------------------

Author  : Manya Agarwal
Project : JanMitra AI
Purpose :
    Upload complex PDFs to Sarvam Document Intelligence,
    automatically split large PDFs,
    download structured JSON output,
    normalize it into project format,
    and feed the RAG ingestion pipeline.

===============================================================================
"""

from __future__ import annotations

import os
import json
import time
import shutil
import logging
import tempfile

from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter

from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError

import sys

BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from preprocessing.document_normalizer import (
    DocumentPage,
    NormalizedDocument,
    document_to_dict,
    normalize_from_sarvam_zip,
    renumber_pages,
)
from preprocessing.sarvam_system.pipeline import (
    DocumentPipeline,
    PipelineConfig,
)

load_dotenv()


# =============================================================================
# Logging
# =============================================================================

logger = logging.getLogger("sarvam_processor")

if not logger.handlers:

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s"
    )

    stream = logging.StreamHandler()

    stream.setFormatter(formatter)

    logger.addHandler(stream)


# Stable, public-by-convention location for visual evidence.  Each document
# gets its own directory below this root; keeping this separate from
# ``processed`` means re-building corpus JSON does not invalidate images.
DEFAULT_IMAGE_OUTPUT_DIR = BACKEND_DIR / "data" / "images"


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class SarvamConfig:

    api_key: str

    language: str = "en-IN"

    output_format: str = "md"

    # Sarvam's Document Intelligence API hard-caps PDF/ZIP uploads at 10
    # pages per job. Keep this <= 10 or every job creation will fail with
    # a 422 max_page_limit_exceeded error.
    max_pages_per_job: int = 10

    # Sarvam upload-size guard. The system splitter reduces the number
    # of pages in a transport chunk until it fits this limit.
    max_chunk_bytes: int = 20_000_000

    poll_interval: int = 5

    timeout: int = 600

    retries: int = 3

    cleanup_temp: bool = True

    # Where cropped chart/graph/table/image blocks get saved. Relative
    # paths are resolved against BACKEND_DIR. Set to None to disable
    # image cropping entirely (blocks will still carry their OCR'd
    # text, just no image_path).
    image_output_dir: Optional[str] = str(DEFAULT_IMAGE_OUTPUT_DIR)


# =============================================================================
# Main Processor
# =============================================================================

class SarvamProcessor:

    """
    Production Ready Sarvam Processor

    Responsibilities

        • Split PDFs

        • Upload to Sarvam

        • Wait for completion

        • Download ZIP

        • Extract JSON

        • Parse layout blocks (and crop out chart/table/image blocks
          from the original PDF, so visual content isn't lost to OCR
          text alone)

        • Merge pages

        • Return normalized document

    """

    def __init__(self, config: Optional[SarvamConfig] = None):

        if config is None:

            api_key = os.getenv("SARVAM_API_KEY")

            if not api_key:

                raise ValueError(
                    "SARVAM_API_KEY missing in .env"
                )

            config = SarvamConfig(api_key=api_key)

        self.config = config

        self.client = SarvamAI(
            api_subscription_key=config.api_key
        )

        # Public processor facade -> executable sarvam_system pipeline.
        # Passing the already-created SDK client also keeps SDK setup in
        # one place for callers that inject or patch it in tests.
        self.pipeline = DocumentPipeline(
            PipelineConfig(
                api_key=config.api_key,
                language=config.language,
                output_format=config.output_format,
                max_pages_per_job=config.max_pages_per_job,
                max_chunk_bytes=config.max_chunk_bytes,
                poll_interval=config.poll_interval,
                timeout=config.timeout,
                retries=config.retries,
                cleanup_temp=config.cleanup_temp,
                artifact_output_dir=(
                    (
                        Path(config.image_output_dir)
                        if Path(config.image_output_dir).is_absolute()
                        else BACKEND_DIR / config.image_output_dir
                    )
                    if config.image_output_dir
                    else None
                ),
            ),
            client=self.client,
        )

        # Temp dirs created for split chunks / downloaded zips, cleaned
        # up at the end of process_pdf() if cleanup_temp is True.
        self._temp_dirs: List[Path] = []

        self._image_output_dir: Optional[Path] = None
        if self.config.image_output_dir:
            configured_image_dir = Path(self.config.image_output_dir)
            self._image_output_dir = (
                configured_image_dir
                if configured_image_dir.is_absolute()
                else BACKEND_DIR / configured_image_dir
            )

        logger.info("Sarvam client initialized.")

        if self._image_output_dir is not None:

            logger.info(
                "Cropped visual blocks will be saved to %s",
                self._image_output_dir,
            )

        else:

            logger.info(
                "image_output_dir is disabled; visual blocks will "
                "have no image_path."
            )


# =============================================================================
# Public Entry
# =============================================================================

    def process_pdf(
        self,
        pdf_path: str | Path
    ) -> NormalizedDocument:
        return self.pipeline.process(pdf_path)

    def process_visual_pages(
        self,
        pdf_path: str | Path,
        page_numbers: List[int],
    ) -> NormalizedDocument:
        """Process only selected 1-based PDF pages with Sarvam.

        This keeps Sarvam usage proportional to visual content while callers
        can retain PyMuPDF text extraction for every page.
        """

        pdf_path = Path(pdf_path)
        selected_pages = sorted(set(page_numbers))
        if not selected_pages:
            return NormalizedDocument(source_file=pdf_path.name)
        return self.pipeline.process(pdf_path, page_numbers=selected_pages)


# =============================================================================
# PDF Splitter
# =============================================================================

    def _split_pdf(
        self,
        pdf_path: Path
    ) -> List[Path]:

        reader = PdfReader(str(pdf_path))

        total_pages = len(reader.pages)

        logger.info(
            f"PDF contains {total_pages} pages."
        )

        if total_pages <= self.config.max_pages_per_job:

            return [pdf_path]

        output_dir = Path(
            tempfile.mkdtemp(prefix="sarvam_split_")
        )

        self._temp_dirs.append(output_dir)

        files: List[Path] = []

        page_limit = self.config.max_pages_per_job

        for start in range(
            0,
            total_pages,
            page_limit
        ):

            writer = PdfWriter()

            end = min(
                start + page_limit,
                total_pages
            )

            for page in range(start, end):

                writer.add_page(reader.pages[page])

            out_file = (
                output_dir /
                f"{pdf_path.stem}_{start+1}_{end}.pdf"
            )

            with open(out_file, "wb") as f:

                writer.write(f)

            files.append(out_file)

        return files


# =============================================================================
# Upload / Process a Single Chunk
# =============================================================================

    def _process_chunk(
        self,
        chunk_path: Path
    ) -> Path:
        """
        Creates a Document Intelligence job for a single PDF chunk
        (<= max_pages_per_job pages), uploads it, starts processing,
        waits for completion and downloads the resulting ZIP.

        Retries the full upload/start/wait cycle up to
        `self.config.retries` times on transient API errors.
        """

        last_error: Optional[Exception] = None

        for attempt in range(1, self.config.retries + 1):

            try:

                job = self.client.document_intelligence.create_job(
                    language=self.config.language,
                    output_format=self.config.output_format,
                )

                logger.info(
                    f"Created job {getattr(job, 'job_id', '<pending>')} "
                    f"for {chunk_path.name} (attempt {attempt})"
                )

                job.upload_file(str(chunk_path))

                job.start()

                status = job.wait_until_complete(
                    poll_interval=self.config.poll_interval,
                    timeout=self.config.timeout,
                )

                job_state = getattr(status, "job_state", None)

                if job_state not in ("Completed", "PartiallyCompleted"):

                    raise RuntimeError(
                        f"Job for {chunk_path.name} ended in state "
                        f"'{job_state}': {status}"
                    )

                if job_state == "PartiallyCompleted":

                    logger.warning(
                        f"{chunk_path.name}: job PartiallyCompleted, "
                        "some pages may be missing from the output."
                    )

                try:

                    metrics = job.get_page_metrics()

                    logger.info(
                        f"{chunk_path.name}: "
                        f"{metrics.get('pages_succeeded', '?')}/"
                        f"{metrics.get('total_pages', '?')} pages succeeded"
                    )

                except Exception:

                    # Metrics are informational only; never fail the
                    # pipeline just because metrics couldn't be fetched.
                    logger.debug(
                        f"Could not fetch page metrics for {chunk_path.name}"
                    )

                download_dir = Path(
                    tempfile.mkdtemp(prefix="sarvam_output_")
                )

                self._temp_dirs.append(download_dir)

                zip_path = download_dir / f"{chunk_path.stem}_output.zip"

                job.download_output(str(zip_path))

                logger.info(
                    f"Downloaded output for {chunk_path.name} -> {zip_path}"
                )

                return zip_path

            except ApiError as e:

                last_error = e

                logger.error(
                    f"Sarvam API error on {chunk_path.name} "
                    f"(attempt {attempt}/{self.config.retries}): "
                    f"{getattr(e, 'status_code', '?')} - "
                    f"{getattr(e, 'body', e)}"
                )

            except Exception as e:

                last_error = e

                logger.error(
                    f"Unexpected error processing {chunk_path.name} "
                    f"(attempt {attempt}/{self.config.retries}): {e}"
                )

            if attempt < self.config.retries:

                backoff = self.config.poll_interval * attempt

                logger.info(f"Retrying in {backoff}s...")

                time.sleep(backoff)

        raise RuntimeError(
            f"Failed to process {chunk_path.name} after "
            f"{self.config.retries} attempts: {last_error}"
        )


# =============================================================================
# ZIP / JSON Parser
# =============================================================================

    def _parse_zip(
        self,
        zip_path: Path,
        source_pdf_path: Optional[Path] = None,
        document_id: Optional[str] = None,
        chunk_index: int = 0,
        page_offset: int = 0,
        page_number_map: Optional[Dict[int, int]] = None,
    ) -> List[DocumentPage]:
        """
        Thin wrapper around document_normalizer.normalize_from_sarvam_zip
        so the ZIP/JSON parsing logic lives in one shared place rather
        than being duplicated across processors.

        source_pdf_path/document_id/chunk_index are forwarded so that
        visual blocks (charts, tables, images -- see
        document_normalizer.VISUAL_LAYOUTS) get cropped out of the
        original PDF and saved to self._image_output_dir.
        """

        return normalize_from_sarvam_zip(
            zip_path,
            source_pdf_path=source_pdf_path,
            image_output_dir=self._image_output_dir,
            document_id=document_id,
            chunk_index=chunk_index,
            page_offset=page_offset,
            page_number_map=page_number_map,
        )


# =============================================================================
# Helpers
# =============================================================================

    def _build_metadata(
        self,
        document: NormalizedDocument
    ) -> Dict[str, Any]:

        total_pages = len(document.pages)

        total_blocks = sum(
            len(page.blocks) for page in document.pages
        )

        confidences = [
            block.confidence
            for page in document.pages
            for block in page.blocks
        ]

        avg_confidence = (
            round(sum(confidences) / len(confidences), 4)
            if confidences else None
        )

        total_images = sum(
            1
            for page in document.pages
            for block in page.blocks
            if block.image_path
        )

        return {
            "total_pages": total_pages,
            "total_blocks": total_blocks,
            "total_images": total_images,
            "average_confidence": avg_confidence,
            "language": self.config.language,
            "output_format": self.config.output_format,
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def _cleanup(self) -> None:

        for temp_dir in self._temp_dirs:

            shutil.rmtree(temp_dir, ignore_errors=True)

        self._temp_dirs.clear()


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> None:

    import argparse

    parser = argparse.ArgumentParser(
        description="Process a PDF through Sarvam Document Intelligence."
    )

    parser.add_argument("pdf_path", help="Path to the input PDF file")

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path to write the normalized JSON output "
             "(default: <pdf_name>.sarvam.json)",
    )

    parser.add_argument(
        "--language", default="en-IN",
        help="Target language code (BCP-47), e.g. en-IN, hi-IN",
    )

    parser.add_argument(
        "--output-format", default="md", choices=["md", "html"],
        help="Sarvam output format for the ZIP content",
    )

    parser.add_argument(
        "--image-output-dir", default=str(DEFAULT_IMAGE_OUTPUT_DIR),
        help="Directory to save cropped chart/table/image blocks into",
    )

    parser.add_argument(
        "--no-images", action="store_true",
        help="Disable cropping/saving visual blocks entirely",
    )

    args = parser.parse_args()

    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:

        raise SystemExit("SARVAM_API_KEY missing in .env")

    config = SarvamConfig(
        api_key=api_key,
        language=args.language,
        output_format=args.output_format,
        image_output_dir=(
            None if args.no_images else args.image_output_dir
        ),
    )

    processor = SarvamProcessor(config=config)

    document = processor.process_pdf(args.pdf_path)

    output_path = Path(
        args.output or f"{Path(args.pdf_path).stem}.sarvam.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:

        json.dump(document_to_dict(document), f, ensure_ascii=False, indent=2)

    logger.info(f"Normalized output written to {output_path}")


if __name__ == "__main__":

    main()
