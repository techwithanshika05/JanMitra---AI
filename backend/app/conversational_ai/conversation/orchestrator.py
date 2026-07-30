from dataclasses import dataclass, field
import re

from sqlalchemy.orm import Session

from app.conversational_ai.adapters.rag_adapter import voice_rag
from app.conversational_ai.adapters.scheme_adapter import search_existing_schemes
from app.conversational_ai.rules import route_rule


@dataclass
class VoiceReply:
    text: str
    language: str
    intent: str
    answer_mode: str
    evidence_status: str
    confidence: float = 0.0
    sources: list[dict] = field(default_factory=list)
    end_call: bool = False


def detected_language(text: str, current: str) -> str:
    if re.search(r"[\u0900-\u097f]", text):
        return "hi-IN"
    words = set(re.findall(r"[a-z]+", text.lower()))
    if words & {"english", "please", "what", "how", "tell", "explain"}:
        return "en-IN"
    return current


class ConversationOrchestrator:
    def __init__(self, db: Session):
        self.db = db

    def respond(self, text: str, current_language: str = "hi-IN") -> VoiceReply:
        language = detected_language(text, current_language)
        rule = route_rule(text, language)
        if rule.matched:
            if rule.intent == "change_language_en":
                language = "en-IN"
            elif rule.intent == "change_language_hi":
                language = "hi-IN"
            return VoiceReply(rule.response, language, rule.intent, "curated_rule", "curated_rule", 1.0, end_call=rule.end_call)

        rag = voice_rag.answer(text, language)
        if rag.evidence_status == "verified_document":
            return VoiceReply(rag.answer, language, "pds_welfare", "rag", rag.evidence_status, rag.confidence, rag.sources)

        schemes = search_existing_schemes(self.db, text)
        if schemes:
            scheme = schemes[0]
            details = scheme["description"] or scheme["benefits"] or ""
            prefix = f"मौजूदा सत्यापित योजना रिकॉर्ड में {scheme['name']} मिला है। " if language.startswith("hi") else f"I found {scheme['name']} in the existing verified scheme records. "
            source = [{"title": scheme["source"] or "JanMitra scheme record", "snippet": details[:180], "score": 1.0}]
            return VoiceReply(prefix + details, language, "scheme_awareness", "existing_scheme", "verified_scheme", 1.0, source)

        fallback = (
            "मुझे उपलब्ध दस्तावेज़ों और योजना रिकॉर्ड में सत्यापित जानकारी नहीं मिली। कृपया संबंधित सरकारी पोर्टल, हेल्पलाइन, CSC या स्थानीय कार्यालय से पुष्टि करें।"
            if language.startswith("hi")
            else "I could not find verified information in the available documents or scheme records. Please confirm through the relevant official portal, helpline, CSC, or local office."
        )
        return VoiceReply(fallback, language, "unknown", "official_resource_referral", "insufficient_evidence")
