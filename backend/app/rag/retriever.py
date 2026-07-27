"""Compatibility proxy; the active implementation is Manya's RAG stack."""
from integration.rag_adapter import rag_adapter


class RetrieverProxy:
    @property
    def ready(self) -> bool:
        try:
            rag_adapter._get_retriever()
            return True
        except Exception:
            return False

    def query(self, text: str, top_k: int | None = None):
        results = rag_adapter.retrieve(text)
        selected = results[:top_k] if top_k else results
        output = []
        for result in selected:
            source = rag_adapter._source(result)
            output.append({
                "text": result.get("text", ""),
                "title": source["title"],
                "source": (result.get("metadata") or {}).get("source_file", ""),
                "score": source["score"],
            })
        return output

    def add_documents(self, chunks):
        return rag_adapter.add_documents(chunks)


retriever = RetrieverProxy()
