
"""
embedding_service.py

Purpose:
--------
Generate multilingual vector embeddings for RAG chunks.

Input:
------
data/processed/chunks.json

Output:
-------
data/processed/embeddings.json

Pipeline:
---------
PDFs
    ↓
pdf_extractor.py
    ↓
text_cleaner.py
    ↓
metadata_builder.py
    ↓
chunker.py
    ↓
data/processed/chunks.json
    ↓
embedding_service.py
    ↓
data/processed/embeddings.json
    ↓
chroma_store.py
    ↓
ChromaDB

Multilingual Retrieval:
-----------------------
The SAME embedding model must be used for:

1. Document chunk embeddings
2. User query embeddings

Example:

English document:
    "Documents required for ration card application"

Hindi query:
    "राशन कार्ड के लिए कौन से दस्तावेज चाहिए?"

Hinglish query:
    "Ration card ke liye kya documents chahiye?"

Because a multilingual embedding model is used, semantically similar
sentences across languages should produce vectors that are relatively
close in embedding space.

Recommended model:
------------------
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

Required packages:
------------------
pip install sentence-transformers torch numpy

Run:
----
python embeddings/embedding_service.py
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

PROCESSED_DIR = DATA_DIR / "processed"

CHUNKS_FILE = PROCESSED_DIR / "chunks.json"

EMBEDDINGS_FILE = PROCESSED_DIR / "embeddings.json"


# ============================================================
# Embedding Configuration
# ============================================================

DEFAULT_MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

DEFAULT_BATCH_SIZE = 32

DEFAULT_NORMALIZE_EMBEDDINGS = True


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Multilingual Embedding Service
# ============================================================

class EmbeddingService:
    """
    Generate multilingual embeddings for document chunks
    and user queries.

    Important:
    ----------
    The same model instance/model name should be used for both:

        document chunks
        user queries

    Otherwise the vectors will not be comparable.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        chunks_file: Path = CHUNKS_FILE,
        output_file: Path = EMBEDDINGS_FILE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        normalize_embeddings: bool = DEFAULT_NORMALIZE_EMBEDDINGS,
        device: Optional[str] = None,
    ) -> None:

        self.model_name = model_name

        self.chunks_file = Path(
            chunks_file
        )

        self.output_file = Path(
            output_file
        )

        self.batch_size = batch_size

        self.normalize_embeddings = (
            normalize_embeddings
        )

        self.device = device

        if self.batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "Initializing multilingual embedding service"
        )

        logger.info(
            "Embedding model: %s",
            self.model_name,
        )

        logger.info(
            "Loading embedding model..."
        )

        try:

            if self.device:

                self.model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                )

            else:

                self.model = SentenceTransformer(
                    self.model_name
                )

        except Exception as error:

            logger.exception(
                "Failed to load embedding model: %s",
                error,
            )

            raise

        self.embedding_dimension = (
            self.model.get_sentence_embedding_dimension()
        )

        logger.info(
            "Embedding model loaded successfully"
        )

        logger.info(
            "Embedding dimension: %s",
            self.embedding_dimension,
        )

        logger.info(
            "Device: %s",
            self.model.device,
        )

    # ========================================================
    # Load Chunks
    # ========================================================

    def load_chunks(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Load chunks from data/processed/chunks.json.
        """

        if not self.chunks_file.exists():

            raise FileNotFoundError(
                f"Chunks file not found: "
                f"{self.chunks_file}"
            )

        logger.info(
            "Loading chunks from: %s",
            self.chunks_file,
        )

        with self.chunks_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        # chunker.py produces:
        #
        # {
        #     "chunking_info": {...},
        #     "summary": {...},
        #     "chunks": [...]
        # }

        if isinstance(data, dict):

            chunks = data.get(
                "chunks",
                []
            )

        elif isinstance(data, list):

            # Optional compatibility if chunks.json
            # directly contains a list.
            chunks = data

        else:

            raise ValueError(
                "Invalid chunks.json structure."
            )

        if not chunks:

            logger.warning(
                "No chunks found in chunks.json"
            )

            return []

        logger.info(
            "Loaded %d chunk(s)",
            len(chunks),
        )

        return chunks

    # ========================================================
    # Validate Chunks
    # ========================================================

    @staticmethod
    def validate_chunks(
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Remove invalid chunks before embedding.

        A valid chunk must contain:

        - chunk_id
        - non-empty text
        """

        valid_chunks = []

        invalid_count = 0

        for chunk in chunks:

            chunk_id = chunk.get(
                "chunk_id"
            )

            text = chunk.get(
                "text",
                ""
            )

            if (
                not chunk_id
                or not isinstance(
                    text,
                    str,
                )
                or not text.strip()
            ):

                invalid_count += 1

                logger.warning(
                    "Skipping invalid chunk: %s",
                    chunk_id,
                )

                continue

            valid_chunks.append(
                chunk
            )

        logger.info(
            "Valid chunks: %d",
            len(valid_chunks),
        )

        if invalid_count:

            logger.warning(
                "Invalid chunks skipped: %d",
                invalid_count,
            )

        return valid_chunks

    # ========================================================
    # Embed Texts
    # ========================================================

    def embed_texts(
        self,
        texts: List[str],
        show_progress_bar: bool = True,
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Used primarily for document chunk embedding.
        """

        if not texts:

            return np.empty(
                (
                    0,
                    self.embedding_dimension,
                )
            )

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
            normalize_embeddings=(
                self.normalize_embeddings
            ),
        )

        return embeddings

    # ========================================================
    # Embed Single Query
    # ========================================================

    def embed_query(
        self,
        query: str,
    ) -> List[float]:
        """
        Generate an embedding for a user query.

        This method will later be used by retriever.py.

        Examples:

        English:
            "How do I apply for a ration card?"

        Hindi:
            "मैं राशन कार्ड के लिए आवेदन कैसे करूं?"

        Hinglish:
            "Ration card ke liye apply kaise karu?"

        All queries are embedded using the SAME multilingual
        embedding model used for document chunks.
        """

        if not query:

            raise ValueError(
                "Query cannot be empty."
            )

        query = query.strip()

        if not query:

            raise ValueError(
                "Query cannot be empty."
            )

        embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=(
                self.normalize_embeddings
            ),
        )

        return embedding.tolist()

    # ========================================================
    # Embed Single Document/Chunk
    # ========================================================

    def embed_document(
        self,
        text: str,
    ) -> List[float]:
        """
        Generate embedding for one document/chunk.
        """

        if not text:

            raise ValueError(
                "Text cannot be empty."
            )

        embedding = self.model.encode(
            text.strip(),
            convert_to_numpy=True,
            normalize_embeddings=(
                self.normalize_embeddings
            ),
        )

        return embedding.tolist()

    # ========================================================
    # Generate Chunk Embeddings
    # ========================================================

    def generate_embeddings(
        self,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for all chunks.

        Embeddings are generated in batches for better
        performance.
        """

        chunks = self.validate_chunks(
            chunks
        )

        if not chunks:

            return []

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        logger.info(
            "Generating embeddings for %d chunks...",
            len(texts),
        )

        embeddings = self.embed_texts(
            texts,
            show_progress_bar=True,
        )

        if len(embeddings) != len(chunks):

            raise RuntimeError(
                "Embedding count does not match "
                "chunk count."
            )

        embedded_chunks = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):

            embedded_chunk = {
                "chunk_id": chunk[
                    "chunk_id"
                ],

                "text": chunk[
                    "text"
                ],

                "embedding": (
                    embedding.tolist()
                ),

                "word_count": chunk.get(
                    "word_count",
                    len(
                        chunk[
                            "text"
                        ].split()
                    ),
                ),

                "character_count": (
                    chunk.get(
                        "character_count",
                        len(
                            chunk[
                                "text"
                            ]
                        ),
                    )
                ),

                "metadata": chunk.get(
                    "metadata",
                    {},
                ),
            }

            embedded_chunks.append(
                embedded_chunk
            )

        logger.info(
            "Generated %d embeddings",
            len(embedded_chunks),
        )

        return embedded_chunks

    # ========================================================
    # Save Embeddings
    # ========================================================

    def save_embeddings(
        self,
        embedded_chunks: List[
            Dict[str, Any]
        ],
    ) -> Path:
        """
        Save embeddings into embeddings.json.

        Note:
        -----
        This JSON file is useful for:

        - debugging
        - inspecting embeddings
        - pipeline demonstration

        Once ChromaDB is added, it can generate/store embeddings
        directly and this intermediate file may become optional.
        """

        output = {
            "embedding_info": {
                "model": (
                    self.model_name
                ),

                "embedding_dimension": (
                    self.embedding_dimension
                ),

                "normalize_embeddings": (
                    self.normalize_embeddings
                ),

                "batch_size": (
                    self.batch_size
                ),

                "generated_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
            },

            "summary": {
                "total_embeddings": len(
                    embedded_chunks
                ),
            },

            "chunks": embedded_chunks,
        }

        logger.info(
            "Saving embeddings to: %s",
            self.output_file,
        )

        with self.output_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                output,
                file,
                ensure_ascii=False,
            )

        logger.info(
            "Embeddings saved successfully"
        )

        return self.output_file

    # ========================================================
    # Process All Chunks
    # ========================================================

    def process_all_chunks(
        self,
    ) -> Dict[str, Any]:
        """
        Complete embedding pipeline.

        chunks.json
            ↓
        Load chunks
            ↓
        Validate chunks
            ↓
        Generate multilingual embeddings
            ↓
        Save embeddings.json
        """

        chunks = self.load_chunks()

        if not chunks:

            logger.warning(
                "No chunks available for embedding."
            )

            return {
                "total_chunks": 0,
                "total_embeddings": 0,
                "output_file": None,
            }

        embedded_chunks = (
            self.generate_embeddings(
                chunks
            )
        )

        output_path = (
            self.save_embeddings(
                embedded_chunks
            )
        )

        result = {
            "total_chunks": len(
                chunks
            ),

            "total_embeddings": len(
                embedded_chunks
            ),

            "embedding_dimension": (
                self.embedding_dimension
            ),

            "model": (
                self.model_name
            ),

            "output_file": str(
                output_path
            ),
        }

        logger.info("=" * 60)

        logger.info(
            "EMBEDDING GENERATION COMPLETED"
        )

        logger.info("=" * 60)

        logger.info(
            "Chunks: %d",
            result[
                "total_chunks"
            ],
        )

        logger.info(
            "Embeddings: %d",
            result[
                "total_embeddings"
            ],
        )

        logger.info(
            "Dimension: %s",
            result[
                "embedding_dimension"
            ],
        )

        logger.info(
            "Model: %s",
            result[
                "model"
            ],
        )

        logger.info("=" * 60)

        return result


