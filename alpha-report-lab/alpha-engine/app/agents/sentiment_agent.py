"""Sentiment Agent — news flow + analyst consensus + narrative."""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict

from app.agents.llm_client import get_openai_client, serialize
from app.agents.llm_metrics import (
    measure_llm_call,
    set_agent_input_messages,
    set_agent_output_messages,
    set_agent_span_attributes,
)
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
AGENT_DESCRIPTION = (
    "Sentiment analyst. Combines news sentiment, social sentiment, and analyst "
    "consensus to produce the Sentiment Analysis section."
)
AGENT_TOOLS = ["get_sentiment_score", "get_analyst_ratings"]


async def _wrap_tool(tool_name: str, fn, *args, **kwargs):
    with tracer.start_as_current_span(f"TOOL {tool_name}") as span:
        span.set_attribute("gen_ai.operation.name", "execute_tool")
        span.set_attribute("gen_ai.tool.name", tool_name)
        span.set_attribute("gen_ai.provider.name", "openai")
        result = fn(*args, **kwargs)
        return result


async def analyze_sentiment(context: ReportContext) -> Dict[str, Any]:
    logger.info(f"[sentiment_agent] Analyzing sentiment for {context.ticker}")
    start = time.time()

    with tracer.start_as_current_span("invoke_agent sentiment_agent") as agent_span:
        set_agent_span_attributes(
            agent_span,
            agent_name="sentiment_agent",
            description=AGENT_DESCRIPTION,
            request_model=settings.OPENAI_FAST_MODEL,
            tool_definitions=AGENT_TOOLS,
            system_instructions=SENTIMENT_PROMPT,
        )
        set_agent_input_messages(agent_span, [
            {"role": "user", "content": f"Sentiment for {context.ticker}"},
        ])

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
        with measure_llm_call("sentiment_agent", settings.OPENAI_FAST_MODEL) as record:
            resp = await client.chat.completions.create(
                model=settings.OPENAI_FAST_MODEL,
                messages=[
                    {"role": "system", "content": SENTIMENT_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )
            record(resp)
        content = resp.choices[0].message.content or ""
        input_tokens = resp.usage.prompt_tokens if resp.usage else 0
        output_tokens = resp.usage.completion_tokens if resp.usage else 0
        tokens = input_tokens + output_tokens

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

        agent_span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
        agent_span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
        set_agent_output_messages(agent_span, [
            {"role": "assistant", "content": content},
        ])

    return {
        "sentiment_section": section,
        "sentiment_data": sentiment,
        "analyst_ratings": ratings,
        "tools_called": ["get_sentiment_score", "get_analyst_ratings"],
    }
