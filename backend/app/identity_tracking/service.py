from datetime import datetime

from sqlalchemy.orm import Session

from app import chat_models
from app.checklists.models import SavedChecklist
from app.chat_identity import ChatIdentity
from app.identity_tracking.models import (
    FeatureActivity,
    GuestClaim,
    SchemeActivity,
    UserPreference,
)
from app.conversational_ai.persistence.models import VoiceSession


def owned_filter(model, identity: ChatIdentity):
    if identity.user_id is not None:
        return model.user_id == identity.user_id
    return model.guest_session_id == identity.guest_id


def track_scheme_activity(
    db: Session,
    identity: ChatIdentity,
    *,
    scheme_id: int,
    action_type: str,
    query_text: str | None = None,
    result_position: int | None = None,
    metadata: dict | None = None,
) -> SchemeActivity:
    row = SchemeActivity(
        scheme_id=scheme_id,
        user_id=identity.user_id,
        guest_session_id=identity.guest_id,
        action_type=action_type,
        query_text=query_text,
        result_position=result_position,
        metadata_json=metadata,
        storage_origin="sqlite" if db.bind and db.bind.dialect.name == "sqlite" else "postgresql",
        sync_status="pending" if db.bind and db.bind.dialect.name == "sqlite" else "synced",
    )
    db.add(row)
    return row


def track_feature_activity(
    db: Session,
    identity: ChatIdentity,
    *,
    feature: str,
    action_type: str,
    reference_id: str | None = None,
    metadata: dict | None = None,
) -> FeatureActivity:
    row = FeatureActivity(
        feature=feature,
        action_type=action_type,
        reference_id=reference_id,
        user_id=identity.user_id,
        guest_session_id=identity.guest_id,
        metadata_json=metadata,
        storage_origin="sqlite" if db.bind and db.bind.dialect.name == "sqlite" else "postgresql",
        sync_status="pending" if db.bind and db.bind.dialect.name == "sqlite" else "synced",
    )
    db.add(row)
    return row


def claim_guest_data(db: Session, *, guest_id: str, user_id: int) -> dict[str, int | bool]:
    existing = db.query(GuestClaim).filter(GuestClaim.guest_session_id == guest_id).first()
    if existing:
        if existing.user_id != user_id:
            raise PermissionError("This guest session was already claimed by another user")
        return {**existing.summary_json, "already_claimed": True}

    summary: dict[str, int | bool] = {
        "chat_sessions": 0,
        "chat_feedback": 0,
        "checklists": 0,
        "scheme_activities": 0,
        "preferences": 0,
        "feature_activities": 0,
        "voice_sessions": 0,
        "already_claimed": False,
    }
    now = datetime.utcnow()

    sessions = db.query(chat_models.ChatSession).filter(
        chat_models.ChatSession.guest_id == guest_id,
        chat_models.ChatSession.user_id.is_(None),
    ).all()
    for row in sessions:
        row.user_id = user_id
        row.claimed_guest_id = guest_id
        row.guest_id = None
        row.ownership_status = "claimed"
        row.claimed_at = now
    summary["chat_sessions"] = len(sessions)

    feedback = db.query(chat_models.ChatFeedback).filter(
        chat_models.ChatFeedback.guest_id == guest_id,
        chat_models.ChatFeedback.user_id.is_(None),
    ).all()
    for row in feedback:
        row.user_id = user_id
        row.claimed_guest_id = guest_id
        row.guest_id = None
        row.identity_key = f"u:{user_id}"
        row.ownership_status = "claimed"
        row.claimed_at = now
    summary["chat_feedback"] = len(feedback)

    checklists = db.query(SavedChecklist).filter(
        SavedChecklist.guest_session_id == guest_id,
        SavedChecklist.user_id.is_(None),
    ).all()
    for row in checklists:
        row.user_id = user_id
        row.claimed_guest_session_id = guest_id
        row.guest_session_id = None
        row.ownership_status = "claimed"
        row.claimed_at = now
    summary["checklists"] = len(checklists)

    activities = db.query(SchemeActivity).filter(
        SchemeActivity.guest_session_id == guest_id,
        SchemeActivity.user_id.is_(None),
    ).all()
    for row in activities:
        row.user_id = user_id
        row.ownership_status = "claimed"
        row.claimed_at = now
    summary["scheme_activities"] = len(activities)

    feature_activities = db.query(FeatureActivity).filter(
        FeatureActivity.guest_session_id == guest_id,
        FeatureActivity.user_id.is_(None),
    ).all()
    for row in feature_activities:
        row.user_id = user_id
        row.ownership_status = "claimed"
        row.claimed_at = now
    summary["feature_activities"] = len(feature_activities)

    voice_sessions = db.query(VoiceSession).filter(
        VoiceSession.guest_session_id == guest_id,
        VoiceSession.user_id.is_(None),
    ).all()
    for row in voice_sessions:
        row.user_id = user_id
        row.claimed_guest_session_id = guest_id
        row.guest_session_id = None
        row.ownership_status = "claimed"
        row.claimed_at = now
    summary["voice_sessions"] = len(voice_sessions)

    preferences = db.query(UserPreference).filter(
        UserPreference.guest_session_id == guest_id,
        UserPreference.user_id.is_(None),
    ).all()
    user_preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    for row in preferences:
        if user_preference:
            db.delete(row)
        else:
            row.user_id = user_id
            row.ownership_status = "claimed"
            row.claimed_at = now
            user_preference = row
    summary["preferences"] = len(preferences)

    db.add(
        GuestClaim(
            guest_session_id=guest_id,
            user_id=user_id,
            summary_json={key: value for key, value in summary.items() if key != "already_claimed"},
        )
    )
    db.flush()
    return summary
