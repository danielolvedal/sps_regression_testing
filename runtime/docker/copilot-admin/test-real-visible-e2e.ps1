[CmdletBinding()]
param(
    [int]$HostRunnerPort = 8876,
    [int]$BackendPort = 8877,
    [int]$BrowserPort = 9322,
    [int]$TimeoutSeconds = 120,
    [switch]$RestartExisting,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$runner = Join-Path $repoRoot 'tools\source\copilot_admin_runner\copilot_admin_runner.py'
$backend = Join-Path $repoRoot 'tools\source\copilot_admin_control_plane\backend\app.py'
$frontend = Join-Path $repoRoot 'tools\source\copilot_admin_control_plane\frontend'
$tmpDir = Join-Path $repoRoot 'tmp\copilot_admin_control_plane\real_visible_e2e'
$isolatedRunnerStateDir = Join-Path $tmpDir 'runner_state'
$null = New-Item -ItemType Directory -Path $tmpDir -Force
$null = New-Item -ItemType Directory -Path $isolatedRunnerStateDir -Force

$hostRunnerUrl = "http://127.0.0.1:$HostRunnerPort"
$backendUrl = "http://127.0.0.1:$BackendPort"

if ($DryRun) {
    [ordered]@{
        status = 'dry_run'
        host_runner_url = $hostRunnerUrl
        backend_url = $backendUrl
        runner = $runner
        backend = $backend
        frontend = $frontend
        tmp_dir = $tmpDir
        isolated_runner_state_dir = $isolatedRunnerStateDir
        browser_port = $BrowserPort
        would_start_hidden_isolated_copilot = $true
        would_start_isolated_browser_port = $true
    } | ConvertTo-Json -Depth 10
    exit 0
}

function Invoke-JsonRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Uri,
        [object]$Body = $null
    )

    $headers = @{ 'X-Trace-Id' = 'real-visible-e2e' }
    $requestTimeout = [Math]::Max(10, [Math]::Min($TimeoutSeconds, 300))
    if ($null -eq $Body) {
        return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -TimeoutSec $requestTimeout
    }
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 10) -TimeoutSec $requestTimeout
}

function Wait-JsonEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [int]$Timeout = 30
    )

    $deadline = (Get-Date).AddSeconds($Timeout)
    $lastError = $null
    while ((Get-Date) -lt $deadline) {
        try {
            return Invoke-JsonRequest -Method GET -Uri $Uri
        } catch {
            $lastError = $_.Exception.Message
            Start-Sleep -Milliseconds 500
        }
    }
    throw "Timed out waiting for $Uri. Last error: $lastError"
}

$hostRunnerProcess = $null
$backendProcess = $null

