"""Shared AsyncOpenAI client and small helper utilities for agents."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.tools.definitions import TOOL_REGISTRY

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    """Return a process-wide AsyncOpenAI client (instrumented by OpenInference)."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
    return _client


def execute_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a registered mock tool and return a JSON-serializable result."""
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    result = fn(**arguments)
    # Convert pydantic or list-of-pydantic to plain data
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if isinstance(result, list):
        return [r.model_dump() if hasattr(r, "model_dump") else r for r in result]
    return result


def serialize(data: Any) -> str:
    """JSON-serialize a value tolerantly (pydantic, lists, dicts)."""
    try:
        if hasattr(data, "model_dump"):
            return json.dumps(data.model_dump(), default=str)
        if isinstance(data, list):
            return json.dumps(
                [d.model_dump() if hasattr(d, "model_dump") else d for d in data],
                default=str,
            )
        return json.dumps(data, default=str)
    except Exception:
        return str(data)
