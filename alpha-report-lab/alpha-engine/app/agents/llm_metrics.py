"""Per-call OTel GenAI metric recording + agent-span helpers.

Records two histograms following the OpenTelemetry GenAI semantic conventions
(https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/):

- gen_ai.client.token.usage      (unit: {token})
- gen_ai.client.operation.duration (unit: s)

Also exposes `set_agent_span_attributes(...)` which applies the canonical
Dynatrace agent-span attribute set:
https://docs.dynatrace.com/docs/shortlink/genai-terms-and-concepts#agent-span-attributes
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterable, Optional

from app import instrumentation
from app.config import settings

logger = logging.getLogger(__name__)


def _base_attrs(agent_name: str, request_model: str, response: Optional[Any] = None,
                operation: str = "chat", provider: str = "openai") -> dict:
    attrs = {
        "gen_ai.operation.name": operation,
        "gen_ai.provider.name": provider,
        "gen_ai.request.model": request_model,
        "gen_ai.agent.name": agent_name,
    }
    if response is not None:
        response_model = getattr(response, "model", None)
        if response_model:
            attrs["gen_ai.response.model"] = response_model
    return attrs


def record_llm_metrics(
    agent_name: str,
    request_model: str,
    response: Optional[Any],
    duration_seconds: float,
    operation: str = "chat",
    provider: str = "openai",
    error: Optional[str] = None,
) -> None:
    """Record both GenAI histograms for a single chat-completion call.

    Safe to call before instrumentation has fully initialized (no-op if so).
    """
    duration_hist = instrumentation.gen_ai_operation_duration
    token_hist = instrumentation.gen_ai_token_usage
    if duration_hist is None or token_hist is None:
        return  # instrumentation not initialized; skip silently

    base = _base_attrs(agent_name, request_model, response, operation, provider)

    duration_attrs = dict(base)
    if error:
        duration_attrs["error.type"] = error
    try:
        duration_hist.record(duration_seconds, attributes=duration_attrs)
    except Exception:  # pragma: no cover - never break the agent on metric error
        logger.debug("Failed to record gen_ai.client.operation.duration", exc_info=True)

    if response is not None and getattr(response, "usage", None) is not None:
        usage = response.usage
        prompt_tokens = getattr(usage, "prompt_tokens", None) or 0
        completion_tokens = getattr(usage, "completion_tokens", None) or 0
        try:
            if prompt_tokens:
                token_hist.record(prompt_tokens,
                                  attributes={**base, "gen_ai.token.type": "input"})
            if completion_tokens:
                token_hist.record(completion_tokens,
                                  attributes={**base, "gen_ai.token.type": "output"})
        except Exception:  # pragma: no cover
            logger.debug("Failed to record gen_ai.client.token.usage", exc_info=True)


@contextmanager
def measure_llm_call(agent_name: str, request_model: str,
                      operation: str = "chat", provider: str = "openai"):
    """Context manager that times an LLM call and records both GenAI metrics.

    Usage:
        with measure_llm_call("research_agent", settings.OPENAI_MODEL) as record:
            response = await client.chat.completions.create(...)
            record(response)

    If `record(response)` is never called (e.g. an exception is raised), the
    duration is still recorded with `error.type` set to the exception class name.
    """
    state: dict = {"response": None, "error": None}

    def record(response: Any) -> None:
        state["response"] = response

    start = time.monotonic()
    try:
        yield record
    except Exception as e:
        state["error"] = type(e).__name__
        raise
    finally:
        duration = time.monotonic() - start
        record_llm_metrics(
            agent_name=agent_name,
            request_model=request_model,
            response=state["response"],
            duration_seconds=duration,
            operation=operation,
            provider=provider,
            error=state["error"],
        )


def set_agent_span_attributes(
    span,
    *,
    agent_name: str,
    description: str,
    request_model: str,
    tool_definitions: Optional[Iterable[str]] = None,
    system_instructions: Optional[str] = None,
    output_type: str = "text",
    provider: str = "openai",
    agent_id: Optional[str] = None,
) -> str:
    """Apply the canonical Dynatrace agent-span attribute set to `span`.

    Returns the `gen_ai.agent.id` that was assigned (callers may want to log it).
    Honors `settings.HIDE_INPUTS` for `gen_ai.system_instructions`.
    """
    aid = agent_id or str(uuid.uuid4())
    span.set_attribute("gen_ai.operation.name", "invoke_agent")
    span.set_attribute("gen_ai.provider.name", provider)
    span.set_attribute("gen_ai.agent.id", aid)
    span.set_attribute("gen_ai.agent.name", agent_name)
    span.set_attribute("gen_ai.agent.description", description)
    span.set_attribute("gen_ai.request.model", request_model)
    span.set_attribute("gen_ai.output.type", output_type)
    if tool_definitions is not None:
        span.set_attribute("gen_ai.tool.definitions",
                           json.dumps([{"name": t} for t in tool_definitions]))
    if system_instructions and not settings.HIDE_INPUTS:
        span.set_attribute("gen_ai.system_instructions", system_instructions)
    return aid


def set_agent_input_messages(span, messages: list[dict]) -> None:
    """Set `gen_ai.input.messages` if inputs aren't hidden by config."""
    if settings.HIDE_INPUTS:
        return
    try:
        span.set_attribute("gen_ai.input.messages", json.dumps(messages))
    except Exception:  # pragma: no cover
        logger.debug("Failed to serialize gen_ai.input.messages", exc_info=True)


def set_agent_output_messages(span, messages: list[dict]) -> None:
    """Set `gen_ai.output.messages` if outputs aren't hidden by config."""
    if settings.HIDE_OUTPUTS:
        return
    try:
        span.set_attribute("gen_ai.output.messages", json.dumps(messages))
    except Exception:  # pragma: no cover
        logger.debug("Failed to serialize gen_ai.output.messages", exc_info=True)
