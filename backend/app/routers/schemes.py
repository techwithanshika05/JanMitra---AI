from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.get("", response_model=list[schemas.SchemeOut])
def list_schemes(db: Session = Depends(get_db)):
    return db.query(models.Scheme).all()


def _matches(scheme: models.Scheme, f: schemas.SchemeFinderRequest) -> tuple[bool, list[str]]:
    """
    Rule-based matching with an explainability trail -- every accepted /
    rejected criterion is recorded so the UI can show "why this scheme"
    exactly as required by the spec (AI Explainability section).
    """
    reasons = []
    ok = True

    if f.state and scheme.state not in (f.state, "All India"):
        ok = False
    elif f.state:
        reasons.append(f"Available in {f.state}")

    if f.age is not None:
        if scheme.min_age and f.age < scheme.min_age:
            ok = False
        elif scheme.max_age and f.age > scheme.max_age:
            ok = False
        else:
            reasons.append(f"Age {f.age} fits the eligible range")

    if f.gender and scheme.gender not in ("All", f.gender):
        ok = False

    if f.income is not None and scheme.max_income is not None and f.income > scheme.max_income:
        ok = False
    elif f.income is not None and scheme.max_income is not None:
        reasons.append(f"Income within limit of ₹{scheme.max_income}")

    if f.occupation and scheme.occupation and scheme.occupation != "any" and scheme.occupation != f.occupation:
        ok = False
    elif f.occupation and scheme.occupation:
        reasons.append(f"Matches occupation: {f.occupation}")

    if f.category and scheme.category and f.category.lower() != scheme.category.lower():
        ok = False

    if scheme.disability_required and not f.disability:
        ok = False

    return ok, reasons


@router.post("/find", response_model=list[schemas.SchemeOut])
def find_schemes(payload: schemas.SchemeFinderRequest, db: Session = Depends(get_db)):
    all_schemes = db.query(models.Scheme).all()
    matched = []
    for s in all_schemes:
        ok, reasons = _matches(s, payload)
        if ok:
            out = schemas.SchemeOut.model_validate(s)
            out.match_reason = "; ".join(reasons) if reasons else "General eligibility criteria satisfied"
            matched.append(out)

    db.add(models.AnalyticsEvent(event_type="scheme_search", payload=payload.model_dump()))
    db.commit()
    return matched


@router.get("/{scheme_id}", response_model=schemas.SchemeOut)
def get_scheme(scheme_id: int, db: Session = Depends(get_db)):
    return db.query(models.Scheme).filter(models.Scheme.id == scheme_id).first()
