# start-frontend.ps1 — Start Next.js Frontend
$Root = Split-Path $PSScriptRoot -Parent
$FrontendPath = Join-Path $Root "alpha-frontend"

$Port = if ($env:ALPHA_FRONTEND_PORT) { $env:ALPHA_FRONTEND_PORT } else { "3000" }

Write-Host "`n  Starting Alpha Frontend on port $Port..." -ForegroundColor Cyan
Write-Host "  Open http://localhost:$Port in your browser" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop.`n" -ForegroundColor DarkGray

Push-Location $FrontendPath
try {
    npm run dev
} finally {
    Pop-Location
}
