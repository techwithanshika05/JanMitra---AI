"""
query_processor.py

Query preprocessing module for the JanMitra RAG system.

Responsibilities:
1. Validate user queries.
2. Normalize whitespace and Unicode.
3. Clean unwanted control characters.
4. Detect the script/language family used in the query.
5. Extract useful query metadata.
6. Generate a retrieval-ready query.
7. Optionally expand common PDS and welfare abbreviations.

This module DOES NOT:
- Generate embeddings.
- Query ChromaDB.
- Call an LLM.

Those responsibilities belong to:
    embeddings/embedding_service.py
    retrieval/retriever.py
    generation/llm_service.py
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


# ============================================================
# Logging
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# Data Models
# ============================================================

@dataclass
class ProcessedQuery:
    """
    Represents a query after preprocessing.

    Attributes:
        original_query:
            The exact query received from the user.

        normalized_query:
            Cleaned and normalized version of the query.

        retrieval_query:
            Query that should be sent to the embedding service
            and retriever.

        detected_language:
            Basic script/language classification.

        query_type:
            Broad intent category such as eligibility, benefits,
            application, documents, status, grievance, etc.

        keywords:
            Important words extracted from the query.

        expanded_terms:
            Abbreviations that were expanded while preparing
            the retrieval query.
    """

    original_query: str
    normalized_query: str
    retrieval_query: str
    detected_language: str
    query_type: str
    keywords: List[str]
    expanded_terms: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the processed query into a dictionary."""
        return asdict(self)


# ============================================================
# Query Processor
# ============================================================

