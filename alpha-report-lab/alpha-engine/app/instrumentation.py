"""OpenInference + OpenTelemetry instrumentation setup.

Must be imported and invoked BEFORE any OpenAI client is created so that the
OpenAI library is monkey-patched with OpenInference tracing.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings

logger = logging.getLogger(__name__)

_provider: Optional[TracerProvider] = None
# Module-level tracer; re-bound in setup_instrumentation()
tracer = trace.get_tracer("alpha-engine", "1.0.0")


def setup_instrumentation() -> TracerProvider:
    """Initialize OTel TracerProvider and install the OpenInference OpenAI instrumentor.

    Returns the configured TracerProvider.
    """
    global _provider, tracer
    if _provider is not None:
        return _provider

    resource = Resource.create({
        "service.name": settings.SERVICE_NAME,
        "service.version": settings.SERVICE_VERSION,
        "deployment.environment": settings.DEPLOYMENT_ENV,
    })

    provider = TracerProvider(resource=resource)

    # Configure OTLP HTTP exporter -> Dynatrace
    if settings.DT_ENV_URL and settings.DT_API_TOKEN:
        endpoint = settings.DT_ENV_URL.rstrip("/") + "/api/v2/otlp/v1/traces"
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers={"Authorization": f"Api-Token {settings.DT_API_TOKEN}"},
        )
        provider.add_span_processor(
            BatchSpanProcessor(
                exporter,
                max_queue_size=2048,
                max_export_batch_size=512,
                schedule_delay_millis=5000,
            )
        )
        logger.info(f"OTLP exporter configured -> {endpoint}")
    else:
        logger.warning("DT_ENV_URL or DT_API_TOKEN not set; spans will not be exported to Dynatrace")

    trace.set_tracer_provider(provider)
    _provider = provider
    tracer = trace.get_tracer("alpha-engine", "1.0.0")

    # Install OpenInference OpenAI instrumentor
    try:
        from openinference.instrumentation import TraceConfig
        from openinference.instrumentation.openai import OpenAIInstrumentor

        config = TraceConfig(
            hide_inputs=settings.HIDE_INPUTS,
            hide_outputs=settings.HIDE_OUTPUTS,
            hide_input_images=settings.HIDE_INPUT_IMAGES,
            hide_embedding_vectors=True,  # always hide — large and not useful in DT
            hide_llm_invocation_parameters=settings.HIDE_LLM_INVOCATION_PARAMETERS,
        )
        OpenAIInstrumentor().instrument(tracer_provider=provider, config=config)
        logger.info("OpenInference OpenAIInstrumentor installed")
    except Exception as e:  # pragma: no cover
        logger.exception(f"Failed to install OpenInference instrumentor: {e}")

    return provider


def shutdown() -> None:
    """Flush and shut down the tracer provider."""
    global _provider
    if _provider is not None:
        try:
            _provider.force_flush()
        except Exception:
            pass
        try:
            _provider.shutdown()
        except Exception:
            pass
        _provider = None
