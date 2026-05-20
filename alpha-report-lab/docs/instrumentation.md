# Observability & Instrumentation

End-to-end guide to the OpenTelemetry + OpenInference instrumentation that
makes the Alpha Engine observable in Dynatrace, including the Dynatrace-side
configuration steps and the pitfalls we hit while wiring it up.

---

## 1. What gets instrumented

The engine is a multi-agent FastAPI application. Every report run produces
the following telemetry:

| Signal | Source | Backend |
|---|---|---|
| **Spans** (traces) | Manual spans + OpenInference auto-instrumentation of `openai` | Dynatrace `/api/v2/otlp/v1/traces` |
| **Metrics** (histograms) | Manual `meter.create_histogram` calls | Dynatrace `/api/v2/otlp/v1/metrics` |
| **Logs** | Stdlib `logging` -> `engine.log` | Dynatrace Log Ingest (via OneAgent file source rule) |

### Span hierarchy per report

```
invoke_agent alpha_orchestrator        (gen_ai.agent.name = alpha_orchestrator)
├── invoke_agent research_agent
│   ├── execute_tool get_company_profile
│   ├── execute_tool get_price_data
│   ├── execute_tool get_financial_metrics
│   ├── execute_tool get_quarterly_earnings
│   ├── execute_tool search_news
│   ├── execute_tool get_peers
│   └── ChatCompletion                  (OpenInference openai.chat span)
├── invoke_agent analysis_agent
│   ├── execute_tool compare_peers
│   ├── execute_tool get_technical_indicators
│   ├── ChatCompletion (fundamental)
│   └── ChatCompletion (technical)
├── invoke_agent sentiment_agent
├── invoke_agent risk_agent
└── invoke_agent writer_agent
    ├── ChatCompletion (executive_summary)
    ├── ChatCompletion (catalysts)
    └── ChatCompletion (recommendation)
```

### Canonical attributes

