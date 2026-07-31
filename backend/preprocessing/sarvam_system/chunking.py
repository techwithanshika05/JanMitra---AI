from dataclasses import dataclass, field

from .documents import Artifact

@dataclass
class RagChunk:
    chunk_id: str
    text: str
    metadata: dict[str, str | int | float | None] = field(default_factory=dict)


class SemanticChunkBuilder:
    def __init__(self, max_characters: int = 2400, overlap: int = 240):
        self.max_characters = max_characters
        self.overlap = overlap

    def build(self, artifacts: list[Artifact]) -> list[RagChunk]:
        chunks: list[RagChunk] = []
        for artifact in artifacts:
            text = artifact.embedding_text.strip()
            if not text:
                continue
            pieces = self._split(text)
            for index, piece in enumerate(pieces):
                chunks.append(RagChunk(
                    chunk_id=f"{artifact.artifact_id}_{index:03d}",
                    text=piece,
                    metadata={
                        "document_id": artifact.document_id,
                        "block_id": artifact.block_id,
                        "content_type": artifact.element_type.value,
                        "page_number": artifact.page_number,
                        "artifact_path": artifact.relative_path or "",
                        "preview_path": str(
                            artifact.metadata.get("preview_path") or ""
                        ),
                        "title": str(artifact.metadata.get("title") or ""),
                        "media_type": artifact.media_type,
                    },
                ))
        return chunks

    def _split(self, text: str) -> list[str]:
        if len(text) <= self.max_characters:
            return [text]
        output: list[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + self.max_characters)
            if end < len(text):
                boundary = text.rfind("\n", start, end)
                if boundary > start:
                    end = boundary
            output.append(text[start:end].strip())
            start = max(end - self.overlap, start + 1)
        return [piece for piece in output if piece]
