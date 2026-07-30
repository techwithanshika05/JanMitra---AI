from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RuleResult:
    matched: bool
    intent: str = ""
    response: str = ""
    end_call: bool = False


def route_rule(text: str, language: str) -> RuleResult:
    value = text.strip().lower()
    hindi = language.startswith("hi")
    if re.search(r"\b(hello|hi|namaste|namaskar)\b|नमस्ते|नमस्कार", value):
        return RuleResult(True, "greeting", "नमस्ते। बताइए, राशन या सरकारी योजना से जुड़ी किस जानकारी में सहायता चाहिए?" if hindi else "Hello. How may I help with ration services or a government welfare scheme?")
    if re.search(r"\b(english|अंग्रेजी|अंग्रेज़ी)\b", value):
        return RuleResult(True, "change_language_en", "Certainly. I will continue in English.")
    if re.search(r"\b(hindi|हिंदी)\b", value):
        return RuleResult(True, "change_language_hi", "ज़रूर। मैं आगे हिंदी में बात करूँगा।")
    if re.search(r"\b(bye|goodbye|end call|stop call)\b|अलविदा|कॉल बंद|बात खत्म", value):
        return RuleResult(True, "end_call", "धन्यवाद। जनमित्र का उपयोग करने के लिए धन्यवाद।" if hindi else "Thank you for using JanMitra. Goodbye.", True)
    if re.search(r"\b(otp|password|pin|aadhaar number|bank account number)\b", value):
        return RuleResult(True, "sensitive_data", "कृपया OTP, पासवर्ड, पूरा आधार नंबर या बैंक विवरण साझा न करें। मैं इनके बिना सामान्य मार्गदर्शन दे सकता हूँ।" if hindi else "Please do not share OTPs, passwords, full Aadhaar numbers, or bank details. I can guide you without them.")
    return RuleResult(False)
