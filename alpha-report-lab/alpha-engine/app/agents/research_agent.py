"""Research Agent — gathers company data and composes the Company Overview."""
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
from app.tools.market_data import get_company_profile, get_price_data
from app.tools.financial_metrics import get_financial_metrics, get_quarterly_earnings
from app.tools.news_search import search_news
from app.tools.peer_comparison import get_peers

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = (
    "You are a senior equity research analyst at a top-tier investment bank. "
    "Your role is to gather and synthesize company data, market positioning, "
    "and recent developments. Be thorough, factual, and cite specific numbers "
    "where relevant. Format output as clean Markdown with headers and bullet points."
)
AGENT_DESCRIPTION = (
    "Senior equity research analyst. Gathers company profile, price data, "
    "financial metrics, earnings, news, and peers; produces the Company "
    "Overview section."
)
AGENT_TOOLS = [
    "get_company_profile", "get_price_data", "get_financial_metrics",
    "get_quarterly_earnings", "search_news", "get_peers",
]


async def _wrap_tool(tool_name: str, fn, *args, **kwargs):
    """Run a mock tool inside a span using OTel GenAI semantic conventions."""
    with tracer.start_as_current_span(f"TOOL {tool_name}") as span:
        span.set_attribute("gen_ai.operation.name", "execute_tool")
        span.set_attribute("gen_ai.tool.name", tool_name)
        span.set_attribute("gen_ai.provider.name", "openai")
        result = fn(*args, **kwargs)
        return result


async def research(context: ReportContext) -> Dict[str, Any]:
    logger.info(f"[research_agent] Starting research for {context.ticker}")
    start = time.time()

    with tracer.start_as_current_span("AGENT research_agent") as agent_span:
        set_agent_span_attributes(
            agent_span,
            agent_name="research_agent",
            description=AGENT_DESCRIPTION,
            request_model=settings.OPENAI_MODEL,
            tool_definitions=AGENT_TOOLS,
            system_instructions=RESEARCH_SYSTEM_PROMPT,
        )
        set_agent_input_messages(agent_span, [
            {"role": "user", "content": f"Research {context.ticker}"},
        ])

        profile = await _wrap_tool("get_company_profile", get_company_profile, context.ticker)
        price = await _wrap_tool("get_price_data", get_price_data, context.ticker)
        metrics = await _wrap_tool("get_financial_metrics", get_financial_metrics, context.ticker)
        earnings = await _wrap_tool("get_quarterly_earnings", get_quarterly_earnings, context.ticker, 4)
        news = await _wrap_tool("search_news", search_news, context.ticker, 30)
        peers = await _wrap_tool("get_peers", get_peers, context.ticker)

        # LLM call — OpenInference auto-instruments this with an openai.chat span
        client = get_openai_client()
        user_prompt = (
            f"Write a concise 'Company Overview' section for {context.ticker} ({profile.name}). "
            f"Include: business model, sector positioning ({profile.sector} / {profile.industry}), "
            f"leadership (CEO: {profile.ceo}), employees ({profile.employees:,}), headquarters "
            f"({profile.hq}). Current price: ${price.current_price:.2f}, market cap "
            f"${price.market_cap/1e9:.1f}B. Revenue TTM: ${metrics.revenue_ttm/1e9:.1f}B, "
            f"YoY growth {metrics.revenue_growth_yoy*100:.1f}%. "
            f"Mention 2-3 notable recent headlines. Use crisp Markdown (300-400 words)."
        )
        with measure_llm_call("research_agent", settings.OPENAI_MODEL) as record:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            record(response)
        content = response.choices[0].message.content or ""
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        tokens = (input_tokens + output_tokens) if usage else 0

        section = ReportSection(
            id=str(uuid.uuid4()),
            title="Company Overview",
            type="company_overview",
            content=content,
            data={
                "price": price.model_dump(),
                "metrics": metrics.model_dump(),
                "earnings": [e.model_dump() for e in earnings],
                "peers": peers,
            },
            agent="research_agent",
            tokens_used=tokens,
            generation_time_ms=int((time.time() - start) * 1000),
        )

        agent_span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
        agent_span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
        set_agent_output_messages(agent_span, [
            {"role": "assistant", "content": content},
        ])

    return {
        "company_profile": profile,
        "price_data": price,
        "financial_metrics": metrics,
        "earnings": earnings,
        "news": news,
        "peers": peers,
        "section": section,
        "tools_called": [
            "get_company_profile", "get_price_data", "get_financial_metrics",
            "get_quarterly_earnings", "search_news", "get_peers",
        ],
    }
