from dataclasses import dataclass
from typing import Any

from app.config import settings
from integration.rag_adapter import rag_adapter


@dataclass
class GroundedResult:
    answer: str
    evidence_status: str
    confidence: float
    sources: list[dict[str, Any]] 
    answer_mode: str = "rag"


class VoiceRAGAdapter:
    def answer(self, query: str, language: str) -> GroundedResult:
        result = rag_adapter.answer(query, "hi" if language.startswith("hi") else "en")
        sources = result.get("sources") or []
        confidence = float(result.get("confidence") or 0.0)
        reliable = bool(result.get("is_grounded")) and bool(sources) and confidence >= settings.MIN_CONFIDENCE_TO_ANSWER
        return GroundedResult(
            answer=str(result.get("answer") or ""),
            evidence_status="verified_document" if reliable else "insufficient_evidence",
            confidence=confidence,
            sources=sources if reliable else [],
        )


voice_rag = VoiceRAGAdapter()
