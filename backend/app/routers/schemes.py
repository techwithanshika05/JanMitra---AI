from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.chat_identity import resolve_identity
from app.config import settings
from app.identity_tracking.service import track_scheme_activity
from integration.rag_adapter import rag_adapter

router = APIRouter(prefix="/schemes", tags=["schemes"])
_rag_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scheme-rag")


@router.get("", response_model=list[schemas.SchemeOut])
def list_schemes(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    resolve_identity(request, response, db)
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

    # The finder UI collects the citizen's social category (General/OBC/SC/ST/BPL),
    # while Scheme.category stores a benefit domain such as "Housing" or
    # "Farmer Welfare". Comparing those two unrelated values rejected every
    # scheme. Keep social category available for the RAG profile, but do not use
    # it as a database-domain filter.
    if f.category:
        reasons.append(f"Citizen category recorded: {f.category}")

    if scheme.disability_required and not f.disability:
        ok = False

    return ok, reasons


def _rule_based_matches(
    db: Session, payload: schemas.SchemeFinderRequest
) -> list[tuple[models.Scheme, schemas.SchemeOut]]:
    matched = []
    for scheme in db.query(models.Scheme).all():
        ok, reasons = _matches(scheme, payload)
        if ok:
            out = schemas.SchemeOut.model_validate(scheme)
            out.match_reason = (
                "; ".join(reasons)
                if reasons
                else "General eligibility criteria satisfied"
            )
            matched.append((scheme, out))
    return matched


def _rag_query(payload: schemas.SchemeFinderRequest) -> str:
    filters = payload.model_dump(exclude_none=True)
    details = ", ".join(
        f"{key.replace('_', ' ')}: {value}"
        for key, value in filters.items()
        if value not in ("", False)
    )
    return (
        "Find a government welfare scheme matching this citizen profile. "
        f"{details or 'No profile filters supplied.'} "
        "Only use verified government scheme documents and cite the source."
    )


def _rag_answer_with_timeout(payload: schemas.SchemeFinderRequest) -> dict:
    future = _rag_executor.submit(rag_adapter.answer, _rag_query(payload), "en")
    try:
        return future.result(timeout=settings.RAG_REQUEST_TIMEOUT_SECONDS)
    except FutureTimeout:
        future.cancel()
        return {
            "answer": "",
            "confidence": 0.0,
            "is_grounded": False,
            "sources": [],
        }


@router.post("/find", response_model=list[schemas.SchemeOut])
def find_schemes(
    payload: schemas.SchemeFinderRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identity = resolve_identity(request, response, db)
    matched_rows = _rule_based_matches(db, payload)
    for position, (scheme, _) in enumerate(matched_rows, start=1):
        track_scheme_activity(
            db,
            identity,
            scheme_id=scheme.id,
            action_type="recommended",
            result_position=position,
            metadata={"filters": payload.model_dump(exclude_none=True)},
        )

    db.add(models.AnalyticsEvent(event_type="scheme_search", payload=payload.model_dump()))
    db.commit()
    return [out for _, out in matched_rows]


@router.post("/find-hybrid", response_model=schemas.HybridSchemeFinderResponse)
def find_schemes_hybrid(
    payload: schemas.SchemeFinderRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Use deterministic eligibility rules first, then grounded RAG fallback."""
    identity = resolve_identity(request, response, db)
    matched_rows = _rule_based_matches(db, payload)
    if matched_rows:
        for position, (scheme, _) in enumerate(matched_rows, start=1):
            track_scheme_activity(
                db,
                identity,
                scheme_id=scheme.id,
                action_type="recommended",
                result_position=position,
                metadata={
                    "filters": payload.model_dump(exclude_none=True),
                    "result_source": "database",
                },
            )
        db.add(
            models.AnalyticsEvent(
                event_type="scheme_search",
                payload={
                    **payload.model_dump(),
                    "result_source": "database",
                    "result_count": len(matched_rows),
                },
            )
        )
        db.commit()
        return schemas.HybridSchemeFinderResponse(
            schemes=[out for _, out in matched_rows],
            result_source="database",
        )

    rag_result = _rag_answer_with_timeout(payload)
    grounded = bool(
        rag_result.get("is_grounded")
        and rag_result.get("sources")
        and float(rag_result.get("confidence") or 0.0)
        >= settings.MIN_CONFIDENCE_TO_ANSWER
    )
    result_source = "rag" if grounded else "none"
    db.add(
        models.AnalyticsEvent(
            event_type="scheme_search",
            payload={
                **payload.model_dump(),
                "result_source": result_source,
                "result_count": 0,
            },
        )
    )
    db.commit()
    if grounded:
        return schemas.HybridSchemeFinderResponse(
            schemes=[],
            result_source="rag",
            rag_result=schemas.SchemeRAGResult(
                answer=rag_result["answer"],
                confidence=rag_result["confidence"],
                sources=rag_result["sources"],
            ),
        )
    return schemas.HybridSchemeFinderResponse(
        schemes=[],
        result_source="none",
        alert=(
            "We could not find a verified matching scheme in the scheme database "
            "or official RAG sources. Please widen your criteria or try again later."
        ),
    )


@router.get("/{scheme_id}", response_model=schemas.SchemeOut)
def get_scheme(
    scheme_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identity = resolve_identity(request, response, db)
    scheme = db.query(models.Scheme).filter(models.Scheme.id == scheme_id).first()
    if scheme is not None:
        track_scheme_activity(
            db, identity, scheme_id=scheme_id, action_type="viewed"
        )
        db.commit()
    return scheme
