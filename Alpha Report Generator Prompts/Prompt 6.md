# Prompt 6: Run Scripts, OneAgent Coexistence & OpenPipeline Configuration

Create all local run scripts, test scripts, and Dynatrace configuration artifacts.
This prompt does NOT include any Docker, Docker Compose, or container-related content.
Everything runs directly on the local Windows machine via PowerShell.
All scripts must be native Windows PowerShell (.ps1) — do NOT create bash scripts,
shell scripts, or Makefiles.

## Files to Create

### 1. scripts/start-all.ps1
Convenience script to start both services locally:

```powershell
# start-all.ps1 — Start both services (engine in background, frontend in foreground)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$EnginePath = Join-Path $Root "alpha-engine"
$FrontendPath = Join-Path $Root "alpha-frontend"

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  Alpha Report Lab — Starting Services" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# Load engine .env into current process
$envFile = Join-Path $EnginePath ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)\s*$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

$EnginePort = if ($env:ALPHA_ENGINE_PORT) { $env:ALPHA_ENGINE_PORT } else { "8000" }
$FrontendPort = if ($env:ALPHA_FRONTEND_PORT) { $env:ALPHA_FRONTEND_PORT } else { "3000" }

# Start Alpha Engine in a background job
Write-Host "  Starting Alpha Engine on port $EnginePort (background)..." -ForegroundColor Yellow
$engineJob = Start-Job -ScriptBlock {
    param($path, $port)
    Set-Location $path
    uvicorn app.main:app --port $port --reload
} -ArgumentList $EnginePath, $EnginePort

Write-Host "  Engine Job ID: $($engineJob.Id)" -ForegroundColor DarkGray

# Wait for engine to be ready
Write-Host "  Waiting for engine to be ready..." -ForegroundColor DarkGray
$ready = $false
for ($i = 1; $i -le 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$EnginePort/health" -Method Get -ErrorAction SilentlyContinue
        if ($response) {
            Write-Host "  Alpha Engine is ready.`n" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {
        # Still starting up
    }
}

if (-Not $ready) {
    Write-Host "  Warning: Engine may not be ready yet. Check with:" -ForegroundColor Yellow
    Write-Host "    Receive-Job -Id $($engineJob.Id)" -ForegroundColor DarkGray
}

# Start Frontend in foreground
Write-Host "  Starting Alpha Frontend on port $FrontendPort (foreground)..." -ForegroundColor Yellow
Write-Host "  Open http://localhost:$FrontendPort in your browser" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop frontend. Then run: .\tasks.ps1 stop`n" -ForegroundColor DarkGray

Push-Location $FrontendPath
try {
    npm run dev
} finally {
    Pop-Location
    Write-Host "`n  Stopping background engine job..." -ForegroundColor Yellow
    Stop-Job -Id $engineJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $engineJob.Id -Force -ErrorAction SilentlyContinue
    Write-Host "  Stopped." -ForegroundColor Green
}
```

### 2. scripts/stop-all.ps1
Stop all running services:

```powershell
# stop-all.ps1 — Stop all running services
Write-Host "`nStopping Alpha Report Lab services..." -ForegroundColor Cyan

# Stop Python/uvicorn processes
$pythonProcs = Get-Process -Name "python", "python3", "uvicorn" -ErrorAction SilentlyContinue
if ($pythonProcs) {
    $pythonProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Alpha Engine stopped." -ForegroundColor Green
} else {
    Write-Host "  Alpha Engine was not running." -ForegroundColor DarkGray
}

# Stop Node.js / Next.js processes
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    $nodeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Alpha Frontend stopped." -ForegroundColor Green
} else {
    Write-Host "  Alpha Frontend was not running." -ForegroundColor DarkGray
}

# Clean up background PowerShell jobs
$bgJobs = Get-Job | Where-Object { $_.State -eq "Running" }
if ($bgJobs) {
    $bgJobs | Stop-Job -PassThru | Remove-Job -Force
    Write-Host "  Background jobs cleaned up." -ForegroundColor Green
} else {
    Write-Host "  No background jobs found." -ForegroundColor DarkGray
}

