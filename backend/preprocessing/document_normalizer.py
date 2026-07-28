"""
document_normalizer.py

Canonical normalized-document schema for the RAG ingestion pipeline,
plus converters that turn raw output from each processing path
(Sarvam Document Intelligence ZIPs, local PyMuPDF extraction) into
that shared schema.
 
This schema lives in its own module -- not inside sarvam_processor.py
or router.py -- so both processing paths (and any future one) produce
interchangeable output without importing each other.
"""

from __future__ import annotations

import io
import json
import logging
import re
import time
import zipfile

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import fitz


logger = logging.getLogger("document_normalizer")

if not logger.handlers:

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s"
    )

    stream = logging.StreamHandler()

    stream.setFormatter(formatter)

    logger.addHandler(stream)


# =============================================================================
# Schema
# =============================================================================

@dataclass
class DocumentBlock:

    page: int

    layout: str

    text: str

    confidence: float

    reading_order: int

    coordinates: Dict[str, float]

    image_path: Optional[str] = None


@dataclass
class DocumentPage:

    page_number: int

    width: int

    height: int

    created_at: str

    blocks: List[DocumentBlock] = field(default_factory=list)


@dataclass
class NormalizedDocument:

    source_file: str

    pages: List[DocumentPage] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Serialization
# =============================================================================

def document_to_dict(document: NormalizedDocument) -> Dict[str, Any]:
    """
    Converts a NormalizedDocument (and nested dataclasses) into a plain
    dict, ready for json.dump() or feeding into the RAG ingestion
    pipeline.
    """

    return {
        "source_file": document.source_file,
        "metadata": document.metadata,
        "pages": [
            {
                "page_number": page.page_number,
                "width": page.width,
                "height": page.height,
                "created_at": page.created_at,
                "blocks": [
                    {
                        "page": block.page,
                        "layout": block.layout,
                        "text": block.text,
                        "confidence": block.confidence,
                        "reading_order": block.reading_order,
                        "coordinates": block.coordinates,
                    }
                    for block in page.blocks
                ],
            }
            for page in document.pages
        ],
    }


def document_from_dict(data: Dict[str, Any]) -> NormalizedDocument:
    """
    Inverse of document_to_dict(). Useful for reloading a previously
    saved normalized document (e.g. re-running validation or
    re-ingesting without re-processing the source PDF).
    """

    pages: List[DocumentPage] = []

    for raw_page in data.get("pages", []):

        blocks = [
            DocumentBlock(
                page=raw_block.get("page", raw_page.get("page_number", 0)),
                layout=raw_block.get("layout", "text"),
                text=raw_block.get("text", ""),
                confidence=float(raw_block.get("confidence", 1.0)),
                reading_order=int(raw_block.get("reading_order", 0)),
                coordinates=raw_block.get("coordinates", {}),
            )
            for raw_block in raw_page.get("blocks", [])
        ]

        pages.append(
            DocumentPage(
                page_number=raw_page.get("page_number", 0),
                width=raw_page.get("width", 0),
                height=raw_page.get("height", 0),
                created_at=raw_page.get("created_at", ""),
                blocks=blocks,
            )
        )

    return NormalizedDocument(
        source_file=data.get("source_file", ""),
        pages=pages,
        metadata=data.get("metadata", {}),
    )


# =============================================================================
# Text Cleaning
# =============================================================================

_WHITESPACE_RE = re.compile(r"[ \t\u00a0]+")

_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

_HYPHEN_LINEBREAK_RE = re.compile(r"(\w)-\n(\w)")


def clean_text(text: Optional[str]) -> str:
    """
    Normalizes extracted text before it's stored: unifies line endings,
    rejoins words split by a hyphen at a line break (a common PDF
    extraction artifact), collapses repeated horizontal whitespace, and
    caps blank lines at one. Conservative on purpose -- it does not
    reflow paragraphs or strip legitimate punctuation.
    """

    if not text:

        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    text = _HYPHEN_LINEBREAK_RE.sub(r"\1\2", text)

    text = _WHITESPACE_RE.sub(" ", text)

    text = _MULTI_NEWLINE_RE.sub("\n\n", text)

    return text.strip()


