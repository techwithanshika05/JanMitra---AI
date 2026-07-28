import io
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.database import get_db
from app import models, schemas
from app.chat_identity import resolve_identity
from app.identity_tracking.service import track_feature_activity

router = APIRouter(prefix="/checklist", tags=["checklist"])

# Dynamic checklist knowledge -- in a full build this would be sourced from
# the RAG knowledge base; kept as structured data here for fast, deterministic
# checklist generation (documents/steps should never be "hallucinated").
CHECKLIST_LIBRARY = {
    "new_ration_card": {
        "documents": [
            "Aadhaar card of all family members",
            "Proof of residence (electricity bill / rent agreement)",
            "Income certificate",
            "Passport-size photographs",
            "Bank account passbook",
        ],
        "steps": [
            "Visit the state PDS portal or nearest Fair Price Shop / Tehsil office",
            "Fill Form for New Ration Card application",
            "Upload/attach required documents",
            "Pay applicable fee (if any)",
            "Note the application/reference number for tracking",
            "Field verification by local Food & Supplies inspector",
            "Card issued/dispatched after approval",
        ],
        "estimated_time": "15-30 days",
    },
    "duplicate_ration_card": {
        "documents": ["FIR copy or self-declaration of loss/damage", "Original ration card (if damaged)", "Aadhaar card", "Recent photograph"],
        "steps": ["Apply for duplicate card on state PDS portal", "Submit loss declaration/FIR", "Pay duplicate card fee", "Verification and reissue"],
        "estimated_time": "7-15 days",
    },
    "address_update": {
        "documents": ["Existing ration card", "New address proof", "Aadhaar card"],
        "steps": ["Submit address change request online/offline", "Field verification of new address", "Updated card issued"],
        "estimated_time": "10-20 days",
    },
    "add_member": {
        "documents": ["Existing ration card", "Aadhaar of new member", "Birth certificate / marriage certificate as applicable"],
        "steps": ["Submit member addition form", "Attach relationship proof", "Verification", "Updated card with new member"],
        "estimated_time": "10-20 days",
    },
    "delete_member": {
        "documents": ["Existing ration card", "Death certificate / proof of migration / separation, as applicable"],
        "steps": ["Submit member deletion request", "Attach supporting proof", "Verification", "Updated card issued"],
        "estimated_time": "7-15 days",
    },
    "migration_transfer": {
        "documents": ["Existing ration card", "New address proof in destination state/district", "Aadhaar card"],
        "steps": ["Apply for ration card portability/transfer (or use One Nation One Ration Card for inter-state)", "Surrender/link old card details", "Verification at new location", "New/linked card activated"],
        "estimated_time": "15-30 days",
    },
    "pmay_housing": {
        "documents": ["Aadhaar card", "Income certificate", "Land/property documents (if any)", "Bank account details", "Passport photo"],
        "steps": ["Register on PMAY portal or via Common Service Centre", "Fill eligibility and application form", "Upload documents", "Track status via application ID"],
        "estimated_time": "Varies by state, typically 30-90 days for approval",
    },
    "scholarship": {
        "documents": ["Aadhaar card", "Income certificate", "Previous year mark sheet", "Caste certificate (if applicable)", "Bank passbook", "Bonafide student certificate"],
        "steps": ["Register on National/State Scholarship Portal", "Fill application with academic + bank details", "Upload documents and submit", "Institution verification", "Disbursal to bank account"],
        "estimated_time": "30-60 days",
    },
}


@router.post("/generate", response_model=schemas.ChecklistResponse)
def generate_checklist(
    payload: schemas.ChecklistRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identity = resolve_identity(request, response, db)
    entry = CHECKLIST_LIBRARY.get(
        payload.service_type,
        {"documents": ["Aadhaar card", "Proof of residence", "Income certificate"],
         "steps": ["Visit the relevant department portal or office", "Submit application with documents", "Track application status"],
         "estimated_time": "Varies"},
    )
    db.add(models.AnalyticsEvent(event_type="checklist_generated", payload={"service_type": payload.service_type}))
    track_feature_activity(
        db,
        identity,
        feature="checklist",
        action_type="generated",
        reference_id=payload.service_type,
    )
    db.commit()

    return schemas.ChecklistResponse(
        service_type=payload.service_type,
        documents=entry["documents"],
        steps=entry["steps"],
        estimated_time=entry["estimated_time"],
        notes="Document requirements can vary slightly by state. Confirm final list at your local office/portal.",
    )


@router.post("/generate/pdf")
def generate_checklist_pdf(
    payload: schemas.ChecklistRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    identity = resolve_identity(request, response, db)
    track_feature_activity(
        db,
        identity,
        feature="checklist",
        action_type="pdf_generated",
        reference_id=payload.service_type,
    )
    db.commit()
    entry = CHECKLIST_LIBRARY.get(payload.service_type, {"documents": [], "steps": [], "estimated_time": "N/A"})

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "JanMitra AI - Document Checklist")
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Service: {payload.service_type.replace('_', ' ').title()}")
    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Required Documents:")
    y -= 20
    c.setFont("Helvetica", 11)
    for doc in entry["documents"]:
        c.drawString(65, y, f"[ ] {doc}")
        y -= 18

    y -= 15
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Application Steps:")
    y -= 20
    c.setFont("Helvetica", 11)
    for i, step in enumerate(entry["steps"], 1):
        c.drawString(65, y, f"{i}. {step}")
        y -= 18

    y -= 15
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, y, "Generated by JanMitra AI. Confirm exact requirements with your local office.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={payload.service_type}_checklist.pdf"},
    )
