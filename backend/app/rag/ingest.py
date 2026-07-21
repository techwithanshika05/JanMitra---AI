"""
Data pipeline: raw/ -> prepared/ -> metadata/ -> embeddings (Chroma)

Stages:
1. Load  - read raw JSON (schemes, FAQs) from data/raw
2. Clean - strip whitespace/HTML, normalize casing for matching fields
3. Chunk - split long text (~300 chars) with slight overlap so each chunk
           stays semantically coherent and citeable on its own
4. Embed - hand chunks to the Retriever, which embeds + stores in Chroma
5. Log   - write chunk counts to data/metadata/ingest_report.json for the
           admin "Knowledge Base" screen

Run:  python -m app.rag.ingest
"""
import json
import os
from datetime import datetime
from app.rag.retriever import retriever

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE, "..", "data")
DATA_DIR = os.path.normpath(DATA_DIR)


def chunk_text(text: str, size: int = 300, overlap: int = 40):
    text = " ".join(text.split())  # normalize whitespace
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks if chunks else [text]


def load_json(name: str):
    path = os.path.join(DATA_DIR, "prepared", name)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ingest_all():
    schemes = load_json("schemes.json")
    faqs = load_json("faqs.json")

    all_chunks = []

    for s in schemes:
        full_text = (
            f"{s['name']}. Category: {s.get('category','')}. "
            f"State: {s.get('state','All India')}. "
            f"Eligibility: age {s.get('min_age','any')}-{s.get('max_age','any')}, "
            f"income under {s.get('max_income','N/A')}, occupation {s.get('occupation','any')}. "
            f"Description: {s.get('description','')}. Benefits: {s.get('benefits','')}."
        )
        for i, ch in enumerate(chunk_text(full_text)):
            all_chunks.append({
                "id": f"scheme-{s['id']}-{i}",
                "text": ch,
                "title": s["name"],
                "source": s.get("official_source", "JanMitra Scheme Database"),
            })

    for f_ in faqs:
        full_text = f"Q: {f_['question']} A: {f_['answer']}"
        for i, ch in enumerate(chunk_text(full_text)):
            all_chunks.append({
                "id": f"faq-{f_['id']}-{i}",
                "text": ch,
                "title": f_["question"],
                "source": f_.get("source", "JanMitra FAQ Bank"),
            })

    retriever.add_documents(all_chunks)

    report = {
        "ingested_at": datetime.utcnow().isoformat(),
        "scheme_records": len(schemes),
        "faq_records": len(faqs),
        "total_chunks": len(all_chunks),
        "vector_backend_ready": retriever.ready,
    }
    os.makedirs(os.path.join(DATA_DIR, "metadata"), exist_ok=True)
    with open(os.path.join(DATA_DIR, "metadata", "ingest_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(f"Ingested {len(all_chunks)} chunks from {len(schemes)} schemes + {len(faqs)} FAQs.")
    print(f"Vector backend ready: {retriever.ready}")


if __name__ == "__main__":
    ingest_all()
