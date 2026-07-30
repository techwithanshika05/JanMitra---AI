import json
import logging
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .documents import (
    BoundingBox,
    DocumentBlock,
    ElementType,
    NormalizedDocument,
    NormalizedPage,
)
from .sarvam import SarvamResult

logger = logging.getLogger(__name__)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def _html_text(source: str) -> str:
    parser = _TextExtractor()
    parser.feed(source)
    return "\n".join(parser.parts)

TYPE_ALIASES = {
    "title": ElementType.HEADING,
    "section_title": ElementType.HEADING,
    "section-title": ElementType.HEADING,
    "heading": ElementType.HEADING,
    "text": ElementType.PARAGRAPH,
    "paragraph": ElementType.PARAGRAPH,
    "list": ElementType.LIST,
    "table": ElementType.TABLE,
    "chart": ElementType.CHART,
    "graph": ElementType.GRAPH,
    "chart/diagram": ElementType.DIAGRAM,
    "diagram": ElementType.DIAGRAM,
    "image": ElementType.IMAGE,
    "picture": ElementType.IMAGE,
    "figure": ElementType.IMAGE,
    "photograph": ElementType.PHOTOGRAPH,
    "image-caption": ElementType.CAPTION,
    "caption": ElementType.CAPTION,
    "formula": ElementType.FORMULA,
    "header": ElementType.HEADER,
    "footer": ElementType.FOOTER,
    "page-number": ElementType.PAGE_NUMBER,
    "page_number": ElementType.PAGE_NUMBER,
    "footnote": ElementType.SOURCE,
    "source": ElementType.SOURCE,
}


