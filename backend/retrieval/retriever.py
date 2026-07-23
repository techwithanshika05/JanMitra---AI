
"""
retriever.py

Purpose:
--------
Retrieve relevant PDS and Social Welfare document chunks from
ChromaDB using multilingual semantic search.

Pipeline:
---------
User Question
    ↓
EmbeddingService
    ↓
Multilingual Query Embedding
    ↓
ChromaStore
    ↓
Vector Similarity Search
    ↓
Optional Metadata Filters
    ↓
Similarity Threshold
    ↓
Relevant Chunks
    ↓
Citation-Ready RAG Context
    ↓
LLM / RAG Service

Supported Queries:
------------------
English:
    "What documents are required for a ration card?"

Hindi:
    "राशन कार्ड के लिए कौन से दस्तावेज चाहिए?"

Hinglish:
    "Ration card ke liye kya documents chahiye?"

Important:
----------
The same embedding model MUST be used for:

1. Document embeddings
2. Query embeddings

This project uses:

sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Required internal modules:
--------------------------
embeddings/embedding_service.py
vectorstore/chroma_store.py

Run:
----
python retrieval/retriever.py
"""

import logging
from typing import Any, Dict, List, Optional

from embeddings.embedding_service import EmbeddingService
from vectorstore.chroma_store import ChromaStore


# ============================================================
# Configuration
# ============================================================

DEFAULT_TOP_K = 5

# Fetch more candidates than ultimately returned.
# This is useful when filtering or deduplicating.
DEFAULT_CANDIDATE_MULTIPLIER = 3

# Retrieval score threshold.
#
# ChromaStore converts cosine distance to:
#
# similarity = 1 - distance
#
# This should NOT be treated as calibrated confidence.
#
# Start low while testing your own dataset, then tune using
# evaluation questions.
DEFAULT_MIN_SIMILARITY = 0.20

DEFAULT_MAX_CONTEXT_CHARACTERS = 12000


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Multilingual Retriever
# ============================================================

