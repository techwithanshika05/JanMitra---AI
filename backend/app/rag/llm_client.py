"""
LLM client abstraction.

Why: the internship spec says "Gemini/OpenAI API" (either), and also says
the app must be judgeable/demoable reliably. Hard-wiring one vendor's SDK
would make the whole app fail to boot without a paid key. Instead:
- If GEMINI_API_KEY or OPENAI_API_KEY is set, call that provider.
- If neither is set, fall back to "retrieval-only" mode: we still run the
  full RAG pipeline (embed -> search -> rank -> confidence score) but
  compose the answer by summarizing the top chunks with a template instead
  of a generative call. This keeps AI Explainability, source citation, and
  confidence scoring fully functional with zero external cost.
"""
from typing import List, Dict
from app.config import settings
from app.rag.prompts import build_prompt


def _confidence_from_scores(scores: List[float]) -> float:
    if not scores:
        return 0.0
    top = scores[0]
    avg = sum(scores) / len(scores)
    return round(0.7 * top + 0.3 * avg, 3)


def _retrieval_only_answer(question: str, chunks: List[Dict], language: str) -> str:
    if not chunks:
        if language == "hi":
            return "क्षमा करें, मुझे इस प्रश्न से जुड़ी जानकारी हमारे ज्ञान आधार में नहीं मिली।"
        return ("I couldn't find relevant information in the knowledge base for this "
                "question. Please rephrase, or check the official department website.")

    bullets = "\n".join(f"- {c['text'][:220].strip()}... (Source: {c['title']})" for c in chunks[:3])
    if language == "hi":
        return f"आपके प्रश्न से संबंधित जानकारी:\n{bullets}\n\nअंतिम पात्रता संबंधित विभाग तय करता है।"
    return (f"Based on available information:\n{bullets}\n\n"
            f"Note: final eligibility/approval is always decided by the concerned government department.")


def _call_gemini(system: str, user: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system)
    resp = model.generate_content(user)
    return resp.text


def _call_openai(system: str, user: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    return resp.choices[0].message.content


def generate_answer(question: str, chunks: List[Dict], language: str = "en") -> Dict:
    scores = [c["score"] for c in chunks]
    confidence = _confidence_from_scores(scores)
    is_grounded = confidence >= settings.MIN_CONFIDENCE_TO_ANSWER and len(chunks) > 0

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
        "This response is generated from available government scheme data and does not "
        "constitute official confirmation of eligibility or approval."
    )

    return {
        "answer": answer,
        "confidence": confidence,
        "is_grounded": is_grounded,
        "disclaimer": disclaimer,
        "sources": [{"title": c["title"], "snippet": c["text"][:180], "score": c["score"]} for c in chunks],
    }
