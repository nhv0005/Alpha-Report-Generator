# Prompt 1: Project Structure & Scaffolding

Create the full project directory structure, all configuration files, and dependency
manifests for the Alpha Report Generator Instrumentation Lab. Do NOT create
application code yet — only scaffolding, dependencies, and configuration.

## Requirements

### 1. Directory Structure
Create under {{PROJECT_ROOT}}:

```
alpha-report-lab/
├── alpha-frontend/                        ← Next.js 14+ App Router
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── .env.local.example
│   ├── .gitignore
│   ├── public/
│   │   └── logo.svg                       ← Simple placeholder logo
│   └── src/
│       ├── app/
│       │   ├── layout.tsx                  ← Root layout (dark theme)
│       │   ├── page.tsx                    ← Dashboard home
│       │   ├── globals.css                 ← Tailwind + custom styles
│       │   ├── reports/
│       │   │   ├── page.tsx                ← Report history list
│       │   │   └── [id]/
│       │   │       └── page.tsx            ← Individual report viewer
│       │   ├── generate/
│       │   │   └── page.tsx                ← Report builder form
│       │   └── api/
│       │       ├── alpha/
│       │       │   ├── generate/route.ts   ← Proxy to Python /api/alpha/generate
│       │       │   ├── status/[id]/route.ts← Proxy to Python /api/alpha/status/:id
│       │       │   └── reports/route.ts    ← Proxy to Python /api/alpha/reports
│       │       └── health/route.ts         ← Combined health check
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx             ← Navigation sidebar
│       │   │   ├── Header.tsx              ← Top header bar
│       │   │   └── StatusBar.tsx           ← Service health indicators
│       │   ├── reports/
│       │   │   ├── ReportCard.tsx           ← Report summary card
│       │   │   ├── ReportViewer.tsx         ← Full report renderer
│       │   │   ├── ReportSection.tsx        ← Individual report section
│       │   │   ├── ScoreGauge.tsx           ← Conviction score gauge
│       │   │   └── MetricsTable.tsx         ← Financial metrics table
│       │   ├── generate/
│       │   │   ├── GenerateForm.tsx         ← Report generation form
│       │   │   ├── TickerInput.tsx          ← Ticker symbol input with validation
│       │   │   └── ProgressTracker.tsx      ← Multi-step generation progress
│       │   └── ui/
│       │       ├── Badge.tsx                ← Status badges
│       │       ├── Card.tsx                 ← Reusable card component
│       │       ├── Skeleton.tsx             ← Loading skeletons
│       │       └── SparkChart.tsx           ← Mini inline chart
│       ├── lib/
│       │   ├── api.ts                       ← API client for Python backend
│       │   ├── types.ts                     ← TypeScript interfaces
│       │   └── utils.ts                     ← Formatting helpers (currency, %, dates)
│       └── hooks/
│           ├── useReport.ts                 ← Report fetching hook
│           └── useGenerateReport.ts         ← Generation with polling hook
│
├── alpha-engine/                            ← Python FastAPI AI Service
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   └── app/
│       ├── __init__.py
│       ├── main.py                          ← FastAPI entry point
│       ├── config.py                        ← Environment config
│       ├── instrumentation.py               ← OpenInference + OTel setup
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── alpha.py                     ← Alpha report endpoints
│       │   ├── health.py                    ← Health check
│       │   └── embeddings.py                ← Embedding endpoint
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── orchestrator.py              ← Multi-agent orchestrator
│       │   ├── research_agent.py            ← Market data & company research
│       │   ├── analysis_agent.py            ← Fundamental & technical analysis
│       │   ├── sentiment_agent.py           ← News & sentiment analysis
│       │   ├── risk_agent.py                ← Risk assessment agent
│       │   └── writer_agent.py              ← Report composition agent
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── market_data.py               ← Mock market data tool
│       │   ├── financial_metrics.py         ← Mock financial metrics tool
│       │   ├── news_search.py               ← Mock news search tool
│       │   └── peer_comparison.py           ← Mock peer comparison tool
│       ├── services/
│       │   ├── __init__.py
│       │   ├── report_store.py              ← In-memory report storage
│       │   └── context.py                   ← Session/report context manager
│       └── models/
│           ├── __init__.py
│           ├── schemas.py                   ← Pydantic request/response models
│           └── report.py                    ← Alpha Report data model
│
├── Makefile                                 ← Convenience commands (local only)
├── README.md                                ← Setup & run instructions
└── .env.example                             ← Root-level env template
```

