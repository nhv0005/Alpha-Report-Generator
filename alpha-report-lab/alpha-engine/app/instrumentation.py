"""OpenInference + OpenTelemetry instrumentation setup.

Must be imported and invoked BEFORE any OpenAI client is created so that the
OpenAI library is monkey-patched with OpenInference tracing.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import (
    Counter,
    Histogram,
    MeterProvider,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality,
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor

from app.config import settings

logger = logging.getLogger(__name__)

_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None
# Module-level tracer; re-bound in setup_instrumentation()
tracer = trace.get_tracer("alpha-engine", "1.0.0")
# Module-level meter + histograms; re-bound in setup_instrumentation()
meter = metrics.get_meter("alpha-engine", "1.0.0")
gen_ai_token_usage = None  # type: ignore[assignment]
gen_ai_operation_duration = None  # type: ignore[assignment]


def setup_instrumentation() -> TracerProvider:
    """Initialize OTel TracerProvider and install the OpenInference OpenAI instrumentor.

    Returns the configured TracerProvider.
    """
    global _provider, _meter_provider, tracer, meter, gen_ai_token_usage, gen_ai_operation_duration
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
        traces_endpoint = settings.DT_ENV_URL.rstrip("/") + "/api/v2/otlp/v1/traces"
        exporter = OTLPSpanExporter(
            endpoint=traces_endpoint,
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
        logger.info(f"OTLP traces exporter configured -> {traces_endpoint}")
    else:
        logger.warning("DT_ENV_URL or DT_API_TOKEN not set; spans will not be exported to Dynatrace")

    # Debug: Console output
    if settings.DEBUG_TRACES:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info("Debug traces enabled: outputting to terminal")

    trace.set_tracer_provider(provider)
    _provider = provider
    tracer = trace.get_tracer("alpha-engine", "1.0.0")

    # --- Metrics (OTel GenAI semantic conventions) ---
    logger.info(
        f"Instrumentation env: DT_ENV_URL={'set' if settings.DT_ENV_URL else 'EMPTY'}, "
        f"DT_API_TOKEN={'set (len=' + str(len(settings.DT_API_TOKEN)) + ')' if settings.DT_API_TOKEN else 'EMPTY'}, "
        f"DEBUG_TRACES={settings.DEBUG_TRACES}"
    )
    metric_readers = []
    metric_exporter = None
    if settings.DT_ENV_URL and settings.DT_API_TOKEN:
        metrics_endpoint = settings.DT_ENV_URL.rstrip("/") + "/api/v2/otlp/v1/metrics"
        # Dynatrace requires DELTA aggregation temporality for counters and
        # histograms; CUMULATIVE payloads are accepted (HTTP 200) then silently
        # dropped. See https://docs.dynatrace.com/docs/shortlink/otel-getstarted-otlpexport#metrics
        delta_temporality = {
            Counter: AggregationTemporality.DELTA,
            UpDownCounter: AggregationTemporality.CUMULATIVE,
            Histogram: AggregationTemporality.DELTA,
            ObservableCounter: AggregationTemporality.DELTA,
            ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
            ObservableGauge: AggregationTemporality.CUMULATIVE,
        }
        metric_exporter = OTLPMetricExporter(
            endpoint=metrics_endpoint,
            headers={"Authorization": f"Api-Token {settings.DT_API_TOKEN}"},
            preferred_temporality=delta_temporality,
        )
        metric_readers.append(
            PeriodicExportingMetricReader(metric_exporter, export_interval_millis=10_000)
        )
        logger.info(
            f"OTLP metrics exporter configured -> {metrics_endpoint} "
            f"(temporality: DELTA for Counter/Histogram, CUMULATIVE for UpDownCounter/Gauge)"
        )
    else:
        logger.warning(
            "OTLP metrics exporter NOT configured: DT_ENV_URL or DT_API_TOKEN is empty"
        )
    if settings.DEBUG_TRACES:
        metric_readers.append(
            PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=15_000)
        )
        logger.info("Console metric exporter enabled (DEBUG_TRACES=true)")

    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)
    _meter_provider = meter_provider
    meter = metrics.get_meter("alpha-engine", "1.0.0")

    # GenAI semantic-convention histograms
    # https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/
    gen_ai_token_usage = meter.create_histogram(
        name="gen_ai.client.token.usage",
        unit="{token}",
        description="Measures number of input and output tokens used.",
    )
    gen_ai_operation_duration = meter.create_histogram(
        name="gen_ai.client.operation.duration",
        unit="s",
        description="GenAI operation duration.",
    )

    # --- Smoke test: record one synthetic data point and force-flush so we
    #     can confirm whether the OTLP HTTP exporter is reaching Dynatrace. ---
    if metric_exporter is not None:
        try:
            gen_ai_operation_duration.record(0.001, attributes={
                "gen_ai.operation.name": "chat",
                "gen_ai.provider.name": "openai",
                "gen_ai.request.model": "startup-smoketest",
                "gen_ai.agent.name": "instrumentation_smoketest",
            })
            gen_ai_token_usage.record(1, attributes={
                "gen_ai.operation.name": "chat",
                "gen_ai.provider.name": "openai",
                "gen_ai.request.model": "startup-smoketest",
                "gen_ai.agent.name": "instrumentation_smoketest",
                "gen_ai.token.type": "input",
            })
            flushed = meter_provider.force_flush(timeout_millis=10_000)
            logger.info(
                f"Metric smoke-test force_flush returned {flushed} "
                f"(True = export attempted; check above for any exporter WARNING)"
            )
        except Exception as e:
            logger.exception(f"Metric smoke test failed: {e}")

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
    """Flush and shut down the tracer + meter providers."""
    global _provider, _meter_provider
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
    if _meter_provider is not None:
        try:
            _meter_provider.force_flush()
        except Exception:
            pass
        try:
            _meter_provider.shutdown()
        except Exception:
            pass
        _meter_provider = None
