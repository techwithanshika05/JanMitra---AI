from app.rag.intent_router import IntentDecision, IntentRouter
from app.rag import response_router


class FakeLLM:
    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def generate(self, **kwargs):
        self.calls += 1
        return self.response


def test_positive_feedback_is_handled_without_llm_or_rag():
    def unexpected_llm():
        raise AssertionError("Common intent should not initialize the LLM")

    decision = IntentRouter(llm_factory=unexpected_llm).route(
        'You gave a good answer for "How do I update my ration card?" Thank you.',
        "en",
    )

    assert decision.kind == "conversation"
    assert "glad" in decision.reply.lower()


def test_unmatched_welfare_query_is_classified_by_project_llm(monkeypatch):
    fake = FakeLLM(
        '{"intent":"pds_welfare","has_new_question":true,'
        '"confidence":0.99,"reply":""}'
    )
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    decision = IntentRouter(llm_factory=lambda: fake).route(
        "How can I add a member to my ration card?", "en"
    )

    assert decision.kind == "pds_welfare"
    assert decision.has_new_question is True
    assert decision.reply is None
    assert fake.calls == 1


def test_project_llm_classifies_and_answers_general_conversation(monkeypatch):
    fake = FakeLLM(
        '{"intent":"out_of_scope","has_new_question":true,"confidence":0.96,'
        '"reply":"JanMitra is designed for PDS and welfare questions. '
        'Please ask me about those services."}'
    )
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    decision = IntentRouter(llm_factory=lambda: fake).route(
        "What do you think about learning guitar?", "en"
    )

    assert decision.kind == "out_of_scope"
    assert "designed for PDS" in decision.reply
    assert fake.calls == 1


def test_mixed_thanks_and_new_question_uses_llm_decision(monkeypatch):
    fake = FakeLLM(
        '{"intent":"pds_welfare","has_new_question":true,'
        '"confidence":0.94,"reply":""}'
    )
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    decision = IntentRouter(llm_factory=lambda: fake).route(
        "Thanks. Can I also remove a member from my ration card?", "en"
    )

    assert decision.kind == "pds_welfare"
    assert decision.has_new_question is True
    assert fake.calls == 1


def test_foodgrain_document_question_routes_to_rag_without_classifier(monkeypatch):
    def unexpected_llm():
        raise AssertionError("Explicit foodgrain evidence queries should route directly")

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    decision = IntentRouter(llm_factory=unexpected_llm).route(
        "TOTAL FOODGRAIN ALLOCATIONS REACHED A RECORD HIGH "
        "OF 1,002 LAKH TONS IN 2021-22",
        "en",
    )

    assert decision.kind == "pds_welfare"
    assert decision.has_new_question is True
    assert decision.confidence == 0.95


def test_response_router_sends_only_domain_queries_to_rag(monkeypatch):
    class FakeIntentRouter:
        def route(self, message, language, conversation_context=None):
            if "ration" in message:
                return IntentDecision("pds_welfare", 0.99, has_new_question=True)
            return IntentDecision("conversation", 0.95, "Happy to chat!")

    class FakeRAG:
        def answer(self, message, language):
            return {
                "answer": "RAG answer",
                "confidence": 0.8,
                "is_grounded": True,
                "disclaimer": "Government data disclaimer",
                "sources": [{"title": "ration.pdf", "snippet": "text", "score": 0.8}],
            }

    monkeypatch.setattr(response_router, "intent_router", FakeIntentRouter())
    monkeypatch.setattr(response_router, "rag_adapter", FakeRAG())
    monkeypatch.setattr(response_router, "curated_answer", lambda *_: None)

    conversation = response_router.generate_chat_response("I like this", "en")
    domain = response_router.generate_chat_response("ration question", "en")

    assert conversation["response_type"] == "conversation"
    assert conversation["sources"] == []
    assert conversation["disclaimer"] == ""
    assert conversation["is_grounded"] is False
    assert domain["answer"] == "RAG answer"
    assert domain["sources"][0]["title"] == "ration.pdf"