### 2. package.json (Next.js Frontend)
- name: "alpha-report-frontend"
- Dependencies: next@14, react@18, react-dom@18, tailwindcss, @tailwindcss/typography,
  lucide-react (icons), clsx, date-fns, uuid
- Dev dependencies: typescript, @types/react, @types/node, autoprefixer, postcss
- Scripts: dev, build, start, lint

### 3. requirements.txt (Python Alpha Engine)
- fastapi[standard]
- uvicorn[standard]
- openai>=1.30
- python-dotenv
- pydantic>=2.0
- openinference-instrumentation-openai
- openinference-instrumentation
- openinference-semantic-conventions
- opentelemetry-sdk
- opentelemetry-exporter-otlp-proto-http
- opentelemetry-api
- httpx

### 4. TypeScript interfaces (src/lib/types.ts)
Define comprehensive TypeScript types:

```typescript
// Core report types
interface AlphaReport {
  id: string;
  ticker: string;
  company_name: string;
  sector: string;
  generated_at: string;
  status: "pending" | "researching" | "analyzing" | "writing" | "complete" | "error";
  recommendation: "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL";
  conviction_score: number;       // 1-10
  target_price: number;
  current_price: number;
  upside_percentage: number;
  risk_rating: "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";
  sections: ReportSection[];
  metadata: ReportMetadata;
}

interface ReportSection {
  id: string;
  title: string;
  type: "executive_summary" | "company_overview" | "fundamental_analysis"
       | "technical_analysis" | "catalysts" | "risk_assessment"
       | "competitive_landscape" | "sentiment" | "recommendation" | "appendix";
  content: string;                 // Markdown content
  data?: Record<string, any>;      // Structured data (metrics, tables)
  agent: string;                   // Which agent produced this section
  tokens_used: number;
  generation_time_ms: number;
}

interface ReportMetadata {
  session_id: string;
  user_id: string;
  model: string;
  total_tokens: number;
  total_generation_time_ms: number;
  agents_used: string[];
  tools_called: string[];
  trace_id?: string;
}

// Generation types
interface GenerateRequest {
  ticker: string;
  investment_horizon: "short_term" | "medium_term" | "long_term";
  risk_tolerance: "conservative" | "moderate" | "aggressive";
  focus_areas?: string[];
  custom_instructions?: string;
  user_id?: string;
}

interface GenerationProgress {
  report_id: string;
  status: string;
  current_step: string;
  steps_completed: number;
  total_steps: number;
  current_agent: string;
  elapsed_time_ms: number;
}

// Financial data types
interface FinancialMetrics {
  market_cap: number;
  pe_ratio: number;
  forward_pe: number;
  peg_ratio: number;
  price_to_book: number;
  ev_to_ebitda: number;
  revenue_ttm: number;
  revenue_growth_yoy: number;
  gross_margin: number;
  operating_margin: number;
  net_margin: number;
  roe: number;
  debt_to_equity: number;
  current_ratio: number;
  free_cash_flow: number;
  dividend_yield: number;
  beta: number;
  fifty_two_week_high: number;
  fifty_two_week_low: number;
}

interface PeerComparison {
  ticker: string;
  company_name: string;
  market_cap: number;
  pe_ratio: number;
  revenue_growth: number;
  margin: number;
}

interface SentimentData {
  overall_score: number;          // -1.0 to 1.0
  news_sentiment: number;
  social_sentiment: number;
  analyst_consensus: string;
  analyst_target_price: number;
  recent_headlines: { title: string; sentiment: string; source: string; date: string }[];
}
```

