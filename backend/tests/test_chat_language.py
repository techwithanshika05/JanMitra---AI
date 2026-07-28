from app.faq_formatter import format_if_informational
from app.rag.language import resolve_response_language
from app.rag.llm_client import generate_answer
from app.rag.curated_faq import curated_answer


def test_devanagari_question_overrides_english_ui_language():
    assert resolve_response_language("राशन कार्ड कैसे बनवाएं?", "en") == "hi"


def test_hindi_fallback_and_disclaimer_are_fully_hindi():
    result = generate_answer("मुझे जानकारी चाहिए", [], "en")
    assert result["answer"]
    assert "I couldn't" not in result["answer"]
    assert "This response" not in result["disclaimer"]
    assert "आधिकारिक" in result["disclaimer"]


def test_hindi_structured_heading_is_localized():
    answer = "योजना की जानकारी\nपहली जानकारी\nदूसरी जानकारी\nतीसरी जानकारी"
    response_type, structured = format_if_informational(
        "योजना कैसे मिलेगी?", answer, "hi"
    )
    assert response_type == "faq"
    assert structured["sections"][0]["heading"] == "मुख्य जानकारी"


def test_ration_card_application_has_curated_faq_structure():
    result = curated_answer("How do I apply for a ration card?", "en")
    assert result is not None
    assert result["response_type"] == "faq"
    assert result["structured_content"]["title"] == "Ration Card Application"
    assert result["structured_content"]["sections"][0]["heading"] == "Required Documents"
    assert len(result["structured_content"]["steps"]) == 4


def test_numbered_scheme_list_is_not_formatted_as_procedural_steps():
    answer = """Here are the top welfare schemes:

1. **Pradhan Mantri Awas Yojana**: Housing assistance.
2. **Pradhan Mantri Ujjwala Yojana**: Clean cooking fuel.
3. **Ayushman Bharat**: Health coverage.

These schemes support housing, clean energy, and healthcare."""
    response_type, structured = format_if_informational(
        "Tell me some welfare schemes top 3", answer, "en"
    )

    assert response_type == "faq"
    assert structured["steps"] == []
    assert structured["sections"][0]["heading"] == "Schemes"
    assert len(structured["sections"][0]["points"]) == 3
    assert structured["sections"][0]["points"][0].startswith("**Pradhan Mantri")
    assert structured["summary"].startswith("These schemes support")


def test_markdown_headings_become_sections_without_visible_markers_or_truncation():
    answer = """## Overview of One Nation One Ration Card

ONORC enables nationwide ration-card portability under the NFSA 2013. It helps migrant families access their entitlement away from home.

## Objective and Intended Beneficiaries
- Supports migrant beneficiaries while preserving access for family members.

## Adding a New Member
- Follow the process on the relevant state food portal."""
    response_type, structured = format_if_informational(
        "Explain ONORC and how to add a member", answer, "en"
    )

    assert response_type == "faq"
    assert structured["title"] == "Overview of One Nation One Ration Card"
    assert structured["summary"].endswith("away from home.")
    assert [section["heading"] for section in structured["sections"]] == [
        "Objective and Intended Beneficiaries",
        "Adding a New Member",
    ]
    assert "##" not in str(structured)
