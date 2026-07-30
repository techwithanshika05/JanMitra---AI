"""Examples of optional fallback adapters.

Install and implement only the processors needed by the deployment. Keeping
these adapters separate prevents heavyweight OCR/chart models from loading on
pages Sarvam already processed successfully.
"""

from pathlib import Path

from .artifacts import FallbackProcessor
from .documents import DocumentBlock, ElementType

class PaddleTableFallback(FallbackProcessor):
    def supports(self, block: DocumentBlock) -> bool:
        return block.element_type == ElementType.TABLE

    def enrich(self, block: DocumentBlock, page_image: Path | None) -> DocumentBlock:
        raise NotImplementedError(
            "Connect PP-StructureV3 here and populate block.html/structured_data"
        )


class ChartParserFallback(FallbackProcessor):
    def supports(self, block: DocumentBlock) -> bool:
        return block.element_type in {ElementType.CHART, ElementType.GRAPH}

    def enrich(self, block: DocumentBlock, page_image: Path | None) -> DocumentBlock:
        raise NotImplementedError(
            "Parse the cropped region, validate labels/values, then populate "
            "categories and series. Never infer missing values."
        )
