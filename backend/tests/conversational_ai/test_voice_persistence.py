from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.chat_identity import ChatIdentity
from app.conversational_ai.persistence.repository import VoiceRepository
from app.database import Base
from app.identity_tracking.service import claim_guest_data
from app.models import User


def test_guest_session_and_structured_turn():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    repo = VoiceRepository(db)
    row = repo.create_session(ChatIdentity(guest_id="00000000-0000-0000-0000-000000000001"), "room-1", "hi-IN")
    repo.add_turn(
        row.id, speaker="agent", text="नमस्ते", language="hi-IN",
        answer_mode="curated_rule", evidence_status="curated_rule",
    )
    db.commit()
    loaded = repo.owned_session(row.id, ChatIdentity(guest_id="00000000-0000-0000-0000-000000000001"), with_turns=True)
    assert loaded.total_turns == 1
    assert loaded.turns[0].original_text == "नमस्ते"


def test_voice_session_is_claimed_with_existing_guest_history():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    user = User(
        name="Voice User", email="voice@example.com", public_id="PDS900001",
        hashed_password="not-used-in-test",
    )
    db.add(user)
    db.flush()
    guest_id = "00000000-0000-0000-0000-000000000002"
    row = VoiceRepository(db).create_session(
        ChatIdentity(guest_id=guest_id), "room-claim", "hi-IN"
    )
    summary = claim_guest_data(db, guest_id=guest_id, user_id=user.id)
    db.commit()
    assert summary["voice_sessions"] == 1
    assert row.user_id == user.id
    assert row.guest_session_id is None
    assert row.claimed_guest_session_id == guest_id
