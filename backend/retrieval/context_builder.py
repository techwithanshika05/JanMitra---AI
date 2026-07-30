"""
context_builder.py

Context construction module for the JanMitra RAG system.

This module receives retrieved document chunks from the retriever
and converts them into clean, structured context that can be passed
to an LLM.

Responsibilities:
1. Normalize retrieved results.
2. Remove empty chunks.
3. Remove duplicate chunks.
4. Sort chunks by relevance.
5. Optionally filter chunks by relevance score.
6. Respect a maximum context character limit.
7. Preserve source metadata.
8. Build readable source references.
9. Produce LLM-ready context.

This module DOES NOT:
- Generate embeddings.
- Search ChromaDB.
- Call the LLM.

Pipeline:

User Query
    ->
QueryProcessor
    ->
Retriever
    ->
ContextBuilder
    ->
LLM
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence


# ============================================================
# Logging
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# Data Models
# ============================================================

@dataclass
class ContextSource:
    """
    Represents the source of a retrieved context chunk.
    """

    source_id: int

    file_name: str = "Unknown document"

    page_number: Optional[int] = None

    chunk_id: Optional[str] = None

    document_id: Optional[str] = None

    score: Optional[float] = None

    distance: Optional[float] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContextChunk:
    """
    Normalized chunk used internally by ContextBuilder.
    """

    text: str

    file_name: str

    page_number: Optional[int]

    chunk_id: Optional[str]

    document_id: Optional[str]

    score: Optional[float]

    distance: Optional[float]

    metadata: Dict[str, Any]

    original_index: int


@dataclass
class BuiltContext:
    """
    Final result returned by ContextBuilder.

    Attributes:
        context:
            Formatted context ready to send to the LLM.

        sources:
            Structured source information.

        chunks:
            Normalized chunks included in the context.

        total_chunks:
            Number of chunks included.

        total_characters:
            Number of characters in the final context.

        truncated:
            True if some retrieved chunks could not be included
            because of the configured context size.
    """

    context: str

    sources: List[ContextSource]

    chunks: List[ContextChunk]

    total_chunks: int

    total_characters: int

    truncated: bool

    def to_dict(self) -> Dict[str, Any]:

        return {
            "context": self.context,
            "sources": [
                source.to_dict()
                for source in self.sources
            ],
            "chunks": [
                asdict(chunk)
                for chunk in self.chunks
            ],
            "total_chunks": self.total_chunks,
            "total_characters": self.total_characters,
            "truncated": self.truncated,
        }


# ============================================================
# Context Builder
# ============================================================

class ContextBuilder:
    """
    Builds LLM-ready context from retrieved document chunks.

    Example:

        builder = ContextBuilder()

        result = builder.build(
            retrieved_results
        )

        print(result.context)
    """

    def __init__(
        self,
        max_context_characters: int = 16000,
        max_chunks: int = 8,
        min_score: Optional[float] = None,
        remove_duplicates: bool = True,
        include_source_headers: bool = True,
    ) -> None:
        """
        Initialize ContextBuilder.

        Args:
            max_context_characters:
                Maximum number of characters allowed in the
                generated context.

            max_chunks:
                Maximum number of chunks included.

            min_score:
                Optional minimum relevance score.

                Leave as None if your retriever returns Chroma
                distances rather than normalized similarity
                scores.

            remove_duplicates:
                Remove duplicate or nearly identical chunks.

            include_source_headers:
                Include source and page information before
                every chunk.
        """

        if max_context_characters <= 0:
            raise ValueError(
                "max_context_characters must be greater than 0."
            )

        if max_chunks <= 0:
            raise ValueError(
                "max_chunks must be greater than 0."
            )

        self.max_context_characters = (
            max_context_characters
        )

        self.max_chunks = max_chunks

        self.min_score = min_score

        self.remove_duplicates = (
            remove_duplicates
        )

        self.include_source_headers = (
            include_source_headers
        )

        logger.info(
            "ContextBuilder initialized | "
            "max_characters=%d | max_chunks=%d",
            self.max_context_characters,
            self.max_chunks,
        )

    # ========================================================
    # Public API
    # ========================================================

    def build(
        self,
        retrieved_results: Sequence[Any],
    ) -> BuiltContext:
        """
        Build context from retrieved results.

        Args:
            retrieved_results:
                Results returned by Retriever.

        Returns:
            BuiltContext
        """

        if not retrieved_results:

            logger.warning(
                "No retrieved results provided "
                "to ContextBuilder."
            )

            return BuiltContext(
                context="",
                sources=[],
                chunks=[],
                total_chunks=0,
                total_characters=0,
                truncated=False,
            )

        # ----------------------------------------------------
        # Normalize results
        # ----------------------------------------------------

        chunks = self._normalize_results(
            retrieved_results
        )

        logger.debug(
            "Normalized %d retrieved chunks.",
            len(chunks),
        )

        # ----------------------------------------------------
        # Remove empty chunks
        # ----------------------------------------------------

        chunks = [
            chunk
            for chunk in chunks
            if chunk.text.strip()
        ]

        # ----------------------------------------------------
        # Filter by score
        # ----------------------------------------------------

        if self.min_score is not None:

            chunks = [
                chunk
                for chunk in chunks
                if (
                    chunk.score is None
                    or chunk.score >= self.min_score
                )
            ]

        # ----------------------------------------------------
        # Remove duplicates
        # ----------------------------------------------------

        if self.remove_duplicates:

            chunks = self._deduplicate_chunks(
                chunks
            )

        # ----------------------------------------------------
        # Sort by relevance
        # ----------------------------------------------------

        chunks = self._sort_chunks(
            chunks
        )

        # ----------------------------------------------------
        # Limit number of chunks
        # ----------------------------------------------------

        chunks_before_limit = len(chunks)

        chunks = chunks[
            :self.max_chunks
        ]

        truncated = (
            chunks_before_limit
            > self.max_chunks
        )

        # ----------------------------------------------------
        # Build formatted context
        # ----------------------------------------------------

        selected_chunks: List[
            ContextChunk
        ] = []

        context_parts: List[str] = []

        current_length = 0

        for source_number, chunk in enumerate(
            chunks,
            start=1,
        ):

            formatted_chunk = (
                self._format_chunk(
                    chunk=chunk,
                    source_number=source_number,
                )
            )

            additional_length = len(
                formatted_chunk
            )

            if context_parts:

                additional_length += 2

            # If adding this chunk exceeds limit
            if (
                current_length
                + additional_length
                > self.max_context_characters
            ):

                truncated = True

                logger.debug(
                    "Context character limit reached."
                )

                break

            context_parts.append(
                formatted_chunk
            )

            selected_chunks.append(
                chunk
            )

            current_length += (
                additional_length
            )

        context = "\n\n".join(
            context_parts
        )

        # ----------------------------------------------------
        # Build structured sources
        # ----------------------------------------------------

        sources = self._build_sources(
            selected_chunks
        )

        result = BuiltContext(
            context=context,
            sources=sources,
            chunks=selected_chunks,
            total_chunks=len(
                selected_chunks
            ),
            total_characters=len(
                context
            ),
            truncated=truncated,
        )

        logger.info(
            "Context built successfully | "
            "chunks=%d | characters=%d | "
            "truncated=%s",
            result.total_chunks,
            result.total_characters,
            result.truncated,
        )

        return result

    # ========================================================
    # Result Normalization
    # ========================================================

    def _normalize_results(
        self,
        results: Sequence[Any],
    ) -> List[ContextChunk]:
        """
        Convert different retriever result formats into
        ContextChunk objects.

        Supports:

        1. Dictionaries

        {
            "text": "...",
            "metadata": {...},
            "score": 0.9
        }

        2. Dictionaries using "document"

        {
            "document": "...",
            "metadata": {...},
            "distance": 0.2
        }

        3. Objects with attributes such as:

            result.text
            result.metadata
            result.score
        """

        normalized: List[
            ContextChunk
        ] = []

        for index, result in enumerate(
            results
        ):

            try:

                chunk = self._normalize_single_result(
                    result=result,
                    index=index,
                )

                if chunk is not None:

                    normalized.append(
                        chunk
                    )

            except Exception:

                logger.exception(
                    "Failed to normalize "
                    "retrieval result at index %d.",
                    index,
                )

        return normalized

    def _normalize_single_result(
        self,
        result: Any,
        index: int,
    ) -> Optional[ContextChunk]:
        """
        Normalize one retrieval result.
        """

        # ----------------------------------------------------
        # Dictionary result
        # ----------------------------------------------------

        if isinstance(
            result,
            dict,
        ):

            text = (
                result.get("text")
                or result.get("document")
                or result.get("content")
                or result.get("page_content")
                or ""
            )

            metadata = (
                result.get("metadata")
                or {}
            )

            score = self._to_float(
                result.get("score")
            )

            distance = self._to_float(
                result.get("distance")
            )

        # ----------------------------------------------------
        # Object result
        # ----------------------------------------------------

        else:

            text = (
                getattr(
                    result,
                    "text",
                    None,
                )
                or getattr(
                    result,
                    "document",
                    None,
                )
                or getattr(
                    result,
                    "content",
                    None,
                )
                or getattr(
                    result,
                    "page_content",
                    None,
                )
                or ""
            )

            metadata = (
                getattr(
                    result,
                    "metadata",
                    None,
                )
                or {}
            )

            score = self._to_float(
                getattr(
                    result,
                    "score",
                    None,
                )
            )

            distance = self._to_float(
                getattr(
                    result,
                    "distance",
                    None,
                )
            )

        # ----------------------------------------------------
        # Validate metadata
        # ----------------------------------------------------

        if not isinstance(
            metadata,
            dict,
        ):

            metadata = {}

        # ----------------------------------------------------
        # Clean text
        # ----------------------------------------------------

        text = self._clean_text(
            str(text)
        )

        if not text:

            return None

        # ----------------------------------------------------
        # Extract common metadata fields
        # ----------------------------------------------------

        file_name = self._get_first_value(
            metadata,
            [
                "file_name",
                "filename",
                "source_file",
                "source",
                "document_name",
            ],
            default="Unknown document",
        )

        page_number = self._get_page_number(
            metadata
        )

        chunk_id = self._get_first_value(
            metadata,
            [
                "chunk_id",
                "id",
            ],
            default=None,
        )

        document_id = self._get_first_value(
            metadata,
            [
                "document_id",
                "doc_id",
            ],
            default=None,
        )

        # Some retrievers may store score/distance
        # inside metadata.

        if score is None:

            score = self._to_float(
                metadata.get(
                    "score"
                )
            )

        if distance is None:

            distance = self._to_float(
                metadata.get(
                    "distance"
                )
            )

        return ContextChunk(
            text=text,
            file_name=str(
                file_name
            ),
            page_number=page_number,
            chunk_id=(
                str(chunk_id)
                if chunk_id is not None
                else None
            ),
            document_id=(
                str(document_id)
                if document_id is not None
                else None
            ),
            score=score,
            distance=distance,
            metadata=dict(
                metadata
            ),
            original_index=index,
        )

    # ========================================================
    # Deduplication
    # ========================================================

    def _deduplicate_chunks(
        self,
        chunks: List[ContextChunk],
    ) -> List[ContextChunk]:
        """
        Remove exact normalized duplicate chunks.

        Duplicate detection is based on a hash of normalized
        text.
        """

        unique_chunks: List[
            ContextChunk
        ] = []

        seen_hashes = set()

        for chunk in chunks:

            normalized_text = re.sub(
                r"\s+",
                " ",
                chunk.text.lower(),
            ).strip()

            text_hash = hashlib.sha256(
                normalized_text.encode(
                    "utf-8"
                )
            ).hexdigest()

            if text_hash in seen_hashes:

                logger.debug(
                    "Duplicate chunk removed: %s",
                    chunk.chunk_id,
                )

                continue

            seen_hashes.add(
                text_hash
            )

            unique_chunks.append(
                chunk
            )

        return unique_chunks

    # ========================================================
    # Sorting
    # ========================================================

    def _sort_chunks(
        self,
        chunks: List[ContextChunk],
    ) -> List[ContextChunk]:
        """
        Sort chunks by relevance.

        Priority:

        1. score:
           Higher score = more relevant.

        2. distance:
           Lower distance = more relevant.

        3. original retrieval order.

        This allows the builder to work with retrievers that
        return either similarity scores or Chroma distances.
        """

        def sort_key(
            chunk: ContextChunk,
        ):

            if chunk.score is not None:

                return (
                    0,
                    -chunk.score,
                    chunk.original_index,
                )

            if chunk.distance is not None:

                return (
                    1,
                    chunk.distance,
                    chunk.original_index,
                )

            return (
                2,
                0,
                chunk.original_index,
            )

        return sorted(
            chunks,
            key=sort_key,
        )

    # ========================================================
    # Context Formatting
    # ========================================================

    def _format_chunk(
        self,
        chunk: ContextChunk,
        source_number: int,
    ) -> str:
        """
        Format one chunk for the LLM.
        """

        if not self.include_source_headers:

            return chunk.text

        header_parts = [
            f"Source {source_number}",
            f"Document: {chunk.file_name}",
        ]

        if chunk.page_number is not None:

            header_parts.append(
                f"Page: {chunk.page_number}"
            )

        if chunk.chunk_id:

            header_parts.append(
                f"Chunk: {chunk.chunk_id}"
            )

        header = " | ".join(
            header_parts
        )

        return (
            f"[{header}]\n"
            f"{chunk.text}"
        )

    # ========================================================
    # Source Construction
    # ========================================================

    def _build_sources(
        self,
        chunks: List[ContextChunk],
    ) -> List[ContextSource]:
        """
        Build structured source objects corresponding to the
        context chunks.

        Each source number matches the number shown inside the
        generated context.
        """

        sources: List[
            ContextSource
        ] = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            source = ContextSource(
                source_id=index,
                file_name=chunk.file_name,
                page_number=chunk.page_number,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                score=chunk.score,
                distance=chunk.distance,
                metadata=chunk.metadata,
            )

            sources.append(
                source
            )

        return sources

    # ========================================================
    # Helper Methods
    # ========================================================

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:
        """
        Clean chunk text without damaging multilingual content.
        """

        text = text.replace(
            "\x00",
            " ",
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    @staticmethod
    def _get_first_value(
        metadata: Dict[str, Any],
        keys: List[str],
        default: Any = None,
    ) -> Any:
        """
        Return the first available non-empty metadata value.
        """

        for key in keys:

            value = metadata.get(
                key
            )

            if value is not None:

                if (
                    isinstance(
                        value,
                        str,
                    )
                    and not value.strip()
                ):

                    continue

                return value

        return default

    @staticmethod
    def _get_page_number(
        metadata: Dict[str, Any],
    ) -> Optional[int]:
        """
        Extract page number from common metadata fields.
        """

        possible_keys = [
            "page_number",
            "page",
            "page_no",
            "page_index",
        ]

        for key in possible_keys:

            value = metadata.get(
                key
            )

            if value is None:

                continue

            try:

                return int(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

        return None

    @staticmethod
    def _to_float(
        value: Any,
    ) -> Optional[float]:
        """
        Safely convert a value to float.
        """

        if value is None:

            return None

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None


# ============================================================
# Manual Test
# ============================================================

def main() -> None:
    """
    Manual test.

    Run from backend directory:

        python -m retrieval.context_builder
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
    )

    # --------------------------------------------------------
    # Example results similar to what a retriever might return
    # --------------------------------------------------------

    test_results = [

        {
            "text": (
                "PM-KISAN provides financial assistance "
                "to eligible farmer families."
            ),
            "metadata": {
                "file_name": (
                    "pm_kisan_guidelines.pdf"
                ),
                "page_number": 5,
                "chunk_id": (
                    "pm_kisan_p5_c1"
                ),
            },
            "score": 0.94,
        },

        {
            "text": (
                "Eligible beneficiaries receive financial "
                "assistance in installments through Direct "
                "Benefit Transfer."
            ),
            "metadata": {
                "file_name": (
                    "pm_kisan_guidelines.pdf"
                ),
                "page_number": 6,
                "chunk_id": (
                    "pm_kisan_p6_c2"
                ),
            },
            "score": 0.89,
        },

        {
            "text": (
                "Applicants should provide the required "
                "identity and land-related information."
            ),
            "metadata": {
                "file_name": (
                    "pm_kisan_faq.pdf"
                ),
                "page_number": 3,
                "chunk_id": (
                    "pm_kisan_faq_p3_c1"
                ),
            },
            "score": 0.81,
        },

    ]

    builder = ContextBuilder(
        max_context_characters=8000,
        max_chunks=5,
    )

    result = builder.build(
        test_results
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "JANMITRA - CONTEXT BUILDER TEST"
    )

    print(
        "=" * 60
    )

    print(
        "\nLLM CONTEXT:\n"
    )

    print(
        result.context
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "SOURCES"
    )

    print(
        "=" * 60
    )

    for source in result.sources:

        print(
            source.to_dict()
        )

    print(
        "\n"
        + "=" * 60
    )

    print(
        f"Chunks: "
        f"{result.total_chunks}"
    )

    print(
        f"Characters: "
        f"{result.total_characters}"
    )

    print(
        f"Truncated: "
        f"{result.truncated}"
    )


if __name__ == "__main__":
    main()