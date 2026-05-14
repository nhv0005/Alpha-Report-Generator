# dt-events.ps1 — Dynatrace Events API v2 helper for task scripts.
#
# Dot-source this from a task script:
#     . "$PSScriptRoot\dt-events.ps1"
#
# Then wrap work with:
#     Invoke-WithDtEvent -TaskName "install" -ScriptBlock { & "$ScriptsDir\install.ps1" }
#
# Reads DT_ENV_URL and DT_API_TOKEN from process env, falling back to
# alpha-engine\.env. The API token MUST have the `events.ingest` scope.
# All event pushes are best-effort: failures never break the wrapped task.

$script:DtEventsRoot = Split-Path $PSScriptRoot -Parent

function Get-DtConfig {
    $envUrl   = $env:DT_ENV_URL
    $apiToken = $env:DT_API_TOKEN

    if (-not $envUrl -or -not $apiToken) {
        $envFile = Join-Path $script:DtEventsRoot "alpha-engine\.env"
        if (Test-Path $envFile) {
            Get-Content $envFile | ForEach-Object {
                if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+)\s*$') {
                    $key = $matches[1].Trim()
                    $val = $matches[2].Trim()
                    if ($key -eq "DT_ENV_URL"   -and -not $envUrl)   { $envUrl   = $val }
                    if ($key -eq "DT_API_TOKEN" -and -not $apiToken) { $apiToken = $val }
                }
            }
        }
    }

    return @{ EnvUrl = $envUrl; ApiToken = $apiToken }
}

function Send-DtEvent {
    param(
        [Parameter(Mandatory=$true)][string]$Title,
        [Parameter(Mandatory=$true)][ValidateSet("CUSTOM_INFO","CUSTOM_DEPLOYMENT","CUSTOM_CONFIGURATION","ERROR_EVENT")][string]$EventType,
        [hashtable]$Properties = @{}
    )

    $cfg = Get-DtConfig
    if (-not $cfg.EnvUrl -or -not $cfg.ApiToken) {
        Write-Host "  [dt-events] DT_ENV_URL/DT_API_TOKEN not set — skipping push." -ForegroundColor DarkGray
        return
    }

    $endpoint = ($cfg.EnvUrl.TrimEnd("/")) + "/api/v2/events/ingest"

    # Stringify all property values (Events API requires string values)
    $propStrings = @{}
    foreach ($k in $Properties.Keys) { $propStrings[$k] = "$($Properties[$k])" }

    $body = @{
        eventType  = $EventType
        title      = $Title
        properties = $propStrings
    } | ConvertTo-Json -Depth 4 -Compress

    try {
        Invoke-RestMethod -Method Post -Uri $endpoint `
            -Headers @{ Authorization = "Api-Token $($cfg.ApiToken)"; "Content-Type" = "application/json" } `
            -Body $body -TimeoutSec 10 | Out-Null
        Write-Host "  [dt-events] $EventType pushed: $Title" -ForegroundColor DarkGray
    } catch {
        Write-Host "  [dt-events] push failed (non-fatal): $($_.Exception.Message)" -ForegroundColor DarkYellow
    }
}

function Invoke-WithDtEvent {
    param(
        [Parameter(Mandatory=$true)][string]$TaskName,
        [Parameter(Mandatory=$true)][scriptblock]$ScriptBlock
    )

    $hostName = [System.Net.Dns]::GetHostName()
    $userName = $env:USERNAME
    $startIso = (Get-Date).ToUniversalTime().ToString("o")

    $baseProps = @{
        "task.name"      = $TaskName
        "task.host"      = $hostName
        "task.user"      = $userName
        "task.os"        = "windows"
        "task.shell"     = "powershell"
        "lab.component"  = "tasks-runner"
        "lab.script"     = "tasks.ps1"
        "task.start_utc" = $startIso
    }

    Send-DtEvent -EventType "CUSTOM_INFO" `
                 -Title "alpha-report-lab task: $TaskName started" `
                 -Properties ($baseProps + @{ "task.status" = "started" })

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $exitCode = 0
    $errMsg = $null

    try {
        & $ScriptBlock
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { $exitCode = $LASTEXITCODE }
    } catch {
        $exitCode = 1
        $errMsg = $_.Exception.Message
        Write-Host "  [dt-events] task '$TaskName' threw: $errMsg" -ForegroundColor Red
    } finally {
        $sw.Stop()
        $durationSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        $status   = if ($exitCode -eq 0) { "success" } else { "failure" }
        $evtType  = if ($exitCode -eq 0) { "CUSTOM_INFO" } else { "ERROR_EVENT" }
        $endProps = $baseProps + @{
            "task.status"           = $status
            "task.exit_code"        = $exitCode
            "task.duration_seconds" = $durationSec
            "task.end_utc"          = (Get-Date).ToUniversalTime().ToString("o")
        }
        if ($errMsg) { $endProps["task.error"] = $errMsg }

        Send-DtEvent -EventType $evtType `
                     -Title ("alpha-report-lab task: {0} {1} ({2}s)" -f $TaskName, $status, $durationSec) `
                     -Properties $endProps
    }

    if ($exitCode -ne 0) { exit $exitCode }
}
