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
        -Method Post -ContentType "application/json" -Body $body

    Write-Host "  Report generation started." -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3 | Write-Host
    Write-Host "`n  Track status with:" -ForegroundColor Yellow
    Write-Host "    Invoke-RestMethod $EngineUrl/api/alpha/status/$($response.report_id)" -ForegroundColor DarkGray
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""