Write-Host "  Done.`n" -ForegroundColor Cyan
```

### 3. scripts/test-alpha-flow.ps1
End-to-end test script:

```powershell
# test-alpha-flow.ps1 — End-to-end Alpha Report flow test
$ErrorActionPreference = "Continue"
$EngineUrl = if ($env:ALPHA_ENGINE_PORT) { "http://localhost:$($env:ALPHA_ENGINE_PORT)" } else { "http://localhost:8000" }
$FrontendUrl = if ($env:ALPHA_FRONTEND_PORT) { "http://localhost:$($env:ALPHA_FRONTEND_PORT)" } else { "http://localhost:3000" }

$Pass = 0
$Fail = 0

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Alpha Report Lab — End-to-End Test Suite" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# --- Test 1: Health Checks ---
Write-Host "--- Test 1: Health Checks ---" -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$EngineUrl/health" -Method Get -TimeoutSec 5 | Out-Null
    Write-Host "  [PASS] Alpha Engine: healthy" -ForegroundColor Green
    $Pass++
} catch {
    Write-Host "  [FAIL] Alpha Engine: unreachable — $($_.Exception.Message)" -ForegroundColor Red
    $Fail++
}

try {
    Invoke-RestMethod -Uri "$FrontendUrl/api/health" -Method Get -TimeoutSec 5 | Out-Null
    Write-Host "  [PASS] Alpha Frontend: healthy" -ForegroundColor Green
    $Pass++
} catch {
    Write-Host "  [FAIL] Alpha Frontend: unreachable — $($_.Exception.Message)" -ForegroundColor Red
    $Fail++
}

# --- Test 2: Generate NVDA Report ---
Write-Host "`n--- Test 2: Generate NVDA Report (Aggressive, Short-Term) ---" -ForegroundColor Yellow
$body = @{
    ticker             = "NVDA"
    investment_horizon = "short_term"
    risk_tolerance     = "aggressive"
    user_id            = "test-suite"
} | ConvertTo-Json

$reportId = $null
try {
    $genResponse = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" `
        -Method Post -ContentType "application/json" -Body $body -TimeoutSec 10
    $reportId = $genResponse.report_id
    Write-Host "  [PASS] Report generation started. ID: $reportId" -ForegroundColor Green
    $Pass++
} catch {
    Write-Host "  [FAIL] Could not start generation: $($_.Exception.Message)" -ForegroundColor Red
    $Fail++
}

# --- Test 3: Poll Status Until Complete ---
if ($reportId) {
    Write-Host "`n--- Test 3: Poll Status (timeout: 120s) ---" -ForegroundColor Yellow
    $timeout = 120
    $elapsed = 0
    $status = "pending"

    while ($status -ne "complete" -and $status -ne "error" -and $elapsed -lt $timeout) {
        Start-Sleep -Seconds 5
        $elapsed += 5
        try {
            $statusResponse = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/status/$reportId" `
                -Method Get -TimeoutSec 5
            $status = $statusResponse.status
            $currentStep = $statusResponse.current_step
            Write-Host "  [$($elapsed)s] Status: $status — Step: $currentStep" -ForegroundColor DarkGray
        } catch {
            Write-Host "  [$($elapsed)s] Status poll failed" -ForegroundColor DarkGray
        }
    }

    if ($status -eq "complete") {
        Write-Host "  [PASS] Report complete in $($elapsed)s" -ForegroundColor Green
        $Pass++
    } else {
        Write-Host "  [FAIL] Report did not complete. Final status: $status" -ForegroundColor Red
        $Fail++
    }

    # --- Test 4: Fetch Full Report ---
    Write-Host "`n--- Test 4: Fetch Full Report ---" -ForegroundColor Yellow
    try {
        $report = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports/$reportId" `
            -Method Get -TimeoutSec 10
        $rec = $report.recommendation
        $score = $report.conviction_score
        $sections = $report.sections.Count
        $totalTokens = $report.metadata.total_tokens

        if ($rec -and $sections -gt 0) {
            Write-Host "  [PASS] Report retrieved successfully." -ForegroundColor Green
            Write-Host "     Ticker:         NVDA"
            Write-Host "     Recommendation: $rec"
            Write-Host "     Conviction:     $score / 10"
            Write-Host "     Sections:       $sections"
            Write-Host "     Total Tokens:   $totalTokens"
            $Pass++
        } else {
            Write-Host "  [FAIL] Report data incomplete." -ForegroundColor Red
            $Fail++
        }
    } catch {
        Write-Host "  [FAIL] Could not fetch report: $($_.Exception.Message)" -ForegroundColor Red
        $Fail++
    }
}

