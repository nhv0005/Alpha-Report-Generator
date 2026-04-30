# Troubleshooting — Alpha Report Lab

## No spans from Python service
**Symptoms**: Service `alpha-engine` not visible in Dynatrace.
**Root cause**: OTLP exporter misconfigured, or OneAgent not injecting the Python process.
**Diagnostic steps**:
- `Get-Service -Name "Dynatrace OneAgent"`
- Check `DT_ENV_URL` and `DT_API_TOKEN` in `alpha-engine/.env`.
- Tail uvicorn logs for `OTLP exporter configured -> ...`.
- Look for `spans will not be exported to Dynatrace` warnings.
**Fix**: Populate `DT_ENV_URL` with the base environment URL (no trailing path) and `DT_API_TOKEN` with a token that has `openTelemetryTrace.ingest`.

## No OpenInference spans (only OneAgent)
**Symptoms**: You see HTTP spans but no `openai.chat`, `research_agent`, `tool:*` spans.
**Root cause**: `openinference-instrumentation-openai` not installed, or `setup_instrumentation()` is called AFTER OpenAI client creation.
**Fix**:
- Confirm `pip show openinference-instrumentation-openai`.
- Ensure the first import in `app/main.py` is `from app.instrumentation import setup_instrumentation; setup_instrumentation()`.

## Duplicate LLM spans
**Symptoms**: Every OpenAI call shows two spans — one from OneAgent, one from OpenInference.
**Fix**: Disable the "Python OpenAI" sensor in OneAgent features (see `docs/oneagent-configuration.md`).

## Prompt section empty in AI Observability Explorer
**Symptoms**: Trace has LLM spans but Prompt tab is blank.
**Root cause**: Either `OPENINFERENCE_HIDE_INPUTS=true`, or OpenPipeline rename rules are missing.
**Fix**:
- Set `OPENINFERENCE_HIDE_INPUTS=false` in `alpha-engine/.env`.
- Configure OpenPipeline per `docs/openpipeline-configuration.md`.
- Confirm with DQL: `fetch spans | filter isNotNull(gen_ai.prompt.0.content)`.

## Token counts missing
**Symptoms**: `llm.token_count.prompt` / `.completion` null.
**Root cause**: Older OpenInference / OpenAI SDK versions or streaming responses.
**Fix**: Pin versions per `requirements.txt`. The lab does not stream, so token counts always come back on the usage field.

## Next.js → Python traces not connected
**Symptoms**: Frontend and Engine spans appear as separate traces.
**Fix**:
- Enable "W3C Trace Context" in OneAgent features.
- Next.js API routes forward `traceparent` / `tracestate` via `src/app/api/_shared.ts:forwardedHeaders()` (already implemented).

## OpenAI API errors
**Symptoms**: Reports hang in `researching` then flip to `error`.
**Diagnostic**: Check engine logs — `openai.RateLimitError`, `openai.AuthenticationError`.
**Fix**:
- Verify `OPENAI_API_KEY`.
- If using a custom endpoint, verify `OPENAI_BASE_URL` is correct.

## Report generation hangs / errors
**Symptoms**: Status stays on `pending` indefinitely.
**Diagnostic**:
- Engine logs will show which agent stalled.
- If an agent's LLM call throws, the orchestrator catches it and sets status to `error`.
**Fix**: Review the specific agent's last span in Dynatrace — `events` will include the exception.

## Background task spans not captured
**Symptoms**: Only the `/api/alpha/generate` span is visible; background orchestrator missing.
**Root cause**: `asyncio.create_task` loses the span context.
**Fix**: The orchestrator wraps its own `using_attributes(...)` + explicit `tracer.start_as_current_span("alpha_orchestrator")` — this creates a fresh root span regardless of parent context.

## Langfuse conflicts
**Symptoms**: OpenInference spans are reshaped or stripped.
**Fix**: If Langfuse Python SDK was imported, uninstall it — it replaces the OpenAI instrumentor. Only one LLM instrumentor should be active.
