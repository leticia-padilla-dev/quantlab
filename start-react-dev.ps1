param(
    [switch]$ForceRestart
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopRoot = Join-Path $RepoRoot "desktop"
$HealthUrl = "http://127.0.0.1:8000/api/paper-sessions-health"
$Token = if ($env:QUANTLAB_LOCAL_API_TOKEN) { $env:QUANTLAB_LOCAL_API_TOKEN } else { "dev-token-123" }

function Test-ResearchUiHealth {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Get-PortOwner {
    Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

function Stop-PortOwner {
    param([object]$Connection)

    if (-not $Connection) {
        return
    }

    $process = Get-Process -Id $Connection.OwningProcess -ErrorAction SilentlyContinue
    if (-not $process) {
        return
    }

    Write-Host "Stopping process $($process.ProcessName) ($($process.Id)) on port 8000..."
    Stop-Process -Id $process.Id -Force
    Start-Sleep -Seconds 1
}

function Wait-ResearchUiHealth {
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        if (Test-ResearchUiHealth) {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

$env:QUANTLAB_LOCAL_API_TOKEN = $Token
$env:PYTHONPATH = "src"

Set-Location $RepoRoot
python -c "from quantlab.reporting.run_index import write_runs_index; print(write_runs_index('outputs/runs'))"

$hasHealthyBackend = Test-ResearchUiHealth
$portOwner = Get-PortOwner

if ($ForceRestart -and $portOwner) {
    Stop-PortOwner -Connection $portOwner
    $hasHealthyBackend = $false
    $portOwner = Get-PortOwner
}

if (-not $hasHealthyBackend) {
    if ($portOwner) {
        Stop-PortOwner -Connection $portOwner
    }

    $serverCommand = @"
`$env:QUANTLAB_LOCAL_API_TOKEN='$Token'
Set-Location '$RepoRoot'
python research_ui\server.py
"@

    Start-Process powershell -ArgumentList "-NoExit", "-Command", $serverCommand -WorkingDirectory $RepoRoot
}

if (-not (Wait-ResearchUiHealth)) {
    throw "research_ui did not respond with HTTP 200 at $HealthUrl after 30 seconds."
}

$desktopCommand = @"
`$env:QUANTLAB_LOCAL_API_TOKEN='$Token'
Set-Location '$DesktopRoot'
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $desktopCommand -WorkingDirectory $DesktopRoot

Write-Host "QuantLab React Desktop starting."
Write-Host "Backend health: $HealthUrl"
Write-Host "Renderer: React via npm run dev"
