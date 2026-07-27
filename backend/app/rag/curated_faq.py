"""Small deterministic answers for exact, high-frequency citizen intents."""
from __future__ import annotations


def curated_answer(message: str, language: str = "en") -> dict | None:
    normalized = " ".join(message.lower().strip().rstrip("?.!").split())
    ration_intent = (
        "apply for a ration card" in normalized
        or "ration card application" in normalized
        or ("राशन कार्ड" in normalized and any(word in normalized for word in ("आवेदन", "बनव")))
    )
    if not ration_intent:
        return None

    hindi = language.lower().startswith("hi")
    title = "राशन कार्ड आवेदन" if hindi else "Ration Card Application"
    documents_heading = "आवश्यक दस्तावेज़" if hindi else "Required Documents"
    sections = [{
        "heading": documents_heading,
        "points": (
            ["परिवार के मुखिया का पहचान प्रमाण", "पते का प्रमाण", "परिवार के सदस्यों का विवरण"]
            if hindi
            else ["Identity proof of the head of family", "Address proof", "Family member details"]
        ),
    }]
    steps = (
        ["राज्य खाद्य पोर्टल खोलें", "आवेदन भरें", "दस्तावेज़ जमा करें", "स्थिति की जाँच करें"]
        if hindi
        else [
            "Open your state food department portal",
            "Complete the ration-card application",
            "Submit the required documents",
            "Track the application using the acknowledgement number",
        ]
    )
    structured = {
        "response_type": "faq",
        "title": title,
        "summary": (
            "आवेदन राज्य के खाद्य एवं नागरिक आपूर्ति विभाग में किया जाता है।"
            if hindi
            else "Apply through the food and civil supplies department for your state."
        ),
        "sections": sections,
        "steps": steps,
        "note": (
            "नियम और दस्तावेज़ राज्य के अनुसार बदल सकते हैं।"
            if hindi
            else "Required documents and procedure can vary by state."
        ),
    }
    return {
        "answer": structured["summary"],
        "confidence": 1.0,
        "is_grounded": True,
        "disclaimer": "",
        "sources": [],
        "response_type": "faq",
        "structured_content": structured,
    }
