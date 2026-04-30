# Prompt 4: Python Alpha Engine — OpenInference + OTel Instrumentation

Add the full OpenInference instrumentation layer to the Python Alpha Engine
created in Prompts 2-3. This is the critical piece that captures Gen AI metadata
attributes for Dynatrace AI Observability.

## Files to Create / Modify

### 1. CREATE: app/instrumentation.py
Central instrumentation setup module:

#### A. OTel TracerProvider
- Resource: service.name="alpha-engine", service.version="1.0.0",
  deployment.environment="local-lab"
- OTLPSpanExporter → {{DT_ENV_URL}}/api/v2/otlp/v1/traces
- BatchSpanProcessor (production-tuned: queue=2048, batch=512, delay=5000ms)

#### B. OpenInference TraceConfig
- Privacy controls driven by environment variables
- hide_embedding_vectors=True (always — vectors are large and not useful in DT)

#### C. OpenInference OpenAIInstrumentor
```python
from openinference.instrumentation.openai import OpenAIInstrumentor
OpenAIInstrumentor().instrument(tracer_provider=provider, config=config)
```

#### D. Export tracer for custom spans
```python
tracer = trace.get_tracer("alpha-engine", "1.0.0")
```
#### E. Graceful shutdown with flush
```python
def shutdown():
    provider.force_flush()
    provider.shutdown()
```
### 2. MODIFY: app/main.py
Import and call setup_instrumentation() BEFORE all other imports
Critical import order:
```python
from app.instrumentation import setup_instrumentation
setup_instrumentation()
# THEN import FastAPI, routes, agents, etc.
```

### 3. MODIFY: app/agents/orchestrator.py
Wrap the full orchestration flow with OpenInference context:
```python
from openinference.instrumentation import using_attributes
from app.instrumentation import tracer

async def generate_alpha_report(request, report_store, context_mgr):
    with using_attributes(
        session_id=report_context.session_id,
        user_id=request.user_id or "anonymous",
        tags=["alpha-report", f"ticker:{request.ticker}",
              f"horizon:{request.investment_horizon}",
              f"risk:{request.risk_tolerance}"],
        metadata={
            "report_id": report_id,
            "ticker": request.ticker,
            "investment_horizon": request.investment_horizon,
            "risk_tolerance": request.risk_tolerance,
            "environment": "local-lab",
        },
    ):
        # AGENT span for the orchestrator
        with tracer.start_as_current_span("alpha_orchestrator") as orch_span:
            orch_span.set_attribute("openinference.span.kind", "AGENT")
            orch_span.set_attribute("input.value", json.dumps({
                "ticker": request.ticker,
                "horizon": request.investment_horizon,
            }))

            # Each agent call below will produce nested spans...
```
### 4. MODIFY: Each agent file (research, analysis, sentiment, risk, writer)
# Example: app/agents/research_agent.py

```python
from app.instrumentation import tracer

async def research(context: ReportContext):
    with tracer.start_as_current_span("research_agent") as agent_span:
        agent_span.set_attribute("openinference.span.kind", "CHAIN")
        agent_span.set_attribute("input.value", f"Research {context.ticker}")

        # Tool calls — each wrapped in a TOOL span
        with tracer.start_as_current_span("tool:get_price_data") as tool_span:
            tool_span.set_attribute("openinference.span.kind", "TOOL")
            tool_span.set_attribute("tool.name", "get_price_data")
            tool_span.set_attribute("tool.parameters", json.dumps({"ticker": context.ticker}))
            tool_span.set_attribute("input.value", context.ticker)
            price_data = get_price_data(context.ticker)
            tool_span.set_attribute("output.value", price_data.model_dump_json())

        # ... more tool calls ...

        # LLM call for company overview — AUTO-instrumented by OpenAIInstrumentor
        # (produces openai.chat span with llm.input_messages, llm.output_messages, etc.)
        overview = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": f"Write a company overview for {context.ticker}..."},
            ],
            temperature=0.3,
        )

        agent_span.set_attribute("output.value", "Research complete")
```
Apply the same pattern to ALL five agents. The key hierarchy is:
alpha_orchestrator (AGENT)
├── research_agent (CHAIN)
│   ├── tool:get_price_data (TOOL)
│   ├── tool:get_financial_metrics (TOOL)
│   ├── tool:get_quarterly_earnings (TOOL)
│   ├── tool:search_news (TOOL)
│   ├── tool:get_peers (TOOL)
│   └── openai.chat (LLM — auto by OpenInference)
├── analysis_agent (CHAIN)
│   ├── tool:compare_peers (TOOL)
│   ├── openai.chat (LLM — fundamental analysis)
│   └── openai.chat (LLM — technical analysis)
├── sentiment_agent (CHAIN)
│   ├── tool:get_sentiment_score (TOOL)
│   ├── tool:get_analyst_ratings (TOOL)
│   └── openai.chat (LLM — sentiment narrative)
├── risk_agent (CHAIN)
│   ├── tool:get_financial_metrics (TOOL)
│   └── openai.chat (LLM — risk assessment)
└── writer_agent (CHAIN)
    ├── openai.chat (LLM — executive summary)
    ├── openai.chat (LLM — catalysts)
    └── openai.chat (LLM — recommendation)
This produces a deeply nested span tree with 20-30 spans per report generation —
ideal for demonstrating Dynatrace AI Observability.

#### 5 MODIFY: app/routes/alpha.py
Add using_attributes to the route handler:
```python
@router.post("/api/alpha/generate")
async def generate_report(request: GenerateRequest):
    with using_attributes(
        session_id=str(uuid.uuid4()),
        user_id=request.user_id or "anonymous",
        tags=["alpha-report", f"ticker:{request.ticker}"],
    ):
        # Start background generation
        report_id = report_store.create_report(request)
        asyncio.create_task(orchestrator.generate_alpha_report(...))
        return {"report_id": report_id, "status": "pending"}
```

#### 6 CREATE: .env with all instrumentation values
Complete .env file with:

OpenInference privacy controls (all set to false for local lab)
Dynatrace OTLP export config
OpenAI credentials
App config

Key Requirements

instrumentation.py MUST be imported FIRST — before any OpenAI client creation
Every agent must be wrapped in a named span with openinference.span.kind
Every tool call must be wrapped in a TOOL span with tool.name, input.value, output.value
The full span tree must be 3-4 levels deep minimum
Include comments in code explaining what each attribute means for DT AI Obs
Privacy controls must work via environment variables without code changes
Include graceful shutdown that flushes pending spans
