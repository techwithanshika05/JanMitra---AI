from integration.rag_adapter import ManyaRAGAdapter


class WorkingRetriever:
    def retrieve(self, query, top_k):
        return [{
            "text": "Submit identity and address documents.",
            "metadata": {"source_file": "ration-guidelines.pdf"},
            "similarity": 0.82,
        }]


class FailingRetriever:
    def retrieve(self, query, top_k):
        raise RuntimeError("retrieval unavailable")


class FailingFactory:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        raise OSError("paging file is too small")


def test_adapter_preserves_legacy_contract():
    result = ManyaRAGAdapter(retriever_factory=WorkingRetriever).answer(
        "What documents are needed?"
    )
    assert result["answer"]
    assert result["is_grounded"] is True
    assert result["sources"][0]["title"] == "ration-guidelines.pdf"
    assert set(result) == {
        "answer", "confidence", "is_grounded", "disclaimer", "sources"
    }


def test_adapter_controls_retrieval_failure():
    result = ManyaRAGAdapter(retriever_factory=FailingRetriever).answer(
        "Unknown query"
    )
    assert result["is_grounded"] is False
    assert result["confidence"] == 0.0
    assert result["sources"] == []


def test_initialization_failure_uses_cooldown_before_retrying():
    factory = FailingFactory()
    now = [100.0]
    adapter = ManyaRAGAdapter(
        retriever_factory=factory,
        retry_cooldown_seconds=60,
        clock=lambda: now[0],
    )

    first = adapter.answer("First query")
    second = adapter.answer("Second query")

    assert first["is_grounded"] is False
    assert second["is_grounded"] is False
    assert factory.calls == 1

    now[0] = 161.0
    adapter.answer("Retry after cooldown")
    assert factory.calls == 2
