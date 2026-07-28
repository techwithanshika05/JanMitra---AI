"""Presentation-only FAQ structuring that preserves the generated answer text."""
import re


FAQ_HINTS = (
    "how to", "steps", "documents", "eligibility", "apply", "application",
    "policy", "scheme", "ration", "required", "process",
)
PROCEDURAL_HINTS = ("how to", "steps", "process", "apply", "application")
LIST_HINTS = ("top", "list", "which", "some")
NUMBERED_ITEM = re.compile(r"^\s*\d+[.)]\s+")
MARKDOWN_HEADING = re.compile(r"^\s*#{1,6}\s+(.+?)\s*#*\s*$")


def _clean(line: str) -> str:
    line = MARKDOWN_HEADING.sub(r"\1", line)
    return re.sub(r"^\s*(?:[-*\u2022]|\d+[.)])\s*", "", line).strip()


def _complete_excerpt(text: str, limit: int = 420) -> str:
    """Keep a complete sentence instead of cutting a word mid-answer."""
    text = re.sub(r"\s+", " ", _clean(text))
    if len(text) <= limit:
        return text
    excerpt = text[: limit + 1]
    sentence_end = max(
        excerpt.rfind("."),
        excerpt.rfind("।"),
        excerpt.rfind("!"),
        excerpt.rfind("?"),
    )
    if sentence_end >= max(100, limit // 2):
        return excerpt[: sentence_end + 1]
    word_end = excerpt.rfind(" ", 0, limit)
    return excerpt[:word_end].rstrip(" ,;:") + "…"


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

    heading_rows = [
        (index, _clean(line))
        for index, line in enumerate(original_lines)
        if MARKDOWN_HEADING.match(line)
    ]
    first_heading = heading_rows[0][1] if heading_rows else ""
    title = first_heading or (
        lines[0] if lines and len(lines[0]) <= 90 else question.strip()
    )
    title = _complete_excerpt(title, 110)
    if not title:
        title = "जानकारी" if language == "hi" else "Information"

    title_index = (
        heading_rows[0][0]
        if heading_rows
        else (0 if lines and lines[0] == title else -1)
    )
    body_lines = original_lines[title_index + 1:] if title_index >= 0 else original_lines

    # Preserve hierarchy supplied by the answer instead of showing Markdown
    # headings as literal "##" bullet items.
    body_headings = [
        (index, _clean(line))
        for index, line in enumerate(body_lines)
        if MARKDOWN_HEADING.match(line)
    ]
    if body_headings:
        intro = body_lines[:body_headings[0][0]]
        summary = _complete_excerpt(
            " ".join(_clean(line) for line in intro if _clean(line))
        )
        sections = []
        for heading_index, (start, heading) in enumerate(body_headings):
            end = (
                body_headings[heading_index + 1][0]
                if heading_index + 1 < len(body_headings)
                else len(body_lines)
            )
            points = [
                _complete_excerpt(line)
                for line in body_lines[start + 1:end]
                if _clean(line)
            ]
            if points:
                sections.append({"heading": heading, "points": points[:10]})
        return "faq", {
            "response_type": "faq",
            "title": title,
            "summary": summary or _complete_excerpt(question),
            "sections": sections,
            "steps": [],
            "note": None,
        }
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
        summary = _complete_excerpt(plain_items[-1] if plain_items else title)
        points = numbered_items + plain_items[:-1]
        steps = []
        if "scheme" in question_lower:
            section_heading = "योजनाएं" if language == "hi" else "Schemes"
        else:
            section_heading = "मुख्य जानकारी" if language == "hi" else "Key information"
    else:
        summary = _complete_excerpt(plain_items[0] if plain_items else answer.strip())
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
