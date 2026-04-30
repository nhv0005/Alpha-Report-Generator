# test-health.ps1 — Health check both services
$EngineUrl = if ($env:ALPHA_ENGINE_PORT) { "http://localhost:$($env:ALPHA_ENGINE_PORT)" } else { "http://localhost:8000" }
$FrontendUrl = if ($env:ALPHA_FRONTEND_PORT) { "http://localhost:$($env:ALPHA_FRONTEND_PORT)" } else { "http://localhost:3000" }

Write-Host "`n--- Alpha Engine Health ---" -ForegroundColor Cyan
try {
    $engineHealth = Invoke-RestMethod -Uri "$EngineUrl/health" -Method Get -TimeoutSec 5
    $engineHealth | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Green
} catch {
    Write-Host "  UNREACHABLE: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n--- Alpha Frontend Health ---" -ForegroundColor Cyan
try {
    $frontendHealth = Invoke-RestMethod -Uri "$FrontendUrl/api/health" -Method Get -TimeoutSec 5
    $frontendHealth | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Green
} catch {
    Write-Host "  UNREACHABLE: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""
