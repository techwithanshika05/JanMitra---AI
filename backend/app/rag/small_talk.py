"""
Small-talk handler — greetings ko RAG se pehle hi pakad leta hai taaki
"hello" jaisi baaton ke liye 0% confidence na aaye.
"""
import re

GREETING_PATTERNS = [
    r"^h(ello|i|ey)+!?$", r"^good\s?(morning|afternoon|evening)!?$",
    r"^namaste!?$", r"^नमस्ते!?$", r"^हेलो!?$", r"^हाय!?$", r"^हैलो!?$",
]
THANKS_PATTERNS = [r"^thank(s| you)!?$", r"^shukriya!?$", r"^धन्यवाद!?$", r"^शुक्रिया!?$"]
HELP_PATTERNS = [r"^help$", r"^what can you do\??$", r"^मदद$", r"^तुम क्या कर सकते हो\??$"]


def _matches_any(text: str, patterns: list) -> bool:
    cleaned = text.strip().lower()
    return any(re.match(p, cleaned, flags=re.IGNORECASE) for p in patterns)


def detect_small_talk(message: str, language: str = "en") -> str | None:
    """Returns a canned reply if this is small talk, else None (-> go to RAG)."""
    if _matches_any(message, GREETING_PATTERNS):
        return (
            "नमस्ते! मैं JanMitra AI हूं। राशन कार्ड, कल्याण योजनाओं, दस्तावेज़ों या शिकायत "
            "दर्ज करने के बारे में पूछें — मैं आधिकारिक जानकारी के आधार पर मदद करूंगा।"
            if language == "hi"
            else "Hello! I'm JanMitra AI. Ask me about ration cards, welfare schemes, "
                 "required documents, or filing a grievance — I'll help using official information."
        )
    if _matches_any(message, THANKS_PATTERNS):
        return (
            "आपका स्वागत है! अगर कोई और सवाल हो तो बेझिझक पूछें।"
            if language == "hi"
            else "You're welcome! Feel free to ask if you have any other questions."
        )
    if _matches_any(message, HELP_PATTERNS):
        return (
            "मैं इसमें मदद कर सकता हूं: राशन कार्ड प्रक्रियाएं, कल्याण योजना खोज, दस्तावेज़ चेकलिस्ट, "
            "और शिकायत दर्ज करने का मार्गदर्शन। बस अपना सवाल पूछें!"
            if language == "hi"
            else "I can help with: ration card processes, welfare scheme discovery, document "
                 "checklists, and grievance filing guidance. Just ask your question!"
        )
    return None