from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ElementType(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    CHART = "chart"
    GRAPH = "graph"
    IMAGE = "image"
    PHOTOGRAPH = "photograph"
    DIAGRAM = "diagram"
    CAPTION = "caption"
    FORMULA = "formula"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    SOURCE = "source"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

    def as_tuple(self) -> tuple[float, float, float, float]:
        return self.x1, self.y1, self.x2, self.y2


class DocumentBlock(BaseModel):
    block_id: str
    document_id: str
    page_number: int = Field(ge=1)
    element_type: ElementType = ElementType.UNKNOWN
    subtype: str | None = None
    reading_order: int = Field(default=0, ge=0)
    bounding_box: BoundingBox | None = None
    text: str = ""
    html: str | None = None
    structured_data: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)
    caption: str | None = None
    parent_section: str | None = None
    source_chunk: int | None = None
    source_job_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedPage(BaseModel):
    page_number: int = Field(ge=1)
    width: float | None = None
    height: float | None = None
    blocks: list[DocumentBlock] = Field(default_factory=list)


class NormalizedDocument(BaseModel):
    document_id: str
    source_file: str
    sha256: str
    pages: list[NormalizedPage] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    artifact_id: str
    document_id: str
    block_id: str
    element_type: ElementType
    page_number: int
    media_type: str
    relative_path: str | None = None
    content: str | None = None
    embedding_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessingManifest(BaseModel):
    document_id: str
    source_file: str
    sha256: str
    status: str = "processing"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None
    errors: list[str] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