### 5. .env.example files
Create for both apps with all required environment variables.

**Root .env.example:**

```env
# ============================================
# Alpha Report Lab — Environment Configuration
# ============================================

# --- OpenAI ---
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
OPENAI_FAST_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# --- Dynatrace ---
DT_ENV_URL=https://YOUR_ENV_ID.live.dynatrace.com
DT_API_TOKEN=dt0c01.YOUR_TOKEN_HERE

# --- App ---
PYTHON_SERVICE_URL=http://localhost:8000
ALPHA_ENGINE_PORT=8000
ALPHA_FRONTEND_PORT=3000
LOG_LEVEL=info

# --- OpenInference Privacy Controls ---
OPENINFERENCE_HIDE_INPUTS=false
OPENINFERENCE_HIDE_OUTPUTS=false
OPENINFERENCE_HIDE_INPUT_IMAGES=true
OPENINFERENCE_HIDE_EMBEDDING_VECTORS=true
OPENINFERENCE_HIDE_LLM_INVOCATION_PARAMETERS=false
```

**alpha-frontend/.env.local.example:**

```env
PYTHON_SERVICE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Alpha Report Lab
```

**alpha-engine/.env.example:**

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
OPENAI_FAST_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
DT_ENV_URL=https://YOUR_ENV_ID.live.dynatrace.com
DT_API_TOKEN=dt0c01.YOUR_TOKEN_HERE
SERVICE_NAME=alpha-engine
PORT=8000
LOG_LEVEL=info
OPENINFERENCE_HIDE_INPUTS=false
OPENINFERENCE_HIDE_OUTPUTS=false
OPENINFERENCE_HIDE_INPUT_IMAGES=true
OPENINFERENCE_HIDE_EMBEDDING_VECTORS=true
OPENINFERENCE_HIDE_LLM_INVOCATION_PARAMETERS=false
```

### 6. Tailwind config
- Dark theme by default
- Custom colors: alpha-green (#10B981), alpha-red (#EF4444), alpha-gold (#F59E0B),
  alpha-blue (#3B82F6)
- Typography plugin enabled for report content rendering

### 7. Makefile (Local Only — No Docker)
### 7. Task Runner & PowerShell Scripts (Windows PowerShell — No Makefile)

Since the local environment is **Windows with PowerShell in Windsurf**, do NOT create
a Makefile. Instead, create PowerShell scripts in a `scripts/` directory and a root
`tasks.ps1` task runner.

#### Directory Addition

```
alpha-report-lab/
├── tasks.ps1                              ← Root task runner (replaces Makefile)
├── scripts/
│   ├── setup.ps1                          ← Create .env files, print instructions
│   ├── install.ps1                        ← Install all dependencies
│   ├── start-engine.ps1                   ← Start Python Alpha Engine
│   ├── start-frontend.ps1                 ← Start Next.js Frontend
│   ├── start-all.ps1                      ← Start both services
│   ├── stop-all.ps1                       ← Stop all running services
│   ├── test-health.ps1                    ← Health check both services
│   ├── test-generate.ps1                  ← Generate a single NVDA report
│   ├── test-full-flow.ps1                 ← End-to-end flow with polling
│   ├── test-multi-ticker.ps1              ← Batch test 5 tickers
│   └── clean.ps1                          ← Remove build artifacts
```

#### tasks.ps1 (Root Task Runner)

```powershell
# tasks.ps1 — Alpha Report Lab Task Runner
# Usage: .\tasks.ps1 <task>
# Example: .\tasks.ps1 setup
#          .\tasks.ps1 run-all
#          .\tasks.ps1 test-flow

