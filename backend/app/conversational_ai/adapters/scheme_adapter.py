from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models


def search_existing_schemes(db: Session, query: str, limit: int = 3) -> list[dict]:
    terms = [term for term in query.lower().split() if len(term) >= 3][:5]
    if not terms:
        return []
    filters = []
    for term in terms:
        pattern = f"%{term}%"
        filters.extend([models.Scheme.name.ilike(pattern), models.Scheme.description.ilike(pattern), models.Scheme.category.ilike(pattern)])
    rows = db.query(models.Scheme).filter(or_(*filters)).limit(limit).all()
    return [{
        "id": row.id, "name": row.name, "description": row.description,
        "benefits": row.benefits, "required_documents": row.required_documents or [],
        "application_steps": row.application_steps or [], "source": row.official_source,
    } for row in rows]
