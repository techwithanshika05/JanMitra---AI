"""
RAG retrieval layer.

Design choices (why):
- ChromaDB (embedded, on-disk) instead of a hosted vector DB: zero infra
  cost for an internship-scale project, persists locally, trivially
  swappable for pgvector/Pinecone later.
- sentence-transformers/all-MiniLM-L6-v2: small (80MB), fast on CPU,
  good semantic quality for short government-FAQ style text.
- Every chunk keeps its `source` and `title` in metadata so every answer
  can be traced back to a document -> supports the "always cite source,
  never hallucinate" requirement.
- If sentence-transformers/chromadb aren't installed yet (e.g. first run
  before `pip install -r requirements.txt`), the module degrades to a
  simple keyword-overlap retriever so the API never hard-crashes.
"""
import os
import re
from typing import List, Dict
from app.config import settings

_HAS_VECTOR_STACK = True
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError:
    _HAS_VECTOR_STACK = False


class Retriever:
    def __init__(self):
        self.ready = False
        self._fallback_corpus: List[Dict] = []  # used if vector stack unavailable

        if _HAS_VECTOR_STACK:
            os.makedirs(settings.CHROMA_DIR, exist_ok=True)
            self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
            self.collection = self.client.get_or_create_collection("janmitra_knowledge")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self.ready = True

    # ---------------- Ingestion ----------------
    def add_documents(self, chunks: List[Dict]):
        """
        chunks: list of {id, text, title, source}
        Embeds and upserts into Chroma (or the fallback in-memory list).
        """
        if self.ready:
            ids = [c["id"] for c in chunks]
            texts = [c["text"] for c in chunks]
            metadatas = [{"title": c["title"], "source": c["source"]} for c in chunks]
            embeddings = self.model.encode(texts, show_progress_bar=False).tolist()
            self.collection.upsert(
                ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings
            )
        else:
            self._fallback_corpus.extend(chunks)

    # ---------------- Retrieval ----------------
    def query(self, text: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or settings.RETRIEVAL_TOP_K
        if self.ready:
            q_emb = self.model.encode([text], show_progress_bar=False).tolist()
            results = self.collection.query(query_embeddings=q_emb, n_results=top_k)
            out = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]
            for doc, meta, dist in zip(docs, metas, dists):
                # Chroma returns cosine distance; convert to a 0-1 similarity score
                score = max(0.0, 1 - dist)
                out.append(
                    {"text": doc, "title": meta.get("title", "Unknown"),
                     "source": meta.get("source", ""), "score": round(score, 3)}
                )
            return out
        else:
            return self._keyword_fallback(text, top_k)

    def _keyword_fallback(self, text: str, top_k: int) -> List[Dict]:
        """Naive overlap scoring so the app still works with zero ML deps installed."""
        query_tokens = set(re.findall(r"\w+", text.lower()))
        scored = []
        for c in self._fallback_corpus:
            doc_tokens = set(re.findall(r"\w+", c["text"].lower()))
            overlap = len(query_tokens & doc_tokens)
            score = overlap / (len(query_tokens) + 1e-6)
            if overlap > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        return [
            {"text": c["text"], "title": c["title"], "source": c["source"], "score": round(min(s, 1.0), 3)}
            for s, c in scored[:top_k]
        ]


# Singleton used across the app
retriever = Retriever()
