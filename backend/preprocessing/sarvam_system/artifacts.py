import html
import json
import logging
import re
from abc import ABC, abstractmethod
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import fitz

from .documents import Artifact, DocumentBlock, ElementType

logger = logging.getLogger(__name__)


class FallbackProcessor(ABC):
    @abstractmethod
    def supports(self, block: DocumentBlock) -> bool: ...

    @abstractmethod
    def enrich(self, block: DocumentBlock, page_image: Path | None) -> DocumentBlock: ...


class NoopFallback(FallbackProcessor):
    def supports(self, block: DocumentBlock) -> bool:
        return True

    def enrich(self, block: DocumentBlock, page_image: Path | None) -> DocumentBlock:
        block.metadata["fallback"] = "not_configured"
        return block


class ArtifactStore:
    def __init__(self, root: Path, document_id: str):
        self.root = (root / document_id).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def write_text(self, relative: str, content: str) -> str:
        target = self.safe_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target.relative_to(self.root).as_posix()

    def write_json(self, relative: str, payload: Any) -> str:
        return self.write_text(relative, json.dumps(payload, ensure_ascii=False, indent=2))

    def safe_path(self, relative: str) -> Path:
        target = (self.root / relative).resolve()
        if self.root != target and self.root not in target.parents:
            raise ValueError("Artifact path escapes document root")
        return target


class PageRegionCropper:
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path

    def crop_png(
        self,
        page_number: int,
        bbox: tuple[float, float, float, float],
        output: Path,
        source_width: float | None = None,
        source_height: float | None = None,
    ) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with fitz.open(self.pdf_path) as pdf:
            page = pdf.load_page(page_number - 1)
            x1, y1, x2, y2 = bbox
            if source_width and source_height:
                x_scale = page.rect.width / source_width
                y_scale = page.rect.height / source_height
                x1, x2 = x1 * x_scale, x2 * x_scale
                y1, y2 = y1 * y_scale, y2 * y_scale
            clip = fitz.Rect(x1, y1, x2, y2) & page.rect
            if clip.is_empty:
                raise ValueError(f"Invalid crop on page {page_number}: {bbox}")
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip, alpha=False)
            pix.save(output)


