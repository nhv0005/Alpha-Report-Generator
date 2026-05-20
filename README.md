# Alpha Report Generator

**Audience:** Dynatrace Solutions Engineers who want to (a) deploy this lab to demo
AI Observability, or (b) fork the prompts to spin up their own AI application with
identical instrumentation patterns.

---

## 1. What This Project Is

The **Alpha Report Generator** is a self-contained, two-service AI application that
produces institutional-grade equity research reports ("Alpha Reports") on demand.
It exists for one reason: to generate a **rich, deeply-nested, business-relevant
span tree** that exercises every surface of Dynatrace AI Observability — multi-agent
orchestration, tool calling, LLM token tracking, session continuity, and end-to-end
distributed tracing across a polyglot stack.

| Layer | Tech | Purpose | Instrumented By |
|---|---|---|---|
| Frontend | Next.js 14 (App Router) on port `3000` | Dashboard, report builder, viewer, API proxy | **Dynatrace OneAgent only** |
| Backend | FastAPI + AsyncOpenAI on port `8000` | Multi-agent AI engine | **OneAgent + OpenInference (spans) + OTel SDK (metrics)** — both OTLP HTTP → Dynatrace |
| Tracing | W3C Trace Context | End-to-end propagation Next.js → Python | OneAgent + OTLP |
| Metrics | OTel GenAI histograms (`gen_ai.client.token.usage`, `gen_ai.client.operation.duration`) | Token + latency series for Dynatrace GenAI app | OTel SDK → OTLP HTTP (DELTA temporality) |
| Task-runner events | Dynatrace Events API v2 | `setup` / `install` / `start` / `test-flow` lifecycle events | `scripts/dt-events.ps1`, `scripts-linux/dt-events.sh` |

Everything runs locally — no Docker required (Docker is optional). Mock financial
data is shipped in-tree, so no real market-data API keys are needed.

---

## 2. The Prompt-Driven Build (How the Codebase Was Generated)

The entire codebase was authored by Cascade from a deterministic chain of prompts
in `Alpha Report Generator Prompts/`. Each prompt is self-contained and idempotent;
re-running them on a fresh repo reproduces the lab.

### Execution order

| # | Prompt | Output |
|---|---|---|
| 0 | `[Instructions]Prompt Context.md` | Domain context, architecture diagram, env vars, why this domain is good for AI Obs demos |
| 1 | `Prompt 1.md` | Full directory scaffolding, configs, types, dependency manifests |
| 2 | `Prompt 2.md` | Mock financial tools, Pydantic data models, in-memory `ReportStore` |
| 3 | `Prompt 3.md` | The 5 agents + orchestrator + FastAPI routes (no instrumentation yet) |
| 4 | `Prompt 4.md` | OpenInference + OTel instrumentation layer overlaid on the agents |
| 5 | `Prompt 5.md` | Next.js frontend (dashboard, builder, viewer, API proxy) |
| 6 | `Prompt 6.md` | Docker, scripts, OneAgent feature flags, OpenPipeline rules |
| 7 | `Prompt 7.md` | DQL validation queries, troubleshooting guide, cheat sheet |

> Prompts 4 and 5 are independent and can run in parallel. Everything else is
> strictly sequential.

### Why this structure matters for SEs reusing the prompts

- **Prompt 0 carries the variables**: `DT_ENV_ID`, `DT_ENV_URL`, `DT_API_TOKEN`,
  `OPENAI_API_KEY`, `OPENAI_MODEL`, `PROJECT_ROOT`. To re-skin this lab for a
  different domain (e.g. legal contract review, customer-support copilot), edit
  Prompt 0 — change the **domain narrative** and the **agent specializations** —
  and re-run Prompts 1–7. The instrumentation pattern (Prompt 4) is domain-agnostic
  and should be copied verbatim.
