from dataclasses import dataclass
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.checklists.note_safety import SensitiveNoteError
from app.checklists.analytics import ChecklistAnalyticsService
from app.checklists.guidance import ChecklistGuidanceService
from app.checklists.intelligence import (
    ChecklistKnowledgeService,
    ChecklistKnowledgeUnavailableError,
    InsufficientChecklistEvidenceError,
)
from app.checklists.repository import ChecklistOwner
from app.checklists.schemas import (
    ChecklistGuidance,
    ChecklistAnalytics,
    ChecklistImportResult,
    ChecklistItemPatch,
    ChecklistKnowledgeRequest,
    ChecklistListResponse,
    ChecklistPatch,
    ChecklistRefreshResult,
    ChecklistResponse,
    GuestChecklistImport,
    SavedChecklistOut,
)
from app.checklists.service import (
    ChecklistImportApprovalRequiredError,
    ChecklistItemNotFoundError,
    ChecklistNotFoundError,
    SavedChecklistService,
)
from app.checklists.storage import (
    ChecklistStorage,
    ChecklistStorageSelection,
)
from app.chat_identity import guest_id_from_request, resolve_identity
from app.database import get_db
from app import auth, models
from app import auth, models

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/checklists", tags=["saved-checklists"])
checklist_storage = ChecklistStorage()
checklist_knowledge = ChecklistKnowledgeService()


@dataclass(frozen=True)
class RequestChecklistIdentity:
    owner: ChecklistOwner
    guest_session_id: str | None


def get_checklist_selection():
    with checklist_storage.repository() as selection:
        yield selection


def get_checklist_knowledge_service() -> ChecklistKnowledgeService:
    return checklist_knowledge


