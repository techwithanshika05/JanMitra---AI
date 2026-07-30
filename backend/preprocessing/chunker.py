
"""
chunker.py

Purpose:
--------
Split cleaned and metadata-enriched PDF documents into smaller,
overlapping chunks suitable for embeddings and RAG retrieval.

Input:
------
data/processed/metadata/
    document1.json
    document2.json
    document3.json

Output:
-------
data/processed/chunks.json

Pipeline:
---------
data/raw/*.pdf
        ↓
pdf_extractor.py
        ↓
data/extracted/*.json
        ↓
text_cleaner.py
        ↓
data/processed/cleaned/*.json
        ↓
metadata_builder.py
        ↓
data/processed/metadata/*.json
        ↓
chunker.py
        ↓
data/processed/chunks.json
        ↓
embedding_service.py
        ↓
ChromaDB

Features:
---------
- Processes all metadata JSON documents automatically
- Uses cleaned_text when available
- Falls back to original text if needed
- Preserves PDF filename
- Preserves page number
- Preserves category
- Preserves service
- Preserves state
- Preserves jurisdiction
- Preserves language
- Preserves document type
- Generates unique chunk IDs
- Uses word-based chunking
- Supports configurable chunk size
- Supports configurable overlap
- Avoids tiny chunks when possible
- Stores chunk statistics
- Produces a single consolidated chunks.json

Default configuration:
----------------------
Chunk size: 600 words
Chunk overlap: 80 words
Minimum chunk size: 50 words

Note:
-----
This implementation chunks page-by-page so that every chunk
has an accurate page_number for source citation.

A chunk will NOT span multiple PDF pages.

Run:
----
python preprocessing/chunker.py
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

PROCESSED_DIR = DATA_DIR / "processed"

METADATA_DIR = PROCESSED_DIR / "metadata"

CHUNKS_FILE = PROCESSED_DIR / "chunks.json"


# ============================================================
# Chunking Configuration
# ============================================================

DEFAULT_CHUNK_SIZE = 600

DEFAULT_CHUNK_OVERLAP = 80

DEFAULT_MIN_CHUNK_SIZE = 50


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Document Chunker
# ============================================================

class DocumentChunker:
    """
    Converts cleaned PDF pages into RAG-friendly chunks.

    Chunking Strategy
    -----------------
    Each page is processed independently.

    Example:

        PDF
         │
         ├── Page 1
         │    ├── Chunk 1
         │    └── Chunk 2
         │
         ├── Page 2
         │    ├── Chunk 3
         │    └── Chunk 4
         │
         └── Page 3
              └── Chunk 5

    This ensures every chunk retains an accurate page number.

    Each generated chunk contains:

        chunk_id
        text
        word_count
        character_count
        metadata

    Metadata includes:

        document_id
        source_file
        title
        page_number
        category
        subcategory
        service
        document_type
        state
        jurisdiction
        language
    """

    def __init__(
        self,
        input_dir: Path = METADATA_DIR,
        output_file: Path = CHUNKS_FILE,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE,
    ) -> None:

        self.input_dir = Path(input_dir)

        self.output_file = Path(output_file)

        self.chunk_size = chunk_size

        self.chunk_overlap = chunk_overlap

        self.min_chunk_size = min_chunk_size

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if self.chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0."
            )

        if self.chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        if self.min_chunk_size < 0:
            raise ValueError(
                "min_chunk_size cannot be negative."
            )

        # ----------------------------------------------------
        # Create required directories
        # ----------------------------------------------------

        self.input_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "DocumentChunker initialized"
        )

        logger.info(
            "Input directory: %s",
            self.input_dir,
        )

        logger.info(
            "Output file: %s",
            self.output_file,
        )

        logger.info(
            "Chunk size: %d words",
            self.chunk_size,
        )

        logger.info(
            "Chunk overlap: %d words",
            self.chunk_overlap,
        )

        logger.info(
            "Minimum chunk size: %d words",
            self.min_chunk_size,
        )

    # ========================================================
    # File Discovery
    # ========================================================

    def find_json_files(
        self,
    ) -> List[Path]:
        """
        Find all metadata JSON documents.
        """

        json_files = sorted(
            [
                file
                for file in self.input_dir.iterdir()
                if file.is_file()
                and file.suffix.lower() == ".json"
            ],
            key=lambda path: path.name.lower(),
        )

        logger.info(
            "Found %d metadata document(s)",
            len(json_files),
        )

        return json_files

    # ========================================================
    # Load JSON Document
    # ========================================================

    @staticmethod
    def load_document(
        json_path: Path,
    ) -> Dict[str, Any]:
        """
        Load a metadata-enriched JSON document.
        """

        with json_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    # ========================================================
    # Text Normalization
    # ========================================================

    @staticmethod
    def normalize_chunk_text(
        text: str,
    ) -> str:
        """
        Perform minimal normalization before chunking.

        The heavy text cleaning has already been handled by
        text_cleaner.py.

        This method only:

        - removes excessive horizontal whitespace
        - removes excessive blank lines
        - trims whitespace
        """

        if not text:
            return ""

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        lines = []

        for line in text.split("\n"):

            line = re.sub(
                r"[ \t]+",
                " ",
                line,
            ).strip()

            lines.append(line)

        text = "\n".join(lines)

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    # ========================================================
    # Word Tokenization
    # ========================================================

    @staticmethod
    def tokenize_words(
        text: str,
    ) -> List[str]:
        """
        Split text into whitespace-separated words.

        This approach works for:

        - English
        - Hindi
        - Hinglish

        because all typically use whitespace-separated tokens.
        """

        if not text:
            return []

        return text.split()

    # ========================================================
    # Basic Word Chunking
    # ========================================================

    def create_word_chunks(
        self,
        text: str,
    ) -> List[str]:
        """
        Create overlapping chunks from text.

        Example:

            chunk_size = 100
            overlap = 20

        Chunk 1:
            words 0 - 99

        Chunk 2:
            words 80 - 179

        Chunk 3:
            words 160 - 259

        This provides contextual overlap between neighboring
        chunks.
        """

        text = self.normalize_chunk_text(
            text
        )

        words = self.tokenize_words(
            text
        )

        if not words:
            return []

        # ----------------------------------------------------
        # Small text
        # ----------------------------------------------------

        if len(words) <= self.chunk_size:

            return [
                " ".join(words)
            ]

        chunks: List[str] = []

        step_size = (
            self.chunk_size
            - self.chunk_overlap
        )

        start = 0

        total_words = len(words)

        while start < total_words:

            end = min(
                start + self.chunk_size,
                total_words,
            )

            chunk_words = words[
                start:end
            ]

            # ------------------------------------------------
            # Avoid tiny final chunks
            # ------------------------------------------------

            if (
                len(chunk_words)
                < self.min_chunk_size
                and chunks
            ):

                previous_chunk_words = (
                    chunks[-1].split()
                )

                combined_words = (
                    previous_chunk_words
                    + chunk_words
                )

                # Remove duplicates caused by overlap where
                # possible by keeping the final merged content.
                chunks[-1] = " ".join(
                    combined_words
                )

                break

            chunk_text = " ".join(
                chunk_words
            ).strip()

            if chunk_text:

                chunks.append(
                    chunk_text
                )

            if end >= total_words:
                break

            start += step_size

        return chunks

    # ========================================================
    # Extract Page Text
    # ========================================================

    @staticmethod
    def get_page_text(
        page: Dict[str, Any],
    ) -> str:
        """
        Get the best available text representation.

        Priority:

        1. cleaned_text
        2. text
        """

        return (
            page.get(
                "cleaned_text"
            )
            or page.get(
                "text"
            )
            or ""
        )

    # ========================================================
    # Build Chunk Metadata
    # ========================================================

    @staticmethod
    def build_chunk_metadata(
        document: Dict[str, Any],
        page: Dict[str, Any],
        chunk_index: int,
        total_page_chunks: int,
    ) -> Dict[str, Any]:
        """
        Build metadata for a chunk.

        Page-level metadata is preferred.

        Document-level metadata is used as fallback.
        """

        document_metadata = (
            document.get(
                "document_metadata",
                {},
            )
        )

        page_metadata = (
            page.get(
                "metadata",
                {},
            )
        )

        def get_value(
            key: str,
            default: Any = None,
        ) -> Any:

            return page_metadata.get(
                key,
                document_metadata.get(
                    key,
                    default,
                ),
            )

        metadata = {
            "document_id": get_value(
                "document_id",
                document.get(
                    "document_id",
                    "unknown_document",
                ),
            ),

            "source_file": get_value(
                "source_file",
                document.get(
                    "source_file",
                    "unknown.pdf",
                ),
            ),

            "title": get_value(
                "title",
                "",
            ),

            "page_number": page.get(
                "page_number",
                page_metadata.get(
                    "page_number"
                ),
            ),

            "category": get_value(
                "category",
                "GENERAL",
            ),

            "subcategory": get_value(
                "subcategory",
                "general",
            ),

            "service": get_value(
                "service",
                "general_information",
            ),

            "document_type": get_value(
                "document_type",
                "GENERAL_DOCUMENT",
            ),

            "state": get_value(
                "state",
                "unknown",
            ),

            "jurisdiction": get_value(
                "jurisdiction",
                "unknown",
            ),

            "language": get_value(
                "language",
                "unknown",
            ),

            "chunk_index_on_page": (
                chunk_index
            ),

            "total_chunks_on_page": (
                total_page_chunks
            ),
        }

        return metadata

    # ========================================================
    # Create Chunk ID
    # ========================================================

    @staticmethod
    def create_chunk_id(
        document_id: str,
        page_number: Any,
        chunk_index: int,
    ) -> str:
        """
        Generate a deterministic unique chunk ID.

        Example:

            up_pds_p12_c3
        """

        safe_document_id = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            str(document_id),
        ).strip("_")

        if not safe_document_id:
            safe_document_id = (
                "unknown_document"
            )

        page_value = (
            page_number
            if page_number is not None
            else 0
        )

        return (
            f"{safe_document_id}"
            f"_p{page_value}"
            f"_c{chunk_index}"
        )

    # ========================================================
    # Chunk Single Page
    # ========================================================

    def chunk_page(
        self,
        document: Dict[str, Any],
        page: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Convert one PDF page into one or more chunks.
        """

        text = self.get_page_text(
            page
        )

        if not text.strip():

            logger.debug(
                "Skipping empty page %s",
                page.get(
                    "page_number"
                ),
            )

            return []

        page_chunks = (
            self.create_word_chunks(
                text
            )
        )

        if not page_chunks:
            return []

        document_metadata = (
            document.get(
                "document_metadata",
                {},
            )
        )

        document_id = (
            document_metadata.get(
                "document_id"
            )
            or document.get(
                "document_id"
            )
            or "unknown_document"
        )

        page_number = page.get(
            "page_number",
            0,
        )

        total_page_chunks = len(
            page_chunks
        )

        chunks = []

        for index, chunk_text in enumerate(
            page_chunks,
            start=1,
        ):

            chunk_id = (
                self.create_chunk_id(
                    document_id,
                    page_number,
                    index,
                )
            )

            metadata = (
                self.build_chunk_metadata(
                    document,
                    page,
                    index,
                    total_page_chunks,
                )
            )

            chunk = {
                "chunk_id": chunk_id,

                "text": chunk_text,

                "word_count": len(
                    chunk_text.split()
                ),

                "character_count": len(
                    chunk_text
                ),

                "metadata": metadata,
            }

            chunks.append(
                chunk
            )

        return chunks

    # ========================================================
    # Chunk Single Document
    # ========================================================

    def chunk_document(
        self,
        document: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Convert all pages in one document into chunks.
        """

        source_file = document.get(
            "source_file",
            "unknown.pdf",
        )

        logger.info(
            "Chunking document: %s",
            source_file,
        )

        pages = document.get(
            "pages",
            [],
        )

        document_chunks = []

        skipped_pages = 0

        for page in pages:

            page_text = (
                self.get_page_text(
                    page
                )
            )

            if not page_text.strip():

                skipped_pages += 1

                continue

            page_chunks = (
                self.chunk_page(
                    document,
                    page,
                )
            )

            document_chunks.extend(
                page_chunks
            )

        logger.info(
            "Chunked %s | Pages: %d | "
            "Skipped empty pages: %d | "
            "Chunks: %d",
            source_file,
            len(pages),
            skipped_pages,
            len(document_chunks),
        )

        return document_chunks

    # ========================================================
    # Process Single File
    # ========================================================

    def process_single_file(
        self,
        json_path: Path,
    ) -> Dict[str, Any]:
        """
        Load and chunk one metadata document.
        """

        document = self.load_document(
            json_path
        )

        chunks = self.chunk_document(
            document
        )

        return {
            "source_file": (
                document.get(
                    "source_file",
                    json_path.name,
                )
            ),

            "status": "success",

            "chunk_count": len(
                chunks
            ),

            "chunks": chunks,
        }

    # ========================================================
    # Process All Documents
    # ========================================================

    def process_all_documents(
        self,
    ) -> Dict[str, Any]:
        """
        Process all metadata JSON documents and create a single
        consolidated chunks.json file.
        """

        json_files = (
            self.find_json_files()
        )

        if not json_files:

            logger.warning(
                "No metadata JSON documents "
                "found in: %s",
                self.input_dir,
            )

            empty_output = {
                "chunking_info": {
                    "chunk_size": (
                        self.chunk_size
                    ),
                    "chunk_overlap": (
                        self.chunk_overlap
                    ),
                    "min_chunk_size": (
                        self.min_chunk_size
                    ),
                    "generated_at": (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    ),
                },

                "summary": {
                    "total_documents": 0,
                    "successful_documents": 0,
                    "failed_documents": 0,
                    "total_chunks": 0,
                },

                "chunks": [],
            }

            self.save_chunks(
                empty_output
            )

            return empty_output

        all_chunks: List[
            Dict[str, Any]
        ] = []

        results = []

        successful_documents = 0

        failed_documents = 0

        for json_path in json_files:

            try:

                result = (
                    self.process_single_file(
                        json_path
                    )
                )

                all_chunks.extend(
                    result["chunks"]
                )

                successful_documents += 1

                results.append(
                    {
                        "source_file": (
                            result[
                                "source_file"
                            ]
                        ),

                        "status": (
                            "success"
                        ),

                        "chunk_count": (
                            result[
                                "chunk_count"
                            ]
                        ),
                    }
                )

            except Exception as error:

                failed_documents += 1

                logger.exception(
                    "Failed to chunk %s: %s",
                    json_path.name,
                    error,
                )

                results.append(
                    {
                        "source_file": (
                            json_path.name
                        ),

                        "status": (
                            "failed"
                        ),

                        "error": str(
                            error
                        ),
                    }
                )

        # ----------------------------------------------------
        # Check duplicate chunk IDs
        # ----------------------------------------------------

        chunk_ids = [
            chunk["chunk_id"]
            for chunk in all_chunks
        ]

        unique_chunk_ids = set(
            chunk_ids
        )

        duplicate_count = (
            len(chunk_ids)
            - len(unique_chunk_ids)
        )

        if duplicate_count > 0:

            logger.warning(
                "Detected %d duplicate chunk ID(s).",
                duplicate_count,
            )

        # ----------------------------------------------------
        # Build final output
        # ----------------------------------------------------

        output = {
            "chunking_info": {
                "strategy": (
                    "page_level_overlapping_word_chunks"
                ),

                "chunk_size": (
                    self.chunk_size
                ),

                "chunk_overlap": (
                    self.chunk_overlap
                ),

                "min_chunk_size": (
                    self.min_chunk_size
                ),

                "generated_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
            },

            "summary": {
                "total_documents": len(
                    json_files
                ),

                "successful_documents": (
                    successful_documents
                ),

                "failed_documents": (
                    failed_documents
                ),

                "total_chunks": len(
                    all_chunks
                ),

                "duplicate_chunk_ids": (
                    duplicate_count
                ),
            },

            "document_results": (
                results
            ),

            "chunks": all_chunks,
        }

        self.save_chunks(
            output
        )

        logger.info("=" * 60)

        logger.info(
            "DOCUMENT CHUNKING COMPLETED"
        )

        logger.info("=" * 60)

        logger.info(
            "Documents: %d",
            len(json_files),
        )

        logger.info(
            "Successful: %d",
            successful_documents,
        )

        logger.info(
            "Failed: %d",
            failed_documents,
        )

        logger.info(
            "Total chunks: %d",
            len(all_chunks),
        )

        logger.info(
            "Duplicate IDs: %d",
            duplicate_count,
        )

        logger.info("=" * 60)

        return output

    # ========================================================
    # Save Chunks
    # ========================================================

    def save_chunks(
        self,
        output: Dict[str, Any],
    ) -> Path:
        """
        Save all chunks into data/processed/chunks.json.
        """

        with self.output_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                output,
                file,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(
            "Saved chunks to: %s",
            self.output_file,
        )

        return self.output_file


# ============================================================
# Main
# ============================================================

def main() -> None:
    """
    Run document chunking directly.
    """

    print(
        "\n"
        + "=" * 60
    )

    print(
        "PDS & SOCIAL WELFARE AI - DOCUMENT CHUNKER"
    )

    print(
        "=" * 60
    )

    chunker = DocumentChunker(
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
        min_chunk_size=DEFAULT_MIN_CHUNK_SIZE,
    )

    output = (
        chunker.process_all_documents()
    )

    summary = output[
        "summary"
    ]

    print(
        "\nChunking Summary"
    )

    print(
        "-" * 60
    )

    print(
        f"Total documents      : "
        f"{summary['total_documents']}"
    )

    print(
        f"Successful documents : "
        f"{summary['successful_documents']}"
    )

    print(
        f"Failed documents     : "
        f"{summary['failed_documents']}"
    )

    print(
        f"Total chunks         : "
        f"{summary['total_chunks']}"
    )

    print(
        f"Duplicate chunk IDs  : "
        f"{summary['duplicate_chunk_ids']}"
    )

    document_results = output.get(
        "document_results",
        [],
    )

    if document_results:

        print(
            "\nDocument Results"
        )

        print(
            "-" * 60
        )

        for result in (
            document_results
        ):

            if (
                result["status"]
                == "success"
            ):

                print(
                    f"[OK] "
                    f"{result['source_file']} "
                    f"| Chunks: "
                    f"{result['chunk_count']}"
                )

            else:

                print(
                    f"[FAILED] "
                    f"{result['source_file']} "
                    f"| Error: "
                    f"{result['error']}"
                )

    print(
        "\nChunks saved to:"
    )

    print(
        CHUNKS_FILE
    )

    print(
        "\n"
        + "=" * 60
    )


if __name__ == "__main__":
    main()

