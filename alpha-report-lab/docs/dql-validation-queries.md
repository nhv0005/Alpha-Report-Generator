# DQL Validation Queries — Alpha Report Lab

Run these in **Observe > Notebooks** to validate instrumentation.

## Confirm Spans Are Flowing

```dql
fetch spans
| filter dt.service.name == "alpha-engine"
| filter start_time > now() - 30m
| summarize count = count(), by: {span.name, span.kind}
| sort count desc
```

## Span Kind Breakdown (AGENT, CHAIN, TOOL, LLM, EMBEDDING)

```dql
fetch spans
| filter dt.service.name == "alpha-engine"
| filter isNotNull(openinference.span.kind)
| summarize count = count(), by: {openinference.span.kind}
```

## Verify Prompt Content on LLM Spans

```dql
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

## Token Consumption by Agent

```dql
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

## Distributed Traces Spanning Both Services

```dql
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

## Tool Call Breakdown

```dql
fetch spans
| filter dt.service.name == "alpha-engine"
| filter openinference.span.kind == "TOOL"
| fields tool.name, duration, input.value
| summarize avg_duration = avg(duration),
            calls = count(),
            by: {tool.name}
| sort calls desc
```

## Reports Grouped by Session

```dql
fetch spans
| filter dt.service.name == "alpha-engine"
| filter isNotNull(session.id)
| summarize span_count = count(),
            agents = collectDistinct(openinference.span.kind),
            by: {session.id, tag.tags}
```

## Confirm gen_ai.prompt.* Populated After OpenPipeline Rename

```dql
fetch spans
| filter dt.service.name == "alpha-engine"
| filter isNotNull(gen_ai.prompt.0.content)
| fields span.name, gen_ai.prompt.0.role, gen_ai.prompt.0.content,
         gen_ai.completion.0.content, gen_ai.usage.input_tokens
| limit 5
```

## Average Report Generation Time

```dql
fetch spans
| filter dt.service.name == "alpha-engine"
| filter span.name == "alpha_orchestrator"
| fields duration, metadata.ticker, metadata.report_id,
         tag.tags, session.id
| summarize avg_duration = avg(duration),
            p95_duration = percentile(duration, 95),
            reports = count()
```

## End-to-End Trace Sampler

```dql
fetch spans
| filter dt.service.name == "alpha-engine"
| filter span.name == "alpha_orchestrator"
| filter start_time > now() - 1h
| fields trace.id, duration, session.id, tag.tags
| sort start_time desc
| limit 10
```