class MultilingualRetriever:
    """
    Retrieval layer for the PDS and Social Welfare RAG system.

    Responsibilities:
    -----------------
    1. Accept English, Hindi, or Hinglish query.
    2. Generate multilingual query embedding.
    3. Search ChromaDB.
    4. Apply optional metadata filters.
    5. Remove results below similarity threshold.
    6. Remove duplicate chunks.
    7. Return ranked results.
    8. Build citation-ready RAG context.

    This class does NOT generate an AI answer.

    It only retrieves evidence.

    The retrieved evidence should later be passed to the LLM
    with a grounded prompt.
    """

    def __init__(
        self,
        embedding_service: Optional[
            EmbeddingService
        ] = None,
        vector_store: Optional[
            ChromaStore
        ] = None,
        default_top_k: int = DEFAULT_TOP_K,
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
    ) -> None:

        logger.info(
            "Initializing MultilingualRetriever"
        )

        # ----------------------------------------------------
        # Embedding Service
        #
        # IMPORTANT:
        # Must use the same model that was used to generate
        # document embeddings.
        # ----------------------------------------------------

        self.embedding_service = (
            embedding_service
            if embedding_service is not None
            else EmbeddingService()
        )

        # ----------------------------------------------------
        # Vector Store
        # ----------------------------------------------------

        self.vector_store = (
            vector_store
            if vector_store is not None
            else ChromaStore()
        )

        if default_top_k <= 0:

            raise ValueError(
                "default_top_k must be greater than 0."
            )

        self.default_top_k = (
            default_top_k
        )

        self.min_similarity = (
            min_similarity
        )

        logger.info(
            "MultilingualRetriever initialized"
        )

        logger.info(
            "Default top_k: %d",
            self.default_top_k,
        )

        logger.info(
            "Minimum similarity: %.4f",
            self.min_similarity,
        )

        logger.info(
            "Vector store records: %d",
            self.vector_store.count(),
        )

    # ========================================================
    # Query Validation
    # ========================================================

    @staticmethod
    def validate_query(
        query: str,
    ) -> str:
        """
        Validate and normalize a user query.
        """

        if not isinstance(
            query,
            str,
        ):

            raise TypeError(
                "Query must be a string."
            )

        query = query.strip()

        if not query:

            raise ValueError(
                "Query cannot be empty."
            )

        return query

    # ========================================================
    # Build Metadata Filter
    # ========================================================

    @staticmethod
    def build_where_filter(
        state: Optional[str] = None,
        category: Optional[str] = None,
        service: Optional[str] = None,
        document_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Optional[
        Dict[str, Any]
    ]:
        """
        Build a ChromaDB metadata filter.

        Example:

        state="uttar_pradesh"
        category="PDS"

        produces:

        {
            "$and": [
                {
                    "state": "uttar_pradesh"
                },
                {
                    "category": "PDS"
                }
            ]
        }

        A single filter produces:

        {
            "state": "uttar_pradesh"
        }
        """

        filters = []

        filter_values = {
            "state": state,
            "category": category,
            "service": service,
            "document_type": (
                document_type
            ),
            "jurisdiction": (
                jurisdiction
            ),
            "language": language,
        }

        for key, value in (
            filter_values.items()
        ):

            if value is None:

                continue

            if isinstance(
                value,
                str,
            ):

                value = (
                    value.strip()
                )

                if not value:

                    continue

            filters.append(
                {
                    key: value
                }
            )

        if not filters:

            return None

        if len(filters) == 1:

            return filters[0]

        return {
            "$and": filters
        }

    # ========================================================
    # Generate Query Embedding
    # ========================================================

    def embed_query(
        self,
        query: str,
    ) -> List[float]:
        """
        Convert the user query into a multilingual vector.

        Examples:

        English:
            What documents are required for ration card?

        Hindi:
            राशन कार्ड के लिए कौन से दस्तावेज चाहिए?

        Hinglish:
            Ration card ke liye kya documents chahiye?

        All queries use the same multilingual model.
        """

        query = self.validate_query(
            query
        )

        logger.info(
            "Generating query embedding"
        )

        return (
            self.embedding_service.embed_query(
                query
            )
        )

    # ========================================================
    # Remove Duplicate Results
    # ========================================================

    @staticmethod
    def deduplicate_results(
        results: List[
            Dict[str, Any]
        ],
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Remove duplicate chunk IDs.

        Results are expected to already be sorted by
        similarity, so the first occurrence is preserved.
        """

        seen_ids = set()

        unique_results = []

        for result in results:

            chunk_id = result.get(
                "chunk_id"
            )

            if not chunk_id:

                continue

            if chunk_id in seen_ids:

                continue

            seen_ids.add(
                chunk_id
            )

            unique_results.append(
                result
            )

        return unique_results

    # ========================================================
    # Similarity Filtering
    # ========================================================

    @staticmethod
    def filter_by_similarity(
        results: List[
            Dict[str, Any]
        ],
        min_similarity: Optional[
            float
        ],
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Remove retrieval results below a minimum similarity.

        If min_similarity is None, all results are retained.
        """

        if min_similarity is None:

            return results

        filtered = []

        for result in results:

            similarity = (
                result.get(
                    "similarity"
                )
            )

            if similarity is None:

                continue

            if (
                similarity
                >= min_similarity
            ):

                filtered.append(
                    result
                )

        return filtered

    # ========================================================
    # Add Rank
    # ========================================================

    @staticmethod
    def add_ranks(
        results: List[
            Dict[str, Any]
        ],
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Add rank numbers to retrieval results.
        """

        ranked_results = []

        for rank, result in enumerate(
            results,
            start=1,
        ):

            ranked_result = (
                result.copy()
            )

            ranked_result[
                "rank"
            ] = rank

            ranked_results.append(
                ranked_result
            )

        return ranked_results

    # ========================================================
    # Retrieve
    # ========================================================

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[
            float
        ] = None,
        state: Optional[str] = None,
        category: Optional[str] = None,
        service: Optional[str] = None,
        document_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Retrieve relevant chunks for a user query.

        Parameters
        ----------
        query:
            English, Hindi, or Hinglish user query.

        top_k:
            Number of final results.

        min_similarity:
            Optional retrieval score threshold.

        state:
            Example:
                "uttar_pradesh"

        category:
            Example:
                "PDS"

        service:
            Example:
                "ration_card_application"

        document_type:
            Example:
                "GUIDELINE"

        jurisdiction:
            Example:
                "state"

        language:
            Usually you should NOT filter by language when doing
            cross-lingual retrieval.

            Example:
            If the user asks in Hindi and your PDF is English,
            language="hindi" would incorrectly exclude the
            English PDF.

            Therefore language filtering is optional.
        """

        query = self.validate_query(
            query
        )

        if top_k is None:

            top_k = (
                self.default_top_k
            )

        if top_k <= 0:

            raise ValueError(
                "top_k must be greater than 0."
            )

        if min_similarity is None:

            min_similarity = (
                self.min_similarity
            )

        logger.info(
            "Retrieving documents for query: %s",
            query,
        )

        # ----------------------------------------------------
        # Build optional metadata filter
        # ----------------------------------------------------

        where_filter = (
            self.build_where_filter(
                state=state,
                category=category,
                service=service,
                document_type=(
                    document_type
                ),
                jurisdiction=(
                    jurisdiction
                ),
                language=language,
            )
        )

        if where_filter:

            logger.info(
                "Metadata filter: %s",
                where_filter,
            )

        # ----------------------------------------------------
        # Generate multilingual query embedding
        # ----------------------------------------------------

        query_embedding = (
            self.embed_query(
                query
            )
        )

        # ----------------------------------------------------
        # Retrieve extra candidates
        #
        # Fetching more than top_k allows us to perform
        # threshold filtering and deduplication.
        # ----------------------------------------------------

        candidate_top_k = max(
            top_k,
            top_k
            * DEFAULT_CANDIDATE_MULTIPLIER,
        )

        raw_results = (
            self.vector_store.search(
                query_embedding=(
                    query_embedding
                ),
                top_k=(
                    candidate_top_k
                ),
                where=(
                    where_filter
                ),
            )
        )

        logger.info(
            "Raw retrieval results: %d",
            len(raw_results),
        )

        # ----------------------------------------------------
        # Sort by similarity
        #
        # Chroma should already return nearest neighbors in
        # order, but explicit sorting keeps behavior clear.
        # ----------------------------------------------------

        raw_results.sort(
            key=lambda item: (
                item.get(
                    "similarity",
                    float("-inf"),
                )
                if item.get(
                    "similarity"
                )
                is not None
                else float("-inf")
            ),
            reverse=True,
        )

        # ----------------------------------------------------
        # Remove duplicates
        # ----------------------------------------------------

        results = (
            self.deduplicate_results(
                raw_results
            )
        )

        # ----------------------------------------------------
        # Similarity threshold
        # ----------------------------------------------------

        results = (
            self.filter_by_similarity(
                results,
                min_similarity,
            )
        )

        # ----------------------------------------------------
        # Limit final results
        # ----------------------------------------------------

        results = results[
            :top_k
        ]

        # ----------------------------------------------------
        # Add rank
        # ----------------------------------------------------

        results = (
            self.add_ranks(
                results
            )
        )

        logger.info(
            "Final retrieval results: %d",
            len(results),
        )

        return results

    # ========================================================
    # Build Citation Label
    # ========================================================

    @staticmethod
    def build_citation_label(
        result: Dict[str, Any],
    ) -> str:
        """
        Build a human-readable source label.

        Example:

        ration_guidelines.pdf, page 12
        """

        metadata = result.get(
            "metadata",
            {},
        )

        source_file = (
            metadata.get(
                "source_file"
            )
            or "Unknown source"
        )

        page_number = (
            metadata.get(
                "page_number"
            )
        )

        if page_number is not None:

            return (
                f"{source_file}, "
                f"page {page_number}"
            )

        return str(
            source_file
        )

    # ========================================================
    # Build RAG Context
    # ========================================================

    def build_context(
        self,
        results: List[
            Dict[str, Any]
        ],
        max_characters: int = DEFAULT_MAX_CONTEXT_CHARACTERS,
    ) -> str:
        """
        Convert retrieval results into a context block that can
        be passed to the LLM.

        Example:

        [Source 1]
        File: ration.pdf
        Page: 12
        Service: ration_card_application

        Applicants must submit...

        [Source 2]
        ...
        """

        if not results:

            return ""

        context_parts = []

        current_length = 0

        for result in results:

            text = (
                result.get(
                    "text",
                    ""
                )
            ).strip()

            if not text:

                continue

            metadata = (
                result.get(
                    "metadata",
                    {},
                )
            )

            rank = result.get(
                "rank",
                len(
                    context_parts
                ) + 1,
            )

            source_file = (
                metadata.get(
                    "source_file",
                    "Unknown source",
                )
            )

            page_number = (
                metadata.get(
                    "page_number",
                    "Unknown",
                )
            )

            title = (
                metadata.get(
                    "title",
                    "",
                )
            )

            category = (
                metadata.get(
                    "category",
                    "",
                )
            )

            service = (
                metadata.get(
                    "service",
                    "",
                )
            )

            state = (
                metadata.get(
                    "state",
                    "",
                )
            )

            source_block = (
                f"[Source {rank}]\n"
                f"File: {source_file}\n"
                f"Page: {page_number}\n"
            )

            if title:

                source_block += (
                    f"Title: {title}\n"
                )

            if category:

                source_block += (
                    f"Category: {category}\n"
                )

            if service:

                source_block += (
                    f"Service: {service}\n"
                )

            if state:

                source_block += (
                    f"State: {state}\n"
                )

            source_block += (
                "\n"
                + text
            )

            # ------------------------------------------------
            # Context size protection
            # ------------------------------------------------

            if (
                current_length
                + len(source_block)
                > max_characters
            ):

                remaining = (
                    max_characters
                    - current_length
                )

                if remaining > 300:

                    context_parts.append(
                        source_block[
                            :remaining
                        ]
                    )

                break

            context_parts.append(
                source_block
            )

            current_length += len(
                source_block
            )

        return "\n\n".join(
            context_parts
        )

    # ========================================================
    # Build Source List
    # ========================================================

    def build_sources(
        self,
        results: List[
            Dict[str, Any]
        ],
    ) -> List[
        Dict[str, Any]
    ]:
        """
        Build structured source information for UI citations.
        """

        sources = []

        seen = set()

        for result in results:

            metadata = (
                result.get(
                    "metadata",
                    {},
                )
            )

            source_file = (
                metadata.get(
                    "source_file",
                    "Unknown source",
                )
            )

            page_number = (
                metadata.get(
                    "page_number"
                )
            )

            source_key = (
                source_file,
                page_number,
            )

            if source_key in seen:

                continue

            seen.add(
                source_key
            )

            sources.append(
                {
                    "source_file": (
                        source_file
                    ),

                    "page_number": (
                        page_number
                    ),

                    "title": (
                        metadata.get(
                            "title",
                            "",
                        )
                    ),

                    "category": (
                        metadata.get(
                            "category",
                            "",
                        )
                    ),

                    "service": (
                        metadata.get(
                            "service",
                            "",
                        )
                    ),

                    "state": (
                        metadata.get(
                            "state",
                            "",
                        )
                    ),

                    "citation": (
                        self.build_citation_label(
                            result
                        )
                    ),
                }
            )

        return sources

    # ========================================================
    # Retrieve for RAG
    # ========================================================

    def retrieve_for_rag(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_similarity: Optional[
            float
        ] = None,
        state: Optional[str] = None,
        category: Optional[str] = None,
        service: Optional[str] = None,
        document_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        High-level retrieval method for the future RAG service.

        Returns:

        {
            "query": "...",
            "results": [...],
            "context": "...",
            "sources": [...],
            "retrieval_count": 5
        }
        """

        results = self.retrieve(
            query=query,
            top_k=top_k,
            min_similarity=(
                min_similarity
            ),
            state=state,
            category=category,
            service=service,
            document_type=(
                document_type
            ),
            jurisdiction=(
                jurisdiction
            ),
        )

        context = (
            self.build_context(
                results
            )
        )

        sources = (
            self.build_sources(
                results
            )
        )

        return {
            "query": query,

            "results": results,

            "context": context,

            "sources": sources,

            "retrieval_count": len(
                results
            ),
        }


# ============================================================
# Display Results
# ============================================================

def print_results(
    query: str,
    results: List[
        Dict[str, Any]
    ],
) -> None:
    """
    Pretty-print retrieval results for local testing.
    """

    print(
        "\n"
        + "=" * 70
    )

    print(
        "QUERY"
    )

    print(
        "=" * 70
    )

    print(
        query
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "RETRIEVAL RESULTS"
    )

    print(
        "=" * 70
    )

    if not results:

        print(
            "No relevant results found."
        )

        return

    for result in results:

        metadata = result.get(
            "metadata",
            {},
        )

        print(
            f"\nRank: "
            f"{result.get('rank')}"
        )

        similarity = result.get(
            "similarity"
        )

        if similarity is not None:

            print(
                f"Similarity: "
                f"{similarity:.4f}"
            )

        print(
            f"Chunk ID: "
            f"{result.get('chunk_id')}"
        )

        print(
            f"Source: "
            f"{metadata.get('source_file')}"
        )

        print(
            f"Page: "
            f"{metadata.get('page_number')}"
        )

        print(
            f"Category: "
            f"{metadata.get('category')}"
        )

        print(
            f"Service: "
            f"{metadata.get('service')}"
        )

        print(
            f"State: "
            f"{metadata.get('state')}"
        )

        print(
            "\nText:"
        )

        text = result.get(
            "text",
            ""
        )

        preview_length = 600

        if len(text) > preview_length:

            text = (
                text[
                    :preview_length
                ]
                + "..."
            )

        print(
            text
        )

        print(
            "-" * 70
        )


# ============================================================
# Main Test
# ============================================================

def main() -> None:
    """
    Run multilingual retrieval tests.

    Before running:
    ---------------
    1. Run pdf_extractor.py
    2. Run text_cleaner.py
    3. Run metadata_builder.py
    4. Run chunker.py
    5. Run embedding_service.py
    6. Run chroma_store.py
    7. Run retriever.py
    """

    print(
        "\n"
        + "=" * 70
    )

    print(
        "PDS & SOCIAL WELFARE AI "
        "- MULTILINGUAL RETRIEVER"
    )

    print(
        "=" * 70
    )

    try:

        retriever = (
            MultilingualRetriever()
        )

    except Exception as error:

        print(
            "\nFailed to initialize retriever."
        )

        print(
            f"Error: {error}"
        )

        return

    # --------------------------------------------------------
    # Check database
    # --------------------------------------------------------

    record_count = (
        retriever.vector_store.count()
    )

    print(
        f"\nChromaDB records: "
        f"{record_count}"
    )

    if record_count == 0:

        print(
            "\nThe ChromaDB collection is empty."
        )

        print(
            "Run chroma_store.py first."
        )

        return

    # --------------------------------------------------------
    # Multilingual test queries
    # --------------------------------------------------------

    test_queries = [
        (
            "What documents are required "
            "for a ration card?"
        ),

        (
            "राशन कार्ड के लिए कौन से "
            "दस्तावेज चाहिए?"
        ),

        (
            "Ration card ke liye kya "
            "documents chahiye?"
        ),
    ]

    for query in test_queries:

        try:

            results = (
                retriever.retrieve(
                    query=query,
                    top_k=5,

                    # Set this to None temporarily
                    # if you want to inspect all
                    # nearest-neighbor results.
                    min_similarity=0.20,
                )
            )

            print_results(
                query,
                results,
            )

        except Exception as error:

            logger.exception(
                "Retrieval failed: %s",
                error,
            )

            print(
                f"\nQuery failed: "
                f"{query}"
            )

            print(
                f"Error: {error}"
            )

    # --------------------------------------------------------
    # RAG-ready example
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "RAG CONTEXT EXAMPLE"
    )

    print(
        "=" * 70
    )

    query = (
        "Ration card ke liye "
        "kya documents chahiye?"
    )

    try:

        rag_data = (
            retriever.retrieve_for_rag(
                query=query,
                top_k=5,
            )
        )

        print(
            "\nContext that will be "
            "sent to the LLM:\n"
        )

        print(
            rag_data[
                "context"
            ]
        )

        print(
            "\nSources:"
        )

        for source in (
            rag_data[
                "sources"
            ]
        ):

            print(
                f"- "
                f"{source['citation']}"
            )

    except Exception as error:

        logger.exception(
            "RAG retrieval test failed: %s",
            error,
        )

        print(
            f"RAG retrieval failed: "
            f"{error}"
        )

    print(
        "\n"
        + "=" * 70
    )


if __name__ == "__main__":
    main()

