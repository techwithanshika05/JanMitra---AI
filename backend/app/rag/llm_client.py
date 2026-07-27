"""Legacy answer contract retained for non-integrated callers and tests."""
from typing import Dict, List

from app.config import settings
from app.rag.language import resolve_response_language
from app.rag.prompts import build_prompt


def _confidence_from_scores(scores: List[float]) -> float:
    if not scores:
        return 0.0
    return round(0.7 * scores[0] + 0.3 * (sum(scores) / len(scores)), 3)


def _retrieval_only_answer(question: str, chunks: List[Dict], language: str) -> str:
    if not chunks:
        if language == "hi":
            return "क्षमा करें, इस प्रश्न से जुड़ी जानकारी हमारे ज्ञान आधार में नहीं मिली।"
        return (
            "I couldn't find relevant information in the knowledge base for this "
            "question. Please rephrase, or check the official department website."
        )

    bullets = "\n".join(
        f"- {chunk['text'][:220].strip()}... (Source: {chunk['title']})"
        for chunk in chunks[:3]
    )
    if language == "hi":
        return (
            f"आपके प्रश्न से संबंधित जानकारी:\n{bullets}\n\n"
            "अंतिम पात्रता संबंधित विभाग तय करता है।"
        )
    return (
        f"Based on available information:\n{bullets}\n\n"
        "Note: final eligibility/approval is always decided by the concerned "
        "government department."
    )


def _call_gemini(system: str, user: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system)
    return model.generate_content(user).text


def _call_openai(system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def generate_answer(
    question: str, chunks: List[Dict], language: str = "en"
) -> Dict:
    language = resolve_response_language(question, language)
    scores = [chunk["score"] for chunk in chunks]
    confidence = _confidence_from_scores(scores)
    is_grounded = confidence >= settings.MIN_CONFIDENCE_TO_ANSWER and bool(chunks)

    if not is_grounded:
        answer = _retrieval_only_answer(question, chunks, language)
    elif settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        prompt = build_prompt(question, chunks, language)
        answer = _call_gemini(prompt["system"], prompt["user"])
    elif settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        prompt = build_prompt(question, chunks, language)
        answer = _call_openai(prompt["system"], prompt["user"])
    else:
        answer = _retrieval_only_answer(question, chunks, language)

    disclaimer = (
        "यह उत्तर उपलब्ध सरकारी योजना डेटा पर आधारित है और पात्रता या स्वीकृति की "
        "आधिकारिक पुष्टि नहीं है।"
        if language == "hi"
        else (
            "This response is generated from available government scheme data and "
            "does not constitute official confirmation of eligibility or approval."
        )
    )
    return {
        "answer": answer,
        "confidence": confidence,
        "is_grounded": is_grounded,
        "disclaimer": disclaimer,
        "sources": [
            {
                "title": chunk["title"],
                "snippet": chunk["text"][:180],
                "score": chunk["score"],
            }
            for chunk in chunks
        ],
    }
