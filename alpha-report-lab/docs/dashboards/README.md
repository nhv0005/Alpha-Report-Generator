# Alpha Report — Dynatrace dashboards

JSON dashboard definitions for the Alpha Report Generator lab. Each file in this
directory is a self-contained Dynatrace **platform dashboard** (the new
Dashboards app schema, not Dashboards Classic) that can be deployed with
`dtctl`.

## Files

| File | What it shows |
|---|---|
| `alpha-report-dashboard.json` | End-to-end view of the engine: token spend per agent/model, p50/p95/p99 latency, finish reasons, tool-call mix, recent reports, and task-runner lifecycle events. |

## Deploy

From the repo root:

```powershell
# create a new dashboard from the JSON definition
dtctl create db --file alpha-report-lab\docs\dashboards\alpha-report-dashboard.json

# list the dashboards you own to find the new ID
dtctl get dashboards -o json | findstr /i "Alpha Report"
```

To update an existing dashboard, use the `id` it was assigned on creation:

```powershell
dtctl update db <dashboard-id> --file alpha-report-lab\docs\dashboards\alpha-report-dashboard.json
```

## What's in `alpha-report-dashboard.json`

Top-to-bottom, the dashboard has 22 tiles in 7 sections:

1. **Header** — title + pointer to `docs/instrumentation.md`.
2. **KPI strip (4 tiles)** — Reports generated · Total tokens · Avg report duration · Error rate (with traffic-light thresholds).
3. **Tokens & cost (4 tiles)**
   - Token usage over time, broken down by `gen_ai.agent.name`.
   - Input vs output tokens (stacked area).
   - Tokens by `gen_ai.request.model` (donut).
   - Top-10 agents by total token consumption (table with input/output/total).
4. **Latency (3 tiles)**
   - p50 / p95 / p99 of `gen_ai.client.operation.duration`.
   - p95 per agent.
   - Agent span duration heatmap.
5. **Run quality & topology (3 tiles)**
   - Orchestrator finish reasons (`stop` / `cancelled` / `error`) — donut.
   - Tool call mix by `gen_ai.tool.name` — bar.
   - Spans per report (trace breakdown, last 25).
6. **Recent reports** — table of the 25 most recent orchestrator spans with token totals, duration, finish reason, and trace ID.
7. **Task-runner lifecycle** — recent `tasks.ps1` / `tasks.sh` events (`setup`, `install`, `start`, `test-flow`) from the Events API.

## Data sources used by the queries

| Tile group | DQL source | Where it's emitted |
|---|---|---|
| KPI tokens, "Tokens & cost" | `gen_ai.client.token.usage` metric (sum / split by `gen_ai.token.type`) | `app/agents/llm_metrics.py` via `measure_llm_call` |
| KPI duration, "Latency" | `gen_ai.client.operation.duration` metric (avg / percentile) | same |
| KPI reports, error rate, finish reasons, recent reports | `fetch spans` on `span.name == "invoke_agent alpha_orchestrator"` | `app/agents/orchestrator.py` |
| Tool-call mix | `fetch spans` on `startsWith(span.name, "execute_tool")` | each agent's `_wrap_tool` helper |
| Task-runner events | `fetch events` filtered by source/name `alpha` / `tasks.*` | `scripts/dt-events.ps1`, `scripts-linux/dt-events.sh` |

## Variables

The dashboard ships three filter variables (top of the page in the UI):

| Variable | Type | Default | What it controls |
|---|---|---|---|
| `timeframe` | timeframe | `now-24h` | Global lookback window. |
| `service_name` | query | `Alpha Engine` | Auto-populated from `dt.entity.service` matching `alpha-engine`. |
| `agent_name` | query | `*` (multi-select) | Auto-populated from distinct `gen_ai.agent.name` values seen in spans. |

Note: the per-tile queries do **not** currently filter on `$service_name` /
`$agent_name` — the variables are wired so you can extend any tile (e.g. add
`| filter gen_ai.agent.name in array($agent_name)` to the latency-by-agent
chart). This keeps the default view broad and avoids hiding data when the
variables haven't been touched.

## Caveats

- **Metric tile naming.** Some tiles query the metric as `gen_ai.client.token.usage` (timeseries form) and others as `gen_ai.client.token.usage_sum` (raw `fetch metric.series` form). Both work because OTel histograms ingest as `<name>_sum`, `<name>_count`, `<name>_min`, `<name>_max`, `<name>_bucket_<n>` series in Grail. If a tile returns no data, swap between the two forms.
- **`event.kind` filter on tile 21.** Adjust if you push events with a different `eventType` from `scripts/dt-events.ps1` (the default helper emits `CUSTOM_INFO`).
- **Heatmap tile (13)** uses `bin(duration_s, 1)` — change the bucket size to 0.5 or 5 depending on your typical agent durations.
- **First-run discoverability.** Some tiles will be empty until you've actually generated a report; run `.\tasks.ps1 test-flow` once before screenshotting.

## Iterating

The fastest loop is:

1. Open the dashboard in the Dynatrace UI, tweak a tile, click **Save**.
2. Run `dtctl get db <id> -o json > alpha-report-lab\docs\dashboards\alpha-report-dashboard.json` to round-trip your changes back into the repo.
3. Commit.
