param(
    [int]$Port = 9222
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$runner = Join-Path $repoRoot 'tools\source\copilot_admin_runner\copilot_admin_runner.py'

$status = python $runner browser-status --port $Port | ConvertFrom-Json
if (-not $status.debug_version_endpoint) {
    throw 'browser-status did not return a debug endpoint.'
}

$dryRun = python $runner browser-start --port $Port --dry-run | ConvertFrom-Json
if ($dryRun.status -ne 'dry_run') {
    throw "Expected browser-start dry_run status, got '$($dryRun.status)'."
}
if (-not ($dryRun.script -like '*start-collaborative-stage-browser.ps1')) {
    throw 'browser-start dry-run did not point at the collaborative browser runtime script.'
}

[ordered]@{
    status = 'passed'
    browser_session_status = $status.status
    browser_start_status = $dryRun.status
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json -Depth 10
