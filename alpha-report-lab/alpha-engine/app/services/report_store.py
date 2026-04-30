"""In-memory report storage (thread-safe via asyncio.Lock)."""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Set

from app.models.report import (
    AlphaReport,
    GenerateRequest,
    GenerationProgress,
    ReportMetadata,
    ReportSection,
)

STEP_ORDER = ["pending", "researching", "analyzing", "assessing_risk", "writing", "complete"]


class ReportStore:
    def __init__(self) -> None:
        self._reports: Dict[str, AlphaReport] = {}
        self._progress: Dict[str, GenerationProgress] = {}
        self._start_times: Dict[str, float] = {}
        self._cancellations: Set[str] = set()
        self._lock = asyncio.Lock()

    async def create_report(self, request: GenerateRequest, model: str) -> str:
        report_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        async with self._lock:
            self._reports[report_id] = AlphaReport(
                id=report_id,
                ticker=request.ticker.upper(),
                status="pending",
                metadata=ReportMetadata(
                    session_id=session_id,
                    user_id=request.user_id or "anonymous",
                    model=model,
                ),
            )
            self._progress[report_id] = GenerationProgress(
                report_id=report_id,
                status="pending",
                current_step="queued",
                steps_completed=0,
                total_steps=len(STEP_ORDER) - 1,
                current_agent="",
                elapsed_time_ms=0,
            )
            self._start_times[report_id] = time.time()
        return report_id

    async def get_report(self, report_id: str) -> Optional[AlphaReport]:
        async with self._lock:
            return self._reports.get(report_id)

    async def update_report(self, report_id: str, **updates) -> None:
        async with self._lock:
            report = self._reports.get(report_id)
            if not report:
                return
            for k, v in updates.items():
                if hasattr(report, k):
                    setattr(report, k, v)

    async def update_status(self, report_id: str, status: str, current_step: str, current_agent: str = "") -> None:
        async with self._lock:
            report = self._reports.get(report_id)
            if report:
                report.status = status  # type: ignore[assignment]
            prog = self._progress.get(report_id)
            if prog:
                prog.status = status  # type: ignore[assignment]
                prog.current_step = current_step
                prog.current_agent = current_agent or prog.current_agent
                try:
                    prog.steps_completed = STEP_ORDER.index(status)
                except ValueError:
                    pass
                start = self._start_times.get(report_id, time.time())
                prog.elapsed_time_ms = int((time.time() - start) * 1000)

    async def add_section(self, report_id: str, section: ReportSection) -> None:
        async with self._lock:
            report = self._reports.get(report_id)
            if not report:
                return
            report.sections.append(section)
            report.metadata.total_tokens += section.tokens_used
            if section.agent and section.agent not in report.metadata.agents_used:
                report.metadata.agents_used.append(section.agent)

    async def add_tools_called(self, report_id: str, tools: List[str]) -> None:
        async with self._lock:
            report = self._reports.get(report_id)
            if not report:
                return
            for t in tools:
                if t not in report.metadata.tools_called:
                    report.metadata.tools_called.append(t)

    async def list_reports(self) -> List[AlphaReport]:
        async with self._lock:
            return list(self._reports.values())

    async def delete_report(self, report_id: str) -> bool:
        async with self._lock:
            if report_id in self._reports:
                del self._reports[report_id]
                self._progress.pop(report_id, None)
                self._start_times.pop(report_id, None)
                self._cancellations.discard(report_id)
                return True
            return False

    async def request_cancel(self, report_id: str) -> bool:
        """Mark a report for cancellation. The orchestrator polls is_cancelled()
        between agent stages and stops cleanly. Returns True if the report
        exists and was in a cancellable state."""
        async with self._lock:
            report = self._reports.get(report_id)
            if not report:
                return False
            if report.status in ("complete", "error", "cancelled"):
                return False
            self._cancellations.add(report_id)
            return True

    async def is_cancelled(self, report_id: str) -> bool:
        async with self._lock:
            return report_id in self._cancellations

    async def get_progress(self, report_id: str) -> Optional[GenerationProgress]:
        async with self._lock:
            prog = self._progress.get(report_id)
            if prog:
                start = self._start_times.get(report_id, time.time())
                prog.elapsed_time_ms = int((time.time() - start) * 1000)
            return prog

    async def finalize(self, report_id: str) -> None:
        async with self._lock:
            report = self._reports.get(report_id)
            if not report:
                return
            start = self._start_times.get(report_id, time.time())
            report.metadata.total_generation_time_ms = int((time.time() - start) * 1000)
