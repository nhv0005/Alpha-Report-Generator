# Task-Runner Observability

Every task invoked through `tasks.ps1` / `tasks.sh` is wrapped with a Dynatrace
**Events API v2** push so you can see in your tenant:

- when a task **started**
- whether it **succeeded** or **failed**
- how **long** it took
- which **host / user / OS** ran it

This complements the per-report OTLP traces emitted by the Python engine.

---

## How it works

- `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\scripts\dt-events.ps1` exposes `Invoke-WithDtEvent`
- `@c:\Users\nicoe.welch\Documents\Windsurf\Alpha Report\alpha-report-lab\scripts-linux\dt-events.sh` exposes `dt_run`

Both dispatchers (`tasks.ps1`, `tasks.sh`) route every task through these
wrappers. The wrapper:

1. Sends a `CUSTOM_INFO` event titled `alpha-report-lab task: <name> started`
2. Runs the actual task
3. On exit, sends a second event:
   - `CUSTOM_INFO` titled `… succeeded (12.3s)` on exit code 0
   - `ERROR_EVENT` titled `… failed (12.3s)` otherwise

Both events carry properties:

| Property | Example |
|---|---|
| `task.name` | `install`, `run-engine`, `test-flow` |
| `task.status` | `started` / `success` / `failure` |
| `task.exit_code` | `0`, `1` |
| `task.duration_seconds` | `12.34` |
| `task.start_utc` / `task.end_utc` | ISO-8601 |
| `task.host` / `task.user` | local hostname / login |
| `task.os` / `task.shell` | `windows`/`powershell`, `linux`/`bash` |
| `lab.component` | `tasks-runner` |
| `lab.script` | `tasks.ps1` / `tasks.sh` |

---

## Prerequisites

The Dynatrace API token in `alpha-engine/.env` must have **two scopes**:

| Scope | Used by |
|---|---|
| `openTelemetryTrace.ingest` | Engine OTLP exporter |
| `events.ingest` | Task-runner observability |

If you re-use the existing token, add the missing scope under
**Access Tokens → Edit token → Scopes**.

If `DT_ENV_URL` or `DT_API_TOKEN` is missing, the wrapper prints a single
`[dt-events] … skipping push.` line and runs the task normally — events are
strictly best-effort and never block work.

---

## DQL — finding task events

```dql
fetch events
| filter event.type == "CUSTOM_INFO" or event.type == "ERROR_EVENT"
| filter lab.component == "tasks-runner"
| fields timestamp, event.type, title, task.name, task.status,
         task.duration_seconds, task.host, task.user
| sort timestamp desc
| limit 50
```

### Average duration per task

```dql
fetch events
| filter lab.component == "tasks-runner"
| filter task.status == "success"
| fieldsAdd dur = toDouble(task.duration_seconds)
| summarize avg_seconds = avg(dur),
            p95_seconds = percentile(dur, 95),
            runs = count(),
            by: { task.name }
| sort runs desc
```

### Recent failures

```dql
fetch events
| filter lab.component == "tasks-runner"
| filter event.type == "ERROR_EVENT"
| fields timestamp, task.name, task.exit_code, task.duration_seconds,
         task.host, task.user, task.error
| sort timestamp desc
```

---

## Disabling

Comment out the `Invoke-WithDtEvent` / `dt_run` calls in `tasks.ps1` /
`tasks.sh`, or simply leave `DT_API_TOKEN` blank — the wrapper becomes a no-op.
