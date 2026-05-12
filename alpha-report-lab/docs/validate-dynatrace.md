# Dynatrace Validation Checklist — Alpha Report Lab

After running `.\tasks.ps1 test-flow`, follow this checklist.

## 1. Service Detection
- [ ] Observe > Services: "alpha-engine" and "alpha-report-frontend" both appear.

## 2. Distributed Traces
- [ ] Observe > Distributed traces, filter by service `alpha-engine`.
- [ ] Open a trace from a report generation request.
- [ ] Confirm the trace spans BOTH services (Next.js → Python).
- [ ] Confirm the span tree is 3-4 levels deep with 20-30 spans.

## 3. AI Observability Explorer
- [ ] Observe > AI Observability: "alpha-engine" appears as an AI service.
- [ ] Model breakdown shows gpt-4o / gpt-4o-mini.
- [ ] Token usage charts populate.

## 4. Span Attributes — OpenInference
- [ ] Open a trace > select an `openai.chat` span.
- [ ] `openinference.span.kind` == "LLM".
- [ ] `llm.input_messages.0.message.content` has prompt text.
- [ ] `llm.output_messages.0.message.content` has completion text.
- [ ] `llm.model_name`, `llm.token_count.prompt`, `llm.token_count.completion` set.
- [ ] `llm.invocation_parameters` contains temperature, model, etc.
- [ ] `session.id` and `user.id` present.
- [ ] `tag.tags` contains `alpha-report` and `ticker:*`.

## 5. Span Tree Structure
- [ ] `alpha_orchestrator` (AGENT) is the root AI span.
- [ ] Under it: research_agent, analysis_agent, sentiment_agent, risk_agent, writer_agent (all CHAIN).
- [ ] Under each agent: `tool:*` spans (TOOL) and `openai.chat` spans (LLM).

## 6. OpenPipeline Rename
- [ ] AI Observability Explorer > trace > Prompt tab shows prompt content.
- [ ] Completion content is displayed.

## 7. DQL Validation

Span kind breakdown:

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter isNotNull(openinference.span.kind)
    | summarize count = count(), by: {openinference.span.kind}

Token usage by model:

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter openinference.span.kind == "LLM"
    | summarize total_input = sum(llm.token_count.prompt),
                total_output = sum(llm.token_count.completion),
                calls = count(),
                by: {llm.model_name}

Session tracking:

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter isNotNull(session.id)
    | summarize span_count = count(), by: {session.id}

## 8. Troubleshooting Quick Reference

**No spans at all from Python**:
- `Get-Service -Name "Dynatrace OneAgent"`
- Check Observe > Infrastructure > Hosts > Processes
- `C:\ProgramData\dynatrace\oneagent\log\`

**OpenInference spans missing**:
- Verify "OpenTelemetry (Python) [Opt-In]" enabled.
- Verify `DT_ENV_URL` + `DT_API_TOKEN` in `alpha-engine/.env`.
- Verify API token has `openTelemetryTrace.ingest` scope.
- Verify `instrumentation.py` is imported BEFORE the OpenAI client.

**Duplicate LLM spans**:
- Disable "Python OpenAI" in OneAgent features.

**Prompt section empty after OpenInference**:
- `OPENINFERENCE_HIDE_INPUTS` is not `true`.
- OpenPipeline rename rules are active.
- Run DQL to confirm `llm.input_messages.0.message.content` exists.

**Traces not connecting Next.js to Python**:
- "W3C Trace Context" is enabled in OneAgent features.
- Next.js API routes forward `traceparent`/`tracestate` headers (`@/app/api/_shared.ts`).
