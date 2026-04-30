# tasks.ps1 — Alpha Report Lab Task Runner
# Usage: .\tasks.ps1 <task>

param(
    [Parameter(Position=0)]
    [ValidateSet(
        "setup", "install",
        "run-engine", "run-frontend", "run-all", "start", "stop", "stop-all",
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
    "start"         { & "$ScriptsDir\start-all.ps1" }
    "stop"          { & "$ScriptsDir\stop-all.ps1" }
    "stop-all"      { & "$ScriptsDir\stop-all.ps1" }
    "test-health"   { & "$ScriptsDir\test-health.ps1" }
    "test-generate" { & "$ScriptsDir\test-generate.ps1" }
    "test-flow"     { & "$ScriptsDir\test-alpha-flow.ps1" }
    "test-batch"    { & "$ScriptsDir\test-multi-ticker.ps1" }
    "clean"         { & "$ScriptsDir\clean.ps1" }
    "help" {
        Write-Host ""
        Write-Host "=========================================" -ForegroundColor Cyan
        Write-Host "  Alpha Report Lab - Task Runner" -ForegroundColor Cyan
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
        Write-Host "    start          Start both (engine bg, frontend fg)"
        Write-Host "    stop           Stop all running services"
        Write-Host "    stop-all       Stop all services and background jobs"
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
