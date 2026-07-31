import logging
from dataclasses import dataclass
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PdfChunk:
    chunk_number: int
    start_page: int
    end_page: int
    path: Path

    @property
    def page_offset(self) -> int:
        return self.start_page - 1


class AdaptivePdfSplitter:
    """Split for API transport; semantic chunking happens after normalization."""

    def __init__(self, max_pages: int = 10, max_bytes: int = 20_000_000):
        self.max_pages = min(max_pages, 10)
        self.max_bytes = max_bytes

    def split(self, source: Path, output_dir: Path) -> list[PdfChunk]:
        reader = PdfReader(str(source))
        output_dir.mkdir(parents=True, exist_ok=True)
        chunks: list[PdfChunk] = []
        start = 0
        chunk_number = 1
        while start < len(reader.pages):
            size = min(self.max_pages, len(reader.pages) - start)
            chunk = self._write(reader, source, output_dir, start, size, chunk_number)
            while chunk.path.stat().st_size > self.max_bytes and size > 1:
                chunk.path.unlink(missing_ok=True)
                size = max(1, size // 2)
                chunk = self._write(
                    reader, source, output_dir, start, size, chunk_number
                )
            chunks.append(chunk)
            logger.info(
                "Prepared chunk %s covering pages %s-%s",
                chunk_number,
                chunk.start_page,
                chunk.end_page,
            )
            start += size
            chunk_number += 1
        return chunks

    def split_failed_chunk(self, chunk: PdfChunk, output_dir: Path) -> list[PdfChunk]:
        page_count = chunk.end_page - chunk.start_page + 1
        if page_count <= 1:
            return [chunk]
        local = AdaptivePdfSplitter(max_pages=max(1, page_count // 2), max_bytes=self.max_bytes)
        parts = local.split(chunk.path, output_dir)
        return [
            PdfChunk(
                chunk_number=chunk.chunk_number * 100 + index,
                start_page=chunk.start_page + part.start_page - 1,
                end_page=chunk.start_page + part.end_page - 1,
                path=part.path,
            )
            for index, part in enumerate(parts, 1)
        ]

    @staticmethod
    def _write(
        reader: PdfReader,
        source: Path,
        output_dir: Path,
        start: int,
        size: int,
        number: int,
    ) -> PdfChunk:
        writer = PdfWriter()
        end = min(start + size, len(reader.pages))
        for index in range(start, end):
            writer.add_page(reader.pages[index])
        path = output_dir / f"{source.stem}.part-{number:04d}.p{start + 1}-{end}.pdf"
        with path.open("wb") as handle:
            writer.write(handle)
        return PdfChunk(number, start + 1, end, path)
