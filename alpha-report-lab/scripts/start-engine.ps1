# start-engine.ps1 — Start Python Alpha Engine
$Root = Split-Path $PSScriptRoot -Parent
$EnginePath = Join-Path $Root "alpha-engine"

$envFile = Join-Path $EnginePath ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)\s*$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

$Port = if ($env:ALPHA_ENGINE_PORT) { $env:ALPHA_ENGINE_PORT } else { "8000" }

Write-Host "`n  Starting Alpha Engine on port $Port..." -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop.`n" -ForegroundColor DarkGray

Push-Location $EnginePath
try {
    uvicorn app.main:app --port $Port --reload
} finally {
    Pop-Location
}