param(
    [Parameter(Position=0)]
    [ValidateSet(
        "setup", "install",
        "run-engine", "run-frontend", "run-all", "stop",
        "test-health", "test-generate", "test-flow", "test-batch",
        "clean", "help"
    )]
    [string]$Task = "help"
)

$ErrorActionPreference = "Stop"
$ScriptsDir = Join-Path $PSScriptRoot "scripts"

switch ($Task) {
    "setup"         { & "$ScriptsDir\setup.ps1" }
    "install"       { & "$ScriptsDir\install.ps1" }
    "run-engine"    { & "$ScriptsDir\start-engine.ps1" }
    "run-frontend"  { & "$ScriptsDir\start-frontend.ps1" }
    "run-all"       { & "$ScriptsDir\start-all.ps1" }
    "stop"          { & "$ScriptsDir\stop-all.ps1" }
    "test-health"   { & "$ScriptsDir\test-health.ps1" }
    "test-generate" { & "$ScriptsDir\test-generate.ps1" }
    "test-flow"     { & "$ScriptsDir\test-full-flow.ps1" }
    "test-batch"    { & "$ScriptsDir\test-multi-ticker.ps1" }
    "clean"         { & "$ScriptsDir\clean.ps1" }
    "help" {
        Write-Host ""
        Write-Host "=========================================" -ForegroundColor Cyan
        Write-Host "  Alpha Report Lab — Task Runner" -ForegroundColor Cyan
        Write-Host "=========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\tasks.ps1 <task>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Setup & Install:" -ForegroundColor Green
        Write-Host "    setup          Create .env files from templates"
        Write-Host "    install        Install Python + Node.js dependencies"
        Write-Host ""
        Write-Host "  Run:" -ForegroundColor Green
        Write-Host "    run-engine     Start Python Alpha Engine (port 8000)"
        Write-Host "    run-frontend   Start Next.js Frontend (port 3000)"
        Write-Host "    run-all        Start both services"
        Write-Host "    stop           Stop all running services"
        Write-Host ""
        Write-Host "  Test:" -ForegroundColor Green
        Write-Host "    test-health    Health check both services"
        Write-Host "    test-generate  Generate a single NVDA report"
        Write-Host "    test-flow      End-to-end flow test with polling"
        Write-Host "    test-batch     Batch test 5 tickers sequentially"
        Write-Host ""
        Write-Host "  Maintenance:" -ForegroundColor Green
        Write-Host "    clean          Remove build artifacts"
        Write-Host "    help           Show this help message"
        Write-Host ""
    }
}
```

#### scripts/setup.ps1

```powershell
# setup.ps1 — Create .env files from examples
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  Alpha Report Lab — Setup" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

$Root = Split-Path $PSScriptRoot -Parent

# Copy .env files if they don't exist
$envMappings = @(
    @{ Source = ".env.example";                     Target = ".env" },
    @{ Source = "alpha-engine\.env.example";        Target = "alpha-engine\.env" },
    @{ Source = "alpha-frontend\.env.local.example"; Target = "alpha-frontend\.env.local" }
)

