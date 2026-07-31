import re
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field


router = APIRouter(prefix="/documents", tags=["documents"])

DOCUMENT_DIR = Path("./uploaded_docs/citizen").resolve()
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024


class DocumentQuestion(BaseModel):
    doc_id: str
    question: str = Field(min_length=1, max_length=1000)
    language: str = "en"


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[\w\u0900-\u097f]+", value.casefold())
        if len(token) > 2
    }


def _document_path(doc_id: str) -> Path:
    try:
        normalized_id = str(uuid.UUID(doc_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc

    matches = list(DOCUMENT_DIR.glob(f"{normalized_id}__*.txt"))
    if not matches:
        raise HTTPException(status_code=404, detail="Document not found")
    return matches[0]


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "document.txt").name
    if Path(filename).suffix.casefold() != ".txt":
        raise HTTPException(status_code=415, detail="Only .txt files are supported")

    content = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Document must be 2 MB or smaller")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Document must be UTF-8 text") from exc
    if not text.strip():
        raise HTTPException(status_code=400, detail="Document is empty")

    doc_id = str(uuid.uuid4())
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)
    DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
    (DOCUMENT_DIR / f"{doc_id}__{safe_filename}").write_text(text, encoding="utf-8")

    return {"doc_id": doc_id, "filename": filename, "status": "ready"}


@router.post("/ask")
def ask_document(payload: DocumentQuestion):
    path = _document_path(payload.doc_id)
    text = path.read_text(encoding="utf-8")
    question_tokens = _tokens(payload.question)

    passages = [
        passage.strip()
        for passage in re.split(r"(?:\r?\n){2,}|(?<=[.!?])\s+", text)
        if passage.strip()
    ]
    ranked = sorted(
        (
            (len(question_tokens & _tokens(passage)), index, passage)
            for index, passage in enumerate(passages)
        ),
        reverse=True,
    )
    matches = [item for item in ranked if item[0] > 0][:3]

    if not matches:
        answer = (
            "मुझे इस दस्तावेज़ में इस सवाल का स्पष्ट उत्तर नहीं मिला।"
            if payload.language.startswith("hi")
            else "I could not find a clear answer to that question in this document."
        )
        return {
            "answer": answer,
            "confidence": 0.0,
            "sources": [],
            "is_grounded": False,
        }

    selected = [item[2] for item in sorted(matches, key=lambda item: item[1])]
    answer = " ".join(selected)
    if len(answer) > 1200:
        answer = f"{answer[:1197].rstrip()}..."
    matched_terms = max(item[0] for item in matches)
    confidence = min(0.95, 0.35 + (matched_terms / max(len(question_tokens), 1)) * 0.6)

    return {
        "answer": answer,
        "confidence": round(confidence, 3),
        "sources": [
            {
                "title": path.name.split("__", 1)[-1],
                "snippet": answer[:240],
                "score": round(confidence, 3),
            }
        ],
        "is_grounded": True,
    }
