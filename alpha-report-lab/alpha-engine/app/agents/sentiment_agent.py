"""Sentiment Agent — news flow + analyst consensus + narrative."""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict

from app.agents.llm_client import get_openai_client, serialize
from app.config import settings
from app.instrumentation import tracer
from app.models.report import ReportSection
from app.services.context import ReportContext
from app.tools.news_search import get_analyst_ratings, get_sentiment_score

logger = logging.getLogger(__name__)

SENTIMENT_PROMPT = (
    "You are a sentiment analysis specialist tracking market narratives, news "
    "flow, and social media sentiment for equities. Quantify sentiment where "
    "possible and identify narrative shifts. Format as Markdown."
)


async def _wrap_tool(tool_name: str, fn, *args, **kwargs):
    with tracer.start_as_current_span(f"tool:{tool_name}") as span:
        span.set_attribute("openinference.span.kind", "TOOL")
        span.set_attribute("tool.name", tool_name)
        params = {"args": args, "kwargs": kwargs}
        span.set_attribute("tool.parameters", serialize(params))
        span.set_attribute("input.value", serialize(params))
        result = fn(*args, **kwargs)
        span.set_attribute("output.value", serialize(result))
        return result


async def analyze_sentiment(context: ReportContext) -> Dict[str, Any]:
    logger.info(f"[sentiment_agent] Analyzing sentiment for {context.ticker}")
    start = time.time()

    with tracer.start_as_current_span("sentiment_agent") as agent_span:
        agent_span.set_attribute("openinference.span.kind", "AGENT")
        agent_span.set_attribute("input.value", f"Sentiment for {context.ticker}")

        sentiment = await _wrap_tool("get_sentiment_score", get_sentiment_score, context.ticker)
        ratings = await _wrap_tool("get_analyst_ratings", get_analyst_ratings, context.ticker)

        client = get_openai_client()
        headline_lines = "\n".join(
            f"- [{h.sentiment}] {h.title} ({h.source}, {h.date})"
            for h in sentiment.recent_headlines[:8]
        )
        prompt = (
            f"Write a Sentiment Analysis section for {context.ticker}. "
            f"Overall sentiment score: {sentiment.overall_score:+.2f} (-1 bearish, +1 bullish). "
            f"News sentiment {sentiment.news_sentiment:+.2f}, social {sentiment.social_sentiment:+.2f}. "
            f"Analyst consensus: {ratings.consensus} across {ratings.num_analysts} analysts "
            f"(Strong Buy {ratings.strong_buy}, Buy {ratings.buy}, Hold {ratings.hold}, "
            f"Sell {ratings.sell}, Strong Sell {ratings.strong_sell}), "
            f"target ${ratings.target_price:.2f}.\n\nRecent headlines:\n{headline_lines}\n\n"
            f"Summarize the dominant narrative, any narrative shifts, and top 3 themes."
        )
        resp = await client.chat.completions.create(
            model=settings.OPENAI_FAST_MODEL,
            messages=[
                {"role": "system", "content": SENTIMENT_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        content = resp.choices[0].message.content or ""
        tokens = resp.usage.total_tokens if resp.usage else 0

        section = ReportSection(
            id=str(uuid.uuid4()),
            title="Sentiment Analysis",
            type="sentiment",
            content=content,
            data={"sentiment": sentiment.model_dump(), "analyst_ratings": ratings.model_dump()},
            agent="sentiment_agent",
            tokens_used=tokens,
            generation_time_ms=int((time.time() - start) * 1000),
        )

        agent_span.set_attribute("output.value", f"sentiment={sentiment.overall_score:+.2f}")
        agent_span.set_attribute("llm.token_count.total", tokens)

    return {
        "sentiment_section": section,
        "sentiment_data": sentiment,
        "analyst_ratings": ratings,
        "tools_called": ["get_sentiment_score", "get_analyst_ratings"],
    }
