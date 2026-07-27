"""Stable FastAPI contract over Manya's completed RAG implementation."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import RLock
from time import monotonic
from typing import Any, Callable

from app.config import settings

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "This response is generated from available government scheme data and "
    "does not constitute official confirmation of eligibility or approval."
)


class RAGInitializationCoolingDown(RuntimeError):
    """Raised while a recent model-initialization failure is cooling down."""


class ManyaRAGAdapter:
    """Lazily initialize one RAG stack and preserve the legacy chat response."""

    def __init__(
        self,
        pipeline_factory: Callable[[], Any] | None = None,
        retriever_factory: Callable[[], Any] | None = None,
        retry_cooldown_seconds: float | None = None,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._pipeline_factory = pipeline_factory
        self._retriever_factory = retriever_factory
        self._pipeline: Any | None = None
        self._retriever: Any | None = None
        self._lock = RLock()
        self._clock = clock
        self._retry_cooldown_seconds = (
            retry_cooldown_seconds
            if retry_cooldown_seconds is not None
            else float(os.getenv("RAG_INIT_RETRY_COOLDOWN_SECONDS", "120"))
        )
        self._retriever_init_error: Exception | None = None
        self._retriever_retry_after = 0.0

    def _build_retriever(self):
        if self._retriever_factory:
            return self._retriever_factory()

        from embeddings.embedding_service import EmbeddingService
        from retrieval.retriever import MultilingualRetriever
        from vectorstore.chroma_store import ChromaStore

        embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL)
        vector_store = ChromaStore(
            persist_directory=Path(settings.CHROMA_DIR),
            collection_name=settings.CHROMA_COLLECTION,
        )
        return MultilingualRetriever(
            embedding_service=embedding_service,
            vector_store=vector_store,
            default_top_k=settings.RETRIEVAL_TOP_K,
        )

    def _get_retriever(self):
        if self._retriever is None:
            with self._lock:
                if self._retriever is None:
                    now = self._clock()
                    if (
                        self._retriever_init_error is not None
                        and now < self._retriever_retry_after
                    ):
                        remaining = max(0.0, self._retriever_retry_after - now)
                        raise RAGInitializationCoolingDown(
                            "RAG initialization is cooling down after a previous "
                            f"failure; retry in {remaining:.0f} seconds"
                        ) from self._retriever_init_error
                    try:
                        self._retriever = self._build_retriever()
                    except Exception as exc:
                        self._retriever_init_error = exc
                        self._retriever_retry_after = (
                            now + self._retry_cooldown_seconds
                        )
                        logger.error(
                            "RAG initialization failed; further initialization "
                            "attempts are paused for %.0f seconds",
                            self._retry_cooldown_seconds,
                        )
                        raise
                    else:
                        self._retriever_init_error = None
                        self._retriever_retry_after = 0.0
        return self._retriever

    def _get_pipeline(self):
        if self._pipeline is None:
            with self._lock:
                if self._pipeline is None:
                    if self._pipeline_factory:
                        self._pipeline = self._pipeline_factory()
                    else:
                        from rag.rag_pipeline import RAGPipeline

                        self._pipeline = RAGPipeline(
                            retriever=self._get_retriever(),
                            top_k=settings.RETRIEVAL_TOP_K,
                        )
        return self._pipeline

    @staticmethod
    def _source(result: dict[str, Any]) -> dict[str, Any]:
        metadata = result.get("metadata") or {}
        title = (
            metadata.get("title")
            or metadata.get("source_file")
            or metadata.get("file_name")
            or "Government document"
        )
        score = result.get("similarity")
        return {
            "title": str(title),
            "snippet": str(result.get("text") or "")[:180],
            "score": round(max(0.0, min(1.0, float(score or 0.0))), 3),
        }

    @staticmethod
    def _controlled_fallback(language: str) -> dict[str, Any]:
        answer = (
            "क्षमा करें, अभी दस्तावेज़ खोज सेवा उपलब्ध नहीं है। कृपया कुछ समय बाद पुनः प्रयास करें।"
            if language == "hi"
            else "The document retrieval service is temporarily unavailable. Please try again shortly."
        )
        return {
            "answer": answer,
            "confidence": 0.0,
            "is_grounded": False,
            "disclaimer": DISCLAIMER,
            "sources": [],
        }

    def _retrieval_only(self, question: str, language: str) -> dict[str, Any]:
        results = self.retrieve(question)
        sources = [self._source(item) for item in results]
        confidence = max((source["score"] for source in sources), default=0.0)
        if not sources:
            return {
                "answer": (
                    "क्षमा करें, उपलब्ध सरकारी दस्तावेज़ों में इस प्रश्न की पर्याप्त जानकारी नहीं मिली।"
                    if language == "hi"
                    else "I could not find enough information in the available government documents."
                ),
                "confidence": 0.0,
                "is_grounded": False,
                "disclaimer": DISCLAIMER,
                "sources": [],
            }
        bullets = "\n".join(
            f"- {source['snippet']}... (Source: {source['title']})"
            for source in sources[:3]
        )
        intro = (
            "उपलब्ध सरकारी दस्तावेज़ों के आधार पर:"
            if language == "hi"
            else "Based on the available government documents:"
        )
        return {
            "answer": f"{intro}\n{bullets}",
            "confidence": confidence,
            "is_grounded": confidence >= settings.MIN_CONFIDENCE_TO_ANSWER,
            "disclaimer": DISCLAIMER,
            "sources": sources,
        }

    def answer(self, question: str, language: str = "en") -> dict[str, Any]:
        normalized_language = "hi" if language.lower().startswith("hi") else "en"
        try:
            if os.getenv("GROQ_API_KEY"):
                response = self._get_pipeline().query(
                    question, top_k=settings.RETRIEVAL_TOP_K
                )
                sources = [
                    {
                        "title": str(
                            item.get("file_name")
                            or item.get("source_id")
                            or "Government document"
                        ),
                        "snippet": "",
                        "score": round(
                            max(0.0, min(1.0, float(item.get("score") or 0.0))), 3
                        ),
                    }
                    for item in response.sources
                ]
                confidence = max(
                    (source["score"] for source in sources), default=0.0
                )
                return {
                    "answer": response.answer,
                    "confidence": confidence,
                    "is_grounded": bool(sources),
                    "disclaimer": DISCLAIMER,
                    "sources": sources,
                }
            return self._retrieval_only(question, normalized_language)
        except RAGInitializationCoolingDown as exc:
            logger.warning("%s", exc)
            return self._controlled_fallback(normalized_language)
        except Exception as exc:
            logger.exception("Manya RAG query failed safely: %s", exc)
            return self._controlled_fallback(normalized_language)

    def retrieve(self, question: str) -> list[dict[str, Any]]:
        """Return Manya retriever results without activating another RAG stack."""
        return self._get_retriever().retrieve(
            query=question, top_k=settings.RETRIEVAL_TOP_K
        )

    def add_documents(self, chunks: list[dict[str, Any]]) -> dict[str, int]:
        """Upsert uploads into Manya's collection without resetting it."""
        retriever = self._get_retriever()
        normalized = [
            {
                "chunk_id": chunk["id"],
                "text": chunk["text"],
                "metadata": {
                    "title": chunk.get("title", "Uploaded document"),
                    "source_file": chunk.get("source", chunk.get("title", "")),
                },
            }
            for chunk in chunks
            if chunk.get("id") and str(chunk.get("text", "")).strip()
        ]
        embedded = retriever.embedding_service.generate_embeddings(normalized)
        return retriever.vector_store.upsert_chunks(embedded)


rag_adapter = ManyaRAGAdapter()
