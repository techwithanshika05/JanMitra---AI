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
# Layouts treated as "visual" -- these get a cropped image saved
# alongside their OCR'd/extracted text, since text alone (e.g. numbers
# read off a bar chart) is a lossy representation of the original.
# =============================================================================

VISUAL_LAYOUTS = {
    "image", "figure", "picture", "chart", "graph", "table", "diagram",
    "flowchart", "flow_chart", "flow chart", "flow-diagram", "flow_diagram",
}


def _safe_document_name(value: str) -> str:
    """Return a portable directory name while preserving useful provenance."""

    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" ._")
    return cleaned or "document"


def _normalise_coordinates(value: Any) -> Dict[str, float]:
    """Accept common Sarvam bounding-box formats and return x1/y1/x2/y2."""

    if isinstance(value, (list, tuple)) and len(value) == 4:
        value = dict(zip(("x1", "y1", "x2", "y2"), value))
    if not isinstance(value, dict):
        return {}

    aliases = {
        "x1": ("x1", "x0", "left", "x"), "y1": ("y1", "y0", "top", "y"),
        "x2": ("x2", "right"), "y2": ("y2", "bottom"),
    }
    result: Dict[str, float] = {}
    try:
        for target, keys in aliases.items():
            for key in keys:
                if key in value and value[key] is not None:
                    result[target] = float(value[key])
                    break
    except (TypeError, ValueError):
        logger.warning("Ignoring malformed visual bounding box: %r", value)
        return {}
    # Some layout APIs emit x/y/width/height instead of two corners.
    try:
        if "x2" not in result and "width" in value and "x1" in result:
            result["x2"] = result["x1"] + float(value["width"])
        if "y2" not in result and "height" in value and "y1" in result:
            result["y2"] = result["y1"] + float(value["height"])
    except (TypeError, ValueError):
        logger.warning("Ignoring malformed visual bounding box: %r", value)
        return {}
    return result if len(result) == 4 else {}


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
                        # NOTE: this was previously missing, which
                        # silently dropped image_path for every block
                        # the moment a NormalizedDocument round-tripped
                        # through JSON (i.e. every document processed
                        # via router.process_directory()).
                        "image_path": block.image_path,
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
                # NOTE: this was previously missing too -- same bug,
                # inverse direction.
                image_path=raw_block.get("image_path"),
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
# Image Cropping Helper
# =============================================================================

def _crop_block_image(
    pdf_doc: "fitz.Document",
    page_number: int,
    coordinates: Dict[str, float],
    reported_width: float,
    reported_height: float,
    output_dir: Path,
    image_id: str,
    dpi: int = 200,
    pad_points: float = 4.0,
) -> Optional[str]:
    """
    Crops a region of a PDF page (given a bounding box in the same
    coordinate space the processor reported page width/height in) and
    saves it as a PNG. Returns the saved path, or None if cropping
    wasn't possible (missing/degenerate coordinates, bad page number,
    I/O failure, etc). Never raises -- a failed crop should not fail
    the whole document.
    """

    try:

        coordinates = _normalise_coordinates(coordinates)
        if not coordinates:

            logger.warning("Skipping visual crop for %s: missing or invalid bounding box.", image_id)

            return None

        if page_number < 1 or page_number > pdf_doc.page_count:

            logger.warning(
                "Cannot crop image for %s: page %d out of range "
                "(document has %d pages).",
                image_id, page_number, pdf_doc.page_count,
            )

            return None

        page = pdf_doc[page_number - 1]

        page_rect = page.rect

        # The bounding box coordinates were reported against
        # (reported_width, reported_height) from the processor's own
        # page-analysis, which doesn't always match the PDF's native
        # point size 1:1. Scale into the actual page's coordinate
        # space before cropping.
        scale_x = (
            page_rect.width / reported_width if reported_width else 1.0
        )

        scale_y = (
            page_rect.height / reported_height if reported_height else 1.0
        )

        x1 = float(coordinates.get("x1", 0)) * scale_x
        y1 = float(coordinates.get("y1", 0)) * scale_y
        x2 = float(coordinates.get("x2", page_rect.width)) * scale_x
        y2 = float(coordinates.get("y2", page_rect.height)) * scale_y

        if x2 < x1:
            x1, x2 = x2, x1

        if y2 < y1:
            y1, y2 = y2, y1

        clip = fitz.Rect(
            max(0.0, x1 - pad_points),
            max(0.0, y1 - pad_points),
            min(page_rect.width, x2 + pad_points),
            min(page_rect.height, y2 + pad_points),
        )

        if clip.is_empty or clip.width < 2 or clip.height < 2:

            logger.warning(
                "Skipping degenerate crop for %s: %s", image_id, clip
            )

            return None

        output_dir.mkdir(parents=True, exist_ok=True)

        out_path = output_dir / f"{image_id}.png"

        # Re-processing a document must be idempotent: do not render the
        # same visual region again and do not modify an existing evidence file.
        if out_path.is_file() and out_path.stat().st_size > 0:
            return str(out_path)

        zoom = dpi / 72.0

        matrix = fitz.Matrix(zoom, zoom)

        pixmap = page.get_pixmap(matrix=matrix, clip=clip)

        pixmap.save(str(out_path))

        return str(out_path)

    except Exception as exc:

        logger.warning(
            "Failed to crop image block %s (page %d): %s",
            image_id, page_number, exc,
        )

        return None


