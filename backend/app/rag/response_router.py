"""Shared response routing for both JanMitra chat API contracts."""
from __future__ import annotations

from app.rag.curated_faq import curated_answer
from app.rag.intent_router import intent_router
from app.rag.language import resolve_response_language
from integration.rag_adapter import rag_adapter


def generate_chat_response(
    message: str,
    language: str | None = None,
    conversation_context: list[dict[str, str]] | None = None,
) -> dict:
    resolved_language = resolve_response_language(message, language)

    curated = curated_answer(message, resolved_language)
    if curated:
        return curated

    decision = intent_router.route(
        message, resolved_language, conversation_context
    )
    if decision.kind == "pds_welfare":
        return rag_adapter.answer(message, resolved_language)

    return {
        "answer": decision.reply or "",
        "confidence": decision.confidence,
        "is_grounded": False,
        "disclaimer": "",
        "sources": [],
        "response_type": decision.kind,
        "structured_content": None,
    }
