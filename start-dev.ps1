$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopRoot = Join-Path $RepoRoot "desktop"
$Token = if ($env:QUANTLAB_LOCAL_API_TOKEN) { $env:QUANTLAB_LOCAL_API_TOKEN } else { "dev-token-123" }

$env:QUANTLAB_LOCAL_API_TOKEN = $Token
$env:PYTHONPATH = "src"

Set-Location $RepoRoot
python -c "from quantlab.reporting.run_index import write_runs_index; print(write_runs_index('outputs/runs'))"

$serverCommand = @"
`$env:QUANTLAB_LOCAL_API_TOKEN='$Token'
Set-Location '$RepoRoot'
python research_ui\server.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $serverCommand -WorkingDirectory $RepoRoot

Start-Sleep -Seconds 2

$desktopCommand = @"
`$env:QUANTLAB_LOCAL_API_TOKEN='$Token'
Set-Location '$DesktopRoot'
npm run start:legacy
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $desktopCommand -WorkingDirectory $DesktopRoot
