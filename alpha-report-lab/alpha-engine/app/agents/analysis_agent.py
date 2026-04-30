"""Analysis Agent — fundamental + technical analysis and target price."""
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
from app.tools.financial_metrics import get_technical_indicators
from app.tools.peer_comparison import compare_peers

logger = logging.getLogger(__name__)

FUNDAMENTAL_PROMPT = (
    "You are a quantitative analyst specializing in equity valuation. Provide "
    "data-driven insights with specific numbers. Use standard valuation frameworks: "
    "DCF, comparable analysis, and sum-of-parts where appropriate. Format as Markdown."
)
TECHNICAL_PROMPT = (
    "You are a technical analyst. Interpret price action, momentum, moving "
    "averages, RSI, MACD, and support/resistance levels. Be specific about "
    "signals and their strength. Format as Markdown."
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


async def analyze(context: ReportContext) -> Dict[str, Any]:
    logger.info(f"[analysis_agent] Analyzing {context.ticker}")
    start = time.time()
    data = context.gathered_data

    with tracer.start_as_current_span("analysis_agent") as agent_span:
        agent_span.set_attribute("openinference.span.kind", "CHAIN")
        agent_span.set_attribute("input.value", f"Analyze {context.ticker}")

        peers_list = data.get("peers", [])
        peer_comparison = await _wrap_tool("compare_peers", compare_peers, context.ticker, peers_list)
        technicals = await _wrap_tool("get_technical_indicators", get_technical_indicators, context.ticker)

        metrics = data.get("financial_metrics")
        price = data.get("price_data")
        client = get_openai_client()

        # Fundamental analysis
        fund_prompt = (
            f"Produce a Fundamental Analysis section for {context.ticker}. "
            f"Key metrics: P/E {metrics.pe_ratio}, Forward P/E {metrics.forward_pe}, "
            f"PEG {metrics.peg_ratio}, P/B {metrics.price_to_book}, EV/EBITDA {metrics.ev_to_ebitda}. "
            f"Revenue TTM ${metrics.revenue_ttm/1e9:.1f}B, growth {metrics.revenue_growth_yoy*100:.1f}%. "
            f"Gross margin {metrics.gross_margin*100:.1f}%, Operating margin {metrics.operating_margin*100:.1f}%, "
            f"Net margin {metrics.net_margin*100:.1f}%, ROE {metrics.roe*100:.1f}%. "
            f"Peer comparison attached. Derive a target price using a combination of relative "
            f"valuation vs peers and a simple DCF-style growth assumption. "
            f"Peer data: {serialize(peer_comparison)[:1200]}. "
            f"Investment horizon: {context.investment_horizon}. Be specific about the target price."
        )
        fund_resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": FUNDAMENTAL_PROMPT},
                {"role": "user", "content": fund_prompt},
            ],
            temperature=0.25,
        )
        fund_content = fund_resp.choices[0].message.content or ""
        fund_tokens = fund_resp.usage.total_tokens if fund_resp.usage else 0

        # Technical analysis
        tech_prompt = (
            f"Produce a Technical Analysis section for {context.ticker}. "
            f"Current price ${price.current_price:.2f}. "
            f"52w high ${price.fifty_two_week_high:.2f}, 52w low ${price.fifty_two_week_low:.2f}. "
            f"RSI(14) {technicals.rsi_14}, MACD {technicals.macd} (signal {technicals.macd_signal}), "
            f"SMA50 ${technicals.sma_50:.2f}, SMA200 ${technicals.sma_200:.2f}, "
            f"Support ${technicals.support:.2f}, Resistance ${technicals.resistance:.2f}. "
            f"Explain the setup and short-term trading signals. Mention momentum regime."
        )
        tech_resp = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": TECHNICAL_PROMPT},
                {"role": "user", "content": tech_prompt},
            ],
            temperature=0.25,
        )
        tech_content = tech_resp.choices[0].message.content or ""
        tech_tokens = tech_resp.usage.total_tokens if tech_resp.usage else 0

        # Extract target price: use a heuristic anchored to peer median P/E applied to current earnings
        peer_pes = [p.pe_ratio for p in peer_comparison if p.pe_ratio and p.pe_ratio > 0]
        median_pe = sorted(peer_pes)[len(peer_pes) // 2] if peer_pes else metrics.pe_ratio
        implied_multiple_price = price.current_price * (median_pe / max(metrics.pe_ratio, 1.0))
        target_price = round(max(implied_multiple_price, price.current_price * 0.8), 2)

        fund_section = ReportSection(
            id=str(uuid.uuid4()),
            title="Fundamental Analysis",
            type="fundamental_analysis",
            content=fund_content,
            data={"peer_comparison": [p.model_dump() for p in peer_comparison]},
            agent="analysis_agent",
            tokens_used=fund_tokens,
            generation_time_ms=int((time.time() - start) * 1000 // 2),
        )
        tech_section = ReportSection(
            id=str(uuid.uuid4()),
            title="Technical Analysis",
            type="technical_analysis",
            content=tech_content,
            data={"technicals": technicals.model_dump()},
            agent="analysis_agent",
            tokens_used=tech_tokens,
            generation_time_ms=int((time.time() - start) * 1000 // 2),
        )

        agent_span.set_attribute("output.value", f"target_price={target_price}")
        agent_span.set_attribute("llm.token_count.total", fund_tokens + tech_tokens)

    return {
        "fundamental_section": fund_section,
        "technical_section": tech_section,
        "target_price": target_price,
        "peer_comparison": peer_comparison,
        "technicals": technicals,
        "tools_called": ["compare_peers", "get_technical_indicators"],
    }
