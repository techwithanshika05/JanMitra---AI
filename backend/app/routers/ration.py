from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/ration", tags=["ration"])

RATION_PROCESSES = {
    "new_card": {
        "title": "Apply for a New Ration Card",
        "explanation": "Issued to households not currently holding any ration card, "
                       "enabling subsidized foodgrain purchase under PDS.",
        "steps": ["Check eligibility (no existing card in household)", "Apply via state PDS portal / CSC / Tehsil office",
                   "Submit Aadhaar, address & income proof", "Field verification", "Card issued (physical/digital)"],
    },
    "duplicate": {
        "title": "Duplicate Ration Card",
        "explanation": "For lost, stolen, or damaged ration cards.",
        "steps": ["File police complaint if lost/stolen (recommended)", "Apply for duplicate on portal",
                   "Pay nominal duplicate fee", "Verification", "Duplicate card issued"],
    },
    "update_member": {
        "title": "Add/Update Family Member",
        "explanation": "Add a newborn, spouse after marriage, or correct member details.",
        "steps": ["Login to PDS portal", "Choose 'Update Member Details'", "Attach relationship proof (birth/marriage certificate)",
                   "Submit for verification", "Updated card reflects new member"],
    },
    "address_update": {
        "title": "Update Address",
        "explanation": "Required when a household shifts residence within the same state.",
        "steps": ["Submit address change request", "Provide new address proof", "Local verification",
                   "Updated card with new address issued"],
    },
    "delete_member": {
        "title": "Delete a Family Member",
        "explanation": "For deceased members or those who have permanently moved out.",
        "steps": ["Submit deletion request with reason", "Attach death certificate or proof of relocation as applicable",
                   "Verification", "Member removed from card"],
    },
    "migration": {
        "title": "Migration / Card Portability",
        "explanation": "For citizens relocating across districts/states; India's One Nation One Ration Card (ONORC) "
                       "allows portability of ration entitlement nationwide.",
        "steps": ["Check ONORC portability via portal or Fair Price Shop e-PoS", "Update address if permanent move",
                   "Use Aadhaar-linked card at any FPS under ONORC", "Formal transfer if settling permanently in new state"],
    },
}


@router.get("/processes")
def list_processes():
    return [{"key": k, "title": v["title"]} for k, v in RATION_PROCESSES.items()]


@router.get("/processes/{process_key}")
def get_process(process_key: str):
    proc = RATION_PROCESSES.get(process_key)
    if not proc:
        raise HTTPException(status_code=404, detail="Unknown ration process")
    return proc
