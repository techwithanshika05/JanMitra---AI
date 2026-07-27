"""Presentation-only FAQ structuring that preserves the generated answer text."""
import re


FAQ_HINTS = (
    "how to", "steps", "documents", "eligibility", "apply", "application",
    "policy", "scheme", "ration", "required", "process",
)
PROCEDURAL_HINTS = ("how to", "steps", "process", "apply", "application")
LIST_HINTS = ("top", "list", "which", "some")
NUMBERED_ITEM = re.compile(r"^\s*\d+[.)]\s+")


def _clean(line: str) -> str:
    return re.sub(r"^\s*(?:[-*\u2022]|\d+[.)])\s*", "", line).strip()


def format_if_informational(
    question: str, answer: str, language: str = "en"
) -> tuple[str, dict | None]:
    original_lines = [line.strip() for line in answer.splitlines() if line.strip()]
    lines = [_clean(line) for line in original_lines if _clean(line)]
    informational = (
        len(answer) >= 280
        or len(lines) >= 4
        or any(hint in question.lower() for hint in FAQ_HINTS)
    )
    if not informational:
        return "plain", None

    title = (lines[0] if lines and len(lines[0]) <= 90 else question.strip())[:90]
    if not title:
        title = "जानकारी" if language == "hi" else "Information"

    body_lines = original_lines[1:] if lines and lines[0] == title else original_lines
    numbered_items = [_clean(line) for line in body_lines if NUMBERED_ITEM.match(line)]
    plain_items = [_clean(line) for line in body_lines if not NUMBERED_ITEM.match(line)]
    question_lower = question.lower()
    procedural = any(hint in question_lower for hint in PROCEDURAL_HINTS)
    list_response = bool(numbered_items) and (
        any(hint in question_lower for hint in LIST_HINTS)
        or "scheme" in question_lower
        or not procedural
    )

    if list_response:
        # Ranked and enumerated answers are information, not application steps.
        summary = (plain_items[-1] if plain_items else title)[:240]
        points = numbered_items + plain_items[:-1]
        steps = []
        if "scheme" in question_lower:
            section_heading = "योजनाएं" if language == "hi" else "Schemes"
        else:
            section_heading = "मुख्य जानकारी" if language == "hi" else "Key information"
    else:
        summary = (plain_items[0] if plain_items else answer.strip())[:240]
        points = plain_items[1:]
        steps = numbered_items if procedural else []
        if numbered_items and not steps:
            points = numbered_items + points
        section_heading = "मुख्य जानकारी" if language == "hi" else "Key information"

    structured = {
        "response_type": "faq",
        "title": title,
        "summary": summary,
        "sections": [{
            "heading": section_heading,
            "points": points[:8],
        }] if points else [],
        "steps": steps[:10],
        "note": None,
    }
    return "faq", structured