# --- Test 5: Generate AAPL Report ---
Write-Host "`n--- Test 5: Generate AAPL Report (Conservative, Long-Term) ---" -ForegroundColor Yellow
$aaplBody = @{
    ticker             = "AAPL"
    investment_horizon = "long_term"
    risk_tolerance     = "conservative"
    user_id            = "test-suite"
} | ConvertTo-Json

try {
    $aaplResponse = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" `
        -Method Post -ContentType "application/json" -Body $aaplBody -TimeoutSec 10
    Write-Host "  [PASS] AAPL report started. ID: $($aaplResponse.report_id)" -ForegroundColor Green
    Write-Host "  (Not waiting for completion — validating list endpoint instead)" -ForegroundColor DarkGray
    $Pass++
} catch {
    Write-Host "  [FAIL] Could not start AAPL report: $($_.Exception.Message)" -ForegroundColor Red
    $Fail++
}

# --- Test 6: List All Reports ---
Write-Host "`n--- Test 6: List All Reports ---" -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $reports = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports" -Method Get -TimeoutSec 10
    $count = if ($reports -is [array]) { $reports.Count } else { 1 }
    if ($count -ge 2) {
        Write-Host "  [PASS] Reports listed: $count reports found." -ForegroundColor Green
        $Pass++
    } else {
        Write-Host "  [FAIL] Expected at least 2 reports, found: $count" -ForegroundColor Red
        $Fail++
    }
} catch {
    Write-Host "  [FAIL] Could not list reports: $($_.Exception.Message)" -ForegroundColor Red
    $Fail++
}

# --- Summary ---
Write-Host "`n============================================" -ForegroundColor Cyan
$summaryColor = if ($Fail -gt 0) { "Red" } else { "Green" }
Write-Host "  Test Summary: $Pass passed, $Fail failed" -ForegroundColor $summaryColor
Write-Host "============================================`n" -ForegroundColor Cyan

if ($Fail -gt 0) { exit 1 }
```

### 4. scripts/test-multi-ticker.ps1
Batch test — generate reports for 5 tickers sequentially:

```powershell
# test-multi-ticker.ps1 — Batch test 5 tickers
$ErrorActionPreference = "Continue"
$EngineUrl = if ($env:ALPHA_ENGINE_PORT) { "http://localhost:$($env:ALPHA_ENGINE_PORT)" } else { "http://localhost:8000" }
$Tickers = @("NVDA", "AAPL", "TSLA", "JPM", "MSFT")

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Multi-Ticker Alpha Report Batch Test" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

$Results = @()

foreach ($ticker in $Tickers) {
    Write-Host "--- Generating report for $ticker ---" -ForegroundColor Yellow
    $startTime = Get-Date

    $body = @{
        ticker             = $ticker
        investment_horizon = "medium_term"
        risk_tolerance     = "moderate"
        user_id            = "batch-test"
    } | ConvertTo-Json

    try {
        $genResponse = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" `
            -Method Post -ContentType "application/json" -Body $body -TimeoutSec 10
        $reportId = $genResponse.report_id

        # Poll until complete (timeout: 180s per ticker)
        $status = "pending"
        $tickerTimeout = 180
        $tickerElapsed = 0
        while ($status -ne "complete" -and $status -ne "error" -and $tickerElapsed -lt $tickerTimeout) {
            Start-Sleep -Seconds 5
            $tickerElapsed += 5
            try {
                $statusResp = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/status/$reportId" `
                    -Method Get -TimeoutSec 5
                $status = $statusResp.status
            } catch {
                # Continue polling
            }
        }

        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)

        if ($status -eq "complete") {
            $report = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports/$reportId" `
                -Method Get -TimeoutSec 10
            $rec = $report.recommendation
            $score = $report.conviction_score
            $tokens = $report.metadata.total_tokens

            Write-Host "  $ticker — $rec (score: $score) — $tokens tokens — $($elapsed)s" -ForegroundColor Green

            $Results += [PSCustomObject]@{
                Ticker         = $ticker
                Recommendation = $rec
                Score          = $score
                Tokens         = $tokens
                "Time(s)"      = $elapsed
            }
        } else {
            Write-Host "  $ticker — FAILED (status: $status after $($elapsed)s)" -ForegroundColor Red
            $Results += [PSCustomObject]@{
                Ticker         = $ticker
                Recommendation = "ERROR"
                Score          = "-"
                Tokens         = "-"
                "Time(s)"      = $elapsed
            }
        }
    } catch {
        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
        Write-Host "  $ticker — FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $Results += [PSCustomObject]@{
            Ticker         = $ticker
            Recommendation = "ERROR"
            Score          = "-"
            Tokens         = "-"
            "Time(s)"      = $elapsed
        }
    }
    Write-Host ""
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Batch Results Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
$Results | Format-Table -AutoSize

