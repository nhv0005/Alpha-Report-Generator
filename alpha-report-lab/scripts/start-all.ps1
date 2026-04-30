# start-all.ps1 — Start both services (engine bg, frontend fg)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$EnginePath = Join-Path $Root "alpha-engine"
$FrontendPath = Join-Path $Root "alpha-frontend"

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  Alpha Report Lab - Starting Services" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

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

Write-Host "  Starting Alpha Engine on port $EnginePort (background)..." -ForegroundColor Yellow
$engineJob = Start-Job -ScriptBlock {
    param($path, $port)
    Set-Location $path
    uvicorn app.main:app --port $port --reload
} -ArgumentList $EnginePath, $EnginePort

Write-Host "  Engine Job ID: $($engineJob.Id)" -ForegroundColor DarkGray

Write-Host "  Waiting for engine to be ready..." -ForegroundColor DarkGray
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$EnginePort/health" -Method Get -ErrorAction SilentlyContinue
        if ($response) {
            Write-Host "  Alpha Engine is ready.`n" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {}
}

if (-Not $ready) {
    Write-Host "  Warning: Engine may not be ready yet. Check with:" -ForegroundColor Yellow
    Write-Host "    Receive-Job -Id $($engineJob.Id)" -ForegroundColor DarkGray
}

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
