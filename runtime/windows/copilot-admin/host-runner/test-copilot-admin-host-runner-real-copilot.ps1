param(
    [switch]$RestartExisting,
    [switch]$LogInput,
    [string]$StartupModel = 'gpt-5-mini',
    [switch]$AllowAll = $true,
    [int]$StartupTimeoutSeconds = 45,
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
    $before = Invoke-RunnerJson -Arguments @($runner, 'copilot-status')
    if (-not $before.running) {
        $startArgs = @($runner, 'copilot-start')
        if ($RestartExisting) { $startArgs += '--restart-existing' }
        if ($LogInput) { $startArgs += '--log-input' }
        if ($StartupModel) { $startArgs += @('--startup-model', $StartupModel) }
        if (-not $AllowAll) { $startArgs += '--no-allow-all' }
        $startResult = Invoke-RunnerJson -Arguments $startArgs
        if ($startResult.status -ne 'started') {
            throw "Expected copilot-start status 'started', got '$($startResult.status)'."
        }
        $startedHere = $true
    } elseif ($RestartExisting) {
        $startArgs = @($runner, 'copilot-start', '--restart-existing')
        if ($LogInput) { $startArgs += '--log-input' }
        if ($StartupModel) { $startArgs += @('--startup-model', $StartupModel) }
        if (-not $AllowAll) { $startArgs += '--no-allow-all' }
        $startResult = Invoke-RunnerJson -Arguments $startArgs
        if ($startResult.status -ne 'started') {
            throw "Expected restarted copilot-start status 'started', got '$($startResult.status)'."
        }
        $startedHere = $true
    }

    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    do {
        $status = Invoke-RunnerJson -Arguments @($runner, 'copilot-status')
        if ($status.running -and $status.state_path -and $status.transcript_path -and $status.input_queue.queue_dir) {
            break
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    if (-not $status.running) {
        throw 'The real node-pty Copilot session did not report running state.'
    }
    if (-not (Test-Path -LiteralPath $status.state_path)) {
        throw 'The node-pty Copilot state file was not written.'
    }
    if (-not $status.log_path) {
        throw 'The node-pty Copilot status did not expose a JSONL log path.'
    }

    $stopResult = $null
    if ($startedHere) {
        $stopResult = Invoke-RunnerJson -Arguments @($runner, 'copilot-stop', '--timeout-seconds', ([string]$StopTimeoutSeconds))
        if ($stopResult.status -ne 'stopped') {
            throw "Expected copilot-stop status 'stopped', got '$($stopResult.status)'."
        }
    }

    [ordered]@{
        status = 'passed'
        mode = if ($startedHere) { 'started_and_stopped_real_copilot' } else { 'observed_existing_real_copilot' }
        start_status = if ($startResult) { $startResult.status } else { $null }
        observed_status = $status.status
        stopped_status = if ($stopResult) { $stopResult.status } else { $null }
        state_path = $status.state_path
        transcript_path = $status.transcript_path
        log_path = $status.log_path
        checked_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 10
} catch {
    if ($startedHere) {
        try {
            python $runner copilot-stop --timeout-seconds $StopTimeoutSeconds | Out-Null
        } catch {
            Write-Warning "Cleanup copilot-stop failed: $($_.Exception.Message)"
        }
    }
    throw
}
