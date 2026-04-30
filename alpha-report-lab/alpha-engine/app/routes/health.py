"""Health check endpoint."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "version": settings.SERVICE_VERSION,
        "model": settings.OPENAI_MODEL,
        "fast_model": settings.OPENAI_FAST_MODEL,
        "deployment_environment": settings.DEPLOYMENT_ENV,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