# =============================================================================
# PyMuPDF -> NormalizedDocument
# =============================================================================

def normalize_from_pymupdf(
    pdf_path: Union[str, Path],
    clean: bool = True,
    routing_confidence: Optional[float] = None,
    image_output_dir: Optional[Union[str, Path]] = None,
    document_id: Optional[str] = None,
) -> NormalizedDocument:
    """
    Extracts plain text per page via PyMuPDF and wraps it in the
    NormalizedDocument schema. `routing_confidence` is optional context
    from DocumentAnalyzer, stored in metadata for traceability, not
    used for anything here.

    If `image_output_dir` is given, embedded raster images on each
    page (photos, charts exported as images, etc) are also extracted
    and saved there, each as its own DocumentBlock with layout="image"
    and image_path set. This is best-effort: PyMuPDF's page.get_images()
    only finds images embedded as XObjects, not vector-drawn charts
    (those require Sarvam's layout detection to crop by bounding box).
    """

    pdf_path = Path(pdf_path)

    doc_id = document_id or pdf_path.stem

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

            reading_order = 0

            if text:

                blocks.append(
                    DocumentBlock(
                        page=i,
                        layout="text",
                        text=text,
                        confidence=1.0,
                        reading_order=reading_order,
                        coordinates={},
                    )
                )

                reading_order += 1

            if image_output_dir is not None:

                out_dir = Path(image_output_dir)

                for img_index, img in enumerate(page.get_images(full=True)):

                    xref = img[0]

                    try:

                        rects = page.get_image_rects(xref)

                    except Exception:

                        rects = []

                    rect = rects[0] if rects else None

                    coordinates = (
                        {
                            "x1": rect.x0, "y1": rect.y0,
                            "x2": rect.x1, "y2": rect.y1,
                        }
                        if rect else {}
                    )

                    image_id = f"{doc_id}_p{i}_img{img_index}"

                    try:

                        out_dir.mkdir(parents=True, exist_ok=True)

                        base_image = doc.extract_image(xref)

                        ext = base_image.get("ext", "png")

                        out_path = out_dir / f"{image_id}.{ext}"

                        with open(out_path, "wb") as f:

                            f.write(base_image["image"])

                        blocks.append(
                            DocumentBlock(
                                page=i,
                                layout="image",
                                text="",
                                confidence=1.0,
                                reading_order=reading_order,
                                coordinates=coordinates,
                                image_path=str(out_path),
                            )
                        )

                        reading_order += 1

                    except Exception as exc:

                        logger.warning(
                            "Failed to extract embedded image %s on "
                            "%s page %d: %s",
                            image_id, pdf_path.name, i, exc,
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
    source_pdf_path: Optional[Union[str, Path]] = None,
    image_output_dir: Optional[Union[str, Path]] = None,
    document_id: Optional[str] = None,
    chunk_index: int = 0,
    page_offset: int = 0,
) -> List[DocumentPage]:
    """
    Opens a ZIP downloaded from Sarvam Document Intelligence, locates
    the structured JSON file (always included alongside the html/md
    output), and converts it into a list of DocumentPage objects.

    Returns a page list rather than a NormalizedDocument because a
    single source PDF may be split into several Sarvam jobs (one per
    <=10-page chunk); the caller is responsible for concatenating and
    re-numbering pages across chunks.

    If `source_pdf_path` and `image_output_dir` are both given, blocks
    whose layout is visual (chart/graph/table/image/figure -- see
    VISUAL_LAYOUTS) get the corresponding region of the PDF cropped
    and saved as a PNG, with the path stored on the block's
    `image_path`. `source_pdf_path` should be the exact PDF file that
    was uploaded to Sarvam for this chunk (page numbers in the JSON
    output are local to that file, 1-indexed from its own start, not
    the original un-split document).
    """

    zip_path = Path(zip_path)

    pages: List[DocumentPage] = []

    pdf_doc: Optional["fitz.Document"] = None

    if source_pdf_path is not None and image_output_dir is not None:

        try:

            pdf_doc = fitz.open(Path(source_pdf_path))

        except Exception as exc:

            logger.warning(
                "Could not open %s for image cropping; visual blocks "
                "in %s will have no image_path: %s",
                source_pdf_path, zip_path.name, exc,
            )

            pdf_doc = None

    try:

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

                pages.extend(
                    _parse_sarvam_payload(
                        payload,
                        clean=clean,
                        pdf_doc=pdf_doc,
                        image_output_dir=(
                            Path(image_output_dir) / _safe_document_name(document_id or zip_path.stem)
                            if image_output_dir is not None else None
                        ),
                        document_id=document_id or zip_path.stem,
                        chunk_index=chunk_index,
                        page_offset=page_offset,
                    )
                )

    finally:

        if pdf_doc is not None:

            pdf_doc.close()

    return pages


