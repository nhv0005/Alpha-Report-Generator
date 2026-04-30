# test-alpha-flow.ps1 — End-to-end Alpha Report flow test
$ErrorActionPreference = "Continue"
$EngineUrl = if ($env:ALPHA_ENGINE_PORT) { "http://localhost:$($env:ALPHA_ENGINE_PORT)" } else { "http://localhost:8000" }
$FrontendUrl = if ($env:ALPHA_FRONTEND_PORT) { "http://localhost:$($env:ALPHA_FRONTEND_PORT)" } else { "http://localhost:3000" }

$Pass = 0
$Fail = 0

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Alpha Report Lab - End-to-End Test Suite" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

Write-Host "--- Test 1: Health Checks ---" -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$EngineUrl/health" -Method Get -TimeoutSec 5 | Out-Null
    Write-Host "  [PASS] Alpha Engine: healthy" -ForegroundColor Green; $Pass++
} catch {
    Write-Host "  [FAIL] Alpha Engine: $($_.Exception.Message)" -ForegroundColor Red; $Fail++
}
try {
    Invoke-RestMethod -Uri "$FrontendUrl/api/health" -Method Get -TimeoutSec 5 | Out-Null
    Write-Host "  [PASS] Alpha Frontend: healthy" -ForegroundColor Green; $Pass++
} catch {
    Write-Host "  [FAIL] Alpha Frontend: $($_.Exception.Message)" -ForegroundColor Red; $Fail++
}

Write-Host "`n--- Test 2: Generate NVDA Report ---" -ForegroundColor Yellow
$body = @{ ticker="NVDA"; investment_horizon="short_term"; risk_tolerance="aggressive"; user_id="test-suite" } | ConvertTo-Json
$reportId = $null
try {
    $r = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 10
    $reportId = $r.report_id
    Write-Host "  [PASS] Started. ID: $reportId" -ForegroundColor Green; $Pass++
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red; $Fail++
}

if ($reportId) {
    Write-Host "`n--- Test 3: Poll Status (timeout: 180s) ---" -ForegroundColor Yellow
    $elapsed = 0; $status = "pending"
    while ($status -ne "complete" -and $status -ne "error" -and $elapsed -lt 180) {
        Start-Sleep -Seconds 5; $elapsed += 5
        try {
            $s = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/status/$reportId" -Method Get -TimeoutSec 5
            $status = $s.status
            Write-Host "  [$($elapsed)s] $status - $($s.current_step)" -ForegroundColor DarkGray
        } catch {}
    }
    if ($status -eq "complete") { Write-Host "  [PASS] Complete in $($elapsed)s" -ForegroundColor Green; $Pass++ }
    else { Write-Host "  [FAIL] Final: $status" -ForegroundColor Red; $Fail++ }

    Write-Host "`n--- Test 4: Fetch Full Report ---" -ForegroundColor Yellow
    try {
        $rep = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports/$reportId" -Method Get -TimeoutSec 10
        if ($rep.recommendation -and $rep.sections.Count -gt 0) {
            Write-Host "  [PASS] Retrieved." -ForegroundColor Green
            Write-Host "     Recommendation: $($rep.recommendation)"
            Write-Host "     Conviction:     $($rep.conviction_score) / 10"
            Write-Host "     Sections:       $($rep.sections.Count)"
            Write-Host "     Total Tokens:   $($rep.metadata.total_tokens)"
            $Pass++
        } else { Write-Host "  [FAIL] Incomplete" -ForegroundColor Red; $Fail++ }
    } catch { Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red; $Fail++ }
}

Write-Host "`n--- Test 5: Generate AAPL Report ---" -ForegroundColor Yellow
$aapl = @{ ticker="AAPL"; investment_horizon="long_term"; risk_tolerance="conservative"; user_id="test-suite" } | ConvertTo-Json
try {
    $a = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/generate" -Method Post -ContentType "application/json" -Body $aapl -TimeoutSec 10
    Write-Host "  [PASS] AAPL started: $($a.report_id)" -ForegroundColor Green; $Pass++
} catch { Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red; $Fail++ }

Write-Host "`n--- Test 6: List All Reports ---" -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $reports = Invoke-RestMethod -Uri "$EngineUrl/api/alpha/reports" -Method Get -TimeoutSec 10
    $count = if ($reports -is [array]) { $reports.Count } else { 1 }
    if ($count -ge 2) { Write-Host "  [PASS] $count reports" -ForegroundColor Green; $Pass++ }
    else { Write-Host "  [FAIL] Found: $count" -ForegroundColor Red; $Fail++ }
} catch { Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red; $Fail++ }

Write-Host "`n============================================" -ForegroundColor Cyan
$color = if ($Fail -gt 0) { "Red" } else { "Green" }
Write-Host "  Test Summary: $Pass passed, $Fail failed" -ForegroundColor $color
Write-Host "============================================`n" -ForegroundColor Cyan

if ($Fail -gt 0) { exit 1 }
