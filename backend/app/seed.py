"""
One-shot seed script.
Run:  python -m app.seed

- Creates DB tables
- Creates a default admin user (admin@janmitra.gov.in / Admin@123)
- Loads sample schemes from data/prepared/schemes.json into SQLite
- Loads sample FAQs from data/prepared/faqs.json into SQLite
- Triggers RAG ingestion (embeds everything into ChromaDB)
"""
import json
import os
from pathlib import Path
from app.database import Base, engine, SessionLocal
from app import models, auth
from app.rag.ingest import ingest_all, DATA_DIR


def _dataset_path(name: str) -> Path | None:
    candidates = (
        Path(DATA_DIR) / "prepared" / name,
        Path(__file__).resolve().parents[1] / "data" / "extracted" / name,
    )
    return next((path for path in candidates if path.exists()), None)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # --- Admin user ---
    if not db.query(models.User).filter(models.User.email == "admin@janmitra.gov.in").first():
        admin_user = models.User(
            name="JanMitra Admin",
            email="admin@janmitra.gov.in",
            hashed_password=auth.hash_password("Admin@123"),
            role="admin",
            preferred_language="en",
        )
        db.add(admin_user)
        print("Created admin user: admin@janmitra.gov.in / Admin@123")

    # --- Schemes ---
    schemes_path = _dataset_path("schemes.json")
    if schemes_path and db.query(models.Scheme).count() == 0:
        with schemes_path.open("r", encoding="utf-8") as f:
            schemes = json.load(f)
        for s in schemes:
            db.add(models.Scheme(
                id=s["id"], name=s["name"], category=s.get("category"),
                state=s.get("state", "All India"), min_age=s.get("min_age"),
                max_age=s.get("max_age"), gender=s.get("gender", "All"),
                max_income=s.get("max_income"), occupation=s.get("occupation"),
                disability_required=s.get("disability_required", False),
                description=s.get("description"), benefits=s.get("benefits"),
                required_documents=s.get("required_documents", []),
                application_steps=s.get("application_steps", []),
                official_source=s.get("official_source"),
            ))
        print(f"Loaded {len(schemes)} schemes")

    # --- FAQs ---
    faqs_path = _dataset_path("faqs.json")
    if faqs_path and db.query(models.FAQ).count() == 0:
        with faqs_path.open("r", encoding="utf-8") as f:
            faqs = json.load(f)
        for fq in faqs:
            db.add(models.FAQ(
                id=fq["id"], question=fq["question"], answer=fq["answer"],
                category=fq.get("category"), language=fq.get("language", "en"),
                source=fq.get("source"),
            ))
        print(f"Loaded {len(faqs)} FAQs")

    db.commit()
    db.close()

    # --- RAG ingestion (embeddings into ChromaDB) ---
    ingest_all()
    print("Seed complete.")


if __name__ == "__main__":
    seed()