# Total tokens
$totalTokens = ($Results | Where-Object { $_.Tokens -ne "-" } | Measure-Object -Property Tokens -Sum).Sum
$totalTime = ($Results | Where-Object { $_."Time(s)" -ne "-" } | Measure-Object -Property "Time(s)" -Sum).Sum
Write-Host "  Total Tokens: $totalTokens" -ForegroundColor Yellow
Write-Host "  Total Time:   $($totalTime)s" -ForegroundColor Yellow
Write-Host ""
```

### 5. docs/oneagent-configuration.md
Step-by-step guide for local OneAgent configuration on Windows:

```markdown
# OneAgent Configuration — Alpha Report Lab (Windows)

## Prerequisites
- Dynatrace OneAgent installed locally on your Windows machine
- Download from: https://docs.dynatrace.com/docs/ingest-from/dynatrace-oneagent/installation
- Run the installer as Administrator

## Verify Process Detection
After starting both services, OneAgent should detect:
- **Python process**: uvicorn app.main:app → Process Group: "uvicorn alpha-engine"
- **Node.js process**: node .next/... → Process Group: "node alpha-report-frontend"

Verify in: Observe > Infrastructure > Hosts > [your host] > Processes

## Feature Flags to Enable/Verify

Navigate to: **Settings > Preferences > OneAgent features**

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

### Recommended: Option A — Disable OneAgent OpenAI Sensor

**Why**: OpenInference creates richer LLM spans than OneAgent's built-in sensor.
Keeping both active creates duplicate spans for every OpenAI call.

**Steps (UI)**:
1. Go to Settings > Preferences > OneAgent features
2. Search for "Python OpenAI"
3. Set to OFF (global) or OFF for the alpha-engine process group
4. Search for "OpenTelemetry (Python)"
5. Set to ON
6. Restart the alpha-engine process (stop and re-run uvicorn)

**Steps (Settings API — PowerShell)**:

Disable Python OpenAI sensor:

    $headers = @{
        "Authorization" = "Api-Token $env:DT_API_TOKEN"
        "Content-Type"  = "application/json"
    }

    $disableOpenAI = @(
        @{
            schemaId      = "builtin:oneagent.features"
            schemaVersion = "1.0"
            scope         = "environment"
            value         = @{
                key     = "PYTHON_OPENAI"
                enabled = $false
            }
        }
    ) | ConvertTo-Json -Depth 5

    Invoke-RestMethod -Uri "$env:DT_ENV_URL/api/v2/settings/objects" `
        -Method Post -Headers $headers -Body $disableOpenAI

Enable OpenTelemetry (Python) [Opt-In]:

    $enableOtel = @(
        @{
            schemaId      = "builtin:oneagent.features"
            schemaVersion = "1.0"
            scope         = "environment"
            value         = @{
                key     = "PYTHON_OTEL_OPT_IN"
                enabled = $true
            }
        }
    ) | ConvertTo-Json -Depth 5

    Invoke-RestMethod -Uri "$env:DT_ENV_URL/api/v2/settings/objects" `
        -Method Post -Headers $headers -Body $enableOtel

