"""Alpha report routes."""
from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from openinference.instrumentation import using_attributes

from app.agents.orchestrator import generate_alpha_report
from app.config import settings
from app.models.report import AlphaReport, GenerateRequest, GenerationProgress

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alpha")


@router.post("/generate")
async def generate(req: GenerateRequest, request: Request):
    """Kick off background report generation and return the report_id."""
    report_store = request.app.state.report_store
    context_mgr = request.app.state.context_mgr

    with using_attributes(
        session_id=str(uuid.uuid4()),
        user_id=req.user_id or "anonymous",
        tags=["alpha-report", f"ticker:{req.ticker}"],
    ):
        report_id = await report_store.create_report(req, settings.OPENAI_MODEL)
        asyncio.create_task(generate_alpha_report(report_id, req, report_store, context_mgr))
        return {"report_id": report_id, "status": "pending"}


@router.get("/status/{report_id}", response_model=GenerationProgress)
async def status(report_id: str, request: Request):
    report_store = request.app.state.report_store
    prog = await report_store.get_progress(report_id)
    if not prog:
        raise HTTPException(404, detail="report not found")
    return prog


@router.get("/reports")
async def list_reports(request: Request):
    report_store = request.app.state.report_store
    reports = await report_store.list_reports()
    # Truncate section content for summary view
    out = []
    for r in reports:
        d = r.model_dump()
        for s in d["sections"]:
            if s.get("content") and len(s["content"]) > 240:
                s["content"] = s["content"][:240] + "..."
        out.append(d)
    return out


@router.get("/reports/{report_id}", response_model=AlphaReport)
async def get_report(report_id: str, request: Request):
    report_store = request.app.state.report_store
    report = await report_store.get_report(report_id)
    if not report:
        raise HTTPException(404, detail="report not found")
    return report


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, request: Request):
    report_store = request.app.state.report_store
    ok = await report_store.delete_report(report_id)
    if not ok:
        raise HTTPException(404, detail="report not found")
    return {"deleted": True, "report_id": report_id}


@router.post("/cancel/{report_id}")
async def cancel_report(report_id: str, request: Request):
    """Request graceful cancellation of an in-progress report. The orchestrator
    checks between agent stages and stops cleanly; status flips to 'cancelled'."""
    report_store = request.app.state.report_store
    report = await report_store.get_report(report_id)
    if not report:
        raise HTTPException(404, detail="report not found")
    ok = await report_store.request_cancel(report_id)
    if not ok:
        # Already terminal — return current status without erroring.
        return {"cancelled": False, "report_id": report_id, "status": report.status}
    logger.info(f"[cancel] cancellation requested for {report_id} (current status: {report.status})")
    return {"cancelled": True, "report_id": report_id, "status": "cancelling"}
