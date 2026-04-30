"""Embeddings endpoint (for future similarity-search features)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.llm_client import get_openai_client
from app.config import settings

router = APIRouter(prefix="/api")


class EmbeddingRequest(BaseModel):
    text: str
    model: Optional[str] = None


@router.post("/embeddings")
async def embeddings(req: EmbeddingRequest):
    client = get_openai_client()
    model = req.model or settings.EMBEDDING_MODEL
    try:
        resp = await client.embeddings.create(model=model, input=req.text)
    except Exception as e:
        raise HTTPException(500, detail=f"embedding failed: {e}")
    vec = resp.data[0].embedding if resp.data else []
    return {
        "embeddings": vec,
        "model": model,
        "usage": getattr(resp, "usage", {}),
        "dimensions": len(vec),
    }