# ============================================================
# Multilingual Test
# ============================================================

def test_multilingual_embeddings(
    service: EmbeddingService,
) -> None:
    """
    Simple demonstration showing how the same multilingual
    model embeds English, Hindi, and Hinglish queries.

    This does NOT prove retrieval quality by itself.
    Proper retrieval evaluation should be performed later
    against ChromaDB.
    """

    print(
        "\n"
        + "=" * 60
    )

    print(
        "MULTILINGUAL EMBEDDING TEST"
    )

    print(
        "=" * 60
    )

    sentences = [
        (
            "Documents required for "
            "ration card application"
        ),

        (
            "राशन कार्ड के लिए कौन से "
            "दस्तावेज चाहिए?"
        ),

        (
            "Ration card ke liye kya "
            "documents chahiye?"
        ),

        (
            "How can I apply for a "
            "housing scheme?"
        ),
    ]

    embeddings = (
        service.embed_texts(
            sentences,
            show_progress_bar=False,
        )
    )

    # Since embeddings are normalized,
    # dot product is equivalent to cosine similarity.

    reference = embeddings[0]

    print(
        "\nReference:"
    )

    print(
        sentences[0]
    )

    print(
        "\nSimilarity Scores"
    )

    print(
        "-" * 60
    )

    for sentence, embedding in zip(
        sentences,
        embeddings,
    ):

        similarity = float(
            np.dot(
                reference,
                embedding,
            )
        )

        print(
            f"{similarity:.4f} | "
            f"{sentence}"
        )

    print(
        "\nHigher scores indicate greater "
        "semantic similarity."
    )

    print(
        "=" * 60
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    """
    Run embedding generation directly.
    """

    print(
        "\n"
        + "=" * 60
    )

    print(
        "PDS & SOCIAL WELFARE AI "
        "- MULTILINGUAL EMBEDDINGS"
    )

    print(
        "=" * 60
    )

    service = EmbeddingService()

    result = (
        service.process_all_chunks()
    )

    print(
        "\nEmbedding Summary"
    )

    print(
        "-" * 60
    )

    print(
        f"Chunks processed   : "
        f"{result['total_chunks']}"
    )

    print(
        f"Embeddings created : "
        f"{result['total_embeddings']}"
    )

    if result.get(
        "embedding_dimension"
    ):

        print(
            f"Embedding dimension: "
            f"{result['embedding_dimension']}"
        )

    if result.get(
        "model"
    ):

        print(
            f"Model              : "
            f"{result['model']}"
        )

    if result.get(
        "output_file"
    ):

        print(
            f"Output             : "
            f"{result['output_file']}"
        )

    # Run multilingual demonstration
    test_multilingual_embeddings(
        service
    )

    print(
        "\n"
        + "=" * 60
    )


if __name__ == "__main__":
    main()

