"""Per-call OTel GenAI metric recording for agent LLM invocations.

Records two histograms following the OpenTelemetry GenAI semantic conventions
(https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/):

- gen_ai.client.token.usage      (unit: {token})
- gen_ai.client.operation.duration (unit: s)

A custom `agent.name` attribute is added to each measurement so per-agent
breakdowns are possible in DQL.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Optional

from app import instrumentation

logger = logging.getLogger(__name__)


def _base_attrs(agent_name: str, request_model: str, response: Optional[Any] = None,
                operation: str = "chat", system: str = "openai") -> dict:
    attrs = {
        "gen_ai.operation.name": operation,
        "gen_ai.system": system,
        "gen_ai.request.model": request_model,
        "agent.name": agent_name,
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
    system: str = "openai",
    error: Optional[str] = None,
) -> None:
    """Record both GenAI histograms for a single chat-completion call.

    Safe to call before instrumentation has fully initialized (no-op if so).
    """
    duration_hist = instrumentation.gen_ai_operation_duration
    token_hist = instrumentation.gen_ai_token_usage
    if duration_hist is None or token_hist is None:
        return  # instrumentation not initialized; skip silently

    base = _base_attrs(agent_name, request_model, response, operation, system)

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
                      operation: str = "chat", system: str = "openai"):
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
            system=system,
            error=state["error"],
        )
