# install.ps1 — Install all dependencies
$Root = Split-Path $PSScriptRoot -Parent

Write-Host "`nInstalling Python dependencies..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "alpha-engine")
try {
    pip install -r requirements.txt
} finally {
    Pop-Location
}

Write-Host "`nInstalling Node.js dependencies..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "alpha-frontend")
try {
    npm install
} finally {
    Pop-Location
}

Write-Host "`n  All dependencies installed." -ForegroundColor Green
