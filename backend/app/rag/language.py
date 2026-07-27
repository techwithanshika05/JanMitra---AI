"""Resolve the response language from message content and UI preference."""
import re

DEVANAGARI = re.compile(r"[\u0900-\u097f]")


def resolve_response_language(message: str, requested_language: str | None) -> str:
    if DEVANAGARI.search(message or ""):
        return "hi"
    requested = (requested_language or "en").lower()
    return "hi" if requested.startswith("hi") else "en"
