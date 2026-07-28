import pytest

from app.checklists.enums import ChecklistItemType
from app.checklists.guidance import ChecklistGuidanceService
from app.checklists.intelligence import (
    ChecklistKnowledgeService,
    ChecklistKnowledgeUnavailableError,
    InsufficientChecklistEvidenceError,
)
from app.checklists.models import ChecklistItem, SavedChecklist
from app.checklists.schemas import ChecklistKnowledgeRequest


def request(language="en"):
    return ChecklistKnowledgeRequest(
        service_id="income_certificate",
        service_name="Income Certificate",
        language=language,
        state="Uttar Pradesh",
    )


def official_results():
    return [
        {
            "text": (
                "Income Certificate\n"
                "SLA / Number of Days: 20 days\n"
                "Documents Required\n"
                "1. Self-declaration form\n"
                "2. Residence proof\n"
                "3. Salary slip for employed applicants\n"
                "Procedure for apply\n"
                "Step 1: Open the official e-District portal\n"
                "Step 2: Fill the application and attach documents\n"
            ),
            "metadata": {"source_file": "income-certificate-guidelines.pdf"},
            "similarity": 0.88,
        }
    ]


def test_build_extracts_only_retrieved_items_citations_and_stable_version():
    service = ChecklistKnowledgeService(retrieve=lambda _query: official_results())
    first = service.build(request())
    second = service.build(request())

    item_types = {item.item_type for item in first.items}
    assert ChecklistItemType.DOCUMENT in item_types
    assert ChecklistItemType.PROCESS_STEP in item_types
    assert ChecklistItemType.TIMELINE in item_types
    assert first.source_citations[0]["title"] == "income-certificate-guidelines.pdf"
    assert first.source_citations[0]["score"] == 0.88
    assert first.source_version.startswith("rag-")
    assert first.source_version == second.source_version


def test_inline_pdf_bullets_are_separate_professional_checklist_items():
    results = [{
        "text": (
            "Documents Required for UP Scholarship - For fresh candidates: "
            "\u2022 Last qualifying exam mark sheet \u2022 Caste certificate "
            "\u2022 Income certificate \u2022 Bank passbook\n"
            "Estimated processing time: within 15 days. "
            "The remaining paragraph contains implementation background."
        ),
        "metadata": {"source_file": "up-scholarship-guidelines.pdf"},
        "similarity": 0.91,
    }]

    built = ChecklistKnowledgeService(retrieve=lambda _query: results).build(request())
    document_titles = [
        item.title for item in built.items
        if item.item_type == ChecklistItemType.DOCUMENT
    ]
    timeline = next(
        item for item in built.items if item.item_type == ChecklistItemType.TIMELINE
    )

    assert document_titles == [
        "Last qualifying exam mark sheet",
        "Caste certificate",
        "Income certificate",
        "Bank passbook",
    ]
    assert timeline.description == "Estimated processing time: within 15 days."


def test_black_circle_pdf_bullets_drop_heading_and_create_independent_items():
    results = [{
        "text": (
            "Documents Required\n"
            "for UP Scholarship: For Fresh Candidate: "
            "\u25cf Last Qualifying Exam Mark Sheet "
            "\u25cf Caste Certificate \u25cf Income Certificate"
        ),
        "metadata": {"source_file": "scholarship.pdf"},
        "similarity": 0.93,
    }]

    built = ChecklistKnowledgeService(retrieve=lambda _query: results).build(request())

    assert [item.title for item in built.items] == [
        "Last Qualifying Exam Mark Sheet",
        "Caste Certificate",
        "Income Certificate",
    ]
    assert all(item.is_required for item in built.items)


def test_known_add_member_service_saves_the_displayed_structured_checklist():
    def retrieval_must_not_run(_query):
        raise AssertionError("Known checklist services must not use unrelated RAG results")

    service = ChecklistKnowledgeService(retrieve=retrieval_must_not_run)
    built = service.build(
        ChecklistKnowledgeRequest(
            service_id="add_member",
            service_name="Ration Card - Add Member",
            language="en",
        )
    )

    assert [item.title for item in built.items[:3]] == [
        "Existing ration card",
        "Aadhaar of new member",
        "Birth certificate / marriage certificate as applicable",
    ]
    assert built.items[3].title == "Submit member addition form"
    assert built.items[-1].item_type == ChecklistItemType.TIMELINE
    assert built.source_version.startswith("library-")


def test_generated_and_low_similarity_sources_are_rejected():
    results = [
        {
            "text": "Required documents\n1. Unverified item",
            "metadata": {"source_file": "setuai_checklist.pdf"},
            "similarity": 0.99,
        },
        {
            "text": "Required documents\n1. Low confidence item",
            "metadata": {"source_file": "official.pdf"},
            "similarity": 0.1,
        },
    ]
    service = ChecklistKnowledgeService(retrieve=lambda _query: results)
    with pytest.raises(InsufficientChecklistEvidenceError):
        service.build(request())


def test_unstructured_evidence_is_not_turned_into_invented_items():
    service = ChecklistKnowledgeService(
        retrieve=lambda _query: [
            {
                "text": "This paragraph discusses a service but gives no checklist.",
                "metadata": {"source_file": "official.pdf"},
                "similarity": 0.9,
            }
        ]
    )
    with pytest.raises(InsufficientChecklistEvidenceError):
        service.build(request())


def test_retrieval_failure_is_reported_as_unavailable():
    def fail(_query):
        raise RuntimeError("embedding service offline")

    with pytest.raises(ChecklistKnowledgeUnavailableError):
        ChecklistKnowledgeService(retrieve=fail).build(request())


def test_guidance_never_emits_reminder_without_consent():
    checklist = SavedChecklist(
        user_id=1,
        service_id="income_certificate",
        service_name="Income Certificate",
        language="hi",
        status="in_progress",
        progress_percentage=50,
        source_version="rag-v1",
        source_citations=[],
        storage_origin="sqlite",
        sync_status="pending",
        items=[
            ChecklistItem(
                id="item-one",
                item_type="document",
                title="निवास प्रमाण",
                sequence_number=1,
                is_required=True,
                is_completed=False,
                source_item_key="document:residence",
                source_state="current",
            )
        ],
    )
    without_consent = ChecklistGuidanceService.build(checklist)
    with_consent = ChecklistGuidanceService.build(
        checklist, reminders_consented=True
    )

    assert without_consent.reminders == []
    assert without_consent.missing_documents == ["निवास प्रमाण"]
    assert len(with_consent.reminders) == 1