def get_request_identity(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> RequestChecklistIdentity:
    identity = resolve_identity(request, response, db)
    return RequestChecklistIdentity(
        owner=ChecklistOwner(
            user_id=identity.user_id,
            guest_session_id=identity.guest_id,
        ),
        guest_session_id=guest_id_from_request(request),
    )


SelectionDep = Annotated[ChecklistStorageSelection, Depends(get_checklist_selection)]
IdentityDep = Annotated[RequestChecklistIdentity, Depends(get_request_identity)]
KnowledgeDep = Annotated[
    ChecklistKnowledgeService, Depends(get_checklist_knowledge_service)
]


def _run(operation):
    try:
        return operation()
    except (ChecklistNotFoundError, ChecklistItemNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChecklistImportApprovalRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except SensitiveNoteError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InsufficientChecklistEvidenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ChecklistKnowledgeUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except IntegrityError as exc:
        logger.warning("Saved checklist integrity conflict: %s", exc)
        raise HTTPException(status_code=409, detail="Checklist data conflict") from exc
    except SQLAlchemyError as exc:
        logger.exception("Saved checklist database operation failed")
        raise HTTPException(
            status_code=503, detail="Checklist storage is temporarily unavailable"
        ) from exc


def _response(
    selection: ChecklistStorageSelection,
    checklist,
) -> ChecklistResponse:
    return ChecklistResponse(
        storage_mode=selection.origin,
        sync_status=checklist.sync_status,
        checklist=SavedChecklistOut.model_validate(checklist),
    )


@router.post("", response_model=ChecklistResponse, status_code=status.HTTP_201_CREATED)
def create_checklist(
    payload: ChecklistKnowledgeRequest,
    identity: IdentityDep,
    selection: SelectionDep,
    knowledge: KnowledgeDep,
):
    service = SavedChecklistService(selection.repository)
    verified_payload = _run(lambda: knowledge.build(payload))
    checklist = _run(
        lambda: service.create(
            identity.owner,
            verified_payload,
            storage_origin=selection.origin,
            sync_status=selection.sync_status,
        )
    )
    return _response(selection, checklist)


@router.get("", response_model=ChecklistListResponse)
def list_checklists(
    identity: IdentityDep,
    selection: SelectionDep,
    archived: bool = Query(default=False),
):
    service = SavedChecklistService(selection.repository)
    rows = _run(
        lambda: service.list_archived(identity.owner)
        if archived
        else service.list_active(identity.owner)
    )
    return ChecklistListResponse(
        storage_mode=selection.origin,
        sync_status=selection.sync_status,
        checklists=[SavedChecklistOut.model_validate(row) for row in rows],
    )


@router.get("/admin/analytics", response_model=ChecklistAnalytics)
def checklist_admin_analytics(
    selection: SelectionDep,
    _admin: models.User = Depends(auth.require_admin),
):
    return ChecklistAnalyticsService.summarize(
        selection.repository,
        active_storage_mode=selection.origin,
    )


@router.get("/{checklist_id}", response_model=ChecklistResponse)
def get_checklist(
    checklist_id: str,
    identity: IdentityDep,
    selection: SelectionDep,
):
    checklist = _run(
        lambda: SavedChecklistService(selection.repository).get(
            checklist_id, identity.owner
        )
    )
    return _response(selection, checklist)


@router.patch("/{checklist_id}", response_model=ChecklistResponse)
def update_checklist(
    checklist_id: str,
    payload: ChecklistPatch,
    identity: IdentityDep,
    selection: SelectionDep,
):
    checklist = _run(
        lambda: SavedChecklistService(selection.repository).update(
            checklist_id, identity.owner, payload
        )
    )
    return _response(selection, checklist)


@router.patch("/{checklist_id}/items/{item_id}", response_model=ChecklistResponse)
def update_checklist_item(
    checklist_id: str,
    item_id: str,
    payload: ChecklistItemPatch,
    identity: IdentityDep,
    selection: SelectionDep,
):
    checklist = _run(
        lambda: SavedChecklistService(selection.repository).update_item(
            checklist_id, item_id, identity.owner, payload
        )
    )
    return _response(selection, checklist)


@router.post("/import-guest", response_model=ChecklistImportResult)
def import_guest_checklists(
    payload: GuestChecklistImport,
    identity: IdentityDep,
    selection: SelectionDep,
):
    if identity.owner.user_id is None:
        raise HTTPException(status_code=401, detail="Login required to import checklists")
    if identity.guest_session_id is None:
        return ChecklistImportResult(
            storage_mode=selection.origin,
            sync_status=selection.sync_status,
            imported_count=0,
            skipped_count=0,
        )

    count = _run(
        lambda: SavedChecklistService(selection.repository).import_guest(
            ChecklistOwner(guest_session_id=identity.guest_session_id),
            identity.owner,
            approved=payload.approved,
        )
    )
    return ChecklistImportResult(
        storage_mode=selection.origin,
        sync_status=selection.sync_status,
        imported_count=count,
        skipped_count=0,
    )


@router.post("/{checklist_id}/refresh", response_model=ChecklistRefreshResult)
def refresh_checklist(
    checklist_id: str,
    identity: IdentityDep,
    selection: SelectionDep,
    knowledge: KnowledgeDep,
):
    service = SavedChecklistService(selection.repository)
    checklist = _run(lambda: service.get(checklist_id, identity.owner))
    payload = _run(
        lambda: knowledge.refresh_payload(
            ChecklistKnowledgeRequest(
                service_id=checklist.service_id,
                service_name=checklist.service_name,
                language=checklist.language,
                state=(checklist.knowledge_context or {}).get("state"),
                category=(checklist.knowledge_context or {}).get("category"),
            )
        )
    )
    result = _run(
        lambda: service.refresh(checklist_id, identity.owner, payload)
    )
    return ChecklistRefreshResult(
        storage_mode=selection.origin,
        sync_status=result.checklist.sync_status,
        checklist=SavedChecklistOut.model_validate(result.checklist),
        new_items=result.new_items,
        changed_items=result.changed_items,
        removed_items=result.removed_items,
        source_version_changed=result.source_version_changed,
    )


@router.get("/{checklist_id}/guidance", response_model=ChecklistGuidance)
def checklist_guidance(
    checklist_id: str,
    identity: IdentityDep,
    selection: SelectionDep,
    reminders_consented: bool = Query(default=False),
):
    checklist = _run(
        lambda: SavedChecklistService(selection.repository).get(
            checklist_id, identity.owner
        )
    )
    return ChecklistGuidanceService.build(
        checklist, reminders_consented=reminders_consented
    )


@router.post("/{checklist_id}/archive", response_model=ChecklistResponse)
def archive_checklist(
    checklist_id: str,
    identity: IdentityDep,
    selection: SelectionDep,
):
    checklist = _run(
        lambda: SavedChecklistService(selection.repository).archive(
            checklist_id, identity.owner
        )
    )
    return _response(selection, checklist)


@router.post("/{checklist_id}/restore", response_model=ChecklistResponse)
def restore_checklist(
    checklist_id: str,
    identity: IdentityDep,
    selection: SelectionDep,
):
    checklist = _run(
        lambda: SavedChecklistService(selection.repository).restore(
            checklist_id, identity.owner
        )
    )
    return _response(selection, checklist)


@router.delete("/{checklist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist(
    checklist_id: str,
    identity: IdentityDep,
    selection: SelectionDep,
):
    _run(
        lambda: SavedChecklistService(selection.repository).delete(
            checklist_id, identity.owner
        )
    )
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)
