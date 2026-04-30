# test-multi-ticker.ps1 — Batch test 5 tickers
$ErrorActionPreference = "Continue"
$EngineUrl = if ($env:ALPHA_ENGINE_PORT) { "http://localhost:$($env:ALPHA_ENGINE_PORT)" } else { "http://localhost:8000" }
$Tickers = @("NVDA", "AAPL", "TSLA", "JPM", "MSFT")

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Multi-Ticker Alpha Report Batch Test" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

$Results = @()

foreach ($ticker in $Tickers) {
    Write-Host "--- $ticker ---" -ForegroundColor Yellow
    $startTime = Get-Date
    $body = @{ ticker=$ticker; investment_horizon="medium_term"; risk_tolerance="moderate"; user_id="batch-test" } | ConvertTo-Json
    try {
        $gen = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 10
        $reportId = $gen.report_id
        $status = "pending"; $elapsed = 0
        while ($status -ne "complete" -and $status -ne "error" -and $elapsed -lt 240) {
            Start-Sleep -Seconds 5; $elapsed += 5
            try { $s = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/status/$reportId" -Method Get -TimeoutSec 5; $status = $s.status } catch {}
        }
        $actualElapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
        if ($status -eq "complete") {
            $rep = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports/$reportId" -Method Get -TimeoutSec 10
            Write-Host "  $ticker - $($rep.recommendation) (conv $($rep.conviction_score)) - $($rep.metadata.total_tokens) tokens - $($actualElapsed)s" -ForegroundColor Green
            $Results += [PSCustomObject]@{
                Ticker = $ticker; Recommendation = $rep.recommendation
                Score = $rep.conviction_score; Tokens = $rep.metadata.total_tokens
                "Time(s)" = $actualElapsed
            }
        } else {
            Write-Host "  $ticker - FAILED ($status, $($actualElapsed)s)" -ForegroundColor Red
            $Results += [PSCustomObject]@{ Ticker=$ticker; Recommendation="ERROR"; Score="-"; Tokens="-"; "Time(s)"=$actualElapsed }
        }
    } catch {
        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
        Write-Host "  $ticker - $($_.Exception.Message)" -ForegroundColor Red
        $Results += [PSCustomObject]@{ Ticker=$ticker; Recommendation="ERROR"; Score="-"; Tokens="-"; "Time(s)"=$elapsed }
    }
    Write-Host ""
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Batch Results Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
$Results | Format-Table -AutoSize

$totalTokens = ($Results | Where-Object { $_.Tokens -ne "-" } | Measure-Object -Property Tokens -Sum).Sum
$totalTime = ($Results | Where-Object { $_."Time(s)" -ne "-" } | Measure-Object -Property "Time(s)" -Sum).Sum
Write-Host "  Total Tokens: $totalTokens" -ForegroundColor Yellow
Write-Host "  Total Time:   $($totalTime)s" -ForegroundColor Yellow
Write-Host ""
