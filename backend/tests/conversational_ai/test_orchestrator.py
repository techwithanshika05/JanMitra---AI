from types import SimpleNamespace

from app.conversational_ai.conversation.orchestrator import ConversationOrchestrator


def test_rule_response_does_not_call_rag(monkeypatch):
    monkeypatch.setattr(
        "app.conversational_ai.conversation.orchestrator.voice_rag.answer",
        lambda *_: (_ for _ in ()).throw(AssertionError("RAG should not run")),
    )
    result = ConversationOrchestrator(SimpleNamespace()).respond("Namaste")
    assert result.answer_mode == "curated_rule"
    assert result.evidence_status == "curated_rule"


def test_reliable_rag_wins(monkeypatch):
    monkeypatch.setattr(
        "app.conversational_ai.conversation.orchestrator.voice_rag.answer",
        lambda *_: SimpleNamespace(
            answer="Verified answer", evidence_status="verified_document",
            confidence=0.91, sources=[{"title": "Official guide"}],
        ),
    )
    result = ConversationOrchestrator(SimpleNamespace()).respond("ration update process")
    assert result.answer_mode == "rag"
    assert result.sources
