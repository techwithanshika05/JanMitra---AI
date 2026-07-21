from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/grievance", tags=["grievance"])

DEPARTMENT_MAP = {
    "ration": "Department of Food, Civil Supplies & Consumer Affairs (State)",
    "scheme": "Concerned Scheme Nodal Ministry/Department",
    "pension": "Department of Social Welfare / Pension Directorate",
    "other": "District Grievance Redressal Cell",
}


@router.post("/guide", response_model=schemas.GrievanceResponse)
def guide_grievance(payload: schemas.GrievanceRequest, db: Session = Depends(get_db)):
    department = DEPARTMENT_MAP.get(payload.category, DEPARTMENT_MAP["other"])

    steps = [
        "Register the grievance on the state CM Helpline / CPGRAMS (pgportal.gov.in) portal, or visit the local office",
        "Provide clear details: what happened, when, ration card/scheme reference number if any",
        "Attach supporting documents/photos if available",
        "Note the complaint registration/reference number",
        "Track status periodically via the portal or helpline",
    ]

    escalation = [
        "If unresolved in expected time, escalate to the District Grievance Officer",
        "Next, escalate to the State Nodal Officer for the department",
        "For persistent non-resolution, approach the State Consumer Grievance Redressal body or RTI route",
    ]

    db.add(models.AnalyticsEvent(event_type="grievance_started", payload={"category": payload.category}))
    db.commit()

    return schemas.GrievanceResponse(
        department=department,
        steps=steps,
        expected_resolution_days=21,
        escalation_path=escalation,
        reference_note="Always save your grievance reference number; it is required for all follow-ups and escalations.",
    )
