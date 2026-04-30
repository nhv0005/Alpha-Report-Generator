# clean.ps1 — Remove build artifacts
$Root = Split-Path $PSScriptRoot -Parent

Write-Host "`nCleaning build artifacts..." -ForegroundColor Cyan

$nodeModules = Join-Path $Root "alpha-frontend\node_modules"
$nextDir = Join-Path $Root "alpha-frontend\.next"
if (Test-Path $nodeModules) { Remove-Item $nodeModules -Recurse -Force; Write-Host "  Removed: alpha-frontend\node_modules" }
if (Test-Path $nextDir) { Remove-Item $nextDir -Recurse -Force; Write-Host "  Removed: alpha-frontend\.next" }

Get-ChildItem -Path (Join-Path $Root "alpha-engine") -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force; Write-Host "  Removed: $($_.FullName)" }
Get-ChildItem -Path (Join-Path $Root "alpha-engine") -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item $_.FullName -Force }

Write-Host "  Done.`n" -ForegroundColor Green
