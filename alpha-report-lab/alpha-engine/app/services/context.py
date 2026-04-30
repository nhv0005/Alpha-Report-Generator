"""Session and report context management."""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.models.report import GenerateRequest


@dataclass
class ReportContext:
    report_id: str
    session_id: str
    user_id: str
    ticker: str
    investment_horizon: str
    risk_tolerance: str
    focus_areas: List[str] = field(default_factory=list)
    custom_instructions: Optional[str] = None
    gathered_data: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    def __init__(self) -> None:
        self._contexts: Dict[str, ReportContext] = {}
        self._lock = asyncio.Lock()

    async def create_context(self, request: GenerateRequest, report_id: str) -> ReportContext:
        ctx = ReportContext(
            report_id=report_id,
            session_id=str(uuid.uuid4()),
            user_id=request.user_id or "anonymous",
            ticker=request.ticker.upper(),
            investment_horizon=request.investment_horizon,
            risk_tolerance=request.risk_tolerance,
            focus_areas=request.focus_areas or [],
            custom_instructions=request.custom_instructions,
        )
        async with self._lock:
            self._contexts[report_id] = ctx
        return ctx

    async def get_context(self, report_id: str) -> Optional[ReportContext]:
        async with self._lock:
            return self._contexts.get(report_id)

    async def update_gathered_data(self, report_id: str, key: str, data: Any) -> None:
        async with self._lock:
            ctx = self._contexts.get(report_id)
            if ctx:
                ctx.gathered_data[key] = data
