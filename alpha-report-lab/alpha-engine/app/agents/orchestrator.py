"""Orchestrator — coordinates all agents to build a complete Alpha Report."""
from __future__ import annotations

import json
import logging
import traceback
import uuid
from typing import Any, Dict

from openinference.instrumentation import using_attributes
from opentelemetry import trace

from app.agents import analysis_agent, research_agent, risk_agent, sentiment_agent, writer_agent
from app.agents.llm_metrics import (
    set_agent_input_messages,
    set_agent_output_messages,
    set_agent_span_attributes,
)
from app.config import settings
from app.instrumentation import tracer
from app.models.report import GenerateRequest
from app.services.context import ContextManager
from app.services.report_store import ReportStore

logger = logging.getLogger(__name__)


class _CancelledByUser(Exception):
    """Raised internally when the user cancels a generation in progress."""


async def _checkpoint(report_store: ReportStore, report_id: str) -> None:
    """Raise _CancelledByUser if the user requested cancellation. Called
    between agent stages so we never abort mid-LLM-call."""
    if await report_store.is_cancelled(report_id):
        raise _CancelledByUser()


async def generate_alpha_report(
    report_id: str,
    request: GenerateRequest,
    report_store: ReportStore,
    context_mgr: ContextManager,
) -> None:
    """Run the full multi-agent flow for a given report_id.

    Runs as a background task kicked off by the /api/alpha/generate route.
    Updates the store with progressive status and sections, and finalizes the
    report with recommendation, target price, risk rating, and conviction.
    """
    report_ctx = await context_mgr.create_context(request, report_id)

    with using_attributes(
        session_id=report_ctx.session_id,
        user_id=request.user_id or "anonymous",
        tags=[
            "alpha-report",
            f"ticker:{request.ticker}",
            f"horizon:{request.investment_horizon}",
            f"risk:{request.risk_tolerance}",
        ],
        metadata={
            "report_id": report_id,
            "ticker": request.ticker,
            "investment_horizon": request.investment_horizon,
            "risk_tolerance": request.risk_tolerance,
            "environment": "local-lab",
        },
    ):
        with tracer.start_as_current_span("invoke_agent alpha_orchestrator") as orch_span:
            set_agent_span_attributes(
                orch_span,
                agent_name="alpha_orchestrator",
                description=(
                    "Supervisor agent. Coordinates research, analysis, sentiment, "
                    "risk, and writer sub-agents to build a complete Alpha Report."
                ),
                request_model=settings.OPENAI_MODEL,
                tool_definitions=[
                    "research_agent", "analysis_agent", "sentiment_agent",
                    "risk_agent", "writer_agent",
                ],
            )
            set_agent_input_messages(orch_span, [
                {"role": "user", "content": json.dumps({
                    "ticker": request.ticker,
                    "horizon": request.investment_horizon,
                    "risk_tolerance": request.risk_tolerance,
                })},
            ])

            # Attach trace_id to report metadata
            trace_id = format(orch_span.get_span_context().trace_id, "032x")
            await report_store.update_report(report_id, metadata=_with_trace(report_store, report_id, trace_id))

            try:
                # --- RESEARCH ---
                await _checkpoint(report_store, report_id)
                await report_store.update_status(report_id, "researching", "Gathering company data", "research_agent")
                research_out = await research_agent.research(report_ctx)
                for k in ("company_profile", "price_data", "financial_metrics", "earnings", "news", "peers"):
                    await context_mgr.update_gathered_data(report_id, k, research_out[k])
                await report_store.add_section(report_id, research_out["section"])
                await report_store.add_tools_called(report_id, research_out["tools_called"])

                profile = research_out["company_profile"]
                price = research_out["price_data"]
                await report_store.update_report(
                    report_id,
                    company_name=profile.name,
                    sector=profile.sector,
                    current_price=price.current_price,
                )

                # --- ANALYSIS + SENTIMENT ---
                await _checkpoint(report_store, report_id)
                await report_store.update_status(report_id, "analyzing", "Running fundamental + technical analysis", "analysis_agent")
                analysis_out = await analysis_agent.analyze(report_ctx)
                await context_mgr.update_gathered_data(report_id, "target_price", analysis_out["target_price"])
                await context_mgr.update_gathered_data(report_id, "peer_comparison", analysis_out["peer_comparison"])
                await report_store.add_section(report_id, analysis_out["fundamental_section"])
                await report_store.add_section(report_id, analysis_out["technical_section"])
                await report_store.add_tools_called(report_id, analysis_out["tools_called"])

                await _checkpoint(report_store, report_id)
                await report_store.update_status(report_id, "analyzing", "Analyzing sentiment and news flow", "sentiment_agent")
                sent_out = await sentiment_agent.analyze_sentiment(report_ctx)
                await context_mgr.update_gathered_data(report_id, "sentiment_data", sent_out["sentiment_data"])
                await context_mgr.update_gathered_data(report_id, "analyst_ratings", sent_out["analyst_ratings"])
                await report_store.add_section(report_id, sent_out["sentiment_section"])
                await report_store.add_tools_called(report_id, sent_out["tools_called"])

                # --- RISK ---
                await _checkpoint(report_store, report_id)
                await report_store.update_status(report_id, "assessing_risk", "Identifying and quantifying risks", "risk_agent")
                risk_out = await risk_agent.assess_risk(report_ctx)
                await context_mgr.update_gathered_data(report_id, "risk_rating", risk_out["risk_rating"])
                await context_mgr.update_gathered_data(report_id, "bear_case_target", risk_out["bear_case_target"])
                await report_store.add_section(report_id, risk_out["risk_section"])
                await report_store.add_tools_called(report_id, risk_out["tools_called"])

                # --- WRITER ---
                await _checkpoint(report_store, report_id)
                await report_store.update_status(report_id, "writing", "Composing executive summary and recommendation", "writer_agent")
                writer_out = await writer_agent.compose_report(report_ctx)
                await report_store.add_section(report_id, writer_out["executive_summary_section"])
                await report_store.add_section(report_id, writer_out["catalysts_section"])
                await report_store.add_section(report_id, writer_out["recommendation_section"])

                # --- FINALIZE ---
                current_price = price.current_price
                target_price = analysis_out["target_price"]
                upside_pct = ((target_price - current_price) / current_price * 100) if current_price else 0.0

                await report_store.update_report(
                    report_id,
                    recommendation=writer_out["recommendation"],
                    conviction_score=writer_out["conviction_score"],
                    target_price=target_price,
                    upside_percentage=round(upside_pct, 2),
                    risk_rating=risk_out["risk_rating"],
                )
                await report_store.finalize(report_id)
                await report_store.update_status(report_id, "complete", "Report complete", "orchestrator")

                orch_span.set_attribute("gen_ai.response.finish_reasons", json.dumps(["stop"]))
                set_agent_output_messages(orch_span, [
                    {"role": "assistant", "content": json.dumps({
                        "recommendation": writer_out["recommendation"],
                        "conviction_score": writer_out["conviction_score"],
                        "target_price": target_price,
                        "upside_pct": round(upside_pct, 2),
                        "risk_rating": risk_out["risk_rating"],
                    })},
                ])
                logger.info(f"[orchestrator] Report {report_id} complete: {writer_out['recommendation']} (conv {writer_out['conviction_score']:.1f})")

            except _CancelledByUser:
                logger.info(f"[orchestrator] Report {report_id} cancelled by user")
                orch_span.set_attribute("gen_ai.response.finish_reasons", json.dumps(["cancelled"]))
                await report_store.update_status(
                    report_id, "cancelled", "Cancelled by user", "orchestrator"
                )
                await report_store.finalize(report_id)
            except Exception as e:
                logger.exception(f"[orchestrator] Report {report_id} failed: {e}")
                orch_span.record_exception(e)
                orch_span.set_attribute("error.type", type(e).__name__)
                orch_span.set_attribute("gen_ai.response.finish_reasons", json.dumps(["error"]))
                await report_store.update_status(report_id, "error", f"Failed: {e}", "orchestrator")


def _with_trace(report_store: ReportStore, report_id: str, trace_id: str):
    """Return a mutated metadata object with trace_id set (best-effort, sync)."""
    # The store uses an async lock elsewhere; reading the in-memory dict directly is safe
    # only for a light mutation. We instead just return a dict that update_report can set.
    report = report_store._reports.get(report_id)  # noqa: SLF001
    if report:
        report.metadata.trace_id = trace_id
        return report.metadata
    return None