class SarvamOutputNormalizer:
    """Tolerant normalizer for common Sarvam ZIP/page JSON variants."""

    def normalize(
        self,
        results: list[SarvamResult],
        document_id: str,
        source_file: str,
        sha256: str,
    ) -> NormalizedDocument:
        pages: list[NormalizedPage] = []
        jobs: list[dict[str, Any]] = []
        for result in results:
            chunk_pages = self._read_zip(result, document_id)
            for page in chunk_pages:
                page.page_number += result.chunk.page_offset
                for block in page.blocks:
                    block.page_number = page.page_number
                    block.source_chunk = result.chunk.chunk_number
                    block.source_job_id = result.job_id
            pages.extend(chunk_pages)
            jobs.append({
                "job_id": result.job_id,
                "status": result.status,
                "start_page": result.chunk.start_page,
                "end_page": result.chunk.end_page,
                "metrics": result.metrics,
            })
        pages.sort(key=lambda page: page.page_number)
        self._repair_reading_order(pages)
        return NormalizedDocument(
            document_id=document_id,
            source_file=source_file,
            sha256=sha256,
            pages=pages,
            metadata={"sarvam_jobs": jobs},
        )

    def _read_zip(self, result: SarvamResult, document_id: str) -> list[NormalizedPage]:
        pages: list[NormalizedPage] = []
        with zipfile.ZipFile(result.zip_path) as archive:
            json_names = sorted(name for name in archive.namelist() if name.endswith(".json"))
            for fallback_page, name in enumerate(json_names, 1):
                payload = json.loads(archive.read(name).decode("utf-8"))
                pages.extend(self._payload_pages(payload, document_id, fallback_page))
            if not pages:
                html_names = sorted(name for name in archive.namelist() if name.endswith(".html"))
                for page_number, name in enumerate(html_names, 1):
                    html = archive.read(name).decode("utf-8", errors="replace")
                    text = _html_text(html)
                    pages.append(self._text_page(document_id, page_number, text, html))
            if not pages:
                markdown_names = sorted(
                    name
                    for name in archive.namelist()
                    if name.lower().endswith((".md", ".markdown", ".txt"))
                )
                for page_number, name in enumerate(markdown_names, 1):
                    text = archive.read(name).decode("utf-8", errors="replace")
                    pages.append(
                        self._text_page(document_id, page_number, text, "")
                    )
        return pages

    def _payload_pages(
        self, payload: Any, document_id: str, fallback_page: int
    ) -> list[NormalizedPage]:
        raw_pages = payload.get("pages") if isinstance(payload, dict) else None
        if not isinstance(raw_pages, list):
            raw_pages = [payload]
        pages: list[NormalizedPage] = []
        for page_index, raw_page in enumerate(raw_pages, fallback_page):
            if not isinstance(raw_page, dict):
                continue
            number = int(
                raw_page.get("page_number")
                or raw_page.get("page_num")
                or raw_page.get("page")
                or page_index
            )
            width = self._number(
                raw_page.get("width") or raw_page.get("image_width")
            )
            height = self._number(
                raw_page.get("height") or raw_page.get("image_height")
            )
            raw_blocks = (
                raw_page.get("blocks")
                or raw_page.get("sections")
                or raw_page.get("elements")
                or []
            )
            blocks = [
                self._block(document_id, number, index, block, width, height)
                for index, block in enumerate(raw_blocks)
                if isinstance(block, dict)
            ]
            if not blocks:
                text = str(raw_page.get("text") or raw_page.get("markdown") or "")
                if text:
                    blocks = [self._text_block(document_id, number, 0, text)]
            pages.append(NormalizedPage(
                page_number=number,
                width=width,
                height=height,
                blocks=blocks,
            ))
        return pages

    def _block(
        self,
        document_id: str,
        page_number: int,
        index: int,
        raw: dict[str, Any],
        coordinate_width: float | None = None,
        coordinate_height: float | None = None,
    ) -> DocumentBlock:
        raw_type = str(
            raw.get("type")
            or raw.get("label")
            or raw.get("layout_tag")
            or "unknown"
        ).lower()
        element_type = TYPE_ALIASES.get(raw_type, ElementType.UNKNOWN)
        bbox = self._bbox(
            raw.get("bbox")
            or raw.get("bounding_box")
            or raw.get("coordinates")
        )
        text = str(raw.get("text") or raw.get("content") or raw.get("markdown") or "")
        html = raw.get("html") or raw.get("text_as_html")
        return DocumentBlock(
            block_id=f"{document_id}_p{page_number:04d}_b{index:04d}",
            document_id=document_id,
            page_number=page_number,
            element_type=element_type,
            subtype=raw_type,
            reading_order=int(raw.get("reading_order") or raw.get("order") or index),
            bounding_box=bbox,
            text=text.strip(),
            html=str(html) if html else None,
            structured_data=raw.get("data") if isinstance(raw.get("data"), dict) else {},
            confidence=self._confidence(raw.get("confidence") or raw.get("score")),
            metadata={
                "raw_keys": sorted(raw.keys()),
                "coordinate_width": coordinate_width,
                "coordinate_height": coordinate_height,
                "sarvam_block_id": raw.get("block_id"),
            },
        )

    def _text_page(
        self, document_id: str, page_number: int, text: str, html: str
    ) -> NormalizedPage:
        block = self._text_block(document_id, page_number, 0, text)
        block.html = html
        return NormalizedPage(page_number=page_number, blocks=[block])

    @staticmethod
    def _text_block(
        document_id: str, page_number: int, index: int, text: str
    ) -> DocumentBlock:
        return DocumentBlock(
            block_id=f"{document_id}_p{page_number:04d}_b{index:04d}",
            document_id=document_id,
            page_number=page_number,
            element_type=ElementType.PARAGRAPH,
            reading_order=index,
            text=text.strip(),
        )

    @staticmethod
    def _bbox(value: Any) -> BoundingBox | None:
        if isinstance(value, list) and len(value) >= 4:
            return BoundingBox(x1=value[0], y1=value[1], x2=value[2], y2=value[3])
        if isinstance(value, dict):
            try:
                return BoundingBox(
                    x1=value.get("x1", value.get("left")),
                    y1=value.get("y1", value.get("top")),
                    x2=value.get("x2", value.get("right")),
                    y2=value.get("y2", value.get("bottom")),
                )
            except Exception:
                return None
        return None

    @staticmethod
    def _confidence(value: Any) -> float | None:
        try:
            score = float(value)
            return max(0.0, min(1.0, score / 100 if score > 1 else score))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _repair_reading_order(pages: list[NormalizedPage]) -> None:
        current_section: str | None = None
        for page in pages:
            page.blocks.sort(key=lambda block: (
                block.reading_order,
                block.bounding_box.y1 if block.bounding_box else 0,
                block.bounding_box.x1 if block.bounding_box else 0,
            ))
            previous_block: DocumentBlock | None = None
            for order, block in enumerate(page.blocks):
                block.reading_order = order
                if block.element_type == ElementType.HEADING and block.text:
                    current_section = " ".join(block.text.split())
                elif current_section and not block.parent_section:
                    block.parent_section = current_section
                if (
                    block.element_type in {
                        ElementType.CHART,
                        ElementType.GRAPH,
                        ElementType.IMAGE,
                        ElementType.DIAGRAM,
                    }
                    and previous_block
                    and previous_block.element_type == ElementType.CAPTION
                    and previous_block.text
                ):
                    block.caption = " ".join(previous_block.text.split())
                previous_block = block
