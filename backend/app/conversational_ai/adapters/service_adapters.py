from app.routers.checklist import CHECKLIST_LIBRARY
from app.routers.grievance import DEPARTMENT_MAP


def checklist_for(service_id: str) -> dict | None:
    return CHECKLIST_LIBRARY.get(service_id)


def grievance_guidance(category: str) -> dict:
    return {
        "department": DEPARTMENT_MAP.get(category, DEPARTMENT_MAP["other"]),
        "steps": [
            "Use the state grievance portal or CPGRAMS, or visit the relevant local office.",
            "Describe what happened and when; avoid sharing OTPs or full identity numbers.",
            "Save the complaint reference number and use it for follow-up.",
        ],
    }
