from types import SimpleNamespace

import pytest

from integration.rag_adapter import ManyaRAGAdapter


@pytest.fixture(autouse=True)
def disable_live_generation(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")


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


class WorkingPipeline:
    def __init__(self, visual_path):
        self.visual_path = visual_path

    def query(self, question, top_k):
        return SimpleNamespace(
            answer="The chart shows the record allocation.",
            sources=[{
                "file_name": "foodgrain.pdf",
                "source_id": "foodgrain",
                "score": 0.91,
            }],
            retrieved_images=[{
                "image_path": str(self.visual_path),
                "layout": "chart",
                "title": "Total foodgrain allocations",
                "page_number": 6,
                "source_file": "foodgrain.pdf",
            }],
        )


def test_adapter_preserves_legacy_contract():
    result = ManyaRAGAdapter(retriever_factory=WorkingRetriever).answer(
        "What documents are needed?"
    )
    assert result["answer"]
    assert result["is_grounded"] is True
    assert result["sources"][0]["title"] == "ration-guidelines.pdf"
    assert set(result) == {
        "answer", "confidence", "is_grounded", "disclaimer", "sources",
        "retrieved_images",
    }
    assert result["retrieved_images"] == []


def test_adapter_controls_retrieval_failure():
    result = ManyaRAGAdapter(retriever_factory=FailingRetriever).answer(
        "Unknown query"
    )
    assert result["is_grounded"] is False
    assert result["confidence"] == 0.0
    assert result["sources"] == []
    assert result["retrieved_images"] == []


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


def test_adapter_exposes_one_safe_visual_url(monkeypatch, tmp_path):
    from integration import rag_adapter as rag_adapter_module

    data_root = tmp_path / "data"
    visual_path = data_root / "retrieved_visuals" / "allocation chart.png"
    visual_path.parent.mkdir(parents=True)
    visual_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(rag_adapter_module, "DATA_ROOT", data_root.resolve())
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    result = ManyaRAGAdapter(
        pipeline_factory=lambda: WorkingPipeline(visual_path)
    ).answer("Show the foodgrain allocation chart")

    assert result["is_grounded"] is True
    assert len(result["retrieved_images"]) == 1
    visual = result["retrieved_images"][0]
    assert visual["url"].endswith(
        "/retrieved_visuals/allocation%20chart.png"
    )
    assert "image_path" not in visual