try {
    $hostRunnerOut = Join-Path $tmpDir 'host-runner-api.out.log'
    $hostRunnerErr = Join-Path $tmpDir 'host-runner-api.err.log'
    $backendOut = Join-Path $tmpDir 'backend.out.log'
    $backendErr = Join-Path $tmpDir 'backend.err.log'

    $previousRunnerStateDir = $env:COPILOT_ADMIN_RUNNER_STATE_DIR
    $env:COPILOT_ADMIN_RUNNER_STATE_DIR = $isolatedRunnerStateDir
    $hostRunnerProcess = Start-Process -FilePath 'python' -ArgumentList @(
        $runner,
        'http-server',
        '--host', '127.0.0.1',
        '--port', [string]$HostRunnerPort
    ) -WorkingDirectory $repoRoot -RedirectStandardOutput $hostRunnerOut -RedirectStandardError $hostRunnerErr -PassThru

    $env:SPS_REPO_ROOT = $repoRoot.Path
    $env:COPILOT_ADMIN_FRONTEND_DIR = $frontend
    $env:COPILOT_ADMIN_HOST_RUNNER_URL = $hostRunnerUrl
    $env:COPILOT_ADMIN_BACKEND_HOST = '127.0.0.1'
    $env:COPILOT_ADMIN_BACKEND_PORT = [string]$BackendPort

    $backendProcess = Start-Process -FilePath 'python' -ArgumentList @(
        $backend,
        '--host', '127.0.0.1',
        '--port', [string]$BackendPort
    ) -WorkingDirectory $repoRoot -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru

    $null = Wait-JsonEndpoint -Uri "$hostRunnerUrl/health" -Timeout 30
    $null = Wait-JsonEndpoint -Uri "$backendUrl/api/health" -Timeout 30

    $preflight = Invoke-JsonRequest -Method GET -Uri "$hostRunnerUrl/status"
    $copilotAlreadyRunning = [bool]$preflight.copilot_session.running
    $browserAlreadyRunning = [bool]$preflight.browser_session.running
    $sessionJob = $null

    if ($copilotAlreadyRunning -and -not $RestartExisting) {
        $browserStart = $null
        if (-not $browserAlreadyRunning) {
            $browserStart = Invoke-JsonRequest -Method POST -Uri "$hostRunnerUrl/browser/start" -Body @{ port = $BrowserPort }
        }
        $sessionJob = [ordered]@{
            status = 'reused_existing'
            reason = 'Existing host-runner-owned Copilot session was already running; real E2E did not open another Copilot window.'
            browser_start = $browserStart
        }
    } else {
        $sessionPayload = @{
            restart_existing = [bool]$RestartExisting
            startup_model = 'gpt-5-mini'
            hidden_window = $true
            port = $BrowserPort
        }
        $sessionJob = Invoke-JsonRequest -Method POST -Uri "$backendUrl/api/session/start" -Body $sessionPayload
        if ($sessionJob.status -notin @('queued', 'running')) {
            throw "Session start job did not enter queued/running state: $($sessionJob | ConvertTo-Json -Depth 10)"
        }
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $status = $null
    while ((Get-Date) -lt $deadline) {
        $status = Invoke-JsonRequest -Method GET -Uri "$backendUrl/api/status"
        $copilotStatus = [string]$status.copilot_session.status
        $browserStatus = [string]$status.browser_session.status
        if (($copilotStatus -in @('running', 'user_input_required')) -and $browserStatus -eq 'running') {
            break
        }
        Start-Sleep -Seconds 2
    }

    if ($null -eq $status) {
        throw 'No backend status was returned.'
    }
    if ([string]$status.browser_session.status -ne 'running') {
        throw "Collaborative browser did not reach running state: $($status.browser_session | ConvertTo-Json -Depth 10)"
    }
    if ([string]$status.copilot_session.status -notin @('running', 'user_input_required')) {
        throw "Copilot session did not reach running/user_input_required state: $($status.copilot_session | ConvertTo-Json -Depth 10)"
    }

    $consoleBefore = Invoke-JsonRequest -Method GET -Uri "$backendUrl/api/copilot/console?limit=12000"
    if ([string]$consoleBefore.status -notin @('running', 'user_input_required')) {
        throw "Copilot console did not expose running/user_input_required state: $($consoleBefore | ConvertTo-Json -Depth 10)"
    }
    $queueDoneBefore = 0
    if ($null -ne $consoleBefore.input_queue -and $null -ne $consoleBefore.input_queue.done) {
        $queueDoneBefore = [int]$consoleBefore.input_queue.done
    }
    $consolePrompt = "Svara kort: copilot-console-real-e2e-$([guid]::NewGuid().ToString('N').Substring(0, 8))"
    $consoleInput = Invoke-JsonRequest -Method POST -Uri "$backendUrl/api/copilot/input" -Body @{
        text = $consolePrompt
        submit = $true
    }
    if (-not [bool]$consoleInput.accepted) {
        throw "Copilot console input was not accepted: $($consoleInput | ConvertTo-Json -Depth 10)"
    }
    $inputPath = $null
    if ($null -ne $consoleInput.response -and $null -ne $consoleInput.response.input -and $null -ne $consoleInput.response.input.input_path) {
        $inputPath = [string]$consoleInput.response.input.input_path
    }

    $consoleObserved = $false
    $consoleAfter = $null
    $consoleDeadline = (Get-Date).AddSeconds([Math]::Min($TimeoutSeconds, 90))
    while ((Get-Date) -lt $consoleDeadline) {
        $consoleAfter = Invoke-JsonRequest -Method GET -Uri "$backendUrl/api/copilot/console?limit=12000"
        $lastInjected = [string]$consoleAfter.last_injected_text
        $doneCount = 0
        if ($null -ne $consoleAfter.input_queue -and $null -ne $consoleAfter.input_queue.done) {
            $doneCount = [int]$consoleAfter.input_queue.done
        }
        $exactInputDone = $false
        if ($inputPath) {
            $exactInputDone = (Test-Path -LiteralPath "$inputPath.done")
        }
        if ($lastInjected -eq $consolePrompt -or $doneCount -gt $queueDoneBefore -or $exactInputDone -or ([string]$consoleAfter.transcript_tail).Contains($consolePrompt)) {
            $consoleObserved = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $consoleObserved) {
        throw "Copilot console input was accepted but not observed in node-pty state before timeout. Last console state: $($consoleAfter | ConvertTo-Json -Depth 10)"
    }

    $frontendEvent = Invoke-JsonRequest -Method POST -Uri "$backendUrl/api/frontend/events" -Body @{
        event = 'real_visible_e2e_observed'
        level = 'info'
        status = 'passed'
    }

    [ordered]@{
        status = 'passed'
        backend_url = $backendUrl
        host_runner_url = $hostRunnerUrl
        preflight_reused_existing = ($copilotAlreadyRunning -and $browserAlreadyRunning -and -not $RestartExisting)
        isolated_runner_state_dir = $isolatedRunnerStateDir
        hidden_copilot_session = $true
        browser_port = $BrowserPort
        session_job = $sessionJob
        copilot_session = $status.copilot_session
        browser_session = $status.browser_session
        copilot_console = [ordered]@{
            before = $consoleBefore
            input = $consoleInput
            after = $consoleAfter
            prompt = $consolePrompt
        }
        status_diode = $status.status_diode
        frontend_event = $frontendEvent
        logs = [ordered]@{
            host_runner_stdout = $hostRunnerOut
            host_runner_stderr = $hostRunnerErr
            backend_stdout = $backendOut
            backend_stderr = $backendErr
        }
    } | ConvertTo-Json -Depth 20
} finally {
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }
    if ($hostRunnerProcess -and -not $hostRunnerProcess.HasExited) {
        Stop-Process -Id $hostRunnerProcess.Id -Force
    }
    if ($null -eq $previousRunnerStateDir) {
        Remove-Item Env:\COPILOT_ADMIN_RUNNER_STATE_DIR -ErrorAction SilentlyContinue
    } else {
        $env:COPILOT_ADMIN_RUNNER_STATE_DIR = $previousRunnerStateDir
    }
}