def _parse_sarvam_payload(
    payload: Any,
    clean: bool,
    pdf_doc: Optional["fitz.Document"] = None,
    image_output_dir: Optional[Path] = None,
    document_id: Optional[str] = None,
    chunk_index: int = 0,
    page_offset: int = 0,
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

        page_number = int(page_number or 0)

        reported_width = float(raw_page.get("width", 0) or 0)

        reported_height = float(raw_page.get("height", 0) or 0)

        page = DocumentPage(
            page_number=page_number,
            width=int(reported_width),
            height=int(reported_height),
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

            coordinates = _normalise_coordinates(
                raw_block.get("coordinates")
                or raw_block.get("bbox")
                or raw_block.get("bounding_box")
                or {}
            )

            text = raw_block.get("text", "") or ""

            if clean:

                text = clean_text(text)

            layout = raw_block.get(
                "layout", raw_block.get("type", "text")
            )

            reading_order = int(raw_block.get("reading_order", order))

            image_path: Optional[str] = None

            if (
                pdf_doc is not None
                and image_output_dir is not None
                and str(layout).lower() in VISUAL_LAYOUTS
            ):

                # page_offset makes names unique when Sarvam receives a
                # split PDF.  The persisted block page is renumbered later.
                image_id = (
                    f"page_{page_number + page_offset}_"
                    f"{_safe_document_name(str(layout).lower())}_"
                    f"{reading_order}"
                )

                image_path = _crop_block_image(
                    pdf_doc=pdf_doc,
                    page_number=page_number,
                    coordinates=coordinates,
                    reported_width=reported_width,
                    reported_height=reported_height,
                    output_dir=image_output_dir,
                    image_id=image_id,
                )

            block = DocumentBlock(
                page=page.page_number,
                layout=layout,
                text=text,
                confidence=float(raw_block.get("confidence", 1.0) or 1.0),
                reading_order=reading_order,
                coordinates=coordinates,
                image_path=image_path,
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

            if not block.text.strip() and not block.image_path:

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

    Note: this does NOT rewrite image_path -- images stay wherever
    they were cropped to; only the logical page_number/block.page
    references are renumbered.
    """

    for offset, page in enumerate(document.pages, start=1):

        page.page_number = offset

        for block in page.blocks:

            block.page = offset
