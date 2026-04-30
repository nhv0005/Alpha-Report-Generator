# OneAgent Configuration — Alpha Report Lab (Windows)

## Prerequisites
- Dynatrace OneAgent installed locally on your Windows machine
- Download from: https://docs.dynatrace.com/docs/ingest-from/dynatrace-oneagent/installation
- Run the installer as Administrator

## Verify Process Detection
After starting both services, OneAgent should detect:
- **Python process**: `uvicorn app.main:app` → Process Group: "uvicorn alpha-engine"
- **Node.js process**: `node .next/...` → Process Group: "node alpha-report-frontend"

Verify in: **Observe > Infrastructure > Hosts > [your host] > Processes**.

## Feature Flags

Navigate to: **Settings > Preferences > OneAgent features**.

| # | Feature (search term)              | Required? | Default  | Purpose                                           |
|---|-------------------------------------|-----------|----------|---------------------------------------------------|
| 1 | Python                             | Yes       | Enabled  | Base Python code module injection                  |
| 2 | Node.js                            | Yes       | Enabled  | Base Node.js code module injection                 |
| 3 | Python FastAPI                     | Yes       | Enabled  | Instruments FastAPI/Starlette routes               |
| 4 | Python OpenAI                      | DISABLE   | Enabled  | Disable to avoid duplicate spans with OpenInference|
| 5 | OpenTelemetry (Python) [Opt-In]    | Yes       | Disabled | Required for OpenInference spans to merge          |
| 6 | Node.js HTTP                       | Yes       | Enabled  | Instruments HTTP client/server in Node.js          |
| 7 | W3C Trace Context                  | Yes       | Enabled  | Cross-service trace correlation                    |

## Coexistence Strategy

### Recommended: Disable OneAgent OpenAI Sensor

**Why**: OpenInference creates richer LLM spans than OneAgent's built-in sensor. Keeping both active produces duplicate spans for every OpenAI call.

**Steps (UI)**:
1. Settings > Preferences > OneAgent features
2. Search for "Python OpenAI" → set to OFF (global or per-process-group)
3. Search for "OpenTelemetry (Python)" → set to ON
4. Restart the alpha-engine process

**Settings API (PowerShell)** — disable Python OpenAI sensor:

    $headers = @{ "Authorization" = "Api-Token $env:DT_API_TOKEN"; "Content-Type" = "application/json" }
    $disableOpenAI = @(@{
        schemaId = "builtin:oneagent.features"; schemaVersion = "1.0"; scope = "environment"
        value = @{ key = "PYTHON_OPENAI"; enabled = $false }
    }) | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri "$env:DT_ENV_URL/api/v2/settings/objects" -Method Post -Headers $headers -Body $disableOpenAI

Enable OpenTelemetry (Python) [Opt-In]:

    $enableOtel = @(@{
        schemaId = "builtin:oneagent.features"; schemaVersion = "1.0"; scope = "environment"
        value = @{ key = "PYTHON_OTEL_OPT_IN"; enabled = $true }
    }) | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri "$env:DT_ENV_URL/api/v2/settings/objects" -Method Post -Headers $headers -Body $enableOtel

Verify current feature states:

    Invoke-RestMethod -Uri "$env:DT_ENV_URL/api/v2/settings/objects?schemaIds=builtin:oneagent.features&scopes=environment&fields=objectId,value" -Method Get -Headers $headers | ConvertTo-Json -Depth 5

### Alternative Options

**Keep Both Active**
- Both OneAgent + OpenInference emit spans for each OpenAI call.
- Pros: Full coverage, no config changes needed.
- Cons: 2x span volume for LLM calls, confusing trace view.

**Keep OneAgent, Add Only Custom Agent Spans**
- Keep "Python OpenAI" enabled.
- Don't install openinference-instrumentation-openai.
- Only add manual CHAIN/TOOL/AGENT spans via OTel API.

## Verify OneAgent Injection
1. Observe > Services — look for "alpha-engine" and "alpha-report-frontend"
2. Open alpha-engine service > Properties — confirm OneAgent version
3. Open a distributed trace — verify spans are appearing

If OneAgent is not detecting the Python process:
- `Get-Service -Name "Dynatrace OneAgent"`
- `Get-Process -Name python*`
- OneAgent logs: `C:\ProgramData\dynatrace\oneagent\log\`