Verify current feature states:

    Invoke-RestMethod -Uri "$env:DT_ENV_URL/api/v2/settings/objects?schemaIds=builtin:oneagent.features&scopes=environment&fields=objectId,value" `
        -Method Get -Headers $headers | ConvertTo-Json -Depth 5

### Alternative Options

**Option B: Keep Both Active**
- Both OneAgent + OpenInference create spans for each OpenAI call
- Pros: Full coverage, no config changes needed
- Cons: 2x span volume for LLM calls, confusing trace view
- When to choose: Quick testing, don't want to touch OneAgent settings

**Option C: Keep OneAgent, Add Only Custom Agent Spans**
- Keep "Python OpenAI" enabled
- Don't install openinference-instrumentation-openai
- Only add manual CHAIN/TOOL/AGENT spans via OTel API
- Pros: Minimal change, no duplication
- Cons: Still missing prompt/completion content on LLM spans

## Verify OneAgent Injection (Windows)
After restarting services, confirm in Dynatrace:
1. Observe > Services — look for "alpha-engine" and "alpha-report-frontend"
2. Open alpha-engine service > Properties — confirm OneAgent version
3. Open a distributed trace — verify spans are appearing

If OneAgent is not detecting the Python process, check:
- OneAgent service is running: Get-Service -Name "Dynatrace OneAgent" in PowerShell
- Python process is visible: Get-Process -Name python* in PowerShell
- OneAgent logs: C:\ProgramData\dynatrace\oneagent\log\
```

### 6. docs/openpipeline-configuration.md
OpenPipeline attribute rename rules:

```markdown
# OpenPipeline Configuration — OpenInference to Dynatrace AI Obs Attribute Mapping

## Why This Is Needed
OpenInference emits span attributes under the llm.* namespace.
Dynatrace's AI Observability Explorer expects the gen_ai.prompt.* / gen_ai.completion.*
namespace to populate the Prompt and Completion sections.

OpenPipeline's fieldsRename processor bridges this gap at ingestion time.

## Configuration Steps

### Step 1: Navigate to OpenPipeline
Settings > Process and contextualize > OpenPipeline > Spans

### Step 2: Create a Custom Processing Rule
- **Rule name**: OpenInference to GenAI Attribute Mapping
- **Matcher**: matchesValue(openinference.span.kind, "LLM") OR isNotNull(llm.model_name)
- **Processor type**: fieldsRename

### Step 3: Field Rename Mappings

| #  | Source (OpenInference)                    | Target (Dynatrace AI Obs)        |
|----|------------------------------------------|----------------------------------|
| 1  | llm.input_messages.0.message.content     | gen_ai.prompt.0.content          |
| 2  | llm.input_messages.0.message.role        | gen_ai.prompt.0.role             |
| 3  | llm.input_messages.1.message.content     | gen_ai.prompt.1.content          |
| 4  | llm.input_messages.1.message.role        | gen_ai.prompt.1.role             |
| 5  | llm.input_messages.2.message.content     | gen_ai.prompt.2.content          |
| 6  | llm.input_messages.2.message.role        | gen_ai.prompt.2.role             |
| 7  | llm.input_messages.3.message.content     | gen_ai.prompt.3.content          |
| 8  | llm.input_messages.3.message.role        | gen_ai.prompt.3.role             |
| 9  | llm.input_messages.4.message.content     | gen_ai.prompt.4.content          |
| 10 | llm.input_messages.4.message.role        | gen_ai.prompt.4.role             |
| 11 | llm.input_messages.5.message.content     | gen_ai.prompt.5.content          |
| 12 | llm.input_messages.5.message.role        | gen_ai.prompt.5.role             |
| 13 | llm.input_messages.6.message.content     | gen_ai.prompt.6.content          |
| 14 | llm.input_messages.6.message.role        | gen_ai.prompt.6.role             |
| 15 | llm.input_messages.7.message.content     | gen_ai.prompt.7.content          |
| 16 | llm.input_messages.7.message.role        | gen_ai.prompt.7.role             |
| 17 | llm.input_messages.8.message.content     | gen_ai.prompt.8.content          |
| 18 | llm.input_messages.8.message.role        | gen_ai.prompt.8.role             |
| 19 | llm.input_messages.9.message.content     | gen_ai.prompt.9.content          |
| 20 | llm.input_messages.9.message.role        | gen_ai.prompt.9.role             |
| 21 | llm.output_messages.0.message.content    | gen_ai.completion.0.content      |
| 22 | llm.output_messages.0.message.role       | gen_ai.completion.0.role         |
| 23 | llm.output_messages.1.message.content    | gen_ai.completion.1.content      |
| 24 | llm.output_messages.1.message.role       | gen_ai.completion.1.role         |
| 25 | llm.model_name                           | gen_ai.request.model             |
| 26 | llm.token_count.prompt                   | gen_ai.usage.input_tokens        |
| 27 | llm.token_count.completion               | gen_ai.usage.output_tokens       |

### Step 4: Automate via Settings API (PowerShell)

    $headers = @{
        "Authorization" = "Api-Token $env:DT_API_TOKEN"
        "Content-Type"  = "application/json"
    }

    # Verify OpenPipeline is accessible
    Invoke-RestMethod -Uri "$env:DT_ENV_URL/api/v2/settings/schemas/builtin:openpipeline" `
        -Method Get -Headers $headers | ConvertTo-Json -Depth 3

