import re


class SensitiveNoteError(ValueError):
    pass


_AADHAAR_NUMBER = re.compile(r"(?<!\d)(?:\d[\s-]?){11}\d(?!\d)")
_OTP_WITH_VALUE = re.compile(
    r"\b(?:otp|one[\s-]*time[\s-]*password)\b.{0,24}\b\d{4,8}\b", re.IGNORECASE
)
_PASSWORD_VALUE = re.compile(
    r"\b(?:password|passcode|pin)\b\s*(?:is|:|=|-)?\s*\S{4,}", re.IGNORECASE
)
_BANK_VALUE = re.compile(
    r"\b(?:bank\s+account|account\s+(?:number|no)|ifsc)\b.{0,32}"
    r"(?:\d{6,18}|[A-Z]{4}0[A-Z0-9]{6})",
    re.IGNORECASE,
)
_DOCUMENT_NUMBER = re.compile(
    r"\b(?:aadhaar|aadhar|pan|ration\s+card|document|certificate)"
    r"\s*(?:number|no|id|#)\b.{0,16}[A-Z0-9-]{5,}",
    re.IGNORECASE,
)


def validate_general_note(note: str | None) -> str | None:
    if note is None:
        return None
    cleaned = note.strip()
    if not cleaned:
        return None
    if len(cleaned) > 1000:
        raise SensitiveNoteError("Checklist notes cannot exceed 1000 characters")

    checks = (
        (_AADHAAR_NUMBER, "Aadhaar numbers"),
        (_OTP_WITH_VALUE, "OTPs"),
        (_PASSWORD_VALUE, "passwords or PINs"),
        (_BANK_VALUE, "bank account details"),
        (_DOCUMENT_NUMBER, "document numbers"),
    )
    for pattern, label in checks:
        if pattern.search(cleaned):
            raise SensitiveNoteError(
                f"Do not store {label} in checklist notes. Add only a general progress note."
            )
    return cleaned
