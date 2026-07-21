"""
Central configuration for JanMitra AI backend.
Reads from environment variables with sane local defaults, so the app
runs out-of-the-box in dev and can be reconfigured for prod via .env.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "JanMitra AI - Welfare & Ration Assistant"

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./janmitra.db")

    # --- Auth / JWT ---
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours

    # --- Vector DB ---
    CHROMA_DIR: str = os.getenv("CHROMA_DIR", "./chroma_store")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # --- LLM Provider ---
    # Set GEMINI_API_KEY or OPENAI_API_KEY in your .env. If neither is set,
    # the /chat endpoint falls back to a deterministic retrieval-only mode
    # (returns the top matched knowledge chunks instead of a generated
    # answer) so the app is still fully demoable with zero API keys.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")  # "gemini" | "openai" | "none"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # --- RAG behavior ---
    RETRIEVAL_TOP_K: int = 4
    MIN_CONFIDENCE_TO_ANSWER: float = 0.35  # below this -> "I don't know, here are sources"

    # --- CORS ---
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
