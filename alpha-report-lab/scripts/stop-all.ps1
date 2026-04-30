# stop-all.ps1 — Stop all running services
Write-Host "`nStopping Alpha Report Lab services..." -ForegroundColor Cyan

$pythonProcs = Get-Process -Name "python", "python3", "uvicorn" -ErrorAction SilentlyContinue
if ($pythonProcs) {
    $pythonProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Alpha Engine stopped." -ForegroundColor Green
} else {
    Write-Host "  Alpha Engine was not running." -ForegroundColor DarkGray
}

$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    $nodeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Alpha Frontend stopped." -ForegroundColor Green
} else {
    Write-Host "  Alpha Frontend was not running." -ForegroundColor DarkGray
}

$bgJobs = Get-Job | Where-Object { $_.State -eq "Running" }
if ($bgJobs) {
    $bgJobs | Stop-Job -PassThru | Remove-Job -Force
    Write-Host "  Background jobs cleaned up." -ForegroundColor Green
} else {
    Write-Host "  No background jobs found." -ForegroundColor DarkGray
}

Write-Host "  Done.`n" -ForegroundColor Cyan