All spans follow the [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) and the [Dynatrace GenAI attribute set](https://docs.dynatrace.com/docs/shortlink/genai-terms-and-concepts).

**Agent spans** (`invoke_agent <name>`):

| Attribute | Example |
|---|---|
| `gen_ai.operation.name` | `invoke_agent` |
| `gen_ai.provider.name` | `openai` |
| `gen_ai.agent.id` | `uuid4` per invocation |
| `gen_ai.agent.name` | `research_agent` |
| `gen_ai.agent.description` | `"Senior equity research analyst..."` |
| `gen_ai.request.model` | `gpt-4o` |
| `gen_ai.output.type` | `text` |
| `gen_ai.tool.definitions` | `[{"name":"get_company_profile"},...]` |
| `gen_ai.system_instructions` | the agent's system prompt (suppressed if `OPENINFERENCE_HIDE_INPUTS=true`) |
| `gen_ai.input.messages` | `[{"role":"user","content":"..."}]` |
| `gen_ai.output.messages` | `[{"role":"assistant","content":"..."}]` |
| `gen_ai.usage.input_tokens` | sum across LLM calls in the agent |
| `gen_ai.usage.output_tokens` | sum across LLM calls in the agent |
| `gen_ai.response.finish_reasons` | orchestrator only: `["stop"|"cancelled"|"error"]` |

**Tool spans** (`execute_tool <name>`):

| Attribute | Example |
|---|---|
| `gen_ai.operation.name` | `execute_tool` |
| `gen_ai.tool.name` | `get_company_profile` |
| `gen_ai.provider.name` | `openai` |

**Metrics** (per OTel GenAI metrics spec):

| Metric | Unit | Type |
|---|---|---|
| `gen_ai.client.token.usage` | `{token}` | Histogram |
| `gen_ai.client.operation.duration` | `s` | Histogram |

Both carry: `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.agent.name`, plus `gen_ai.token.type` (`input`/`output`) on the token histogram.

---

## 2. Code layout

| File | Purpose |
|---|---|
| `alpha-engine/app/main.py` | App entry point. **Configures logging FIRST**, then calls `setup_instrumentation()`, then imports the rest. |
| `alpha-engine/app/instrumentation.py` | OTel TracerProvider + MeterProvider setup. Wires the OTLP HTTP exporters to Dynatrace. Installs `OpenAIInstrumentor`. Records a startup smoke-test data point. |
| `alpha-engine/app/agents/llm_metrics.py` | Helpers: `measure_llm_call(...)` (records both histograms with canonical attrs), `set_agent_span_attributes(...)`, `set_agent_input_messages(...)`, `set_agent_output_messages(...)`. |
| `alpha-engine/app/agents/<agent>.py` | Each agent declares `AGENT_DESCRIPTION` + `AGENT_TOOLS` constants and calls the helpers above inside its `invoke_agent <name>` span. |
| `alpha-engine/app/agents/orchestrator.py` | Top-level `invoke_agent alpha_orchestrator` span; wraps the entire pipeline. |

### 2.1 Instrumentation hierarchy & module relationships

The instrumentation is intentionally split into three concentric layers so
that adding a new agent never requires touching the SDK setup, and changing
the SDK setup never requires touching agent code.

```
                          ┌──────────────────────────────────────┐
                          │              .env file               │
                          │  DT_ENV_URL, DT_API_TOKEN,           │
                          │  OPENAI_*, SERVICE_NAME,             │
                          │  DEBUG_TRACES, HIDE_INPUTS, ...      │
                          └────────────────┬─────────────────────┘
                                           │  load_dotenv() + os.getenv
                                           ▼
                          ┌──────────────────────────────────────┐
              Layer 0:    │             app/config.py            │
              Config      │   @dataclass Settings  →  settings   │
                          │   (single immutable singleton)       │
                          └────────────────┬─────────────────────┘
                                           │  from app.config import settings
                          ┌────────────────┴─────────────────────┐
                          ▼                                      ▼
        ┌──────────────────────────────────┐   ┌──────────────────────────────────┐
Layer 1:│       app/instrumentation.py     │   │      app/agents/llm_metrics.py   │
SDK     │  - TracerProvider + OTLP traces  │   │  - measure_llm_call(...)         │
setup + │  - MeterProvider + OTLP metrics  │◄──┤  - record_llm_metrics(...)       │
helpers │    (DELTA temporality)           │   │  - set_agent_span_attributes(...)│
        │  - OpenAIInstrumentor().instrument()│  - set_agent_input_messages(...) │
        │  - module-level: tracer, meter,  │   │  - set_agent_output_messages(...)│
        │    gen_ai_token_usage,           │   │                                  │
        │    gen_ai_operation_duration     │   │  Reads instrumentation.tracer /  │
        └────────────────┬─────────────────┘   │  .gen_ai_token_usage /           │
                         │                     │  .gen_ai_operation_duration      │
                         │ from app.instrumentation import tracer
                         │                                                       │
                         ▼                                                       ▼
        ┌────────────────────────────────────────────────────────────────────────┐
Layer 2:│                       app/agents/<agent>.py                            │
Agents  │   research_agent.py · analysis_agent.py · sentiment_agent.py           │
        │   risk_agent.py     · writer_agent.py    · orchestrator.py             │
        │                                                                        │
        │   with tracer.start_as_current_span("invoke_agent <name>") as span:    │
        │       set_agent_span_attributes(span, ...)        ← from llm_metrics   │
        │       set_agent_input_messages(span, ...)         ← from llm_metrics   │
        │       with measure_llm_call(<name>, model) as r:  ← from llm_metrics   │
        │           response = await client.chat.completions.create(...)         │
        │           r(response)                                                  │
        │       set_agent_output_messages(span, ...)        ← from llm_metrics   │
        └────────────────────────────────┬───────────────────────────────────────┘
                                         │
                                         ▼
        ┌────────────────────────────────────────────────────────────────────────┐
                              OTLP HTTP exporters
              (traces) → DT_ENV_URL/api/v2/otlp/v1/traces
              (metrics)→ DT_ENV_URL/api/v2/otlp/v1/metrics  (DELTA, every 10s)
        └────────────────────────────────────────────────────────────────────────┘
```

#### Bootstrap order (`main.py`)

`main.py` is the only place that knows about the bootstrap sequence. The
order is non-negotiable and is the cause of pitfalls §5.1 and §5.3:

```
main.py
 │
 1. import settings from app.config            ← pure config, no OTel imports
 │
 2. logging.basicConfig(...)                   ← MUST be before step 4
 │
 3. raise log level on every "opentelemetry.*" logger
 │
 4. from app.instrumentation import setup_instrumentation
 │  setup_instrumentation()                    ← MUST be before step 5
 │      • build TracerProvider + OTLP trace exporter
 │      • build MeterProvider + OTLP metric exporter (DELTA temporality)
 │      • create gen_ai.client.token.usage / .operation.duration histograms
 │      • smoke-test record + force_flush
 │      • OpenAIInstrumentor().instrument()    ← monkey-patches `openai`
 │
 5. import the rest of the app (FastAPI, routes, agents, openai client, ...)
```

See `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\main.py:11-36`.

#### Who imports whom (one-liner each)

| Module | Imports from `app.config` | Imports from `app.instrumentation` | Imports from `app.agents.llm_metrics` |
|---|:-:|:-:|:-:|
| `app/main.py` | ✅ `settings` | ✅ `setup_instrumentation`, `shutdown` | — |
| `app/instrumentation.py` | ✅ `settings` | (defines) | — |
| `app/agents/llm_metrics.py` | ✅ `settings` (privacy flags) | ✅ `tracer`, `gen_ai_token_usage`, `gen_ai_operation_duration` (module-level) | (defines) |
| `app/agents/<agent>.py` | ✅ `settings` (model name) | ✅ `tracer` | ✅ `measure_llm_call`, `set_agent_span_attributes`, `set_agent_input_messages`, `set_agent_output_messages` |
| `app/agents/orchestrator.py` | ✅ `settings` | ✅ `tracer` | ✅ `set_agent_span_attributes`, `set_agent_input_messages`, `set_agent_output_messages` |

The graph is **acyclic** and one-directional (`config → instrumentation →
llm_metrics → agents`). Nothing flows the other way, which is what lets
`main.py` enforce the bootstrap order described above.

#### Role of each module

**`app/config.py`** — *the only place that reads `os.environ`.*
Loads `.env` via `python-dotenv`, builds a single immutable `Settings`
dataclass instance, and exports it as `settings`. Every other module
imports this singleton; nobody else calls `os.getenv` for instrumentation
config. This is what guarantees the OTLP endpoint, token, and privacy
flags are consistent across the trace exporter, the metric exporter, and
every agent. See `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\config.py:19-52`.

**`app/instrumentation.py`** — *the OTel SDK boundary.*
The only file that imports from `opentelemetry.sdk.*`. It owns:

- the `TracerProvider` with the OTLP HTTP trace exporter,
- the `MeterProvider` with the OTLP HTTP metric exporter (DELTA temporality),
- the two GenAI histograms (`gen_ai.client.token.usage`, `gen_ai.client.operation.duration`),
- the `OpenAIInstrumentor` install,
- module-level handles (`tracer`, `meter`, `gen_ai_token_usage`, `gen_ai_operation_duration`) that everyone else imports.

If you want to add a new exporter, change temporality, or wire in a new
auto-instrumentor, this is the **only** file you touch.

**`app/agents/llm_metrics.py`** — *the agent-facing API over the SDK.*
A thin façade so that agents never need to know about OTel attribute
names, histogram instruments, or aggregation rules. Provides four helpers:

- `measure_llm_call(agent, model)` — context manager that times the LLM call and writes both histograms with the canonical `gen_ai.*` attribute set, including `error.type` if an exception escapes.
- `set_agent_span_attributes(span, ...)` — stamps the canonical agent-span attribute set from the Dynatrace docs.
- `set_agent_input_messages(span, ...)` / `set_agent_output_messages(span, ...)` — set `gen_ai.input.messages` / `gen_ai.output.messages` while honoring the `HIDE_INPUTS` / `HIDE_OUTPUTS` privacy flags.

This indirection is what makes the GenAI-attribute standardization
enforceable: a typo like `agent.name` (instead of `gen_ai.agent.name`) is
impossible because no agent writes attribute names directly.

**`app/agents/<agent>.py` and `orchestrator.py`** — *pure business logic.*
Each agent declares two constants (`AGENT_DESCRIPTION`, `AGENT_TOOLS`) and
follows the same five-step skeleton: open span → set attrs → run tools as
child spans → wrap LLM call in `measure_llm_call` → attach
`gen_ai.usage.*_tokens` + output messages. Agents never import from the
OTel SDK directly.

---

### 2.2 Where each attribute / metric is captured in code

The tables in §1 are the *contract*. The snippets below show the exact lines
in the codebase that produce each piece of telemetry, so you can see how to
add a new agent or extend an existing one.

#### a) TracerProvider, MeterProvider, and the two GenAI histograms

Both histograms (`gen_ai.client.token.usage` and
`gen_ai.client.operation.duration`) are created **once** at startup in
`alpha-engine/app/instrumentation.py` and re-used by every agent:

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\instrumentation.py:140-151
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
```

The DELTA temporality fix from §5.2 lives a few lines above:

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\instrumentation.py:105-117
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
```

#### b) Recording the two histograms (`measure_llm_call`)

Every LLM call is wrapped by the `measure_llm_call` context manager defined
in `alpha-engine/app/agents/llm_metrics.py`. It times the call, then writes
both histograms with the canonical `gen_ai.*` attribute set:

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py:62-83
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
```

The `gen_ai.token.type` dimension (`"input"` / `"output"`) is **only** added
to the token histogram, never to the duration histogram — that's how
Dynatrace can split tokens by type without polluting the duration series.

#### c) Canonical agent-span attributes (`set_agent_span_attributes`)

Every agent span gets the same canonical attribute set via this single
helper, so adding a new agent only requires defining `AGENT_DESCRIPTION` +
`AGENT_TOOLS` and calling the helper:

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py:140-153
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
```

`gen_ai.input.messages` and `gen_ai.output.messages` are set by the two
sibling helpers, both of which respect the `HIDE_INPUTS` / `HIDE_OUTPUTS`
privacy switches (see §3):

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py:156-173
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
```

#### d) An end-to-end example: `research_agent`

This is the canonical pattern every agent follows — start the
`invoke_agent <name>` span, apply the attribute set, run tools as
`execute_tool <name>` child spans, wrap the LLM call with
`measure_llm_call`, then attach token totals + output messages back onto
the agent span:

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\research_agent.py:58-69
    with tracer.start_as_current_span("invoke_agent research_agent") as agent_span:
        set_agent_span_attributes(
            agent_span,
            agent_name="research_agent",
            description=AGENT_DESCRIPTION,
            request_model=settings.OPENAI_MODEL,
            tool_definitions=AGENT_TOOLS,
            system_instructions=RESEARCH_SYSTEM_PROMPT,
        )
        set_agent_input_messages(agent_span, [
            {"role": "user", "content": f"Research {context.ticker}"},
        ])
```

Each tool gets its own `execute_tool` span with `gen_ai.tool.name`:

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\research_agent.py:44-51
async def _wrap_tool(tool_name: str, fn, *args, **kwargs):
    """Run a mock tool inside a span using OTel GenAI semantic conventions."""
    with tracer.start_as_current_span(f"execute_tool {tool_name}") as span:
        span.set_attribute("gen_ai.operation.name", "execute_tool")
        span.set_attribute("gen_ai.tool.name", tool_name)
        span.set_attribute("gen_ai.provider.name", "openai")
        result = fn(*args, **kwargs)
        return result
```

The LLM call itself is wrapped by `measure_llm_call`, and per-agent token
totals are attached back onto the agent span:

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\research_agent.py:89-98
        with measure_llm_call("research_agent", settings.OPENAI_MODEL) as record:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            record(response)
```

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\research_agent.py:121-125
        agent_span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
        agent_span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
        set_agent_output_messages(agent_span, [
            {"role": "assistant", "content": content},
        ])
```

The other four agents (`analysis_agent.py`, `sentiment_agent.py`,
`risk_agent.py`, `writer_agent.py`) follow the **exact same pattern** — if
you want to add a sixth agent, copy this skeleton.

#### e) `gen_ai.response.finish_reasons` (orchestrator only)

The orchestrator span uses `gen_ai.response.finish_reasons` to record the
terminal state of an entire report run — `stop`, `cancelled`, or `error`:

```@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\orchestrator.py:166-189
                orch_span.set_attribute("gen_ai.response.finish_reasons", json.dumps(["stop"]))
                set_agent_output_messages(orch_span, [
                    {"role": "assistant", "content": json.dumps({
                        "recommendation": writer_out["recommendation"],
```
```
            except _CancelledByUser:
                logger.info(f"[orchestrator] Report {report_id} cancelled by user")
                orch_span.set_attribute("gen_ai.response.finish_reasons", json.dumps(["cancelled"]))
```
```
                orch_span.record_exception(e)
                orch_span.set_attribute("error.type", type(e).__name__)
                orch_span.set_attribute("gen_ai.response.finish_reasons", json.dumps(["error"]))
```

This is what powers the "agent-level error rate" DQL in §7.

#### f) Attribute / metric → code-location cheat sheet

| Attribute or metric | Defined / set in |
|---|---|
| `gen_ai.client.token.usage` (histogram) | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\instrumentation.py:142-146` |
| `gen_ai.client.operation.duration` (histogram) | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\instrumentation.py:147-151` |
| `gen_ai.token.type` (input/output dimension) | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py:76-81` |
| `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model` (metric attrs) | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py:28-40` |
| `gen_ai.agent.id`, `gen_ai.agent.name`, `gen_ai.agent.description`, `gen_ai.output.type`, `gen_ai.tool.definitions`, `gen_ai.system_instructions` (agent span) | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py:140-152` |
| `gen_ai.input.messages` / `gen_ai.output.messages` | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py:156-173` |
| `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` (agent span totals) | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\research_agent.py:121-122` (one per agent) |
| `gen_ai.tool.name` (tool span) | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\research_agent.py:46-49` |
| `gen_ai.response.finish_reasons` | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\orchestrator.py:166-189` |
| Smoke-test data point at startup | `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\instrumentation.py:155-176` |

---

## 3. Required environment variables

Set these in `alpha-engine/.env` (or your shell):

```bash
# Dynatrace OTLP ingest endpoint and token
DT_ENV_URL=https://<tenant>.live.dynatrace.com         # NO trailing slash
DT_API_TOKEN=dt0c01.XXXXXXXX...                        # see scopes below

# OpenAI
OPENAI_API_KEY=sk-...

# Optional debugging
DEBUG_TRACES=true                                      # adds Console exporters
LOG_LEVEL=info

# Privacy controls (forwarded to OpenInference TraceConfig)
OPENINFERENCE_HIDE_INPUTS=false
OPENINFERENCE_HIDE_OUTPUTS=false
OPENINFERENCE_HIDE_LLM_INVOCATION_PARAMETERS=false
```

The engine **only** exports to Dynatrace if both `DT_ENV_URL` and
`DT_API_TOKEN` are set. The startup banner makes this explicit:

```
[INFO] app.instrumentation: Instrumentation env: DT_ENV_URL=set, DT_API_TOKEN=set (len=96), DEBUG_TRACES=True
[INFO] app.instrumentation: OTLP traces exporter configured -> https://.../api/v2/otlp/v1/traces
[INFO] app.instrumentation: OTLP metrics exporter configured -> https://.../api/v2/otlp/v1/metrics (temporality: DELTA for Counter/Histogram, CUMULATIVE for UpDownCounter/Gauge)
[INFO] app.instrumentation: Metric smoke-test force_flush returned True
[INFO] app.instrumentation: OpenInference OpenAIInstrumentor installed
```

If you don't see all five lines after a restart, **stop and read them** —
something is misconfigured.

---

## 4. Dynatrace-side configuration

### 4.1 Create the API token

In Dynatrace **Access Tokens** → **Generate new token** with at minimum:

- ☑ `openTelemetryTrace.ingest` — required for spans
- ☑ `metrics.ingest` — required for the GenAI histograms
- ☑ `logs.ingest` — only if you want logs ingested via API (not needed if OneAgent is shipping the file)
- ☑ `events.ingest` — only if you call the events API

Copy the token (`dt0c01....`, ~96 chars) into `DT_API_TOKEN`.

### 4.2 OneAgent log forwarding (optional but recommended)

If a OneAgent is installed on the host, point it at `engine.log` so logs get
correlated with the spans automatically. See
[`docs/oneagent-configuration.md`](./oneagent-configuration.md).

### 4.3 OpenPipeline / SDLC processing (optional)

If you want to derive structured fields out of the engine's text logs, see
[`docs/openpipeline-configuration.md`](./openpipeline-configuration.md).

---

## 5. Pitfalls we hit (so you don't have to)

These are the four bugs that bit us during initial setup. All four are
**fixed in the current code**, but understanding them is essential when
you change the instrumentation later.

### 5.1 ⚠️ `logging.basicConfig()` must run BEFORE `setup_instrumentation()`

**Symptom:** None of the `logger.info("OTLP ... configured")` startup banners
appear in `engine.log`. Errors from the OTLP exporters (401/403/timeouts) are
also invisible because they go through the same un-handler-attached loggers.

**Cause:** `logging.basicConfig()` only attaches handlers if the root logger
has none. `setup_instrumentation()` calls `logger.info()` early; if it runs
before `basicConfig()`, those messages fire under Python's "last resort"
handler which prints WARNING+ only to stderr, then `basicConfig()` is a no-op
because handlers now exist on stderr.

**Fix:** In `main.py`, configure logging **first**, then import and call
`setup_instrumentation()`:

```python
# main.py
import logging
from app.config import settings  # safe — no instrumentation imports

logging.basicConfig(level=..., format=...)
for name in ("opentelemetry", "opentelemetry.exporter.otlp.proto.http.metric_exporter", ...):
    logging.getLogger(name).setLevel(logging.INFO)

# NOW import + run instrumentation
from app.instrumentation import setup_instrumentation
setup_instrumentation()
```

### 5.2 ⚠️ Dynatrace requires DELTA aggregation temporality (the silent killer)

**Symptom:** Spans flow into Dynatrace fine. The OTLP **metrics** POST returns
HTTP 200 with no error from the SDK, but `fetch metric.series | filter
startsWith(metric.key, "gen_ai")` returns **zero rows**, forever. No warnings
in the engine log either.

**Cause:** The OpenTelemetry Python SDK defaults to **CUMULATIVE** aggregation
temporality for `Counter`, `UpDownCounter`, and `Histogram`. Dynatrace's OTLP
metric ingest accepts CUMULATIVE payloads with HTTP 200 then **silently
drops them**. Only DELTA payloads are persisted.

You can confirm this is biting you by enabling `DEBUG_TRACES=true` and
looking at the Console exporter dump: each metric will show
`"aggregation_temporality": 2` (= CUMULATIVE).

**Fix:** Pass an explicit `preferred_temporality` map to `OTLPMetricExporter`:

```python
from opentelemetry.sdk.metrics import Counter, Histogram, UpDownCounter, ObservableCounter, ObservableUpDownCounter, ObservableGauge
from opentelemetry.sdk.metrics.export import AggregationTemporality

delta_temporality = {
    Counter:                  AggregationTemporality.DELTA,
    UpDownCounter:            AggregationTemporality.CUMULATIVE,
    Histogram:                AggregationTemporality.DELTA,
    ObservableCounter:        AggregationTemporality.DELTA,
    ObservableUpDownCounter:  AggregationTemporality.CUMULATIVE,
    ObservableGauge:          AggregationTemporality.CUMULATIVE,
}

OTLPMetricExporter(
    endpoint=metrics_endpoint,
    headers={"Authorization": f"Api-Token {DT_API_TOKEN}"},
    preferred_temporality=delta_temporality,
)
```

### 5.3 ⚠️ `setup_instrumentation()` must run BEFORE the OpenAI client is created

**Symptom:** No `openai.chat` / `ChatCompletion` spans appear at all. Manual
agent spans still work but the LLM call inside them is invisible.

**Cause:** OpenInference's `OpenAIInstrumentor().instrument()` works by
**monkey-patching** the `openai` module. If any code has already imported
`openai` and built a client instance before instrumentation runs, that client
holds references to the un-patched methods and emits no spans.

**Fix:** In `main.py`, the very first non-stdlib import block must be
instrumentation, then `setup_instrumentation()` is called, then everything
else (including anything that touches `openai`) is imported. The current
`main.py` enforces this order with a comment.

### 5.4 ⚠️ Don't mix `gen_ai.system` (deprecated) with `gen_ai.provider.name`

**Symptom:** Dynatrace's built-in GenAI dashboards show "unknown provider"
or your service doesn't show up under the GenAI section even though spans
arrive.

**Cause:** Older OTel GenAI conventions used `gen_ai.system`. The Dynatrace
semantic dictionary now expects **`gen_ai.provider.name`**. Similarly,
custom attributes like `agent.name` (without the `gen_ai.` prefix) will not
be picked up by the GenAI app.

**Fix:** Use only the canonical names from the Dynatrace docs:

| Use ✅ | Don't use ❌ |
|---|---|
| `gen_ai.provider.name` | `gen_ai.system` |
| `gen_ai.agent.name` | `agent.name` |
| `gen_ai.usage.input_tokens` + `gen_ai.usage.output_tokens` | `llm.token_count.total` |

Also remove `openinference.span.kind` if you want pure semconv compliance —
Dynatrace doesn't need it (it does its own classification from
`gen_ai.operation.name`).

### 5.5 ⚠️ `DEBUG_TRACES=true` adds a Console metric exporter (very noisy)

The Console exporter dumps every metric collection cycle (every ~15s) as a
multi-kB JSON blob into `engine.log`. That makes ad-hoc grepping painful and
also blows up Dynatrace log ingest if the file is being shipped. Leave
`DEBUG_TRACES=false` unless you're actively debugging the SDK pipeline.

---

## 6. Verifying the wiring is live (4 checks in 5 minutes)

After every restart, run these checks in order. If any fails, jump to the
matching pitfall in §5.

### Check 1 — Startup banner

```powershell
Get-Content alpha-engine\engine.log -Tail 30
```

You should see all five `[INFO] app.instrumentation: ...` lines listed in §3,
including `Metric smoke-test force_flush returned True`.

### Check 2 — Spans landing in Dynatrace

```dql
fetch spans, from: now()-15m
| filter service.name == "Alpha Engine"
| filter startsWith(span.name, "invoke_agent")
| sort start_time desc
| fields start_time, span.name, gen_ai.agent.name, gen_ai.agent.id, gen_ai.usage.input_tokens, gen_ai.usage.output_tokens
| limit 10
```

Expect 6 rows per report run (1 orchestrator + 5 sub-agents).

### Check 3 — Smoke-test metric landing in Dynatrace

```dql
fetch metric.series, from: now()-15m
| filter metric.key == "gen_ai.client.token.usage_sum"
| filter gen_ai.agent.name == "instrumentation_smoketest"
| limit 5
```

If this returns 0 rows but the engine startup log says
`force_flush returned True`, you almost certainly have a **temporality
mismatch** (§5.2) or **token scope** issue (§4.1).

### Check 4 — Real GenAI metrics

```dql
timeseries tokens = sum(gen_ai.client.token.usage),
  by: { gen_ai.agent.name, gen_ai.token.type, gen_ai.request.model },
  from: now()-1h
```

Should produce one series per `(agent, token_type, model)` combination.

---

## 7. Useful follow-up DQL

**Per-report cost** (input + output tokens × $/token):

```dql
timeseries
  in_tok  = sum(gen_ai.client.token.usage, filter: { gen_ai.token.type == "input" }),
  out_tok = sum(gen_ai.client.token.usage, filter: { gen_ai.token.type == "output" }),
  by: { gen_ai.request.model },
  from: now()-24h
```

**Latency p95 per agent:**

```dql
timeseries p95_s = percentile(gen_ai.client.operation.duration, 95),
  by: { gen_ai.agent.name }, from: now()-24h
```

**Agent-level error rate** (orchestrator finish reasons):

```dql
fetch spans, from: now()-24h
| filter span.name == "invoke_agent alpha_orchestrator"
| summarize
    total = count(),
    errors = countIf(gen_ai.response.finish_reasons == "[\"error\"]")
```

---

## 8. Where to look when something is wrong

1. **`alpha-engine\engine.log`** — startup banner, OTel SDK warnings, exporter failures.
2. **`fetch dt.system.events`** in Dynatrace — ingest-side rejections.
3. **Console exporter output** (when `DEBUG_TRACES=true`) — confirms what the SDK is *trying* to send before the wire.
4. **Token in Dynatrace UI → Access Tokens** — verify scopes and not expired/revoked.
5. **`docs/troubleshooting.md`** — environment-level issues (proxy, DNS, OneAgent).