def _now() -> str:

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# =============================================================================
# PyMuPDF -> NormalizedDocument
# =============================================================================

def normalize_from_pymupdf(
    pdf_path: Union[str, Path],
    clean: bool = True,
    routing_confidence: Optional[float] = None,
) -> NormalizedDocument:
    """
    Extracts plain text per page via PyMuPDF and wraps it in the
    NormalizedDocument schema. `routing_confidence` is optional context
    from DocumentAnalyzer, stored in metadata for traceability, not
    used for anything here.
    """

    pdf_path = Path(pdf_path)

    doc = fitz.open(pdf_path)

    pages: List[DocumentPage] = []

    try:

        if doc.is_encrypted and not doc.authenticate(""):

            raise ValueError(
                f"{pdf_path.name} is password-protected; cannot "
                "normalize without credentials."
            )

        for i, page in enumerate(doc, start=1):

            raw_text = page.get_text("text")

            text = clean_text(raw_text) if clean else raw_text.strip()

            blocks: List[DocumentBlock] = []

            if text:

                blocks.append(
                    DocumentBlock(
                        page=i,
                        layout="text",
                        text=text,
                        confidence=1.0,
                        reading_order=0,
                        coordinates={},
                    )
                )

            rect = page.rect

            pages.append(
                DocumentPage(
                    page_number=i,
                    width=int(rect.width),
                    height=int(rect.height),
                    created_at=_now(),
                    blocks=blocks,
                )
            )

    finally:

        doc.close()

    document = NormalizedDocument(
        source_file=pdf_path.name,
        pages=pages,
    )

    total_blocks = sum(len(p.blocks) for p in pages)

    document.metadata = {
        "total_pages": len(pages),
        "total_blocks": total_blocks,
        "average_confidence": 1.0 if total_blocks else None,
        "processor": "pymupdf",
        "routing_confidence": routing_confidence,
        "processed_at": _now(),
    }

    return document


# =============================================================================
# Sarvam ZIP -> DocumentPage list
# =============================================================================

def normalize_from_sarvam_zip(
    zip_path: Union[str, Path],
    clean: bool = True,
) -> List[DocumentPage]:
    """
    Opens a ZIP downloaded from Sarvam Document Intelligence, locates
    the structured JSON file (always included alongside the html/md
    output), and converts it into a list of DocumentPage objects.

    Returns a page list rather than a NormalizedDocument because a
    single source PDF may be split into several Sarvam jobs (one per
    <=10-page chunk); the caller is responsible for concatenating and
    re-numbering pages across chunks.
    """

    zip_path = Path(zip_path)

    pages: List[DocumentPage] = []

    with zipfile.ZipFile(zip_path, "r") as archive:

        json_names = [
            name for name in archive.namelist()
            if name.lower().endswith(".json")
        ]

        if not json_names:

            logger.warning(
                "No JSON file found inside %s; skipping page "
                "extraction for this chunk.",
                zip_path.name,
            )

            return pages

        for json_name in sorted(json_names):

            with archive.open(json_name) as f:

                try:

                    payload = json.load(
                        io.TextIOWrapper(f, encoding="utf-8")
                    )

                except json.JSONDecodeError as e:

                    logger.error(
                        "Could not decode %s in %s: %s",
                        json_name, zip_path.name, e,
                    )

                    continue

            pages.extend(_parse_sarvam_payload(payload, clean))

    return pages


