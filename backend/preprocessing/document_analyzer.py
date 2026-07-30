"""
document_analyzer.py

Production-ready PDF analyzer for RAG ingestion.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple, Union
import json
import logging
import statistics
import time

import fitz


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PageAnalysis:
    page_number: int
    character_count: int
    word_count: int
    image_count: int
    drawing_count: int
    has_text: bool
    scanned_page: bool
    needs_ocr: bool


@dataclass
class DocumentAnalysisResult:
    document_id: str
    source_file: str
    total_pages: int
    text_pages: int
    empty_pages: int
    scanned_pages: int
    image_pages: int
    drawing_pages: int
    total_images: int
    total_drawings: int
    average_characters_per_page: float
    average_words_per_page: float
    recommended_processor: str
    confidence: float
    processing_time_seconds: float
    pages: List[PageAnalysis]


class DocumentAnalyzer:
    """
    Heuristically decides, per PDF, whether it can be handled cheaply
    by a local text extractor (PyMuPDF) or needs to be routed to a
    heavier OCR/layout pipeline (Sarvam Document Intelligence).
    """

    # Max weighted score recommend_processor() can produce; used to
    # normalize confidence into a real [0, 1] range.
    _MAX_SCORE = 9

    def __init__(
        self,
        min_text_characters: int = 100,
        scanned_page_max_characters: int = 50,
        max_drawings_per_page: int = 5000,
    ):
        self.min_text_characters = min_text_characters

        # A page below this many characters (but with at least one
        # image) is treated as a scanned page. Kept as its own knob
        # rather than reusing min_text_characters, since "likely scanned"
        # and "has usable text" are different bars.
        self.scanned_page_max_characters = scanned_page_max_characters

        # Safety valve: pages with pathologically complex vector art
        # (dense charts/graphs) can make get_drawings() slow. Past this
        # count we stop trusting the exact number and just cap it, so
        # one bad page can't stall the whole batch.
        self.max_drawings_per_page = max_drawings_per_page

    def analyze_page(self, page: fitz.Page, page_no: int) -> PageAnalysis:
        text = page.get_text("text")
        chars = len(text)
        words = len(text.split())

        try:
            images = page.get_images(full=True)
        except Exception as e:
            logger.debug("get_images failed on page %d: %s", page_no, e)
            images = []

        try:
            drawings = page.get_drawings()
        except Exception as e:
            logger.debug("get_drawings failed on page %d: %s", page_no, e)
            drawings = []

        image_count = len(images)
        drawing_count = min(len(drawings), self.max_drawings_per_page)

        has_text = chars >= self.min_text_characters
        scanned = chars < self.scanned_page_max_characters and image_count > 0
        needs_ocr = scanned

        return PageAnalysis(
            page_number=page_no,
            character_count=chars,
            word_count=words,
            image_count=image_count,
            drawing_count=drawing_count,
            has_text=has_text,
            scanned_page=scanned,
            needs_ocr=needs_ocr,
        )

    def recommend_processor(
        self,
        pages: List[PageAnalysis]
    ) -> Tuple[str, float]:

        if not pages:
            # No pages to judge — default to the cheap path rather than
            # crashing; caller can decide what an empty PDF means for
            # their pipeline.
            logger.warning("recommend_processor called with 0 pages")
            return "pymupdf", 0.0

        total = len(pages)

        scanned_ratio = sum(p.scanned_page for p in pages) / total
        image_ratio = sum(p.image_count > 0 for p in pages) / total
        drawing_ratio = sum(p.drawing_count > 0 for p in pages) / total
        avg_chars = statistics.mean(p.character_count for p in pages)

        score = 0

        if scanned_ratio > 0.20:
            score += 3
        if image_ratio > 0.30:
            score += 2
        if drawing_ratio > 0.20:
            score += 2
        if avg_chars < 120:
            score += 2

        processor = "sarvam" if score >= 5 else "pymupdf"
        confidence = min(score / self._MAX_SCORE, 1.0)

        logger.info(
            "Routing decision: processor=%s score=%d/%d "
            "(scanned_ratio=%.2f image_ratio=%.2f drawing_ratio=%.2f "
            "avg_chars=%.1f)",
            processor, score, self._MAX_SCORE,
            scanned_ratio, image_ratio, drawing_ratio, avg_chars,
        )

        return processor, confidence

    def analyze_pdf(
        self,
        pdf_path: Union[str, Path]
    ) -> DocumentAnalysisResult:

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)

        start = time.perf_counter()

        logger.info("Analyzing %s", pdf_path.name)

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise ValueError(f"Could not open {pdf_path.name}: {e}") from e

        try:
            if doc.is_encrypted and not doc.authenticate(""):
                raise ValueError(
                    f"{pdf_path.name} is password-protected; "
                    "cannot analyze without credentials."
                )

            pages = [
                self.analyze_page(page, i + 1)
                for i, page in enumerate(doc)
            ]

            processor, confidence = self.recommend_processor(pages)

            result = DocumentAnalysisResult(
                document_id=pdf_path.stem,
                source_file=str(pdf_path.resolve()),
                total_pages=len(pages),
                text_pages=sum(p.has_text for p in pages),
                empty_pages=sum(p.character_count == 0 for p in pages),
                scanned_pages=sum(p.scanned_page for p in pages),
                image_pages=sum(p.image_count > 0 for p in pages),
                drawing_pages=sum(p.drawing_count > 0 for p in pages),
                total_images=sum(p.image_count for p in pages),
                total_drawings=sum(p.drawing_count for p in pages),
                average_characters_per_page=statistics.mean(
                    p.character_count for p in pages
                ) if pages else 0,
                average_words_per_page=statistics.mean(
                    p.word_count for p in pages
                ) if pages else 0,
                recommended_processor=processor,
                confidence=confidence,
                processing_time_seconds=round(
                    time.perf_counter() - start,
                    3
                ),
                pages=pages,
            )

            return result

        finally:
            doc.close()

    def route(
        self,
        pdf_path: Union[str, Path],
        sarvam_processor=None,
    ):
        """
        Analyze a PDF and, if a SarvamProcessor instance is supplied,
        immediately hand off documents that need OCR/layout parsing.
        Kept as an optional hook (no hard import of sarvam_processor)
        so this module works standalone.

        Returns (DocumentAnalysisResult, normalized_document_or_None).
        """

        result = self.analyze_pdf(pdf_path)

        if result.recommended_processor != "sarvam" or sarvam_processor is None:
            return result, None

        logger.info(
            "%s routed to Sarvam (confidence=%.2f)",
            result.document_id, result.confidence,
        )

        normalized_document = sarvam_processor.process_pdf(pdf_path)

        return result, normalized_document

    @staticmethod
    def save_report(
        result: DocumentAnalysisResult,
        output_path: Union[str, Path]
    ) -> None:
        Path(output_path).write_text(
            json.dumps(asdict(result), indent=2),
            encoding="utf-8"
        )

    @staticmethod
    def print_summary(result: DocumentAnalysisResult) -> None:
        print("=" * 60)
        print("DOCUMENT ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Document : {result.document_id}")
        print(f"Pages    : {result.total_pages}")
        print(f"Text     : {result.text_pages}")
        print(f"Scanned  : {result.scanned_pages}")
        print(f"Images   : {result.total_images}")
        print(f"Drawings : {result.total_drawings}")
        print(f"Processor: {result.recommended_processor}")
        print(f"Confidence: {result.confidence:.2f}")
        print("=" * 60)


def main() -> None:

    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze a PDF and recommend a processing pipeline."
    )

    parser.add_argument("pdf_path", help="Path to the input PDF file")

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path to write the JSON analysis report "
             "(default: <pdf_name>.analysis.json)",
    )

    parser.add_argument(
        "--min-text-characters", type=int, default=100,
        help="Minimum characters on a page to count it as having text",
    )

    args = parser.parse_args()

    analyzer = DocumentAnalyzer(
        min_text_characters=args.min_text_characters
    )

    result = analyzer.analyze_pdf(args.pdf_path)

    analyzer.print_summary(result)

    output_path = Path(
        args.output or f"{Path(args.pdf_path).stem}.analysis.json"
    )

    analyzer.save_report(result, output_path)

    logger.info("Report written to %s", output_path)


if __name__ == "__main__":
    main()