foreach ($mapping in $envMappings) {
    $src = Join-Path $Root $mapping.Source
    $dst = Join-Path $Root $mapping.Target
    if (-Not (Test-Path $dst)) {
        if (Test-Path $src) {
            Copy-Item $src $dst
            Write-Host "  Created: $($mapping.Target)" -ForegroundColor Green
        } else {
            Write-Host "  Warning: $($mapping.Source) not found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Exists:  $($mapping.Target) (skipped)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "    1. Edit .env with your OpenAI API key and Dynatrace credentials"
Write-Host "    2. Run: .\tasks.ps1 install"
Write-Host "    3. Run: .\tasks.ps1 run-all"
Write-Host ""
```

#### scripts/install.ps1

```powershell
# install.ps1 — Install all dependencies
$Root = Split-Path $PSScriptRoot -Parent

Write-Host "`nInstalling Python dependencies..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "alpha-engine")
pip install -r requirements.txt
Pop-Location

Write-Host "`nInstalling Node.js dependencies..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "alpha-frontend")
npm install
Pop-Location

Write-Host "`n  All dependencies installed." -ForegroundColor Green
```

#### scripts/start-engine.ps1

```powershell
# start-engine.ps1 — Start Python Alpha Engine
$Root = Split-Path $PSScriptRoot -Parent
$EnginePath = Join-Path $Root "alpha-engine"

# Load .env if present
$envFile = Join-Path $EnginePath ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)\s*$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

$Port = if ($env:ALPHA_ENGINE_PORT) { $env:ALPHA_ENGINE_PORT } else { "8000" }

Write-Host "`n  Starting Alpha Engine on port $Port..." -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop.`n" -ForegroundColor DarkGray

Push-Location $EnginePath
uvicorn app.main:app --port $Port --reload
Pop-Location
```

#### scripts/start-frontend.ps1

```powershell
# start-frontend.ps1 — Start Next.js Frontend
$Root = Split-Path $PSScriptRoot -Parent
$FrontendPath = Join-Path $Root "alpha-frontend"

$Port = if ($env:ALPHA_FRONTEND_PORT) { $env:ALPHA_FRONTEND_PORT } else { "3000" }

Write-Host "`n  Starting Alpha Frontend on port $Port..." -ForegroundColor Cyan
Write-Host "  Open http://localhost:$Port in your browser" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop.`n" -ForegroundColor DarkGray

Push-Location $FrontendPath
npm run dev
Pop-Location
```

#### scripts/start-all.ps1

```powershell
# start-all.ps1 — Start both services (engine in background, frontend in foreground)
$Root = Split-Path $PSScriptRoot -Parent
$EnginePath = Join-Path $Root "alpha-engine"
$FrontendPath = Join-Path $Root "alpha-frontend"

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  Alpha Report Lab — Starting Services" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# Load engine .env
$envFile = Join-Path $EnginePath ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)\s*$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
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
    Write-Host "  Warning: Engine may not be ready yet. Check job output with:" -ForegroundColor Yellow
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

#### scripts/stop-all.ps1

```powershell
# stop-all.ps1 — Stop all running services
Write-Host "`nStopping Alpha Report Lab services..." -ForegroundColor Cyan

# Stop uvicorn processes
$uvicornProcs = Get-Process -Name "uvicorn", "python" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*app.main:app*" -or $_.CommandLine -like "*uvicorn*" }

if ($uvicornProcs) {
    $uvicornProcs | Stop-Process -Force
    Write-Host "  Alpha Engine stopped." -ForegroundColor Green
} else {
    Write-Host "  Alpha Engine was not running." -ForegroundColor DarkGray
}

# Stop Node.js / Next.js processes
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*next*" -or $_.CommandLine -like "*alpha-frontend*" }

if ($nodeProcs) {
    $nodeProcs | Stop-Process -Force
    Write-Host "  Alpha Frontend stopped." -ForegroundColor Green
} else {
    Write-Host "  Alpha Frontend was not running." -ForegroundColor DarkGray
}

# Clean up background jobs
Get-Job | Where-Object { $_.State -eq "Running" } | Stop-Job -PassThru | Remove-Job -Force
Write-Host "  Background jobs cleaned up." -ForegroundColor Green

Write-Host "  Done.`n" -ForegroundColor Cyan
```

#### scripts/test-health.ps1

```powershell
# test-health.ps1 — Health check both services
$EngineUrl = if ($env:ALPHA_ENGINE_PORT) { "http://localhost:$($env:ALPHA_ENGINE_PORT)" } else { "http://localhost:8000" }
$FrontendUrl = if ($env:ALPHA_FRONTEND_PORT) { "http://localhost:$($env:ALPHA_FRONTEND_PORT)" } else { "http://localhost:3000" }

Write-Host "`n--- Alpha Engine Health ---" -ForegroundColor Cyan
try {
    $engineHealth = Invoke-RestMethod -Uri "$EngineUrl/health" -Method Get
    $engineHealth | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Green
} catch {
    Write-Host "  UNREACHABLE: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n--- Alpha Frontend Health ---" -ForegroundColor Cyan
try {
    $frontendHealth = Invoke-RestMethod -Uri "$FrontendUrl/api/health" -Method Get
    $frontendHealth | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Green
} catch {
    Write-Host "  UNREACHABLE: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""
```

#### scripts/test-generate.ps1

```powershell
# test-generate.ps1 — Generate a single NVDA report
$EngineUrl = if ($env:ALPHA_ENGINE_PORT) { "http://localhost:$($env:ALPHA_ENGINE_PORT)" } else { "http://localhost:8000" }

Write-Host "`nGenerating NVDA Alpha Report..." -ForegroundColor Cyan

$body = @{
    ticker              = "NVDA"
    investment_horizon  = "medium_term"
    risk_tolerance      = "moderate"
    user_id             = "lab-tester"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body

    Write-Host "  Report generation started." -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3 | Write-Host
    Write-Host "`n  Track status with:" -ForegroundColor Yellow
    Write-Host "    Invoke-RestMethod http://localhost:8000/api/alpha/status/$($response.report_id)" -ForegroundColor DarkGray
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""
```

#### scripts/test-full-flow.ps1

```powershell
# test-full-flow.ps1 — End-to-end flow test with polling
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
    Invoke-RestMethod -Uri "$EngineUrl/health" -Method Get | Out-Null
    Write-Host "  [PASS] Alpha Engine: healthy" -ForegroundColor Green
    $Pass++
} catch {
    Write-Host "  [FAIL] Alpha Engine: unreachable" -ForegroundColor Red
    $Fail++
}

try {
    Invoke-RestMethod -Uri "$FrontendUrl/api/health" -Method Get | Out-Null
    Write-Host "  [PASS] Alpha Frontend: healthy" -ForegroundColor Green
    $Pass++
} catch {
    Write-Host "  [FAIL] Alpha Frontend: unreachable" -ForegroundColor Red
    $Fail++
}

# --- Test 2: Generate NVDA Report ---
Write-Host "`n--- Test 2: Generate NVDA Report ---" -ForegroundColor Yellow
$body = @{
    ticker             = "NVDA"
    investment_horizon = "short_term"
    risk_tolerance     = "aggressive"
    user_id            = "test-suite"
} | ConvertTo-Json

try {
    $genResponse = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" `
        -Method Post -ContentType "application/json" -Body $body
    $reportId = $genResponse.report_id
    Write-Host "  [PASS] Report generation started. ID: $reportId" -ForegroundColor Green
    $Pass++
} catch {
    Write-Host "  [FAIL] Could not start generation: $($_.Exception.Message)" -ForegroundColor Red
    $Fail++
    $reportId = $null
}

# --- Test 3: Poll Status ---
if ($reportId) {
    Write-Host "`n--- Test 3: Poll Status (timeout: 120s) ---" -ForegroundColor Yellow
    $timeout = 120
    $elapsed = 0
    $status = "pending"

    while ($status -ne "complete" -and $status -ne "error" -and $elapsed -lt $timeout) {
        Start-Sleep -Seconds 5
        $elapsed += 5
        try {
            $statusResponse = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/status/$reportId" -Method Get
            $status = $statusResponse.status
            $currentStep = $statusResponse.current_step
            Write-Host "  [$elapsed s] Status: $status — Step: $currentStep" -ForegroundColor DarkGray
        } catch {
            Write-Host "  [$elapsed s] Status poll failed" -ForegroundColor DarkGray
        }
    }

    if ($status -eq "complete") {
        Write-Host "  [PASS] Report complete in ${elapsed}s" -ForegroundColor Green
        $Pass++
    } else {
        Write-Host "  [FAIL] Report did not complete. Final status: $status" -ForegroundColor Red
        $Fail++
    }

    # --- Test 4: Fetch Full Report ---
    Write-Host "`n--- Test 4: Fetch Full Report ---" -ForegroundColor Yellow
    try {
        $report = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports/$reportId" -Method Get
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
Write-Host "`n--- Test 5: Generate AAPL Report ---" -ForegroundColor Yellow
$aaplBody = @{
    ticker             = "AAPL"
    investment_horizon = "long_term"
    risk_tolerance     = "conservative"
    user_id            = "test-suite"
} | ConvertTo-Json

try {
    $aaplResponse = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" `
        -Method Post -ContentType "application/json" -Body $aaplBody
    Write-Host "  [PASS] AAPL report started. ID: $($aaplResponse.report_id)" -ForegroundColor Green
    $Pass++
} catch {
    Write-Host "  [FAIL] Could not start AAPL report." -ForegroundColor Red
    $Fail++
}

# --- Test 6: List All Reports ---
Write-Host "`n--- Test 6: List All Reports ---" -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $reports = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports" -Method Get
    $count = $reports.Count
    if ($count -ge 2) {
        Write-Host "  [PASS] Reports listed: $count reports found." -ForegroundColor Green
        $Pass++
    } else {
        Write-Host "  [FAIL] Expected at least 2 reports, found: $count" -ForegroundColor Red
        $Fail++
    }
} catch {
    Write-Host "  [FAIL] Could not list reports." -ForegroundColor Red
    $Fail++
}

# --- Summary ---
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Test Summary: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -gt 0) { "Red" } else { "Green" })
Write-Host "============================================`n" -ForegroundColor Cyan

if ($Fail -gt 0) { exit 1 }
```

#### scripts/test-multi-ticker.ps1

```powershell
# test-multi-ticker.ps1 — Batch test 5 tickers
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
            -Method Post -ContentType "application/json" -Body $body
        $reportId = $genResponse.report_id

        # Poll until complete
        $status = "pending"
        while ($status -ne "complete" -and $status -ne "error") {
            Start-Sleep -Seconds 5
            try {
                $statusResp = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/status/$reportId" -Method Get
                $status = $statusResp.status
            } catch {
                $status = "error"
            }
        }

        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)

        $report = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports/$reportId" -Method Get
        $rec = $report.recommendation
        $score = $report.conviction_score
        $tokens = $report.metadata.total_tokens

        Write-Host "  $ticker — $rec (score: $score) — $tokens tokens — ${elapsed}s" -ForegroundColor Green

        $Results += [PSCustomObject]@{
            Ticker         = $ticker
            Recommendation = $rec
            Score          = $score
            Tokens         = $tokens
            TimeSec        = $elapsed
        }
    } catch {
        Write-Host "  $ticker — FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $Results += [PSCustomObject]@{
            Ticker         = $ticker
            Recommendation = "ERROR"
            Score          = "-"
            Tokens         = "-"
            TimeSec        = "-"
        }
    }
    Write-Host ""
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Batch Results Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
$Results | Format-Table -AutoSize
```

#### scripts/clean.ps1

```powershell
# clean.ps1 — Remove build artifacts
$Root = Split-Path $PSScriptRoot -Parent

