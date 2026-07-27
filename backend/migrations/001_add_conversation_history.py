"""Create additive conversation tables using the configured SQLAlchemy engine.

Run from ``backend`` with:
    python migrations/001_add_conversation_history.py
"""
from app import chat_models  # noqa: F401
from app.database import Base, engine


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Conversation history tables are ready.")
