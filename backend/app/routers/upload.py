import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, auth
from app.rag.retriever import retriever
from app.rag.ingest import chunk_text

router = APIRouter(prefix="/upload", tags=["upload"])
UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: models.User = Depends(auth.require_admin),
):
    """
    Admin-only: upload a policy document/FAQ text file. For simplicity this
    accepts .txt (PDF text-extraction can be wired in via pypdf without
    changing this contract). Content is chunked and embedded immediately so
    it becomes retrievable in the chat/RAG pipeline right away.
    """
    file_id = str(uuid.uuid4())
    path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    content_bytes = await file.read()
    with open(path, "wb") as f:
        f.write(content_bytes)

    try:
        text = content_bytes.decode("utf-8", errors="ignore")
    except Exception:
        text = ""

    chunks = [
        {"id": f"doc-{file_id}-{i}", "text": ch, "title": file.filename, "source": file.filename}
        for i, ch in enumerate(chunk_text(text))
    ]
    retriever.add_documents(chunks)

    doc = models.Document(
        title=file.filename, source_type="policy_pdf", file_path=path,
        chunk_count=len(chunks), uploaded_by=admin.id, status="processed",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"id": doc.id, "title": doc.title, "chunks_indexed": doc.chunk_count, "status": doc.status}


@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(auth.require_admin),
):
    return db.query(models.Document).all()