Write-Host "`nCleaning build artifacts..." -ForegroundColor Cyan

# Node.js artifacts
$nodeModules = Join-Path $Root "alpha-frontend\node_modules"
$nextDir = Join-Path $Root "alpha-frontend\.next"
if (Test-Path $nodeModules) { Remove-Item $nodeModules -Recurse -Force; Write-Host "  Removed: alpha-frontend\node_modules" }
if (Test-Path $nextDir) { Remove-Item $nextDir -Recurse -Force; Write-Host "  Removed: alpha-frontend\.next" }

# Python artifacts
Get-ChildItem -Path (Join-Path $Root "alpha-engine") -Recurse -Directory -Filter "__pycache__" |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force; Write-Host "  Removed: $($_.FullName)" }
Get-ChildItem -Path (Join-Path $Root "alpha-engine") -Recurse -Filter "*.pyc" |
    ForEach-Object { Remove-Item $_.FullName -Force }

Write-Host "  Done.`n" -ForegroundColor Green
```

#### Update README.md — Usage Section

Replace the Makefile usage instructions in the README with:

```markdown
## Running the Lab (Windows PowerShell)

All tasks are managed through `tasks.ps1` at the project root.

### First Time Setup

    .\tasks.ps1 setup          # Create .env files from templates
    # Edit .env with your API keys
    .\tasks.ps1 install        # Install Python + Node.js dependencies

