"""Risk Agent — identify, categorize, and quantify risks."""
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
from app.tools.financial_metrics import get_financial_metrics

logger = logging.getLogger(__name__)

RISK_PROMPT = (
    "You are a risk management specialist at a hedge fund. Your job is to identify, "
    "categorize, and quantify risks for investment positions. Consider market risk, "
    "sector risk, company-specific risk, regulatory risk, execution risk, and macro "
    "risk. Be contrarian — always consider the bear case. Format as Markdown with a "
    "clear ranked risk matrix and a bear-case price target."
)
AGENT_DESCRIPTION = (
    "Risk specialist. Identifies and quantifies top risks; assigns an overall "
    "risk rating and a bear-case price target."
)
AGENT_TOOLS = ["get_financial_metrics"]


async def _wrap_tool(tool_name: str, fn, *args, **kwargs):
    with tracer.start_as_current_span(f"execute_tool {tool_name}") as span:
        span.set_attribute("gen_ai.operation.name", "execute_tool")
        span.set_attribute("gen_ai.tool.name", tool_name)
        span.set_attribute("gen_ai.provider.name", "openai")
        result = fn(*args, **kwargs)
        return result


def _risk_rating(metrics, sentiment_score: float, risk_tolerance: str) -> str:
    score = 0
    if metrics.debt_to_equity > 1.5:
        score += 2
    if metrics.current_ratio < 1.0:
        score += 1
    if metrics.revenue_growth_yoy < 0:
        score += 2
    if metrics.beta > 1.5:
        score += 1
    if sentiment_score < -0.2:
        score += 1
    if risk_tolerance == "conservative":
        score += 1
    if score >= 5:
        return "VERY_HIGH"
    if score >= 3:
        return "HIGH"
    if score >= 1:
        return "MEDIUM"
    return "LOW"


async def assess_risk(context: ReportContext) -> Dict[str, Any]:
    logger.info(f"[risk_agent] Assessing risk for {context.ticker}")
    start = time.time()
    data = context.gathered_data

    with tracer.start_as_current_span("invoke_agent risk_agent") as agent_span:
        set_agent_span_attributes(
            agent_span,
            agent_name="risk_agent",
            description=AGENT_DESCRIPTION,
            request_model=settings.OPENAI_MODEL,
            tool_definitions=AGENT_TOOLS,
            system_instructions=RISK_PROMPT,
        )
        set_agent_input_messages(agent_span, [
            {"role": "user", "content": f"Assess risk for {context.ticker} (tolerance {context.risk_tolerance})"},
        ])

        metrics = await _wrap_tool("get_financial_metrics", get_financial_metrics, context.ticker)
        price = data.get("price_data")
        sentiment = data.get("sentiment_data")
        sentiment_score = getattr(sentiment, "overall_score", 0.0) if sentiment else 0.0

        client = get_openai_client()
        prompt = (
            f"Write a Risk Assessment for {context.ticker}. "
            f"Debt/Equity {metrics.debt_to_equity}, Current Ratio {metrics.current_ratio}, "
            f"Beta {metrics.beta}, Revenue growth {metrics.revenue_growth_yoy*100:.1f}%, "
            f"Operating margin {metrics.operating_margin*100:.1f}%. "
            f"Current sentiment score {sentiment_score:+.2f}. "
            f"Risk tolerance: {context.risk_tolerance}. Investment horizon: {context.investment_horizon}. "
            f"Produce a ranked top-5 risks table (probability x impact), a bear-case price target "
            f"(below the current ${price.current_price:.2f} price), and an overall risk rating "
            f"of LOW / MEDIUM / HIGH / VERY_HIGH."
        )
        with measure_llm_call("risk_agent", settings.OPENAI_MODEL) as record:
            resp = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": RISK_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            record(resp)
        content = resp.choices[0].message.content or ""
        input_tokens = resp.usage.prompt_tokens if resp.usage else 0
        output_tokens = resp.usage.completion_tokens if resp.usage else 0
        tokens = input_tokens + output_tokens

        rating = _risk_rating(metrics, sentiment_score, context.risk_tolerance)
        bear_multiplier = {"LOW": 0.92, "MEDIUM": 0.85, "HIGH": 0.75, "VERY_HIGH": 0.62}[rating]
        bear_case_target = round(price.current_price * bear_multiplier, 2)

        section = ReportSection(
            id=str(uuid.uuid4()),
            title="Risk Assessment",
            type="risk_assessment",
            content=content,
            data={"risk_rating": rating, "bear_case_target": bear_case_target},
            agent="risk_agent",
            tokens_used=tokens,
            generation_time_ms=int((time.time() - start) * 1000),
        )

        agent_span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
        agent_span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
        set_agent_output_messages(agent_span, [
            {"role": "assistant", "content": content},
        ])

    return {
        "risk_section": section,
        "risk_rating": rating,
        "bear_case_target": bear_case_target,
        "tools_called": ["get_financial_metrics"],
    }
