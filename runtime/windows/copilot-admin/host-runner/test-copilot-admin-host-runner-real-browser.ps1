param(
    [int]$Port = 9322,
    [int]$StartupTimeoutSeconds = 30,
    [int]$StopTimeoutSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
$runner = Join-Path $repoRoot 'tools\source\copilot_admin_runner\copilot_admin_runner.py'
$startedHere = $false
$startResult = $null

function Invoke-RunnerJson([string[]]$Arguments) {
    $json = python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Host runner failed for arguments '$($Arguments -join ' ')'."
    }
    return $json | ConvertFrom-Json
}

try {
    $before = Invoke-RunnerJson -Arguments @($runner, 'browser-status', '--port', ([string]$Port))
    if (-not $before.running) {
        $startResult = Invoke-RunnerJson -Arguments @($runner, 'browser-start', '--port', ([string]$Port))
        if ($startResult.status -ne 'started') {
            throw "Expected browser-start status 'started', got '$($startResult.status)'."
        }
        $startedHere = $true
    }

    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    do {
        $status = Invoke-RunnerJson -Arguments @($runner, 'browser-status', '--port', ([string]$Port))
        if ($status.running -and $status.debug_version_endpoint -and $status.debug_targets_endpoint) {
            break
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    if (-not $status.running) {
        throw 'The real collaborative browser session did not expose a debug endpoint.'
    }
    if (-not (Test-Path -LiteralPath $status.state_path)) {
        throw 'The collaborative browser state file was not written.'
    }

    $stopResult = $null
    if ($startedHere) {
        $stopResult = Invoke-RunnerJson -Arguments @($runner, 'browser-stop', '--port', ([string]$Port), '--timeout-seconds', ([string]$StopTimeoutSeconds))
        if ($stopResult.status -ne 'stopped') {
            throw "Expected browser-stop status 'stopped', got '$($stopResult.status)'."
        }
    }

    [ordered]@{
        status = 'passed'
        mode = if ($startedHere) { 'started_and_stopped_real_browser' } else { 'observed_existing_real_browser' }
        port = $Port
        start_status = if ($startResult) { $startResult.status } else { $null }
        observed_status = $status.status
        stopped_status = if ($stopResult) { $stopResult.status } else { $null }
        state_path = $status.state_path
        debug_version_endpoint = $status.debug_version_endpoint
        checked_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 10
} catch {
    if ($startedHere) {
        try {
            python $runner browser-stop --port $Port --timeout-seconds $StopTimeoutSeconds | Out-Null
        } catch {
            Write-Warning "Cleanup browser-stop failed: $($_.Exception.Message)"
        }
    }
    throw
}
