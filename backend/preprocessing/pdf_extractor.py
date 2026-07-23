"""
pdf_extractor.py

Purpose:
--------
Extract text page-by-page from all PDF files stored in data/raw/
and save the extracted content as JSON files inside data/extracted/.

Input:
------
data/raw/
    document1.pdf
    document2.pdf
    document3.pdf

Output:
-------
data/extracted/
    document1.json
    document2.json
    document3.json

Required package:
-----------------
pip install pymupdf

Run directly:
-------------
python preprocessing/pdf_extractor.py
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF


# ============================================================
# Configuration
# ============================================================

# Current file:
# backend/preprocessing/pdf_extractor.py
#
# PROJECT_ROOT becomes:
# backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXTRACTED_DIR = DATA_DIR / "extracted"


# ============================================================
# Logging Configuration
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# PDF Extractor
# ============================================================

class PDFExtractor:
    """
    Extracts page-level text and basic metadata from PDF files.

    The extractor:
    - Automatically discovers PDFs inside data/raw/
    - Extracts text page by page
    - Preserves page numbers
    - Detects pages with no extractable text
    - Marks pages that may require OCR
    - Saves one JSON file per PDF
    - Continues processing if one PDF fails
    """

    def __init__(
        self,
        raw_dir: Path = RAW_DIR,
        output_dir: Path = EXTRACTED_DIR,
    ) -> None:

        self.raw_dir = Path(raw_dir)
        self.output_dir = Path(output_dir)

        # Create folders if they do not exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("PDFExtractor initialized")
        logger.info("Raw PDF directory: %s", self.raw_dir)
        logger.info("Extraction output directory: %s", self.output_dir)

    # ========================================================
    # Utility Methods
    # ========================================================

    @staticmethod
    def _safe_pdf_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """
        Convert PyMuPDF metadata into a JSON-safe dictionary.
        """

        if not metadata:
            return {}

        safe_metadata: Dict[str, str] = {}

        for key, value in metadata.items():
            safe_metadata[str(key)] = str(value) if value is not None else ""

        return safe_metadata

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Perform only minimal normalization.

        Full text cleaning should be handled later by text_cleaner.py.

        Here we only:
        - Normalize line endings
        - Remove null characters
        - Strip leading/trailing whitespace
        """

        if not text:
            return ""

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        text = text.replace("\x00", "")

        return text.strip()

    # ========================================================
    # PDF Discovery
    # ========================================================

    def find_pdf_files(self) -> List[Path]:
        """
        Find all PDF files directly inside data/raw/.

        Files are sorted by filename for predictable processing.
        """

        pdf_files = sorted(
            [
                file
                for file in self.raw_dir.iterdir()
                if file.is_file() and file.suffix.lower() == ".pdf"
            ],
            key=lambda path: path.name.lower(),
        )

        logger.info("Found %d PDF file(s)", len(pdf_files))

        return pdf_files

    # ========================================================
    # Single PDF Extraction
    # ========================================================

    def extract_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract text page-by-page from a single PDF.

        Parameters
        ----------
        pdf_path:
            Path to the PDF file.

        Returns
        -------
        dict
            Structured document containing:
            - document_id
            - source_file
            - source_path
            - total_pages
            - extraction metadata
            - PDF metadata
            - page-level extracted text
        """

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF file does not exist: {pdf_path}"
            )

        logger.info("Processing PDF: %s", pdf_path.name)

        document: Optional[fitz.Document] = None

        try:
            document = fitz.open(pdf_path)

            # Handle encrypted PDFs
            if document.needs_pass:
                raise ValueError(
                    f"PDF is password protected: {pdf_path.name}"
                )

            total_pages = len(document)

            pdf_metadata = self._safe_pdf_metadata(
                document.metadata
            )

            pages: List[Dict[str, Any]] = []

            successful_pages = 0
            empty_pages = 0
            failed_pages = 0

            for page_index in range(total_pages):

                page_number = page_index + 1

                try:
                    page = document.load_page(page_index)

                    # Extract plain text
                    raw_text = page.get_text("text")

                    text = self._normalize_text(raw_text)

                    has_text = bool(text)

                    # Empty pages may be scanned/image-only pages
                    needs_ocr = not has_text

                    if has_text:
                        successful_pages += 1
                    else:
                        empty_pages += 1

                    page_data = {
                        "page_number": page_number,
                        "text": text,
                        "character_count": len(text),
                        "word_count": len(text.split()) if text else 0,
                        "has_text": has_text,
                        "needs_ocr": needs_ocr,
                        "extraction_error": None,
                    }

                    pages.append(page_data)

                    if has_text:
                        logger.info(
                            "Extracted page %d/%d from %s (%d characters)",
                            page_number,
                            total_pages,
                            pdf_path.name,
                            len(text),
                        )
                    else:
                        logger.warning(
                            "No text found on page %d/%d of %s. "
                            "Page may require OCR.",
                            page_number,
                            total_pages,
                            pdf_path.name,
                        )

                except Exception as page_error:

                    failed_pages += 1

                    logger.error(
                        "Failed to extract page %d from %s: %s",
                        page_number,
                        pdf_path.name,
                        page_error,
                    )

                    # Keep the page entry so page numbering remains intact
                    pages.append(
                        {
                            "page_number": page_number,
                            "text": "",
                            "character_count": 0,
                            "word_count": 0,
                            "has_text": False,
                            "needs_ocr": False,
                            "extraction_error": str(page_error),
                        }
                    )

            document_id = pdf_path.stem

            result: Dict[str, Any] = {
                "document_id": document_id,
                "source_file": pdf_path.name,
                "source_path": str(pdf_path.relative_to(PROJECT_ROOT)),
                "file_size_bytes": pdf_path.stat().st_size,
                "total_pages": total_pages,
                "extraction_summary": {
                    "successful_pages": successful_pages,
                    "empty_pages": empty_pages,
                    "failed_pages": failed_pages,
                    "pages_requiring_ocr": empty_pages,
                },
                "pdf_metadata": pdf_metadata,
                "extraction_info": {
                    "extractor": "PyMuPDF",
                    "extracted_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
                "pages": pages,
            }

            logger.info(
                "Completed PDF: %s | Pages: %d | "
                "Text pages: %d | Empty/OCR pages: %d | Failed: %d",
                pdf_path.name,
                total_pages,
                successful_pages,
                empty_pages,
                failed_pages,
            )

            return result

        except Exception as error:

            logger.exception(
                "Failed to process PDF %s: %s",
                pdf_path.name,
                error,
            )

            raise

        finally:

            if document is not None:
                document.close()

    # ========================================================
    # Save Extracted JSON
    # ========================================================

    def save_extracted_document(
        self,
        document_data: Dict[str, Any],
    ) -> Path:
        """
        Save extracted PDF data as a JSON file.
        """

        document_id = document_data["document_id"]

        output_path = self.output_dir / f"{document_id}.json"

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as json_file:

            json.dump(
                document_data,
                json_file,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(
            "Saved extracted document: %s",
            output_path,
        )

        return output_path

    # ========================================================
    # Process Single PDF
    # ========================================================

    def process_single_pdf(
        self,
        pdf_path: Path,
    ) -> Dict[str, Any]:
        """
        Extract and save a single PDF.
        """

        document_data = self.extract_pdf(pdf_path)

        output_path = self.save_extracted_document(
            document_data
        )

        return {
            "source_file": pdf_path.name,
            "status": "success",
            "output_file": str(output_path),
            "total_pages": document_data["total_pages"],
            "empty_pages": document_data[
                "extraction_summary"
            ]["empty_pages"],
            "failed_pages": document_data[
                "extraction_summary"
            ]["failed_pages"],
        }

    # ========================================================
    # Process All PDFs
    # ========================================================

    def process_all_pdfs(
        self,
    ) -> Dict[str, Any]:
        """
        Process every PDF directly inside data/raw/.

        Returns a summary of the complete extraction run.
        """

        pdf_files = self.find_pdf_files()

        if not pdf_files:

            logger.warning(
                "No PDF files found in: %s",
                self.raw_dir,
            )

            return {
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0,
                "results": [],
            }

        results: List[Dict[str, Any]] = []

        successful_files = 0
        failed_files = 0

        logger.info(
            "Starting extraction for %d PDF file(s)",
            len(pdf_files),
        )

        for pdf_path in pdf_files:

            try:

                result = self.process_single_pdf(
                    pdf_path
                )

                results.append(result)

                successful_files += 1

            except Exception as error:

                failed_files += 1

                results.append(
                    {
                        "source_file": pdf_path.name,
                        "status": "failed",
                        "error": str(error),
                    }
                )

                logger.error(
                    "Skipping failed PDF: %s",
                    pdf_path.name,
                )

        summary = {
            "total_files": len(pdf_files),
            "successful_files": successful_files,
            "failed_files": failed_files,
            "results": results,
        }

        logger.info("=" * 60)
        logger.info("PDF EXTRACTION COMPLETED")
        logger.info("=" * 60)
        logger.info(
            "Total PDFs: %d",
            len(pdf_files),
        )
        logger.info(
            "Successful: %d",
            successful_files,
        )
        logger.info(
            "Failed: %d",
            failed_files,
        )
        logger.info("=" * 60)

        return summary


# ============================================================
# Main
# ============================================================

def main() -> None:
    """
    Run PDF extraction when this file is executed directly.
    """

    print("\n" + "=" * 60)
    print("PDS & SOCIAL WELFARE AI - PDF EXTRACTION")
    print("=" * 60)

    extractor = PDFExtractor()

    summary = extractor.process_all_pdfs()

    print("\nExtraction Summary")
    print("-" * 60)
    print(f"Total PDFs     : {summary['total_files']}")
    print(f"Successful     : {summary['successful_files']}")
    print(f"Failed         : {summary['failed_files']}")

    if summary["results"]:

        print("\nProcessed Files")
        print("-" * 60)

        for result in summary["results"]:

            if result["status"] == "success":

                print(
                    f"[OK] {result['source_file']} "
                    f"| Pages: {result['total_pages']} "
                    f"| Empty/OCR: {result['empty_pages']} "
                    f"| Failed pages: {result['failed_pages']}"
                )

            else:

                print(
                    f"[FAILED] {result['source_file']} "
                    f"| Error: {result['error']}"
                )

    print("\nExtracted JSON directory:")
    print(EXTRACTED_DIR)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

