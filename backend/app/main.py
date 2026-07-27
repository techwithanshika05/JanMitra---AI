"""
JanMitra AI - backend entrypoint.

Why FastAPI: async-native, automatic OpenAPI docs (great for judges to
explore /docs live), first-class Pydantic validation which pairs cleanly
with the strict response schemas this app needs for explainability.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import (
    admin,
    analytics,
    auth,
    chat,
    chat_history,
    checklist,
    grievance,
    ration,
    schemes,
    upload,
)

# Create tables if they don't exist yet (simple approach suitable for an
# internship-scale project; swap for Alembic migrations in production).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered assistant for PDS/Ration services and government welfare schemes.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(schemes.router)
app.include_router(checklist.router)
app.include_router(ration.router)
app.include_router(grievance.router)
app.include_router(upload.router)
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(chat_history.router)


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
