"""
router.py

Routes PDFs between two processing paths based on DocumentAnalyzer's
per-page heuristics:

    "pymupdf" -> cheap local text extraction (document_analyzer.py's
                 recommendation for mostly-text, non-scanned PDFs)
    "sarvam"  -> Sarvam Document Intelligence (sarvam_processor.py's
                 OCR/layout pipeline, for scanned/image/graph-heavy PDFs)

Both paths are normalized into the same NormalizedDocument /
DocumentPage / DocumentBlock schema defined in document_normalizer.py,
so downstream RAG ingestion never has to know which path a given PDF
took.

This file expects document_analyzer.py, sarvam_processor.py, and
document_normalizer.py to live alongside it (same package / working
directory).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .document_analyzer import DocumentAnalyzer, DocumentAnalysisResult
from .sarvam_processor import SarvamProcessor, SarvamConfig
from .document_normalizer import (
    NormalizedDocument,
    document_to_dict,
    normalize_from_pymupdf,
)


logger = logging.getLogger("router")

if not logger.handlers:

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s"
    )

    stream = logging.StreamHandler()

    stream.setFormatter(formatter)

    logger.addHandler(stream)


# =============================================================================
# Result Model
# =============================================================================

@dataclass
class RouteResult:

    document_id: str

    source_file: str

    processor_used: str

    recommended_processor: str

    confidence: float

    status: str  # "success" | "failed"

    error: Optional[str]

    output_path: Optional[str]

    analysis: Optional[Dict[str, Any]]

    processing_time_seconds: float


# =============================================================================
# Router
# =============================================================================

class DocumentRouter:
    """
    Decides, per PDF, whether to extract text locally with PyMuPDF or
    hand the document off to Sarvam Document Intelligence, then
    normalizes both outcomes into the same schema.
    """

    def __init__(
        self,
        analyzer: Optional[DocumentAnalyzer] = None,
        sarvam_processor: Optional[SarvamProcessor] = None,
        force_processor: Optional[str] = None,
        fallback_to_pymupdf: bool = True,
    ):
        if force_processor not in (None, "pymupdf", "sarvam"):

            raise ValueError(
                "force_processor must be 'pymupdf', 'sarvam' or None, "
                f"got {force_processor!r}"
            )

        self.analyzer = analyzer or DocumentAnalyzer()

        self.sarvam_processor = sarvam_processor

        self.force_processor = force_processor

        # If a PDF is recommended for Sarvam but no SarvamProcessor is
        # configured (e.g. missing API key), fall back to pymupdf
        # instead of failing the whole file. Quality may suffer on
        # scanned/graphic-heavy pages, but the pipeline keeps moving.
        self.fallback_to_pymupdf = fallback_to_pymupdf


# =============================================================================
# Public Entry Points
# =============================================================================

    def process_pdf(
        self,
        pdf_path: Union[str, Path],
    ) -> Tuple[RouteResult, Optional[NormalizedDocument]]:

        pdf_path = Path(pdf_path)

        start = time.perf_counter()

        if not pdf_path.exists():

            raise FileNotFoundError(pdf_path)

        try:

            analysis = self.analyzer.analyze_pdf(pdf_path)

        except Exception as e:

            logger.error("Analysis failed for %s: %s", pdf_path.name, e)

            return self._failure_result(pdf_path, start, str(e)), None

        processor = self.force_processor or analysis.recommended_processor

        if processor == "sarvam" and self.sarvam_processor is None:

            if self.fallback_to_pymupdf:

                logger.warning(
                    "%s recommended for Sarvam but no SarvamProcessor "
                    "is configured; falling back to pymupdf (quality "
                    "may suffer on scanned/graphic-heavy pages).",
                    pdf_path.name,
                )

                processor = "pymupdf"

            else:

                error = (
                    "Document requires Sarvam processing but no "
                    "SarvamProcessor was configured (missing "
                    "SARVAM_API_KEY?)."
                )

                logger.error("%s: %s", pdf_path.name, error)

                return self._failure_result(
                    pdf_path, start, error, analysis, processor
                ), None

        logger.info(
            "%s -> %s (recommended=%s, confidence=%.2f, forced=%s)",
            pdf_path.name,
            processor,
            analysis.recommended_processor,
            analysis.confidence,
            self.force_processor is not None,
        )

        try:

            if processor == "sarvam":

                document = self.sarvam_processor.process_pdf(pdf_path)

            else:

                document = self._process_with_pymupdf(pdf_path, analysis)

        except Exception as e:

            logger.error(
                "Processing failed for %s via %s: %s",
                pdf_path.name, processor, e
            )

            return self._failure_result(
                pdf_path, start, str(e), analysis, processor
            ), None

        route_result = RouteResult(
            document_id=pdf_path.stem,
            source_file=str(pdf_path.resolve()),
            processor_used=processor,
            recommended_processor=analysis.recommended_processor,
            confidence=analysis.confidence,
            status="success",
            error=None,
            output_path=None,
            analysis=self._slim_analysis(analysis),
            processing_time_seconds=round(
                time.perf_counter() - start, 3
            ),
        )

        return route_result, document

    def process_directory(
        self,
        input_dir: Union[str, Path],
        output_dir: Union[str, Path],
        pattern: str = "*.pdf",
    ) -> List[RouteResult]:

        input_dir = Path(input_dir)

        output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_files = sorted(input_dir.glob(pattern))

        if not pdf_files:

            logger.warning(
                "No files matching %s in %s", pattern, input_dir
            )

        results: List[RouteResult] = []

        for pdf_path in pdf_files:

            route_result, document = self.process_pdf(pdf_path)

            if document is not None:

                out_file = output_dir / f"{pdf_path.stem}.json"

                with open(out_file, "w", encoding="utf-8") as f:

                    json.dump(
                        document_to_dict(document),
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )

                route_result.output_path = str(out_file)

            results.append(route_result)

        manifest_path = output_dir / "manifest.json"

        with open(manifest_path, "w", encoding="utf-8") as f:

            json.dump(
                [asdict(r) for r in results],
                f,
                ensure_ascii=False,
                indent=2,
            )

        succeeded = sum(1 for r in results if r.status == "success")

        logger.info(
            "Processed %d/%d files successfully. Manifest -> %s",
            succeeded, len(results), manifest_path,
        )

        return results


# =============================================================================
# Local PyMuPDF Path
# =============================================================================

    def _process_with_pymupdf(
        self,
        pdf_path: Path,
        analysis: DocumentAnalysisResult,
    ) -> NormalizedDocument:
        """
        Thin wrapper around document_normalizer.normalize_from_pymupdf
        so local extraction lives in one shared place rather than
        being duplicated across processors.
        """

        return normalize_from_pymupdf(
            pdf_path,
            routing_confidence=analysis.confidence,
        )


# =============================================================================
# Helpers
# =============================================================================

    def _slim_analysis(
        self,
        analysis: DocumentAnalysisResult,
    ) -> Dict[str, Any]:

        return {
            "total_pages": analysis.total_pages,
            "scanned_pages": analysis.scanned_pages,
            "image_pages": analysis.image_pages,
            "drawing_pages": analysis.drawing_pages,
            "recommended_processor": analysis.recommended_processor,
            "confidence": analysis.confidence,
        }

    def _failure_result(
        self,
        pdf_path: Path,
        start: float,
        error: str,
        analysis: Optional[DocumentAnalysisResult] = None,
        processor: Optional[str] = None,
    ) -> RouteResult:

        return RouteResult(
            document_id=pdf_path.stem,
            source_file=str(pdf_path.resolve()),
            processor_used=processor or "none",
            recommended_processor=(
                analysis.recommended_processor if analysis else "unknown"
            ),
            confidence=analysis.confidence if analysis else 0.0,
            status="failed",
            error=error,
            output_path=None,
            analysis=self._slim_analysis(analysis) if analysis else None,
            processing_time_seconds=round(time.perf_counter() - start, 3),
        )


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> None:

    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(
        description=(
            "Route PDFs between local PyMuPDF extraction and Sarvam "
            "Document Intelligence, and normalize the output for RAG "
            "ingestion."
        )
    )

    parser.add_argument(
        "input_path",
        help="A single PDF file or a directory of PDFs",
    )

    parser.add_argument(
        "-o", "--output-dir",
        default="./router_output",
        help="Directory to write normalized JSON + manifest",
    )

    parser.add_argument(
        "--pattern",
        default="*.pdf",
        help="Glob pattern used when input_path is a directory",
    )

    parser.add_argument(
        "--force-processor",
        choices=["pymupdf", "sarvam"],
        default=None,
        help="Skip analysis and force a specific processor for every file",
    )

    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help=(
            "Fail instead of falling back to pymupdf when Sarvam is "
            "needed but unavailable"
        ),
    )

    parser.add_argument(
        "--language", default="en-IN",
        help="Sarvam target language code (BCP-47), e.g. en-IN, hi-IN",
    )

    parser.add_argument(
        "--output-format", default="md", choices=["md", "html"],
        help="Sarvam output format for the ZIP content",
    )

    args = parser.parse_args()

    api_key = os.getenv("SARVAM_API_KEY")

    sarvam_processor: Optional[SarvamProcessor] = None

    if api_key:

        sarvam_processor = SarvamProcessor(
            SarvamConfig(
                api_key=api_key,
                language=args.language,
                output_format=args.output_format,
            )
        )

    else:

        logger.warning(
            "SARVAM_API_KEY not set; documents needing Sarvam will %s.",
            "fall back to pymupdf" if not args.no_fallback else "fail",
        )

    router = DocumentRouter(
        sarvam_processor=sarvam_processor,
        force_processor=args.force_processor,
        fallback_to_pymupdf=not args.no_fallback,
    )

    input_path = Path(args.input_path)

    output_dir = Path(args.output_dir)

    if input_path.is_dir():

        router.process_directory(
            input_path, output_dir, pattern=args.pattern
        )

        return

    output_dir.mkdir(parents=True, exist_ok=True)

    route_result, document = router.process_pdf(input_path)

    if document is not None:

        out_file = output_dir / f"{input_path.stem}.json"

        with open(out_file, "w", encoding="utf-8") as f:

            json.dump(
                document_to_dict(document),
                f,
                ensure_ascii=False,
                indent=2,
            )

        route_result.output_path = str(out_file)

        logger.info("Normalized output written to %s", out_file)

    report_file = output_dir / f"{input_path.stem}.route.json"

    with open(report_file, "w", encoding="utf-8") as f:

        json.dump(asdict(route_result), f, ensure_ascii=False, indent=2)

    if route_result.status == "failed":

        raise SystemExit(
            f"Failed to process {input_path.name}: {route_result.error}"
        )


if __name__ == "__main__":

    main()