"""Writer Agent — composes the final polished report (executive summary, catalysts, recommendation)."""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from typing import Any, Dict

from app.agents.llm_client import get_openai_client
from app.config import settings
from app.instrumentation import tracer
from app.models.report import ReportSection
from app.services.context import ReportContext

logger = logging.getLogger(__name__)

WRITER_PROMPT = (
    "You are a senior investment writer at a premier research firm. Your writing "
    "is clear, concise, and compelling. You synthesize complex analysis into "
    "executive-ready narratives. Format all output in clean Markdown with headers, "
    "bullet points, bold key figures, and tables where appropriate."
)


def _parse_recommendation(text: str, target_price: float, current_price: float) -> tuple[str, float]:
    """Extract recommendation and conviction score from LLM text, with heuristic fallback."""
    rec = "HOLD"
    score = 5.0
    t_upper = text.upper()
    for candidate in ["STRONG_BUY", "STRONG BUY", "STRONG_SELL", "STRONG SELL", "BUY", "SELL", "HOLD"]:
        if candidate in t_upper:
            rec = candidate.replace(" ", "_")
            break
    m = re.search(r"conviction[^0-9]{0,12}(\d+(?:\.\d+)?)\s*/\s*10", text, re.IGNORECASE)
    if m:
        try:
            score = float(m.group(1))
        except ValueError:
            pass
    else:
        # Derive from upside
        upside = (target_price - current_price) / current_price if current_price else 0
        if upside > 0.2:
            rec, score = "STRONG_BUY", 8.5
        elif upside > 0.08:
            rec, score = "BUY", 7.0
        elif upside < -0.15:
            rec, score = "STRONG_SELL", 2.5
        elif upside < -0.05:
            rec, score = "SELL", 3.5
        else:
            rec, score = "HOLD", 5.5
    return rec, max(1.0, min(10.0, score))


async def compose_report(context: ReportContext) -> Dict[str, Any]:
    logger.info(f"[writer_agent] Composing final report for {context.ticker}")
    start = time.time()
    data = context.gathered_data
    price = data.get("price_data")
    target_price = data.get("target_price", 0.0)
    risk_rating = data.get("risk_rating", "MEDIUM")
    sentiment = data.get("sentiment_data")
    bear_case = data.get("bear_case_target", 0.0)

    with tracer.start_as_current_span("writer_agent") as agent_span:
        agent_span.set_attribute("openinference.span.kind", "CHAIN")
        agent_span.set_attribute("input.value", f"Compose report for {context.ticker}")

        client = get_openai_client()

        upside_pct = ((target_price - price.current_price) / price.current_price * 100) if price.current_price else 0.0
        common_ctx = (
            f"Ticker: {context.ticker}\n"
            f"Current: ${price.current_price:.2f}\n"
            f"Target: ${target_price:.2f} ({upside_pct:+.1f}% upside)\n"
            f"Bear case: ${bear_case:.2f}\n"
            f"Risk rating: {risk_rating}\n"
            f"Sentiment: {sentiment.overall_score:+.2f} (consensus {sentiment.analyst_consensus})\n"
            f"Horizon: {context.investment_horizon}\n"
            f"Risk tolerance: {context.risk_tolerance}\n"
        )

        # Executive Summary
        exec_prompt = (
            f"Write the Executive Summary (3-4 paragraphs) with thesis, conviction level, "
            f"target price, and risk/reward framing.\n\n{common_ctx}"
        )
        exec_resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "system", "content": WRITER_PROMPT}, {"role": "user", "content": exec_prompt}],
            temperature=0.4,
        )
        exec_content = exec_resp.choices[0].message.content or ""
        exec_tokens = exec_resp.usage.total_tokens if exec_resp.usage else 0

        # Catalysts
        cat_prompt = (
            f"Write a Catalyst Identification section. Include upcoming earnings, regulatory "
            f"changes, product launches, and macro catalysts that could impact the thesis. "
            f"Provide 5-7 specific, ranked catalysts with expected timing.\n\n{common_ctx}"
        )
        cat_resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "system", "content": WRITER_PROMPT}, {"role": "user", "content": cat_prompt}],
            temperature=0.4,
        )
        cat_content = cat_resp.choices[0].message.content or ""
        cat_tokens = cat_resp.usage.total_tokens if cat_resp.usage else 0

        # Recommendation
        rec_prompt = (
            f"Write the final Recommendation section. Provide a clear BUY / HOLD / SELL "
            f"(or STRONG_BUY / STRONG_SELL) call with a Conviction Score X/10, a single-line "
            f"thesis, target price, recommended timeframe, and position-sizing guidance "
            f"appropriate for a {context.risk_tolerance} investor.\n\n{common_ctx}"
        )
        rec_resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "system", "content": WRITER_PROMPT}, {"role": "user", "content": rec_prompt}],
            temperature=0.3,
        )
        rec_content = rec_resp.choices[0].message.content or ""
        rec_tokens = rec_resp.usage.total_tokens if rec_resp.usage else 0

        recommendation, conviction = _parse_recommendation(rec_content, target_price, price.current_price)

        exec_section = ReportSection(
            id=str(uuid.uuid4()), title="Executive Summary", type="executive_summary",
            content=exec_content, agent="writer_agent", tokens_used=exec_tokens,
            generation_time_ms=int((time.time() - start) * 1000 // 3),
        )
        cat_section = ReportSection(
            id=str(uuid.uuid4()), title="Catalyst Identification", type="catalysts",
            content=cat_content, agent="writer_agent", tokens_used=cat_tokens,
            generation_time_ms=int((time.time() - start) * 1000 // 3),
        )
        rec_section = ReportSection(
            id=str(uuid.uuid4()), title="Recommendation", type="recommendation",
            content=rec_content, data={"recommendation": recommendation, "conviction_score": conviction},
            agent="writer_agent", tokens_used=rec_tokens,
            generation_time_ms=int((time.time() - start) * 1000 // 3),
        )

        agent_span.set_attribute("output.value", f"{recommendation} ({conviction:.1f}/10)")
        agent_span.set_attribute("llm.token_count.total", exec_tokens + cat_tokens + rec_tokens)

    return {
        "executive_summary_section": exec_section,
        "catalysts_section": cat_section,
        "recommendation_section": rec_section,
        "recommendation": recommendation,
        "conviction_score": conviction,
        "tools_called": [],
    }
