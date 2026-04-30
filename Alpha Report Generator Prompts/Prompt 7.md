# Prompt 7: Validation Suite — Dynatrace Query Language (DQL) Queries, Troubleshooting & Cheat Sheet

Create the final validation and troubleshooting artifacts.

## Files to Create

### 1. docs/dql-validation-queries.md
Organized by validation goal:

#### Confirm Spans Are Flowing
```DQL
-- All alpha-engine spans in last 30 minutes
fetch spans
| filter dt.service.name == "alpha-engine"
| filter start_time > now() - 30m
| summarize count = count(), by: {span.name, span.kind}
| sort count desc
```

```DQL
-- Span kind breakdown (AGENT, CHAIN, TOOL, LLM, EMBEDDING)
fetch spans
| filter dt.service.name == "alpha-engine"
| filter isNotNull(openinference.span.kind)
| summarize count = count(), by: {openinference.span.kind}
```
```DQL
-- Verify prompt content is captured on LLM spans
fetch spans
| filter dt.service.name == "alpha-engine"
| filter openinference.span.kind == "LLM"
| fields span.name, llm.model_name,
         llm.input_messages.0.message.role,
         llm.input_messages.0.message.content,
         llm.output_messages.0.message.content,
         llm.token_count.prompt, llm.token_count.completion
| limit 10
```

```DQL
-- Token consumption breakdown by agent (parent span name)
fetch spans
| filter dt.service.name == "alpha-engine"
| filter openinference.span.kind == "LLM"
| fieldsAdd agent = span.parent_name
| summarize total_input = sum(llm.token_count.prompt),
            total_output = sum(llm.token_count.completion),
            calls = count(),
            by: {llm.model_name, agent}
| sort total_input desc
```

```DQL
-- Distributed traces spanning both services
fetch spans
| filter trace.id IN (
    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter span.name == "alpha_orchestrator"
    | filter start_time > now() - 1h
    | fields trace.id
  )
| summarize services = collectDistinct(dt.service.name),
            span_count = count(),
            by: {trace.id}
| filter arraySize(services) > 1
```

```DQL
-- Tool call breakdown: which tools, how often, how fast
fetch spans
| filter dt.service.name == "alpha-engine"
| filter openinference.span.kind == "TOOL"
| fields tool.name, duration, input.value
| summarize avg_duration = avg(duration),
            calls = count(),
            by: {tool.name}
| sort calls desc
```

```DQL
-- Reports grouped by session
fetch spans
| filter dt.service.name == "alpha-engine"
| filter isNotNull(session.id)
| summarize span_count = count(),
            agents = collectDistinct(openinference.span.kind),
            by: {session.id, tag.tags}
```
```DQL
-- Confirm gen_ai.prompt.* populated after OpenPipeline rename
fetch spans
| filter dt.service.name == "alpha-engine"
| filter isNotNull(gen_ai.prompt.0.content)
| fields span.name, gen_ai.prompt.0.role, gen_ai.prompt.0.content,
         gen_ai.completion.0.content, gen_ai.usage.input_tokens
| limit 5
```
```DQL
-- Average report generation time and token usage
fetch spans
| filter dt.service.name == "alpha-engine"
| filter span.name == "alpha_orchestrator"
| fields duration, metadata.ticker, metadata.report_id,
         tag.tags, session.id
| summarize avg_duration = avg(duration),
            p95_duration = percentile(duration, 95),
            reports = count()
```

```DQL
-- Average report generation time and token usage
fetch spans
| filter dt.service.name == "alpha-engine"
| filter span.name == "alpha_orchestrator"
| fields duration, metadata.ticker, metadata.report_id,
         tag.tags, session.id
| summarize avg_duration = avg(duration),
            p95_duration = percentile(duration, 95),
            reports = count()
```

### 2. docs/troubleshooting.md
Common issues and fixes:

No spans from Python service
No OpenInference spans (only OneAgent)
Duplicate LLM spans
Prompt section empty in Explorer
Token counts missing
Next.js → Python traces not connected
OpenAI API errors
Report generation hangs/errors
Background task spans not captured
Langfuse conflicts (if applicable)

For each: symptoms, root cause, diagnostic steps, fix.

### 3. docs/cheat-sheet.md
One-page quick reference:
Start the Lab
# Terminal 1: Alpha Engine
cd alpha-engine && source .env && uvicorn app.main:app --port 8000 --reload

# Terminal 2: Next.js Frontend
cd alpha-frontend && npm run dev

# Browser: http://localhost:3000

Quick Test Commands:
# Generate NVDA report
curl -s -X POST http://localhost:3000/api/alpha/generate \
  -H "Content-Type: application/json" \
  -d '{"ticker":"NVDA","investment_horizon":"medium_term","risk_tolerance":"moderate"}' | jq

# Check status (replace REPORT_ID)
curl -s http://localhost:3000/api/alpha/status/REPORT_ID | jq

# Get full report
curl -s http://localhost:3000/api/alpha/reports/REPORT_ID | jq

# List all reports
curl -s http://localhost:3000/api/alpha/reports | jq