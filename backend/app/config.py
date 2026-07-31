"""
Central configuration for JanMitra AI backend.
Reads from environment variables with sane local defaults, so the app
runs out-of-the-box in dev and can be reconfigured for prod via .env.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "JanMitra AI - Welfare & Ration Assistant"

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SQLITE_FALLBACK_URL: str = os.getenv(
        "SQLITE_FALLBACK_URL", "sqlite:///./janmitra.db"
    )
    DATABASE_CONNECT_TIMEOUT: int = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "3"))

    # --- Auth / JWT ---
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"

    # --- Fixed administrator ---
    # Override both values in production. This account is the only identity
    # accepted by the dedicated admin login endpoint.
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@janmitra.in").strip().lower()
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin@123")

    # --- Vector DB ---
    CHROMA_DIR: str = str(
        Path(os.getenv("CHROMA_DIR", "./data/vector_db/chroma")).resolve()
    )
    CHROMA_COLLECTION: str = os.getenv(
        "CHROMA_COLLECTION", "pds_welfare_knowledge"
    )
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
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
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    MIN_CONFIDENCE_TO_ANSWER: float = float(
        os.getenv("MIN_CONFIDENCE_TO_ANSWER", "0.35")
    )
    RAG_REQUEST_TIMEOUT_SECONDS: float = float(
        os.getenv("RAG_REQUEST_TIMEOUT_SECONDS", "12")
    )
    CHAT_RAG_TIMEOUT_SECONDS: float = float(
        os.getenv("CHAT_RAG_TIMEOUT_SECONDS", "60")
    )

    # --- Conversational voice agent (LiveKit + Sarvam) ---
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    VOICE_AGENT_NAME: str = os.getenv("VOICE_AGENT_NAME", "janmitra-scheme-agent")
    VOICE_DEFAULT_LANGUAGE: str = os.getenv("VOICE_DEFAULT_LANGUAGE", "hi-IN")
    VOICE_ROOM_TTL_MINUTES: int = int(os.getenv("VOICE_ROOM_TTL_MINUTES", "30"))
    SARVAM_STT_MODEL: str = os.getenv("SARVAM_STT_MODEL", "saaras:v3")
    SARVAM_STT_MODE: str = os.getenv("SARVAM_STT_MODE", "codemix")
    SARVAM_TTS_MODEL: str = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
    SARVAM_TTS_SPEAKER: str = os.getenv("SARVAM_TTS_SPEAKER", "shubh")
    SARVAM_TTS_PACE: float = float(os.getenv("SARVAM_TTS_PACE", "0.9"))
    SARVAM_LLM_MODEL: str = os.getenv("SARVAM_LLM_MODEL", "sarvam-105b")

    # --- CORS ---
    ALLOWED_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]
    ALLOWED_ORIGIN_REGEX: str = os.getenv(
        "ALLOWED_ORIGIN_REGEX",
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    )


settings = Settings()