Note: OpenPipeline configuration is best done through the Dynatrace UI for complex
fieldsRename rules with multiple mappings. Use the UI steps above for initial setup,
then export via Settings API for automation.

### Step 5: Validation DQL Queries

Confirm rename is working (run in Dynatrace Notebooks):

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter isNotNull(gen_ai.prompt.0.content)
    | fields span.name, gen_ai.prompt.0.role, gen_ai.prompt.0.content,
             gen_ai.completion.0.content, gen_ai.usage.input_tokens
    | limit 5

Compare source and target on same span:

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter isNotNull(llm.model_name)
    | fields span.name, llm.model_name, gen_ai.request.model,
             llm.token_count.prompt, gen_ai.usage.input_tokens
    | limit 5
```

### 7. docs/validate-dynatrace.md
Post-test validation checklist:

```markdown
# Dynatrace Validation Checklist — Alpha Report Lab

After running .\tasks.ps1 test-flow, follow this checklist to validate
instrumentation in Dynatrace.

## 1. Service Detection
- [ ] Navigate to: Observe > Services
- [ ] Confirm "alpha-engine" service appears
- [ ] Confirm "alpha-report-frontend" service appears

## 2. Distributed Traces
- [ ] Navigate to: Observe > Distributed traces
- [ ] Filter by service: "alpha-engine"
- [ ] Open a trace from a report generation request
- [ ] Confirm trace spans BOTH services (Next.js to Python)
- [ ] Confirm span tree is 3-4 levels deep with 20-30 spans

## 3. AI Observability Explorer
- [ ] Navigate to: Observe > AI Observability
- [ ] Confirm "alpha-engine" appears as an AI service
- [ ] Click into the service — verify model breakdown
- [ ] Verify token usage charts populate

## 4. Span Attributes — OpenInference
- [ ] Open a trace > select an openai.chat span
- [ ] Confirm openinference.span.kind = "LLM"
- [ ] Confirm llm.input_messages.0.message.content has prompt text
- [ ] Confirm llm.output_messages.0.message.content has completion text
- [ ] Confirm llm.model_name is set
- [ ] Confirm llm.token_count.prompt and llm.token_count.completion are set
- [ ] Confirm llm.invocation_parameters contains temperature, model, etc.
- [ ] Confirm session.id and user.id are present
- [ ] Confirm tag.tags contains alpha-report and ticker values

## 5. Span Tree Structure
- [ ] Verify alpha_orchestrator span (AGENT) is the root AI span
- [ ] Under it: research_agent, analysis_agent, sentiment_agent,
      risk_agent, writer_agent (all CHAIN)
- [ ] Under each agent: tool:* spans (TOOL) and openai.chat spans (LLM)

## 6. OpenPipeline Rename (if configured)
- [ ] Open AI Observability Explorer > select a trace > Prompt tab
- [ ] Confirm prompt content is displayed (not empty)
- [ ] Confirm completion content is displayed

## 7. DQL Validation
Run these in Observe > Notebooks:

OpenInference span kind breakdown:

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

End-to-end traces:

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter span.name == "alpha_orchestrator"
    | filter start_time > now() - 1h
    | fields trace.id, duration, session.id, tag.tags
    | sort start_time desc
    | limit 10

Tool execution analysis:

    fetch spans
    | filter dt.service.name == "alpha-engine"
    | filter openinference.span.kind == "TOOL"
    | summarize avg_duration = avg(duration),
                calls = count(),
                by: {tool.name}
    | sort calls desc