class _TableSanitizer(HTMLParser):
    allowed_tags = {
        "table", "caption", "thead", "tbody", "tfoot", "tr", "th", "td"
    }
    allowed_attrs = {"rowspan", "colspan", "scope"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.output: list[str] = []
        self.text: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag not in self.allowed_tags:
            return
        safe_attrs = "".join(
            f' {name}="{html.escape(value or "", quote=True)}"'
            for name, value in attrs
            if name in self.allowed_attrs
        )
        self.output.append(f"<{tag}{safe_attrs}>")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.allowed_tags:
            self.output.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.output.append(html.escape(data))
        if data.strip():
            self.text.append(data.strip())


def sanitize_table_html(source: str) -> str:
    parser = _TableSanitizer()
    parser.feed(source)
    return "".join(parser.output)


def table_text(source: str) -> str:
    parser = _TableSanitizer()
    parser.feed(source)
    return " ".join(parser.text)


class ElementRouter:
    def __init__(
        self,
        store: ArtifactStore,
        cropper: PageRegionCropper,
        fallbacks: list[FallbackProcessor] | None = None,
        confidence_threshold: float = 0.65,
    ):
        self.store = store
        self.cropper = cropper
        self.fallbacks = fallbacks or [NoopFallback()]
        self.confidence_threshold = confidence_threshold

    def route(self, block: DocumentBlock) -> Artifact | None:
        if self._needs_fallback(block):
            block = self._fallback(block)
        handlers = {
            ElementType.TABLE: self._table,
            ElementType.CHART: self._chart,
            ElementType.GRAPH: self._chart,
            ElementType.IMAGE: self._image,
            ElementType.PHOTOGRAPH: self._image,
            ElementType.DIAGRAM: self._diagram,
        }
        handler = handlers.get(block.element_type, self._text)
        return handler(block)

    def _needs_fallback(self, block: DocumentBlock) -> bool:
        if block.confidence is not None and block.confidence < self.confidence_threshold:
            return True
        if block.element_type == ElementType.TABLE:
            return not block.html and not block.structured_data
        if block.element_type in {ElementType.CHART, ElementType.GRAPH}:
            return not block.structured_data
        return False

    def _fallback(self, block: DocumentBlock) -> DocumentBlock:
        for fallback in self.fallbacks:
            if fallback.supports(block):
                return fallback.enrich(block, None)
        return block

    def _text(self, block: DocumentBlock) -> Artifact | None:
        text = " ".join(block.text.split())
        if not text or block.element_type in {
            ElementType.HEADER, ElementType.FOOTER, ElementType.PAGE_NUMBER
        }:
            return None
        prefix = "# " if block.element_type == ElementType.HEADING else ""
        content = prefix + text
        path = self.store.write_text(
            f"text/{block.block_id}.md", content
        )
        return self._artifact(block, "text/markdown", path, content, content)

    def _table(self, block: DocumentBlock) -> Artifact:
        source = (
            block.html
            or self._table_from_data(block.structured_data)
            or self._table_from_markdown(block.text)
        )
        safe = sanitize_table_html(source or "<table></table>")
        path = self.store.write_text(f"tables/{block.block_id}.html", safe)
        json_path = self.store.write_json(
            f"tables/{block.block_id}.json", block.structured_data
        )
        preview_path = self._crop_visual(block, "tables")
        searchable = table_text(safe)
        embedding = self._context(block, f"Table: {searchable}")
        return self._artifact(
            block,
            "text/html",
            path,
            safe,
            embedding,
            {
                "structured_data_path": json_path,
                "preview_path": preview_path,
            },
        )

    def _chart(self, block: DocumentBlock) -> Artifact:
        spec = self._chart_spec(block)
        preview_path = self._crop_visual(block, "charts")
        if preview_path:
            spec["preview_path"] = preview_path
        json_path = self.store.write_json(f"charts/{block.block_id}.json", spec)
        html_card = self._chart_html(spec)
        html_path = self.store.write_text(f"charts/{block.block_id}.html", html_card)
        if spec["verification_status"] == "verified":
            chart_context = "Chart: " + " ".join(
                str(spec.get(key, ""))
                for key in ("title", "chart_type", "description", "categories", "series")
            )
        else:
            searchable_labels = self._chart_searchable_labels(block.text)
            chart_context = (
                f"Chart: {spec['title']} ({spec['chart_type']}). "
                f"Visible labels: {searchable_labels}. "
                "Visual values require verification from the saved PNG preview."
            )
        embedding = self._context(block, chart_context)
        return self._artifact(
            block,
            "text/html",
            html_path,
            html_card,
            embedding,
            {
                "spec_path": json_path,
                "preview_path": preview_path,
                "title": spec["title"],
                "verification_status": spec["verification_status"],
            },
        )

    @staticmethod
    def _chart_searchable_labels(source: str) -> str:
        """Keep chart words searchable without indexing uncertain numeric values."""
        without_numbers = re.sub(
            r"(?<![A-Za-z])(?:₹|\$)?[~<>]?\d[\d,]*(?:\.\d+)?%?",
            " ",
            source,
        )
        without_markdown = re.sub(r"[:|*`#\-]+", " ", without_numbers)
        words = re.findall(r"[A-Za-z][A-Za-z/()&.]*", without_markdown)
        return " ".join(words[:160])

    def _image(self, block: DocumentBlock) -> Artifact:
        relative = self._crop_visual(block, "images") or ""
        embedding = self._context(block, f"Image: {block.text or block.caption or 'visual element'}")
        return self._artifact(block, "image/png", relative or None, None, embedding)

    def _crop_visual(self, block: DocumentBlock, directory: str) -> str | None:
        if not block.bounding_box:
            return None
        relative = f"{directory}/{block.block_id}.png"
        output = self.store.safe_path(relative)
        output.parent.mkdir(parents=True, exist_ok=True)
        self.cropper.crop_png(
            block.page_number,
            block.bounding_box.as_tuple(),
            output,
            source_width=block.metadata.get("coordinate_width"),
            source_height=block.metadata.get("coordinate_height"),
        )
        return relative

    def _diagram(self, block: DocumentBlock) -> Artifact:
        nodes = block.structured_data.get("nodes")
        edges = block.structured_data.get("edges")
        if nodes and edges:
            spec = {"renderer": "mermaid", "nodes": nodes, "edges": edges}
            path = self.store.write_json(f"diagrams/{block.block_id}.json", spec)
            preview_path = self._crop_visual(block, "diagrams")
            return self._artifact(
                block, "application/json", path, json.dumps(spec),
                self._context(block, f"Diagram: {block.text}"),
                {"preview_path": preview_path},
            )
        return self._image(block)

    @staticmethod
    def _table_from_data(data: dict[str, Any]) -> str:
        headers = data.get("headers") or []
        rows = data.get("rows") or []
        if not headers and not rows:
            return ""
        head = "".join(f"<th>{html.escape(str(value))}</th>" for value in headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
            for row in rows if isinstance(row, list)
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    @staticmethod
    def _table_from_markdown(source: str) -> str:
        rows = [
            [cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in source.splitlines()
            if line.strip().startswith("|") and line.strip().endswith("|")
        ]
        if len(rows) < 2:
            return ""
        separator = rows[1]
        if not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in separator):
            return ""
        headers = rows[0]
        body_rows = rows[2:]
        head = "".join(f"<th>{html.escape(value)}</th>" for value in headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(value)}</td>" for value in row) + "</tr>"
            for row in body_rows
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    @staticmethod
    def _chart_spec(block: DocumentBlock) -> dict[str, Any]:
        data = block.structured_data
        categories = data.get("categories") or data.get("x_axis", {}).get("values", [])
        series = data.get("series") or []
        reliable = bool(categories and series)
        return {
            "chart_id": block.block_id,
            "chart_type": data.get("chart_type") or block.subtype or "unknown",
            "title": ElementRouter._chart_title(block),
            "description": data.get("description") or block.text,
            "categories": categories,
            "series": series if reliable else [],
            "source_page": block.page_number,
            "verification_status": "verified" if reliable else "visual_only",
            "render": {"library": "echarts", "renderer": "svg"},
        }

    @staticmethod
    def _chart_title(block: DocumentBlock) -> str:
        explicit = block.structured_data.get("title") or block.caption
        if explicit:
            return " ".join(str(explicit).split())

        rows = [
            [cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in block.text.splitlines()
            if line.strip().startswith("|") and line.strip().endswith("|")
        ]
        headers = rows[0] if rows else []
        dimension = headers[0] if headers else ""
        measures = []
        for header in headers[1:5]:
            cleaned = re.sub(r"\s*\([^)]*\)", "", header).strip()
            cleaned = re.sub(r"\b(?:estimated?|calculated)\b", "", cleaned, flags=re.I)
            cleaned = " ".join(cleaned.split()).strip(" -/")
            if cleaned and cleaned.lower() not in {"value", "values"}:
                measures.append(cleaned)
        if measures:
            if len(measures) == 1:
                subject = measures[0]
            else:
                subject = ", ".join(measures[:-1]) + f" and {measures[-1]}"
            derived = f"{subject} by {dimension}" if dimension else subject
        elif block.parent_section:
            derived = block.parent_section
        else:
            derived = f"Chart on page {block.page_number}"

        if block.parent_section and block.parent_section.lower() not in derived.lower():
            derived = f"{block.parent_section}: {derived}"
        return " ".join(derived.split())

    @staticmethod
    def _chart_html(spec: dict[str, Any]) -> str:
        title = html.escape(str(spec["title"]))
        description = html.escape(str(spec["description"]))
        encoded = html.escape(json.dumps(spec, ensure_ascii=False), quote=True)
        note = (
            "Interactive SVG chart data is available."
            if spec["verification_status"] == "verified"
            else "Exact plotted values were not reliable; no values were invented."
        )
        preview = ""
        if spec.get("preview_path"):
            preview_src = html.escape(Path(str(spec["preview_path"])).name)
            preview = (
                f'<img class="document-chart__preview" src="{preview_src}" '
                f'alt="{title}" loading="lazy">'
            )
        return (
            f'<figure class="document-chart" data-chart-spec="{encoded}">'
            f"<h3>{title}</h3><p>{description}</p>"
            f"{preview}"
            f'<div class="document-chart__canvas" role="img" aria-label="{title}"></div>'
            f"<figcaption>{html.escape(note)} Page {spec['source_page']}.</figcaption>"
            "</figure>"
        )

    @staticmethod
    def _context(block: DocumentBlock, content: str) -> str:
        return "\n".join(filter(None, [
            block.parent_section,
            block.caption,
            content.strip(),
            f"Source page: {block.page_number}",
        ]))

    @staticmethod
    def _artifact(
        block: DocumentBlock,
        media_type: str,
        path: str | None,
        content: str | None,
        embedding: str,
        metadata: dict[str, Any] | None = None,
    ) -> Artifact:
        return Artifact(
            artifact_id=f"artifact_{block.block_id}",
            document_id=block.document_id,
            block_id=block.block_id,
            element_type=block.element_type,
            page_number=block.page_number,
            media_type=media_type,
            relative_path=path,
            content=content,
            embedding_text=embedding,
            metadata={
                "reading_order": block.reading_order,
                "confidence": block.confidence,
                **(metadata or {}),
            },
        )