class QueryProcessor:
    """
    Prepares user queries for semantic retrieval.

    Example:

        processor = QueryProcessor()

        result = processor.process(
            "What is the eligibility for PM Kisan?"
        )

        print(result.retrieval_query)
    """

    # --------------------------------------------------------
    # Common abbreviations
    #
    # These expansions can improve semantic retrieval when
    # government documents use the full form while users use
    # abbreviations.
    # --------------------------------------------------------

    ABBREVIATIONS: Dict[str, str] = {
        "pds": "Public Distribution System",
        "nfsa": "National Food Security Act",
        "pm kisan": "Pradhan Mantri Kisan Samman Nidhi",
        "pm-kisan": "Pradhan Mantri Kisan Samman Nidhi",
        "pmay": "Pradhan Mantri Awas Yojana",
        "pmjay": "Pradhan Mantri Jan Arogya Yojana",
        "pm-jay": "Pradhan Mantri Jan Arogya Yojana",
        "mgnrega": (
            "Mahatma Gandhi National Rural Employment "
            "Guarantee Act"
        ),
        "mnrega": (
            "Mahatma Gandhi National Rural Employment "
            "Guarantee Act"
        ),
        "bpl": "Below Poverty Line",
        "apl": "Above Poverty Line",
        "aay": "Antyodaya Anna Yojana",
        "phh": "Priority Household",
        "dbt": "Direct Benefit Transfer",
        "uidai": "Unique Identification Authority of India",
    }

    # --------------------------------------------------------
    # Query intent patterns
    # --------------------------------------------------------

    QUERY_TYPE_PATTERNS: Dict[str, List[str]] = {
        "eligibility": [
            "eligible",
            "eligibility",
            "qualify",
            "qualification",
            "who can apply",
            "am i eligible",
            "criteria",
            "पात्र",
            "पात्रता",
            "योग्य",
        ],

        "benefits": [
            "benefit",
            "benefits",
            "amount",
            "money",
            "financial assistance",
            "how much",
            "subsidy",
            "लाभ",
            "फायदा",
            "राशि",
            "पैसे",
        ],

        "application": [
            "apply",
            "application",
            "register",
            "registration",
            "how to apply",
            "process",
            "procedure",
            "आवेदन",
            "अप्लाई",
            "पंजीकरण",
        ],

        "documents": [
            "document",
            "documents",
            "required documents",
            "certificate",
            "proof",
            "aadhaar",
            "दस्तावेज",
            "कागजात",
            "प्रमाण पत्र",
        ],

        "status": [
            "status",
            "track",
            "application status",
            "payment status",
            "check status",
            "स्थिति",
            "स्टेटस",
        ],

        "grievance": [
            "complaint",
            "complain",
            "grievance",
            "problem",
            "issue",
            "helpline",
            "शिकायत",
            "समस्या",
            "हेल्पलाइन",
        ],

        "scheme_information": [
            "what is",
            "tell me about",
            "explain",
            "information",
            "details",
            "scheme",
            "yojana",
            "योजना",
            "जानकारी",
            "बताओ",
            "क्या है",
        ],
    }

    # --------------------------------------------------------
    # Stopwords
    #
    # Only used for lightweight keyword extraction.
    # They are NOT removed from the retrieval query.
    # --------------------------------------------------------

    ENGLISH_STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }

    def __init__(
        self,
        min_query_length: int = 2,
        max_query_length: int = 2000,
        enable_abbreviation_expansion: bool = True,
    ) -> None:
        """
        Initialize QueryProcessor.

        Args:
            min_query_length:
                Minimum allowed query length.

            max_query_length:
                Maximum allowed query length.

            enable_abbreviation_expansion:
                Whether common abbreviations should be expanded
                for retrieval.
        """

        self.min_query_length = min_query_length
        self.max_query_length = max_query_length
        self.enable_abbreviation_expansion = (
            enable_abbreviation_expansion
        )

        logger.info(
            "QueryProcessor initialized"
        )

    # ========================================================
    # Public API
    # ========================================================

    def process(
        self,
        query: str,
    ) -> ProcessedQuery:
        """
        Process a raw user query.

        Args:
            query:
                Raw question entered by the user.

        Returns:
            ProcessedQuery object.

        Raises:
            TypeError:
                If query is not a string.

            ValueError:
                If query is empty or outside allowed length.
        """

        self._validate_query(query)

        original_query = query

        normalized_query = self._normalize_query(
            query
        )

        self._validate_query(
            normalized_query
        )

        detected_language = self._detect_language(
            normalized_query
        )

        query_type = self._detect_query_type(
            normalized_query
        )

        keywords = self._extract_keywords(
            normalized_query
        )

        retrieval_query = normalized_query
        expanded_terms: Dict[str, str] = {}

        if self.enable_abbreviation_expansion:
            (
                retrieval_query,
                expanded_terms,
            ) = self._expand_abbreviations(
                normalized_query
            )

        result = ProcessedQuery(
            original_query=original_query,
            normalized_query=normalized_query,
            retrieval_query=retrieval_query,
            detected_language=detected_language,
            query_type=query_type,
            keywords=keywords,
            expanded_terms=expanded_terms,
        )

        logger.debug(
            "Query processed: %s",
            result.to_dict(),
        )

        return result

    # ========================================================
    # Validation
    # ========================================================

    def _validate_query(
        self,
        query: str,
    ) -> None:
        """
        Validate query type and length.
        """

        if not isinstance(query, str):
            raise TypeError(
                "Query must be a string."
            )

        stripped_query = query.strip()

        if not stripped_query:
            raise ValueError(
                "Query cannot be empty."
            )

        if len(stripped_query) < self.min_query_length:
            raise ValueError(
                f"Query must contain at least "
                f"{self.min_query_length} characters."
            )

        if len(stripped_query) > self.max_query_length:
            raise ValueError(
                f"Query cannot exceed "
                f"{self.max_query_length} characters."
            )

    # ========================================================
    # Normalization
    # ========================================================

    def _normalize_query(
        self,
        query: str,
    ) -> str:
        """
        Normalize Unicode, whitespace, and control characters.

        Hindi and other multilingual characters are preserved.
        """

        # Unicode normalization
        query = unicodedata.normalize(
            "NFKC",
            query,
        )

        # Remove control characters while keeping useful
        # whitespace such as spaces.
        query = "".join(
            char
            for char in query
            if not unicodedata.category(
                char
            ).startswith("C")
            or char in "\t\n"
        )

        # Convert newlines and tabs to spaces
        query = query.replace(
            "\n",
            " ",
        )

        query = query.replace(
            "\t",
            " ",
        )

        # Collapse multiple spaces
        query = re.sub(
            r"\s+",
            " ",
            query,
        )

        return query.strip()

    # ========================================================
    # Language Detection
    # ========================================================

    def _detect_language(
        self,
        query: str,
    ) -> str:
        """
        Perform lightweight script detection.

        Returns:
            "hindi"
            "english"
            "mixed"
            "unknown"

        This intentionally avoids an external language detection
        dependency. It is sufficient for routing and metadata.

        The multilingual embedding model should handle the
        actual semantic representation.
        """

        devanagari_count = len(
            re.findall(
                r"[\u0900-\u097F]",
                query,
            )
        )

        latin_count = len(
            re.findall(
                r"[A-Za-z]",
                query,
            )
        )

        if (
            devanagari_count > 0
            and latin_count > 0
        ):
            return "mixed"

        if devanagari_count > 0:
            return "hindi"

        if latin_count > 0:
            return "english"

        return "unknown"

    # ========================================================
    # Query Type Detection
    # ========================================================

    def _detect_query_type(
        self,
        query: str,
    ) -> str:
        """
        Detect broad query intent.

        This is rule-based and intentionally lightweight.

        Retrieval itself should still be semantic.
        """

        query_lower = query.lower()

        scores: Dict[str, int] = {}

        for (
            query_type,
            patterns,
        ) in self.QUERY_TYPE_PATTERNS.items():

            score = 0

            for pattern in patterns:
                if pattern.lower() in query_lower:
                    score += 1

            if score > 0:
                scores[query_type] = score

        if not scores:
            return "general"

        return max(
            scores,
            key=scores.get,
        )

    # ========================================================
    # Keyword Extraction
    # ========================================================

    def _extract_keywords(
        self,
        query: str,
    ) -> List[str]:
        """
        Extract lightweight keywords from the query.

        This method does not modify the retrieval query.
        """

        words = re.findall(
            r"[\w\u0900-\u097F-]+",
            query.lower(),
            flags=re.UNICODE,
        )

        keywords: List[str] = []

        seen = set()

        for word in words:

            cleaned_word = word.strip("-_")

            if not cleaned_word:
                continue

            if (
                cleaned_word
                in self.ENGLISH_STOPWORDS
            ):
                continue

            if len(cleaned_word) < 2:
                continue

            if cleaned_word in seen:
                continue

            seen.add(
                cleaned_word
            )

            keywords.append(
                cleaned_word
            )

        return keywords

    # ========================================================
    # Abbreviation Expansion
    # ========================================================

    def _expand_abbreviations(
        self,
        query: str,
    ) -> tuple[str, Dict[str, str]]:
        """
        Add full forms of recognized abbreviations.

        Instead of replacing the user's original wording,
        the full form is appended.

        Example:

            Input:
                "PM Kisan eligibility"

            Output:
                "PM Kisan eligibility
                 Pradhan Mantri Kisan Samman Nidhi"

        This preserves the original query while adding semantic
        context useful for embedding-based retrieval.
        """

        query_lower = query.lower()

        expansions: List[str] = []

        expanded_terms: Dict[str, str] = {}

        # Sort longest keys first to avoid shorter terms
        # matching before longer ones.
        sorted_abbreviations = sorted(
            self.ABBREVIATIONS.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

        for (
            abbreviation,
            full_form,
        ) in sorted_abbreviations:

            pattern = (
                r"(?<!\w)"
                + re.escape(
                    abbreviation
                )
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                query_lower,
                flags=re.IGNORECASE,
            ):

                if (
                    full_form.lower()
                    not in query_lower
                ):
                    expansions.append(
                        full_form
                    )

                    expanded_terms[
                        abbreviation
                    ] = full_form

        if not expansions:
            return query, {}

        # Remove duplicate expansions while maintaining order
        unique_expansions = list(
            dict.fromkeys(
                expansions
            )
        )

        retrieval_query = (
            query
            + " "
            + " ".join(
                unique_expansions
            )
        )

        return (
            retrieval_query.strip(),
            expanded_terms,
        )

    # ========================================================
    # Convenience Methods
    # ========================================================

    def get_retrieval_query(
        self,
        query: str,
    ) -> str:
        """
        Process a query and return only the string that should
        be embedded for semantic retrieval.
        """

        return self.process(
            query
        ).retrieval_query

    def get_query_metadata(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Process a query and return metadata useful for logging,
        analytics, or retrieval decisions.
        """

        processed = self.process(
            query
        )

        return {
            "detected_language": (
                processed.detected_language
            ),
            "query_type": (
                processed.query_type
            ),
            "keywords": (
                processed.keywords
            ),
            "expanded_terms": (
                processed.expanded_terms
            ),
        }


# ============================================================
# Manual Test
# ============================================================

def main() -> None:
    """
    Simple manual test for QueryProcessor.

    Run from backend directory:

        python -m retrieval.query_processor
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
    )

    processor = QueryProcessor()

    test_queries = [
        "What are the eligibility criteria for PM Kisan?",
        "What benefits are available under PDS?",
        "PMAY के लिए कौन पात्र है?",
        "राशन कार्ड के लिए आवेदन कैसे करें?",
        "How can I check my application status?",
        "NFSA क्या है?",
    ]

    print(
        "\n"
        + "=" * 60
    )

    print(
        "JANMITRA - QUERY PROCESSOR TEST"
    )

    print(
        "=" * 60
    )

    for query in test_queries:

        try:

            result = processor.process(
                query
            )

            print(
                f"\nOriginal Query:\n"
                f"{result.original_query}"
            )

            print(
                f"\nNormalized Query:\n"
                f"{result.normalized_query}"
            )

            print(
                f"\nRetrieval Query:\n"
                f"{result.retrieval_query}"
            )

            print(
                f"\nLanguage: "
                f"{result.detected_language}"
            )

            print(
                f"Query Type: "
                f"{result.query_type}"
            )

            print(
                f"Keywords: "
                f"{result.keywords}"
            )

            print(
                f"Expanded Terms: "
                f"{result.expanded_terms}"
            )

            print(
                "\n"
                + "-" * 60
            )

        except Exception as exc:

            logger.exception(
                "Failed to process query: %s",
                exc,
            )


if __name__ == "__main__":
    main()