## 8. Troubleshooting Quick Reference

**No spans at all from Python:**
- Verify OneAgent service: Get-Service -Name "Dynatrace OneAgent"
- Verify Python detected: check Observe > Infrastructure > Hosts > Processes
- Check OneAgent logs: C:\ProgramData\dynatrace\oneagent\log\

**OpenInference spans missing:**
- Verify "OpenTelemetry (Python) [Opt-In]" is enabled
- Verify OTLP endpoint in .env is correct
- Verify API token has openTelemetryTrace.ingest scope
- Verify instrumentation.py is imported BEFORE OpenAI client

**Duplicate LLM spans:**
- Disable "Python OpenAI" in OneAgent features

**Prompt section empty after OpenInference:**
- Check OPENINFERENCE_HIDE_INPUTS is not true in .env
- Verify OpenPipeline rename rules are active
- Run DQL to confirm llm.input_messages.0.message.content exists

**Traces not connecting Next.js to Python:**
- Verify W3C Trace Context is enabled in OneAgent features
- Verify Next.js API routes forward traceparent/tracestate headers
- Check headers in Python: log request.headers in FastAPI middleware
```

### 8. UPDATE: tasks.ps1
Add the new script targets to the existing tasks.ps1 from Prompt 1.

Add these entries to the ValidateSet and switch block in tasks.ps1:

```powershell
# Add to the ValidateSet parameter:
# "start", "stop-all", "test-flow", "test-batch"

# Add to the switch block:
    "start"         { & "$ScriptsDir\start-all.ps1" }
    "stop-all"      { & "$ScriptsDir\stop-all.ps1" }
    "test-flow"     { & "$ScriptsDir\test-alpha-flow.ps1" }
    "test-batch"    { & "$ScriptsDir\test-multi-ticker.ps1" }

# Add to the help output:
    Write-Host "    start          Start both services (engine bg, frontend fg)"
    Write-Host "    stop-all       Stop all running services and background jobs"
    Write-Host "    test-flow      Full end-to-end flow test with polling"
    Write-Host "    test-batch     Batch test 5 tickers sequentially"
```

The complete updated ValidateSet should be:

```powershell
[ValidateSet(
    "setup", "install",
    "run-engine", "run-frontend", "run-all", "start", "stop", "stop-all",
    "test-health", "test-generate", "test-flow", "test-batch",
    "clean", "help"
)]
```

### 9. UPDATE: README.md
Replace any bash/Makefile usage sections with PowerShell equivalents:

```markdown
## Running the Lab (Windows PowerShell)

All tasks are managed through tasks.ps1 at the project root.

### First Time Setup

    .\tasks.ps1 setup          # Create .env files from templates
    # Edit .env with your API keys and Dynatrace credentials
    .\tasks.ps1 install        # Install Python + Node.js dependencies

### Start Services

    .\tasks.ps1 start          # Start both (engine background, frontend foreground)
    .\tasks.ps1 run-engine     # Start Python engine only
    .\tasks.ps1 run-frontend   # Start Next.js frontend only
    .\tasks.ps1 stop           # Stop foreground services
    .\tasks.ps1 stop-all       # Stop all services and background jobs

### Run Tests

    .\tasks.ps1 test-health    # Health check both services
    .\tasks.ps1 test-generate  # Generate a single NVDA report
    .\tasks.ps1 test-flow      # Full end-to-end flow test with polling
    .\tasks.ps1 test-batch     # Batch test 5 tickers sequentially

### Maintenance

    .\tasks.ps1 clean          # Remove build artifacts
    .\tasks.ps1 help           # Show all available tasks

### PowerShell Execution Policy
If you get an execution policy error, run this once in an elevated PowerShell:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

### OneAgent Configuration
See docs/oneagent-configuration.md for full setup instructions including
Settings API automation via PowerShell.

### OpenPipeline Setup
See docs/openpipeline-configuration.md for attribute rename rules.

### Validation
See docs/validate-dynatrace.md for the post-test checklist and DQL queries.
```

Produce ALL files with complete content. Do NOT create any bash scripts (.sh),
shell scripts, Makefiles, or Docker-related files. All scripts must be
Windows PowerShell (.ps1) only.