def _parse_sarvam_payload(
    payload: Any,
    clean: bool,
) -> List[DocumentPage]:
    """
    Normalizes Sarvam's page-level JSON structure into DocumentPage
    objects. Written defensively against minor key-naming variations
    (e.g. "pages" vs "page_results", "blocks" vs "elements") since
    third-party API responses can shift between versions.
    """

    raw_pages: List[Dict[str, Any]]

    if isinstance(payload, dict):

        raw_pages = (
            payload.get("pages")
            or payload.get("page_results")
            or payload.get("results")
            or []
        )

    elif isinstance(payload, list):

        raw_pages = payload

    else:

        raw_pages = []

    pages: List[DocumentPage] = []

    for raw_page in raw_pages:

        page_index = raw_page.get("page_index")

        page_number = (
            raw_page.get("page_number")
            or raw_page.get("page")
            or (page_index + 1 if isinstance(page_index, int) else 0)
        )

        page = DocumentPage(
            page_number=int(page_number or 0),
            width=int(raw_page.get("width", 0) or 0),
            height=int(raw_page.get("height", 0) or 0),
            created_at=raw_page.get(
                "created_at", raw_page.get("timestamp", "")
            ),
        )

        raw_blocks = (
            raw_page.get("blocks")
            or raw_page.get("elements")
            or raw_page.get("layout_blocks")
            or []
        )

        for order, raw_block in enumerate(raw_blocks):

            coordinates = (
                raw_block.get("coordinates")
                or raw_block.get("bbox")
                or raw_block.get("bounding_box")
                or {}
            )

            # Normalize a bbox given as [x1, y1, x2, y2] into a dict,
            # in case Sarvam returns coordinates that way.
            if isinstance(coordinates, list) and len(coordinates) == 4:

                coordinates = {
                    "x1": coordinates[0],
                    "y1": coordinates[1],
                    "x2": coordinates[2],
                    "y2": coordinates[3],
                }

            text = raw_block.get("text", "") or ""

            if clean:

                text = clean_text(text)

            block = DocumentBlock(
                page=page.page_number,
                layout=raw_block.get(
                    "layout", raw_block.get("type", "text")
                ),
                text=text,
                confidence=float(raw_block.get("confidence", 1.0) or 1.0),
                reading_order=int(raw_block.get("reading_order", order)),
                coordinates=coordinates,
            )

            page.blocks.append(block)

        pages.append(page)

    return pages


# =============================================================================
# Validation
# =============================================================================

def validate_document(document: NormalizedDocument) -> List[str]:
    """
    Sanity-checks a NormalizedDocument before it's handed to the RAG
    ingestion pipeline. Returns a list of human-readable warnings;
    an empty list means the document looks clean. Non-fatal by design
    -- callers decide whether any of these warnings should block
    ingestion.
    """

    warnings: List[str] = []

    if not document.pages:

        warnings.append("document has no pages")

        return warnings

    seen_page_numbers = set()

    for page in document.pages:

        if page.page_number <= 0:

            warnings.append(
                f"page has non-positive page_number: {page.page_number}"
            )

        if page.page_number in seen_page_numbers:

            warnings.append(
                f"duplicate page_number: {page.page_number}"
            )

        seen_page_numbers.add(page.page_number)

        if not page.blocks:

            warnings.append(
                f"page {page.page_number} has no blocks (likely blank "
                "or extraction failed)"
            )

        for block in page.blocks:

            if not block.text.strip():

                warnings.append(
                    f"empty block text on page {page.page_number}"
                )

            if not (0.0 <= block.confidence <= 1.0):

                warnings.append(
                    f"confidence out of range on page "
                    f"{page.page_number}: {block.confidence}"
                )

    return warnings


# =============================================================================
# Merge Helper
# =============================================================================

def renumber_pages(document: NormalizedDocument) -> None:
    """
    Re-numbers pages sequentially (and updates each block's page
    reference to match) in place. Used after merging pages from
    multiple split-chunk jobs, each of which numbers its own pages
    starting at 1, into a single continuous sequence.
    """

    for offset, page in enumerate(document.pages, start=1):

        page.page_number = offset

        for block in page.blocks:

            block.page = offset