- **Prompt 3 defines the agent topology**. This is the single most important file
  to edit if you want a different agent fan-out (e.g. 3 agents instead of 5, or a
  hierarchical sub-agent pattern instead of sequential).
- **Prompt 4 is the instrumentation contract**. Do not modify this when re-skinning
  unless you want to change the span hierarchy. Keeping it untouched guarantees the
  resulting traces look identical in Dynatrace regardless of domain.

---

## 3. Agentic Patterns Deployed

The lab intentionally implements a **sequential multi-agent orchestrator** with
**LLM-driven tool calling** — the two patterns that produce the richest traces in
Dynatrace AI Observability today.

### 3.1 Pattern A — Orchestrator + Specialist Agents (sequential pipeline)

`@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\orchestrator.py:33-167`

The orchestrator is a deterministic Python coroutine, not an LLM. It runs five
specialist agents in a fixed sequence and threads a shared `ReportContext` between
them. Each specialist owns a focused system prompt and a small toolset:

| Agent | System Prompt Persona | Tools | Output |
|---|---|---|---|
| `research_agent` | Senior equity research analyst | `get_price_data`, `get_financial_metrics`, `get_quarterly_earnings`, `search_news`, `get_peers` | Company Overview section |
| `analysis_agent` | Quantitative analyst | `compare_peers`, `get_technical_indicators` | Fundamental + Technical sections, target price |
| `sentiment_agent` | Sentiment specialist | `get_sentiment_score`, `get_analyst_ratings` | Sentiment section |
| `risk_agent` | Hedge-fund risk manager (contrarian) | `get_financial_metrics` | Risk Assessment, bear case, risk rating |
| `writer_agent` | Senior investment writer | none (pure synthesis) | Executive Summary, Catalysts, Recommendation |

**Why deterministic orchestration instead of an LLM router?** Two reasons:

1. **Reproducible demos.** Every report produces the same span shape; SEs can build
   muscle memory around the trace tree.
2. **Real-world fidelity.** Most production agentic systems today use deterministic
   orchestration over LLM routing for cost, latency, and reliability.

### 3.2 Pattern B — Context object as shared memory

`@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\services\context.py`

A `ReportContext` dataclass (one per report) accumulates `gathered_data` across
agents. The orchestrator writes tool outputs into the context after each stage so
downstream agents can read them without re-calling tools. This produces the typical
"context window grows over time" pattern you see in production agent systems — and
it surfaces in Dynatrace as **growing prompt sizes per LLM span as the report
progresses**, which is a great talking point.

### 3.3 Pattern C — LLM tool calling with explicit TOOL spans

Each agent wraps tool invocations in a manually-instrumented `TOOL` span (see
`_wrap_tool` in `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\analysis_agent.py:31-40`),
even though tools are deterministic Python functions. This is intentional:

- It mirrors what OpenAI's tool-calling loop produces in real systems.
- It guarantees `openinference.span.kind=TOOL`, `tool.name`, `tool.parameters`,
  `input.value`, and `output.value` attributes are always present, so DQL queries
  in Prompt 7 work without per-agent special-casing.
- LLM spans (`openai.chat`) are produced **automatically** by the
  `OpenAIInstrumentor` from OpenInference — no manual span code needed.

### 3.4 Resulting span hierarchy

This is the structure SEs should expect in Dynatrace Distributed Trace view for
every report generation:

```
alpha_orchestrator                 (AGENT)
├── research_agent                 (CHAIN)
│   ├── tool:get_price_data        (TOOL)
│   ├── tool:get_financial_metrics (TOOL)
│   ├── tool:get_quarterly_earnings(TOOL)
│   ├── tool:search_news           (TOOL)
│   ├── tool:get_peers             (TOOL)
│   └── openai.chat                (LLM — auto)
├── analysis_agent                 (CHAIN)
│   ├── tool:compare_peers         (TOOL)
│   ├── tool:get_technical_indicators (TOOL)
│   ├── openai.chat                (LLM — fundamental)
│   └── openai.chat                (LLM — technical)
├── sentiment_agent                (CHAIN)
│   ├── tool:get_sentiment_score   (TOOL)
│   ├── tool:get_analyst_ratings   (TOOL)
│   └── openai.chat                (LLM)
├── risk_agent                     (CHAIN)
│   ├── tool:get_financial_metrics (TOOL)
│   └── openai.chat                (LLM)
└── writer_agent                   (CHAIN)
    ├── openai.chat                (LLM — executive summary)
    ├── openai.chat                (LLM — catalysts)
    └── openai.chat                (LLM — recommendation)
```

A single report generates **20–30 spans across 4 hierarchy levels** plus two
OTel histogram series per LLM call. All agent / tool / orchestrator spans are
emitted with **canonical `gen_ai.*` attributes directly from the code** —
no OpenPipeline rename required. The `ChatCompletion` / `openai.chat` leaf
spans (which still use OpenInference's `llm.*` namespace) are the only ones
that optionally benefit from an OpenPipeline rename — see Prompt 6 and
[`docs/openpipeline-configuration.md`](./alpha-report-lab/docs/openpipeline-configuration.md).

---

## 4. The Instrumentation Layer (Prompt 4 deep-dive)

Four things make AI Observability work in this codebase. For the full deep-dive
(architecture diagram, module hierarchy, per-attribute code citations, common
pitfalls, verification DQL), see
**[`docs/instrumentation.md`](./alpha-report-lab/docs/instrumentation.md)** —
it's the canonical reference for instrumenting any future AI app the same way.

### 4.1 `setup_instrumentation()` runs first

`@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\instrumentation.py:47-195`

This must execute **before any OpenAI client is constructed**, because
`OpenAIInstrumentor().instrument()` monkey-patches the OpenAI SDK at import time.
`app/main.py` enforces this by configuring logging first, then importing
instrumentation, then everything else.

The function:
1. Creates an OTel `TracerProvider` with `service.name=alpha-engine` and
   exports spans via OTLP HTTP to `{DT_ENV_URL}/api/v2/otlp/v1/traces`.
2. Creates an OTel `MeterProvider` exporting metrics via OTLP HTTP to
   `{DT_ENV_URL}/api/v2/otlp/v1/metrics` with **DELTA** aggregation temporality
   (Dynatrace silently drops CUMULATIVE metric payloads — pitfall §5.2 in the
   instrumentation doc).
3. Creates the two GenAI histograms (`gen_ai.client.token.usage`,
   `gen_ai.client.operation.duration`) and emits a startup smoke-test data
   point so a broken token / wrong endpoint surfaces within 10 seconds of boot.
4. Installs `OpenAIInstrumentor` with a `TraceConfig` whose privacy toggles
   (`hide_inputs`, `hide_outputs`, etc.) are env-driven so SEs can demo PII
   redaction without code changes.

### 4.2 Native `gen_ai.*` attributes via `llm_metrics.py` helpers

`@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py`

All manual agent / tool / orchestrator spans are stamped with the canonical
Dynatrace GenAI attribute set (`gen_ai.operation.name`, `gen_ai.agent.name`,
`gen_ai.request.model`, `gen_ai.tool.definitions`, `gen_ai.input.messages`,
`gen_ai.usage.input_tokens`, `gen_ai.response.finish_reasons`, etc.) through
four small helpers — `set_agent_span_attributes`, `set_agent_input_messages`,
`set_agent_output_messages`, and the `measure_llm_call` context manager that
also records both histograms. Agents never write attribute names directly,
which makes typos like `agent.name` (vs `gen_ai.agent.name`) impossible.

### 4.3 Session/user/tag/metadata attribution

The orchestrator and the FastAPI route both wrap the run in
`openinference.instrumentation.using_attributes(...)`. This attaches
`session.id`, `user.id`, `tag.tags`, and arbitrary `metadata.*` fields to
**every child span**. In Dynatrace this lights up:

- **Session view** — group all spans for one report under one session.
- **Tag filtering** — filter by `ticker:NVDA`, `horizon:medium_term`, etc.
- **Metadata search** — find a specific `report_id` instantly.

### 4.4 Task-runner lifecycle events (Dynatrace Events API v2)

`@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\scripts\dt-events.ps1`
/ `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\scripts-linux\dt-events.sh`

Every `tasks.ps1` / `tasks.sh` dispatch (`setup`, `install`, `start`,
`test-flow`, etc.) is wrapped by a helper that pushes start / end events to
Dynatrace with status (`success` / `failure`) and duration. This gives SEs
a deployment / lab-setup audit trail right next to their spans and metrics.
See [`docs/task-runner-observability.md`](./alpha-report-lab/docs/task-runner-observability.md)
for the event schema, required token scope (`events.ingest`), and DQL queries.

### 4.5 OpenPipeline rename for residual `llm.*` attributes (optional)

The only `llm.*` attributes left in the data stream are on the OpenInference
auto-instrumented `ChatCompletion` / `openai.chat` leaf spans. If you want
those to also appear under `gen_ai.*` in Dynatrace, Prompt 6 ships an
OpenPipeline rule set in
[`docs/openpipeline-configuration.md`](./alpha-report-lab/docs/openpipeline-configuration.md).
All manually-instrumented spans already use `gen_ai.*` natively, so the
Dynatrace GenAI app surfaces work without it.

---

## 5. Deploying the Lab

Prereqs: Node 18+, Python 3.12+, OneAgent installed locally, OpenAI key, Dynatrace
API token with the following scopes:

- `openTelemetryTrace.ingest` — for agent / tool / LLM spans
- `metrics.ingest` — for the GenAI token + latency histograms
- `events.ingest` — for task-runner lifecycle events (optional but recommended)
- `logs.ingest` — only if logs are pushed via API instead of OneAgent file rule

```powershell
# from repo root
cd alpha-report-lab
.\tasks.ps1 setup       # creates .env files from templates
# edit alpha-report-lab\alpha-engine\.env with DT_ENV_URL, DT_API_TOKEN, OPENAI_API_KEY
.\tasks.ps1 install     # pip install + npm install
.\tasks.ps1 start       # engine background, frontend foreground
.\tasks.ps1 test-flow   # end-to-end smoke test with status polling
```

OneAgent settings to verify (`Settings → Preferences → OneAgent features`):

| Feature | State |
|---|---|
| Python | Enabled |
| Node.js | Enabled |
| Python FastAPI | Enabled |
| **Python OpenAI** | **Disabled** (avoid duplicate spans with OpenInference) |
| OpenTelemetry (Python) [Opt-In] | **Enabled** |
| W3C Trace Context | Enabled |

Validation DQL queries are in `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\docs\dql-validation-queries.md`.
Cheat sheet for live demos: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\docs\cheat-sheet.md`.

---

## 6. Forking This for Your Own AI App

If you want to demo AI Observability in a different vertical (legal, healthcare,
support, retail), do this:

1. **Copy the prompts folder.** Treat it as a template.
2. **Edit Prompt 0** — replace the Alpha Report domain narrative with your domain.
   Keep the architecture diagram, env vars, and "Why this domain is perfect for AI
   Obs" structure.
3. **Edit Prompt 3 only** — redefine the agent personas and their tools. Keep the
   orchestrator pattern (sequential, deterministic, shared context). Change agent
   names if you want different span names in the trace tree.
4. **Edit Prompt 2** — replace mock financial tools with mock tools for your
   domain. Keep tool signatures function-call-friendly and return Pydantic models.
5. **Do NOT edit Prompt 4** — copy verbatim. The instrumentation contract is what
   makes the Dynatrace experience identical across forks.
6. **Edit Prompt 5** — reskin the frontend.
7. **Re-run all prompts** in order against an empty repo using a fresh Cascade
   session. Use `[Instructions]Prompt Context.md` first to seed.

The result: a new domain-specific AI app with the same 20–30-span tree, same DQL
queries, same OpenPipeline config — drop it into any Dynatrace tenant and the AI
Obs surfaces work out of the box.

---

## 7. Suggested Demo Flow (5–7 min)

1. Open the frontend at `http://localhost:3000`, generate an `NVDA` report.
2. While it runs (~30–60s), open Dynatrace **Distributed Traces**, filter by
   `service.name = alpha-engine`, find the latest trace.
3. Walk the span tree top-down: `alpha_orchestrator` → agents → tools + LLM calls.
   Highlight `openinference.span.kind` color-coding.
4. Click an `openai.chat` span — show `gen_ai.input.messages`,
   `gen_ai.output.messages`, `gen_ai.usage.input_tokens`, model name, latency.
5. Open **AI Observability app** — show the same trace as a session, with token
   spend, agent breakdown, and tool-call summary, all powered by the OTel
   GenAI histograms emitted by the engine.
6. Run the token-by-agent DQL query from `dql-validation-queries.md` to show
   per-agent cost attribution sourced from `gen_ai.client.token.usage`.
7. (Bonus) Toggle `OPENINFERENCE_HIDE_INPUTS=true` in `alpha-engine/.env`, restart engine, generate another
   report — show prompt content disappearing from spans (privacy story).

---

## 8. Reference Files

### Code

- Prompts: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\Alpha Report Generator Prompts\`
- Engine entrypoint: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\main.py`
- Instrumentation SDK setup: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\instrumentation.py`
- GenAI metric + span helpers: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\llm_metrics.py`
- Config / env loader: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\config.py`
- Orchestrator: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-engine\app\agents\orchestrator.py`
- Frontend root: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\alpha-frontend\src\app\page.tsx`
- Task runner (PowerShell / Bash): `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\tasks.ps1` · `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\tasks.sh`
- Dynatrace event helpers: `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\scripts\dt-events.ps1` · `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\scripts-linux\dt-events.sh`

### Documentation

- **Instrumentation deep-dive (start here for any new AI app):** [`docs/instrumentation.md`](./alpha-report-lab/docs/instrumentation.md) — architecture diagram, module hierarchy, every `gen_ai.*` attribute mapped to the line that sets it, the four common pitfalls, and verification DQL.
- Task-runner observability (Events API v2): [`docs/task-runner-observability.md`](./alpha-report-lab/docs/task-runner-observability.md)
- DQL validation queries: [`docs/dql-validation-queries.md`](./alpha-report-lab/docs/dql-validation-queries.md)
- OneAgent setup: [`docs/oneagent-configuration.md`](./alpha-report-lab/docs/oneagent-configuration.md)
- OpenPipeline rules (optional `llm.* → gen_ai.*` rename for OpenInference leaf spans): [`docs/openpipeline-configuration.md`](./alpha-report-lab/docs/openpipeline-configuration.md)
- Cloud VM deployment: [`docs/cloud-vm-deployment.md`](./alpha-report-lab/docs/cloud-vm-deployment.md)
- Live-demo cheat sheet: [`docs/cheat-sheet.md`](./alpha-report-lab/docs/cheat-sheet.md)

### Reusing this pattern in a new AI app

If you're spinning up a different AI application and want the same Dynatrace
experience, the only file you need to read end-to-end is
[`docs/instrumentation.md`](./alpha-report-lab/docs/instrumentation.md).
It covers how to wire OpenTelemetry + an OTel framework like OpenInference
into a Python/FastAPI service so it lands cleanly in Dynatrace AI
Observability with `gen_ai.*` attributes, token/latency histograms, and a
working GenAI-app dashboard out of the box.
