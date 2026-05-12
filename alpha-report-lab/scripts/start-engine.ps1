# start-engine.ps1 — Start Python Alpha Engine (in venv)
$Root = Split-Path $PSScriptRoot -Parent
$EnginePath = Join-Path $Root "alpha-engine"
$VenvPath = Join-Path $EnginePath ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

$envFile = Join-Path $EnginePath ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)\s*$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

# Ensure virtual environment exists
if (-Not (Test-Path $VenvPython)) {
    Write-Host "`n  Creating Python virtual environment at .venv..." -ForegroundColor Yellow
    python -m venv $VenvPath
    if (-Not (Test-Path $VenvPython)) {
        Write-Host "  Failed to create venv. Is Python installed?" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Installing requirements into venv..." -ForegroundColor Yellow
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r (Join-Path $EnginePath "requirements.txt")
}

# Activate venv for this process
$env:VIRTUAL_ENV = $VenvPath
$env:PATH = (Join-Path $VenvPath "Scripts") + ";" + $env:PATH

$Port = if ($env:ALPHA_ENGINE_PORT) { $env:ALPHA_ENGINE_PORT } else { "8000" }

Write-Host "`n  Starting Alpha Engine on port $Port (venv)..." -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop.`n" -ForegroundColor DarkGray

Push-Location $EnginePath
try {
    & $VenvPython -m uvicorn app.main:app --port $Port --reload
} finally {
    Pop-Location
}
