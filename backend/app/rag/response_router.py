"""Shared response routing for both JanMitra chat API contracts."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from app.config import settings
from app.rag.curated_faq import curated_answer
from app.rag.intent_router import intent_router
from app.rag.language import resolve_response_language
from integration.rag_adapter import rag_adapter

_chat_rag_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="chat-rag")


def _rag_answer_with_deadline(message: str, language: str) -> dict:
    future = _chat_rag_executor.submit(rag_adapter.answer, message, language)
    try:
        return future.result(timeout=settings.CHAT_RAG_TIMEOUT_SECONDS)
    except FutureTimeout:
        future.cancel()
        return {
            "answer": "",
            "confidence": 0.0,
            "is_grounded": False,
            "disclaimer": "",
            "sources": [],
            "response_type": "rag_timeout",
            "structured_content": None,
        }


def generate_chat_response(
    message: str,
    language: str | None = None,
    conversation_context: list[dict[str, str]] | None = None,
) -> dict:
    resolved_language = resolve_response_language(message, language)

    decision = intent_router.route(
        message, resolved_language, conversation_context
    )
    if decision.kind == "pds_welfare":
        rag_result = _rag_answer_with_deadline(message, resolved_language)
        if rag_result.get("is_grounded") and rag_result.get("sources"):
            return {
                **rag_result,
                "api_status": "working",
                "alert": "Live RAG and Groq API answered this question from indexed sources.",
            }

        curated = curated_answer(message, resolved_language)
        if curated:
            return {
                **curated,
                "api_status": "fallback",
                "alert": (
                    "The live RAG or Groq API is unavailable or did not return "
                    "grounded evidence. Showing a verified curated answer."
                ),
            }

        return {
            **rag_result,
            "api_status": "unavailable",
            "alert": (
                "The live RAG or Groq API is unavailable or could not find "
                "grounded evidence for this project-related question."
            ),
        }

    return {
        "answer": decision.reply or "",
        "confidence": decision.confidence,
        "is_grounded": False,
        "disclaimer": "",
        "sources": [],
        "response_type": decision.kind,
        "structured_content": None,
        "api_status": "not_used",
        "alert": "",
    }
