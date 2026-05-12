# setup.ps1 — Create .env files from examples
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  Alpha Report Lab - Setup" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

$Root = Split-Path $PSScriptRoot -Parent

$envMappings = @(
    @{ Source = "alpha-engine\.env.example";         Target = "alpha-engine\.env" },
    @{ Source = "alpha-frontend\.env.local.example"; Target = "alpha-frontend\.env.local" }
)

foreach ($mapping in $envMappings) {
    $src = Join-Path $Root $mapping.Source
    $dst = Join-Path $Root $mapping.Target
    if (-Not (Test-Path $dst)) {
        if (Test-Path $src) {
            Copy-Item $src $dst
            Write-Host "  Created: $($mapping.Target)" -ForegroundColor Green
        } else {
            Write-Host "  Warning: $($mapping.Source) not found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Exists:  $($mapping.Target) (skipped)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Yellow
Write-Host "    1. Edit alpha-engine\.env with your OpenAI API key and Dynatrace credentials"
Write-Host "    2. Run: .\tasks.ps1 install"
Write-Host "    3. Run: .\tasks.ps1 run-all"
Write-Host ""