### Start Services

    .\tasks.ps1 run-all        # Start both (engine background, frontend foreground)
    .\tasks.ps1 run-engine     # Start Python engine only
    .\tasks.ps1 run-frontend   # Start Next.js frontend only
    .\tasks.ps1 stop           # Stop all services

### Run Tests

    .\tasks.ps1 test-health    # Health check both services
    .\tasks.ps1 test-generate  # Generate a single NVDA report
    .\tasks.ps1 test-flow      # Full end-to-end flow test
    .\tasks.ps1 test-batch     # Batch test 5 tickers

### Maintenance

    .\tasks.ps1 clean          # Remove build artifacts
    .\tasks.ps1 help           # Show all available tasks

### PowerShell Execution Policy
If you get an execution policy error, run this once in an elevated PowerShell:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Produce ALL PowerShell scripts with complete content. Do NOT create a Makefile
or any bash/shell scripts.

### 8. README.md

```markdown
# 📊 Alpha Report Lab

**AI-Powered Investment Research • Dynatrace Instrumentation Demo**

A two-service application that generates institutional-grade Alpha Reports using
a multi-agent AI system, instrumented with Dynatrace OneAgent and OpenInference
for full AI Observability.

## Architecture

  Next.js Frontend (3000) ──HTTP──→ Python Alpha Engine (8000)
       │                                    │
       │ OneAgent                           │ OneAgent + OpenInference
       └──────────→ Dynatrace SaaS ←───────┘

## Prerequisites

- **Node.js 18+** — https://nodejs.org
- **Python 3.12+** — https://python.org
- **Dynatrace OneAgent** — installed locally on your machine
- **OpenAI API key** — or compatible endpoint
- **Dynatrace API token** — with `openTelemetryTrace.ingest` scope

## Quick Start

  1. Clone and setup:
     git clone <repo> && cd alpha-report-lab
     make setup

  2. Edit .env with your API keys

  3. Install dependencies:
     make install

  4. Start both services:
     make run-all

  5. Open browser: http://localhost:3000

## OneAgent Configuration

After installing OneAgent, enable these features in
Settings > Preferences > OneAgent features:

| Feature                           | Required | Default  |
|-----------------------------------|----------|----------|
| Python                            | Yes      | Enabled  |
| Node.js                           | Yes      | Enabled  |
| Python FastAPI                    | Yes      | Enabled  |
| Python OpenAI                     | Disable* | Enabled  |
| OpenTelemetry (Python) [Opt-In]   | Yes      | Disabled |
| W3C Trace Context                 | Yes      | Enabled  |

*Disable Python OpenAI to avoid duplicate spans with OpenInference

## Environment Variables

See .env.example for the complete reference.

## Testing

  make test-health       # Check both services
  make test-generate     # Generate a report for NVDA
  make test-full-flow    # End-to-end flow with polling
```

Produce ALL files with complete content.